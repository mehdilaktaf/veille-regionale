"""Client HTTP de base pour les RAA partagés entre les départements.

Fournit la session HTTP, le téléchargement de PDF avec contrôle
d'en-tête, et l'extraction de mois à partir des libellés/fichiers du
site (qui comportent des fautes de saisie : « 20/08/026 »,
« 19//06/2026 », « 23062026 », dates sans année, etc.).
"""

import logging
import os
import re
import time
import json
from collections import Counter
from urllib.parse import unquote, urljoin
import http.client

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

MONTHS_FR = {
    "janvier": "01", "fevrier": "02", "février": "02", "mars": "03",
    "avril": "04", "mai": "05", "juin": "06", "juillet": "07",
    "aout": "08", "août": "08", "septembre": "09", "octobre": "10",
    "novembre": "11", "decembre": "12", "décembre": "12",
    # variante des slugs CMS tronqués (« ...-decembe_2018.pdf »)
    "decembe": "12",
}

# Noms des mois (« MM » -> nom), pour construire les URLs/page de mois
MONTH_NAMES_FR = {
    "01": "janvier", "02": "février", "03": "mars", "04": "avril",
    "05": "mai", "06": "juin", "07": "juillet", "08": "août",
    "09": "septembre", "10": "octobre", "11": "novembre", "12": "décembre",
}

# Ancrage « du » dans un nom de fichier ou un texte de lien ; capture le
# texte qui suit, là où se trouve la date. Un parsing non ancré daterait
# faussement des numéros de document (ex. « 2026-069 » lu en 26/06).
_DU_ANCRE = re.compile(r"\bdu\s+(.{0,40})")

# Mois seul, sans jour (noms d'archive : « decembe_2018 »,
# « RAA mensuel n° 89 - Décembre 2018 ») ; tirets bas tolérés, « decembe »
# pour le slug tronqué de « décembre ». Frontières : pas de lettre avant ni
# après (« maison »/« maintenant » ne comptent pas, mais « _mai_2026 » oui).
_MONTH_ONLY = re.compile(
    r"(?<![a-zA-Z])(janvier|fevrier|février|mars|avril|juillet|juin|aout|août|"
    r"septembre|octobre|novembre|decembre|décembre|decembe|mai)"
    r"(?![a-zA-Z])[\s_]*(?:-?(\d{4}))?",
    re.IGNORECASE,
)

# Date numérique tolérante : jj/mm/année, séparateurs répétés ou variés,
# année à 2-4 chiffres optionnelle (« 20/08/026 », « 19//06/2026 »,
# « 17/08 »). Le (?<!\d) évite de lire le suffixe d'un numéro : « 2017-01 »
# (année-mois) ne donne pas le 17/01.
_DATE_NUM = re.compile(r"(?<!\d)(\d{1,2})[\s/\-.]+(\d{1,2})(?:[\s/\-.]+(\d{2,4}))?")

# Date compacte sans séparateur : « 23062026 »
_DATE_COMPACT = re.compile(r"(?<!\d)(\d{2})(\d{2})(\d{4})(?!\d)")

# Date française : « 5 janvier 2024 », ordinal (« 1er juillet 2026 »)
# et année optionnelle (« 08 janvier_tempete »)
_DATE_FR = re.compile(
    r"(\d{1,2})(?:er|ère)?[\s_]+(janvier|fevrier|février|mars|avril|mai|juin|juillet|"
    r"aout|août|septembre|octobre|novembre|decembre|décembre|decembe)"
    r"(?:[\s_]+(\d{4}))?",
    re.IGNORECASE,
)


# Liens de téléchargement de la plateforme CMS : a.fr-link--download sur
# les années récentes ; sur les années anciennes (ex. Mayenne ≤ 2024) les
# liens sont des a.fr-link simples menant directement à un .pdf.
DOWNLOAD_LINK_SELECTOR = "a.fr-link--download, a.fr-link[href$='.pdf']"


class RaaError(Exception):
    """Erreur lors de la récupération des documents RAA."""


class QuotaExceededError(RaaError):
    """Levée lorsque le quota de téléchargements par heure est atteint."""


