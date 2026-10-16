"""Client HTTP (sans navigateur) du RAA de la Seine-et-Marne.

Le site utilise un formulaire avec un menu déroulant <select name="Liste-liste-docs">.
L'envoi du formulaire (POST) génère un panneau de téléchargement contenant le lien
du PDF et une date générée par le CMS (span.fr-link__detail), source de vérité.
"""

import logging
import re
import time
from urllib.parse import unquote, urljoin

import requests
from bs4 import BeautifulSoup

from src.raa_client import (
    DOWNLOAD_LINK_SELECTOR,
    RaaError,
    RaaHttpClient,
    _DATE_FR,
    MONTHS_FR,
    link_day_month,
    parse_day_month,
    parse_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)

SeineEtMarneRaaError = RaaError


def label_day_month(label, value=""):
    """Extrait (jour, mois) d'une option du menu.
    
    Le format est typiquement 'RAA n°D77-30-09-2026.pdf'.
    """
    match = _DATE_FR.search(label.replace("-", " "))
    if match:
        month = MONTHS_FR.get(match.group(2).lower())
        if month:
            return (int(match.group(1)), int(month))
    
    # Repli sur parsing numérique simple (JJ-MM-YYYY)
    num_match = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", label)
    if num_match:
        day, month = int(num_match.group(1)), int(num_match.group(2))
        if 1 <= day <= 31 and 1 <= month <= 12:
            return (day, month)
            
    return None


def label_month(label, value=""):
    """Extrait le mois (« MM ») d'une option du menu."""
    day_month = label_day_month(label, value)
    if day_month is None:
        return None
    return f"{day_month[1]:02d}"


class SeineEtMarneRaaClient(RaaHttpClient):
    """Client HTTP (sans navigateur) du RAA de la Seine-et-Marne."""

    def __init__(self, base_url, year=None, timeout=60):
        super().__init__(base_url, timeout)
        if year is not None:
            # URL attendue: /Publications/Recueils-des-actes-administratifs-RAA/RAA-YYYY
            self.base_url = urljoin(self.base_url, f"/Publications/Recueils-des-actes-administratifs-RAA/RAA-{year}")

    def _post(self, payload, max_retries=3):
        last_exc = None
        for attempt in range(max_retries + 1):
            self._throttle()
            try:
                response = self.session.post(
                    self.base_url, data=payload, timeout=self.timeout
                )
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < max_retries:
                    delay = self._retry_delay(exc, 10)
                    logger.warning(
                        "Échec du POST pour %s (tentative %d/%d) : %s",
                        payload.get("Liste-liste-docs"), attempt + 1,
                        max_retries + 1, exc,
                    )
                    time.sleep(delay)
        raise RaaError(
            f"Échec du POST pour {payload.get('Liste-liste-docs')} "
            f"après {max_retries + 1} tentatives"
        ) from last_exc

    def list_documents(self):
        """Retourne la liste des documents du menu annuel : (value, label, mois)."""
        response = self._get(self.base_url)
        soup = BeautifulSoup(response.text, "html.parser")
        select = soup.select_one("select#Liste-liste-docs")
        if select is None:
            raise RaaError(
                f"Formulaire « Liste-liste-docs » introuvable sur {self.base_url}"
            )
        return self._menu_documents(select)

    @staticmethod
    def _menu_documents(select):
        """Documents du menu : (value, label, mois pré-filtre)."""
        documents = []
        for option in select.find_all("option"):
            value = (option.get("value") or "").strip()
            if not value or value == "":
                continue
            label = option.get("title") or option.get_text(strip=True)
            documents.append((value, label, label_month(label, value)))
        return documents

    def get_download_url(self, doc_value):
        """POST le champ « Liste-liste-docs » et retourne (url_pdf, jour_mois)."""
        response = self._post({"Liste-liste-docs": doc_value})
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Recherche du lien de téléchargement
        link = soup.find("a", class_="fr-link--download")
        if link is None or not link.get("href"):
            raise RaaError(
                f"Lien de téléchargement introuvable pour {doc_value}"
            )
            
        url = urljoin(self.base_url, link["href"])
        day_month = None
        detail = link.find("span", class_="fr-link__detail")
        if detail is not None:
            day_month = parse_day_month(detail.get_text(strip=True))
            if day_month is None:
                logger.warning(
                    "Date CMS inexploitable pour %s : %s",
                    doc_value, detail.get_text(strip=True),
                )
        return url, day_month

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique croissant."""
        documents = self.list_documents()
        candidates = [(v, l) for v, l, m in documents if m == month]
        sweep = [(v, l) for v, l, m in documents if m is None]
        
        if not candidates and not sweep:
            logger.info("Aucun document trouvé pour le mois %s.", month)
            return []
            
        results = []
        for value, label in candidates + sweep:
            try:
                url, span_day_month = self.get_download_url(value)
                span_month = (
                    f"{span_day_month[1]:02d}" if span_day_month is not None else None
                )
                if span_month is not None and span_month != month:
                    logger.warning(
                        "Exclu : mois CMS %s différent du mois cible %s : %s",
                        span_month, month, label,
                    )
                    continue
                
                # Jour pour le tri : CMS d'abord, libellé en repli
                if span_day_month is not None:
                    sort_day = span_day_month[0]
                else:
                    label_date = label_day_month(label, value)
                    sort_day = label_date[0] if label_date is not None else 99
                
                if span_month is None:
                    logger.warning("Date non vérifiée (panneau sans date) : %s", label)
                else:
                    logger.info("Lien trouvé (vérifié %s) : %s", span_month, url)
                
                name = value.split("/")[-1] + ".pdf"
                results.append((sort_day, name, url))
            except RaaError as e:
                logger.error("Erreur lors de la récupération de %s : %s", label, e)
                continue

        results.sort(key=lambda item: (item[0], item[1]))
        return [(url, name) for _, name, url in results]
