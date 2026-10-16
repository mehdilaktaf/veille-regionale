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
    link_day_month,
    parse_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)

class IsereRaaClient(RaaHttpClient):
    """Client HTTP du RAA de l'Isère.
    Page annuelle avec un select dont le POST génère le lien de téléchargement.
    """

    def __init__(self, base_url, year=None, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

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
                        payload.get("select_name"), attempt + 1,
                        max_retries + 1, exc,
                    )
                    time.sleep(delay)
        raise RaaError(
            f"Échec du POST pour {payload.get('select_name')} "
            f"après {max_retries + 1} tentatives"
        ) from last_exc

    def list_documents(self):
        """Retourne la liste des documents du menu annuel :
        (value, label, jour_mois).
        """
        response = self._get(self.base_url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Le nom du select contient l'année et peut varier légèrement
        # On cherche le select qui contient 'liste-docs' dans son nom
        select = soup.find("select", id=lambda x: x and "liste-docs" in x)
        if select is None:
            raise RaaError(
                f"Formulaire de sélection introuvable sur {self.base_url}"
            )
        
        self.select_name = select["name"]
        
        documents = []
        for option in select.find_all("option"):
            value = (option.get("value") or "").strip()
            if not value:
                continue
            label = option.get("title") or option.get_text(strip=True)
            
            # On utilise parse_day_month pour extraire la date du libellé
            # Exemple : "Recueil des actes administratifs spécial n°362 du 15 septembre 2026"
            day_month = parse_day_month(label)
            documents.append((value, label, day_month))
            
        return documents

    def get_download_url(self, doc_value):
        """POST la valeur sélectionnée et retourne (url_pdf, jour_mois_cms)."""
        response = self._post({self.select_name: doc_value})
        soup = BeautifulSoup(response.text, "html.parser")
        
        link = soup.select_one(DOWNLOAD_LINK_SELECTOR)
        if link is None or not link.get("href"):
            raise RaaError(
                f"Lien de téléchargement introuvable pour {doc_value}"
            )
            
        url = urljoin(self.base_url, link["href"])
        day_month = link_day_month(link)
        
        return url, day_month

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique croissant."""
        documents = self.list_documents()
        
        # Pré-filtre sur le libellé du menu
        candidates = [(v, l) for v, l, dm in documents if dm and f"{dm[1]:02d}" == month]
        sweep = [(v, l) for v, l, dm in documents if dm is None]
        
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
                
                # Jour pour le tri
                if span_day_month is not None:
                    sort_day = span_day_month[0]
                else:
                    # Repli sur le libellé
                    dm = parse_day_month(label)
                    sort_day = dm[0] if dm is not None else 99
                
                if span_month is None:
                    logger.warning("Date non vérifiée (panneau sans date) : %s", label)
                else:
                    logger.info("Lien trouvé (vérifié %s) : %s", span_month, url)
                
                name = value.split("/")[-1]
                if not name.lower().endswith(".pdf"):
                    name += ".pdf"
                results.append((sort_day, name, url))
            except RaaError as e:
                logger.error("Erreur lors de la récupération de %s : %s", label, e)
                continue
                
        results.sort(key=lambda item: (item[0], item[1]))
        return [(url, name) for _, name, url in results]