class QuotaManager:
    """Gère un quota de téléchargements persistant par fenêtre d'une heure."""
    FILE_PATH = ".quota_state.json"
    LIMIT = 9
    WINDOW = 3600  # 1 heure en secondes

    @classmethod
    def check_and_increment(cls):
        now = time.time()
        state = {"start_time": now, "count": 0}

        if os.path.exists(cls.FILE_PATH):
            try:
                with open(cls.FILE_PATH, "r") as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Réinitialisation si la fenêtre d'une heure est passée
        if now - state.get("start_time", 0) > cls.WINDOW:
            state = {"start_time": now, "count": 0}

        if state["count"] >= cls.LIMIT:
            raise QuotaExceededError(
                f"Quota atteint : maximum {cls.LIMIT} fichiers par heure."
            )

        state["count"] += 1
        with open(cls.FILE_PATH, "w") as f:
            json.dump(state, f)

    @classmethod
    def get_quota_status(cls):
        """Retourne (utilisé, restant, temps_restant_sec)."""
        now = time.time()
        state = {"start_time": now, "count": 0}
        if os.path.exists(cls.FILE_PATH):
            try:
                with open(cls.FILE_PATH, "r") as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        elapsed = now - state.get("start_time", 0)
        if elapsed > cls.WINDOW:
            return 0, cls.LIMIT, 0
        
        count = state.get("count", 0)
        return count, max(0, cls.LIMIT - count), int(cls.WINDOW - elapsed)

    @classmethod
    def get_start_time(cls):
        """Retourne le timestamp de début de la fenêtre de quota actuelle."""
        if os.path.exists(cls.FILE_PATH):
            try:
                with open(cls.FILE_PATH, "r") as f:
                    state = json.load(f)
                    return state.get("start_time", time.time())
            except (json.JSONDecodeError, IOError):
                pass
        return time.time()


def parse_day_month(text):
    """Extrait (jour, mois) d'un texte contenant une date.

    Retourne None si aucune date n'est trouvée ou si elle est invalide
    (jour/mois hors bornes).
    """
    for match in _DATE_NUM.finditer(text):
        day, month = int(match.group(1)), int(match.group(2))
        if 1 <= day <= 31 and 1 <= month <= 12:
            return (day, month)
    match = _DATE_COMPACT.search(text)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        if 1 <= day <= 31 and 1 <= month <= 12:
            return (day, month)
    match = _DATE_FR.search(text)
    if match:
        month = MONTHS_FR.get(match.group(2).lower())
        if month:
            return (int(match.group(1)), int(month))
    return None


def parse_month(text):
    """Extrait le mois (« MM ») d'un texte contenant une date.

    Retourne None si aucune date n'est trouvée ou si elle est invalide.
    """
    day_month = parse_day_month(text)
    if day_month is None:
        return None
    return f"{day_month[1]:02d}"


def du_day_month(text):
    """Extrait (jour, mois) d'un texte ancré sur « du » (noms de fichier,
    textes de lien du type « RAA du 28 août 2026 »). None si aucune date.

    Les tirets bas sont normalisés en espaces : les archives hébergent des
    noms de fichier en slug sans accents (« raa_special_du_29_decembre_2017 »).
    """
    match = _DU_ANCRE.search(text.replace("_", " "))
    if match:
        return parse_day_month(match.group(1))
    return None


def du_month(text):
    """Extrait le mois (« MM ») d'un texte ancré sur « du ». None sinon."""
    day_month = du_day_month(text)
    if day_month is None:
        return None
    return f"{day_month[1]:02d}"


def relaxed_day_month(text):
    """Extrait (jour, mois) d'un texte, en tolérant l'absence de jour.

    Retourne (jour, mois) si la date complète est présente, (None, mois)
    si seul le mois est lisible (« decembe_2018 », « Décembre 2018 »),
    sinon None. Sert de source secondaire de date pour les documents
    d'archives dont le jour est perdu.
    """
    day_month = parse_day_month(text)
    if day_month is not None:
        return day_month
    match = _MONTH_ONLY.search(text.replace("_", " "))
    if match:
        month = MONTHS_FR.get(match.group(1).lower())
        if month is not None:
            return (None, int(month))
    return None


