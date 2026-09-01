"""Client HTTP (sans navigateur) du RAA de la Vendée.

Le site génère le lien de téléchargement en réponse à un POST vers la
même URL que la page annuelle, avec le champ « Liste-liste-docs ».
Le panneau de téléchargement (span.fr-link__detail) porte une date
générée par le CMS : c'est la source de vérité pour le mois d'un
document, les libellés du menu comportant des fautes de saisie
(« 20/08/026 », « 19//06/2026 », dates absentes).
"""

import logging
import re
import time

import requests
from bs4 import BeautifulSoup

from raa_client import (
    RaaError,
    RaaHttpClient,
    _DATE_FR,
    MONTHS_FR,
    parse_day_month,
    parse_month,
)

logger = logging.getLogger(__name__)

VendeeRaaError = RaaError

# Ancrage « publié » (éventuellement suivi de « le ») dans un libellé ;
# capture le texte qui suit, là où se trouve la date.
_PUBLIE_LABEL = re.compile(r"publi[ée]?\s*(?:le)?\s*(.+)", re.IGNORECASE)

# Mêmes ancrages dans la valeur (slug) : « publie-le-20-08-026 »,
# « publie-17-08-2026 ».
_PUBLIE_SLUG = re.compile(
    r"publie(?:-le)?-(\d{1,2})-(\d{1,2})(?:-(\d{2,4}))?", re.IGNORECASE
)


def label_day_month(label, value=""):
    """Extrait (jour, mois) d'une option du menu (libellé + valeur).

    Le libellé n'est parsé qu'ancré sur « publié » : un parsing libre
    daterait faussement des numéros de document (ex. « 2026-118 » lu en
    26/11). En repli : la valeur (slug), puis une date française du
    libellé. Retourne None si aucune date fiable.
    """
    dates = []
    match = _PUBLIE_LABEL.search(label)
    if match:
        day_month = parse_day_month(match.group(1))
        if day_month:
            dates.append(("label", day_month))
    match = _PUBLIE_SLUG.search(value)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        if 1 <= day <= 31 and 1 <= month <= 12:
            dates.append(("slug", (day, month)))
    if not dates:
        match = _DATE_FR.search(label)
        if match:
            month = MONTHS_FR.get(match.group(2).lower())
            if month:
                return (int(match.group(1)), int(month))
        return None
    if len(dates) == 2 and dates[0][1][1] != dates[1][1][1]:
        logger.warning(
            "Mois divergents libellé (%s) / valeur (%s) : %s",
            f"{dates[0][1][1]:02d}", f"{dates[1][1][1]:02d}", label,
        )
    return dates[0][1]


def label_month(label, value=""):
    """Extrait le mois (« MM ») d'une option du menu. None si incertain."""
    day_month = label_day_month(label, value)
    if day_month is None:
        return None
    return f"{day_month[1]:02d}"


class VendeeRaaClient(RaaHttpClient):
    """Client HTTP (sans navigateur) du RAA de la Vendée."""

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
        """Retourne la liste des documents de la page : (value, label, mois).

        Le mois est extrait du libellé (pré-filtre) ; None si l'option ne
        porte pas de date exploitable.
        """
        response = self._get(self.base_url)
        soup = BeautifulSoup(response.text, "html.parser")
        select = soup.select_one("select#Liste-liste-docs")
        if select is None:
            raise RaaError(
                f"Formulaire « Liste-liste-docs » introuvable sur {self.base_url}"
            )
        documents = []
        for option in select.find_all("option"):
            value = (option.get("value") or "").strip()
            if not value:
                continue
            label = option.get("title") or option.get_text(strip=True)
            documents.append((value, label, label_month(label, value)))
        return documents

    def get_download_url(self, doc_value):
        """POST le champ « Liste-liste-docs » et retourne (url_pdf, jour_mois).

        Le jour et le mois CMS sont lus dans span.fr-link__detail
        (« PDF - 19,38 Mb - 29/11/2024 ») ; (jour, mois) ou None si le
        span est absent ou inexploitable.
        """
        response = self._post({"Liste-liste-docs": doc_value})
        soup = BeautifulSoup(response.text, "html.parser")
        panel = soup.select_one("div.liste_deroulante")
        link = None
        if panel is not None:
            link = panel.find("a", class_="fr-link--download")
        if link is None:
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
        """Retourne les liens des PDF du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier).

        Le libellé du menu ne sélectionne que les candidats ; le mois
        faisant foi est celui du panneau de téléchargement (CMS). Les
        documents sans date au menu sont aussi vérifiés (« balayeur »).
        Un document dont la date CMS diffère du mois cible est exclu
        avec un warning.
        """
        documents = self.list_documents()
        candidates = [(v, l) for v, l, m in documents if m == month]
        sweep = [(v, l) for v, l, m in documents if m is None]
        if not candidates and not sweep:
            logger.info("Aucun document trouvé pour le mois %s.", month)
            return []
        for _, label in sweep:
            logger.info("Document sans date au menu, vérification : %s", label)
        results = []
        for value, label in candidates + sweep:
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
        results.sort(key=lambda item: (item[0], item[1]))
        return [(url, name) for _, name, url in results]