def month_of_text(text):
    """Retourne le code « MM » du premier mois (en lettres) présent dans le
    texte, ou None. Les tirets bas sont normalisés (« RAA_Janvier_02-2026-001 »
    → « 01 ») ; « Sommaire RAA » → None."""
    match = _MONTH_ONLY.search(text.replace("_", " "))
    if match:
        return MONTHS_FR.get(match.group(1).lower())
    return None


def link_day_month(link):
    """Extrait (jour, mois) du span.fr-link__detail d'un lien (ou None)."""
    detail = link.find("span", class_="fr-link__detail")
    if detail is None:
        return None
    return parse_day_month(detail.get_text(strip=True))


def find_annual_href(soup, needle):
    """Retourne l'href de la carte h2.fr-card__title dont le texte contient
    needle (ou None). La comparaison est insensible à la casse, aux accents
    et aux espaces multiples : les cartes d'archives oscillent entre « RAA
    Année 2013 », « RAA année 2012 », « RAA  Année 2022 » (double espace)
    et « RAA ANNEE 2026 » (Bas-Rhin, sans accent)."""
    needle_norm = " ".join(unidecode(needle).lower().split())
    for h2 in soup.select("h2.fr-card__title"):
        link = h2.find("a")
        if link and link.get("href"):
            text_norm = " ".join(
                unidecode(link.get_text(strip=True)).lower().split()
            )
            if needle_norm in text_norm:
                return link["href"]
    return None


def dedupe_documents(documents):
    """Conserve une entrée par nom de fichier.

    Un même fichier peut être posté deux fois (ré-upload) : l'entrée
    datée par le CMS (jour_mois_cms non nul) est conservée.
    """
    seen = {}
    for url, name, cms_day_month, second_day_month in documents:
        previous = seen.get(name)
        if previous is None or (cms_day_month is not None and previous[2] is None):
            seen[name] = (url, name, cms_day_month, second_day_month)
    return list(seen.values())


def _bulk_reupload_inversion(documents):
    """True si la date CMS ne peut pas faire foi : une même date (jour+mois)
    couvre la majorité des documents datés par le CMS, et les dates
    secondaires la contredisent — signature d'un re-upload en masse
    (pages d'archives, ex. Maine-et-Loire ≤ 2021 : tous les liens portent
    la date de re-publication, la vraie date de publication étant dans le
    nom de fichier)."""
    cms_dates = [day_month for _, _, day_month, _ in documents if day_month is not None]
    if len(cms_dates) < 3:
        return False
    mode_date, count = Counter(cms_dates).most_common(1)[0]
    if count * 2 <= len(cms_dates):
        return False
    contradicting = sum(
        1
        for _, _, day_month, second in documents
        if day_month == mode_date and second is not None and second[1] != day_month[1]
    )
    return contradicting * 2 >= count


def select_month_documents(documents, month, secondary_source="nom de fichier"):
    """Filtre et trie des documents pour un mois donné.

    documents : itérable de (url, nom, jour_mois_cms, jour_mois_secondaire).
    Chaque date est (jour, mois), le jour pouvant être None (mois seul).
    Le mois CMS fait foi (désaccord avec le secondaire → warning) ; sans
    date CMS, le secondaire est utilisé avec un warning « non vérifié » ;
    sans aucune date → exclu (warning).
    Sur une page de re-upload en masse (voir _bulk_reupload_inversion),
    c'est le secondaire qui fait foi.

    Retourne (url, nom) en ordre chronologique croissant (jour, nom) ;
    un jour inconnu est classé en début de mois.
    """
    documents = list(documents)
    inverted = _bulk_reupload_inversion(documents)
    if inverted:
        logger.warning(
            "Re-upload en masse supposé : date CMS identique sur l'essentiel "
            "des documents et contredite par le %s — le %s fait foi.",
            secondary_source, secondary_source,
        )

    results = []

    def _append(day_month, name, url):
        day = day_month[0] if day_month[0] is not None else 0
        results.append((day, name, url))

    for url, name, cms_day_month, second_day_month in documents:
        if inverted:
            if second_day_month is None:
                logger.warning("Document sans date exploitable (exclu) : %s", name)
            elif f"{second_day_month[1]:02d}" == month:
                _append(second_day_month, name, url)
            continue
        if cms_day_month is not None:
            if second_day_month is not None and second_day_month[1] != cms_day_month[1]:
                logger.warning(
                    "Mois divergents CMS (%02d) / %s (%02d) : %s "
                    "(le mois CMS fait foi)",
                    cms_day_month[1], secondary_source, second_day_month[1], name,
                )
            if f"{cms_day_month[1]:02d}" != month:
                continue
            _append(cms_day_month, name, url)
        elif second_day_month is not None and f"{second_day_month[1]:02d}" == month:
            if second_day_month[0] is None:
                logger.warning(
                    "Date non vérifiée (jour inconnu, classé en début de mois) : %s",
                    name,
                )
            else:
                logger.warning("Date non vérifiée (pas de span CMS) : %s", name)
            _append(second_day_month, name, url)
        else:
            logger.warning("Document sans date exploitable (exclu) : %s", name)
            continue
    results.sort(key=lambda item: (item[0], item[1]))
    if not results:
        logger.info("Aucun document trouvé pour le mois %s.", month)
    return [(url, name) for _, name, url in results]


class RaaHttpClient:
    """Client HTTP de base : session commune et téléchargement de PDF."""

    def __init__(self, base_url, timeout=60, request_delay=2.0):
        self.base_url = base_url
        self.timeout = timeout
        # Délai minimum entre deux requêtes réseau : les WAF des sites de
        # préfectures coupent la connexion (RemoteDisconnected) après ~40
        # requêtes rapides. Spacer les appels évite d'atteindre ce seuil.
        self.request_delay = request_delay
        self._last_request_ts = 0.0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Referer": base_url,
        })

    def _throttle(self):
        """Maintient au moins ``request_delay`` secondes entre deux requêtes
        réseau (voir l'initialisation de request_delay)."""
        if self.request_delay <= 0:
            return
        elapsed = time.monotonic() - self._last_request_ts
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self._last_request_ts = time.monotonic()

    @staticmethod
    def _retry_delay(exc, backoff):
        """Cooldown plus long sur une coupure de connexion (signature du
        blocage WAF) ou un refus/indisponibilité, que sur une autre erreur."""
        if isinstance(
            exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
        ):
            return 90
        if isinstance(exc, requests.exceptions.HTTPError):
            status = exc.response.status_code if exc.response is not None else None
            if status in (403, 429, 502, 503, 504):
                return 90
        return backoff

    def _get(self, url, retries=4, backoff=10):
        """GET avec re-essais : les WAF de préfectures coupent la connexion
        sur les accès répétés ; un cooldown long permet de traverser un
        blocage momentané plutôt que d'abandonner."""
        for attempt in range(retries + 1):
            self._throttle()
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as exc:
                # Fast fail sur signature WAF (RemoteDisconnected / Connection aborted)
                if "RemoteDisconnected" in str(exc) or "Connection aborted" in str(exc):
                    raise RaaError(f"Blocage WAF détecté (connexion coupée) : {exc}") from exc
                if attempt >= retries:
                    raise RaaError(
                        f"Échec de la requête GET {url} : {exc}"
                    ) from exc
                delay = self._retry_delay(exc, backoff)
                logger.warning(
                    "Retente GET %s dans %d s (tentative %d/%d, %s)",
                    url, delay, attempt + 1, retries + 1, exc,
                )
                time.sleep(delay)

    def _post(self, url, data=None, retries=4, backoff=10):
        """POST avec re-essais, même politique que _get."""
        for attempt in range(retries + 1):
            self._throttle()
            try:
                response = self.session.post(url, data=data, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as exc:
                # Fast fail sur signature WAF (RemoteDisconnected / Connection aborted)
                if "RemoteDisconnected" in str(exc) or "Connection aborted" in str(exc):
                    raise RaaError(f"Blocage WAF détecté (connexion coupée) : {exc}") from exc
                if attempt >= retries:
                    raise RaaError(
                        f"Échec de la requête POST {url} : {exc}"
                    ) from exc
                delay = self._retry_delay(exc, backoff)
                logger.warning(
                    "Retente POST %s dans %d s (tentative %d/%d, %s)",
                    url, delay, attempt + 1, retries + 1, exc,
                )
                time.sleep(delay)

    @staticmethod
    def _is_complete_pdf(path):
        """True si le fichier existe et est un PDF complet (entête %PDF- et
        marqueur %%EOF) : permet de reprendre un run interrompu sans
        retélécharger, tout en re-téléchargeant les fichiers tronqués."""
        if not os.path.isfile(path):
            return False
        size = os.path.getsize(path)
        if size < 1024:
            return False
        with open(path, "rb") as pdf_file:
            if pdf_file.read(5) != b"%PDF-":
                return False
            pdf_file.seek(max(0, size - 4096))
            return b"%%EOF" in pdf_file.read()

    def download(self, url, dest_path, retries=4, backoff=10):
        """Télécharge le PDF en binaire et vérifie qu'il est complet, avec
        re-essais et reprise : un fichier déjà complet n'est pas retéléchargé."""
        if self._is_complete_pdf(dest_path):
            logger.info("Déjà téléchargé (reprise) : %s", dest_path)
            return

        # Vérification et incrémentation du quota
        QuotaManager.check_and_increment()

        for attempt in range(retries + 1):
            self._throttle()
            try:
                with self.session.get(url, timeout=self.timeout, stream=True) as response:
                    response.raise_for_status()
                    with open(dest_path, "wb") as pdf_file:
                        for chunk in response.iter_content(chunk_size=65536):
                            pdf_file.write(chunk)
                break
            except requests.exceptions.RequestException as exc:
                # Fast fail sur signature WAF (RemoteDisconnected / Connection aborted)
                if "RemoteDisconnected" in str(exc) or "Connection aborted" in str(exc):
                    raise RaaError(f"Blocage WAF détecté (connexion coupée) : {exc}") from exc
                if attempt >= retries:
                    raise RaaError(
                        f"Échec du téléchargement de {url} : {exc}"
                    ) from exc
                delay = self._retry_delay(exc, backoff)
                logger.warning(
                    "Retente du téléchargement de %s dans %d s "
                    "(tentative %d/%d, %s)",
                    url, delay, attempt + 1, retries + 1, exc,
                )
                time.sleep(delay)
        if not self._is_complete_pdf(dest_path):
            raise RaaError(
                f"Le fichier téléchargé n'est pas un PDF valide : {dest_path}"
            )


class AnnualPageRaaClient(RaaHttpClient):
    """Client pour les sites structurés en deux pages :

    - une page publications avec des cartes « Année YYYY »
      (h2.fr-card__title, texte repéré par card_needle) ;
    - une page annuelle listant directement les liens de téléchargement
      (span.fr-link__detail CMS = « PDF - 10,51 Mb - 28/08/2026 »,
      source de vérité pour la date de publication).

    Si ``archives_needle`` est donné (texte de la carte « Archives »),
    les cartes d'années absentes de la page publications sont cherchées
    sous cette carte (années antérieures : Maine-et-Loire, Martinique).
    """

    def __init__(self, base_url, card_needle, timeout=60, archives_needle=None):
        super().__init__(base_url, timeout)
        self.card_needles = (
            (card_needle,) if isinstance(card_needle, str) else tuple(card_needle)
        )
        self.card_needle = self.card_needles[0]
        self.archives_needle = archives_needle
        self.annual_page_url = None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None).

        Cherche d'abord sur la page publications, puis sous la carte
        « Archives » si ``archives_needle`` est défini.
        """
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        for needle in self.card_needles:
            href = find_annual_href(soup, needle)
            if href is not None:
                return urljoin(self.base_url, href)
        if self.archives_needle is not None:
            archives_href = find_annual_href(soup, self.archives_needle)
            if archives_href is not None:
                archives_soup = BeautifulSoup(
                    self._get(urljoin(self.base_url, archives_href)).text,
                    "html.parser",
                )
                for needle in self.card_needles:
                    href = find_annual_href(archives_soup, needle)
                    if href is not None:
                        return urljoin(self.base_url, href)
        return None

    def list_documents(self):
        """Retourne les documents de la page annuelle :
        (url, nom, jour_mois_cms, jour_mois_nom).

        jour_mois_cms vient du span.fr-link__detail (source de vérité) ;
        jour_mois_nom du nom de fichier (pré-filtre, parfois fautif).
        """
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(
                    f"Page annuelle introuvable ({self.card_needle!r}) "
                    f"sur {self.base_url}"
                )
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        container = soup.select_one(".fr-col-12.fr-col-md-8") or soup
        documents = []
        for link in container.select(DOWNLOAD_LINK_SELECTOR):
            href = link.get("href")
            if not href:
                continue
            name = unquote(href.split("/")[-1])
            # Nom ancré sur « du » d'abord (normalise les tirets bas, ex.
            # « RAA n°52 Bis du 15_05_2026.pdf »), parsing tolérant en repli.
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    link_day_month(link),
                    du_day_month(name) or relaxed_day_month(name),
                )
            )
        return documents

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier).

        Le mois faisant foi est celui du span CMS ; en l'absence de span
        (défensif), le nom de fichier est utilisé avec un warning.
        """
        return select_month_documents(self.list_documents(), month)


class MonthCardsRaaClient(RaaHttpClient):
    """Client pour les sites à page annuelle de cartes « Mois YYYY »
    (h2.fr-card__title), chaque carte menant à une page listant les liens
    a.fr-link--download (date = span.fr-link__detail CMS, sinon texte du
    lien ancré sur « du »).

    base_url doit être la page annuelle. Si la page annuelle ne porte
    aucune carte mois (années anciennes), les liens sont listés
    directement sur la page annuelle.

    Toutes les pages de mois de l'année sont traversées (« balayeur »)
    afin de ne rater aucun document dont le mois CMS diffère du mois de
    la page qui le porte ; le mois CMS fait ensuite foi.
    """

    def _next_page_url(self, soup):
        for link in soup.select("ul.fr-pagination__list li a"):
            if link.get_text(strip=True) == "Suivant" and link.get("href"):
                return urljoin(self.base_url, link["href"])
        return None

    def _collect(self, soup, documents):
        for link in soup.select(DOWNLOAD_LINK_SELECTOR):
            href = link.get("href")
            if not href:
                continue
            name = unquote(href.split("/")[-1])
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    link_day_month(link),
                    relaxed_day_month(link.get_text(strip=True)),
                )
            )

    def list_documents(self):
        """Retourne les documents de l'année : (url, nom, jour_mois_cms,
        jour_mois_secondaire), dédoublonnés par nom de fichier."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        month_hrefs = [
            link["href"]
            for h2 in soup.select("h2.fr-card__title")
            for link in [h2.find("a")]
            if link is not None and link.get("href")
        ]
        documents = []
        if not month_hrefs:
            self._collect(soup, documents)
            return dedupe_documents(documents)
        for href in month_hrefs:
            url = urljoin(self.base_url, href)
            while url is not None:
                page_soup = BeautifulSoup(self._get(url).text, "html.parser")
                self._collect(page_soup, documents)
                url = self._next_page_url(page_soup)
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des PDF du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier).
        
        Optimisation PoC : ne visite que les pages de cartes correspondant
        au mois demandé au lieu de scanner toute l'année.
        """
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        month_hrefs = [
            link["href"]
            for h2 in soup.select("h2.fr-card__title")
            for link in [h2.find("a")]
            if link is not None and link.get("href") and month_of_text(link.get_text()) == month
        ]
        
        if not month_hrefs:
            # Repli : si aucune carte mois n'est trouvée, on collecte sur la page annuelle
            documents = []
            self._collect(soup, documents)
            return select_month_documents(documents, month, secondary_source="texte du lien")

        all_docs = []
        for href in month_hrefs:
            url = urljoin(self.base_url, href)
            while url is not None:
                page_soup = BeautifulSoup(self._get(url).text, "html.parser")
                self._collect(page_soup, all_docs)
                url = self._next_page_url(page_soup)
        
        return select_month_documents(dedupe_documents(all_docs), month, secondary_source="texte du lien")
