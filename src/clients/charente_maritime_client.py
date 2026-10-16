import logging
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

from src.raa_client import RaaHttpClient, RaaError, parse_day_month, parse_month, select_month_documents, dedupe_documents, relaxed_day_month

logger = logging.getLogger(__name__)

class CharenteMaritimeRaaClient(RaaHttpClient):
    """Client HTTP pour le RAA de la Charente-Maritime.
    Structure : Page RAA -> Select Année -> POST -> Panneau de téléchargement.
    Pattern similaire à la Vendée.
    """

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year

    def _get_year_value(self):
        """Trouve la valeur du select pour l'année ciblée."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        # On cherche l'option qui contient l'année
        for option in soup.find_all("option"):
            if str(self.year) in option.get_text():
                return option.get("value")
        raise RaaError(f"Option pour l'année {self.year} introuvable sur {self.base_url}")

    def list_documents(self):
        """Liste les documents de l'année via le POST du select d'année.
        Retourne une liste de (value, label, mois).
        """
        year_value = self._get_year_value()
        
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        select_element = soup.find("select")
        if not select_element:
            raise RaaError("Aucun élément <select> trouvé sur la page.")
        
        select_name = select_element.get("name")
        
        # POST pour obtenir la page des documents de l'année
        payload = {select_name: year_value}
        response = self._post(self.base_url, data=payload)
        soup_res = BeautifulSoup(response.text, "html.parser")
        
        # On cherche si les documents sont dans un second select (pattern Vendée)
        # ou dans des liens directs.
        doc_select = soup_res.find("select")
        if doc_select:
            documents = []
            for option in doc_select.find_all("option"):
                value = (option.get("value") or "").strip()
                if not value:
                    continue
                label = option.get("title") or option.get_text(strip=True)
                documents.append((value, label, parse_month(label)))
            return documents

        # Repli : liens directs sur la page
        documents = []
        for link in soup_res.find_all("a", href=True):
            text = link.get_text(strip=True)
            if "RAA" in text.upper() or "Recueil" in text:
                doc_url = urljoin(self.base_url, link["href"])
                documents.append((doc_url, text, parse_month(text)))
        
        return documents

    def get_download_url(self, doc_value):
        """Récupère l'URL du PDF et sa date CMS.
        Si doc_value est une URL, on check si c'est un PDF.
        Sinon on tente un POST (pattern Vendée).
        """
        if doc_value.startswith("http") and doc_value.endswith(".pdf"):
            return doc_value, None
            
        # Tenter le POST comme pour la Vendée
        # On doit retrouver le nom du select sur la page des documents
        # Pour simplifier, on tente le même select_name que pour l'année
        # ou on cherche un nouveau select sur la page
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        select_name = soup.find("select").get("name")
        
        try:
            response = self._post(self.base_url, data={select_name: doc_value})
            soup_res = BeautifulSoup(response.text, "html.parser")
            link = soup_res.select_one("a.fr-link--download") or soup_res.find("a", class_="fr-link--download")
            if not link or not link.get("href"):
                raise RaaError(f"Lien PDF introuvable pour {doc_value}")
            
            url = urljoin(self.base_url, link["href"])
            day_month = None
            detail = link.find("span", class_="fr-link__detail")
            if detail:
                day_month = parse_day_month(detail.get_text(strip=True))
            return url, day_month
        except Exception as e:
            if doc_value.startswith("http"):
                soup_inter = BeautifulSoup(self._get(doc_value).text, "html.parser")
                pdf_link = soup_inter.find("a", href=lambda x: x and x.endswith(".pdf"))
                if pdf_link:
                    return urljoin(doc_value, pdf_link["href"]), None
            raise RaaError(f"Impossible de récupérer l'URL pour {doc_value} : {e}")

    def documents_for_month(self, month):
        """Filtre les documents pour le mois donné et récupère les URLs finales."""
        all_docs = self.list_documents()
        candidates = [(v, l) for v, l, m in all_docs if m == month or m is None]
        
        if not candidates:
            logger.info("Aucun document trouvé pour le mois %s.", month)
            return []
        
        results = []
        for value, label in candidates:
            try:
                url, span_day_month = self.get_download_url(value)
                span_month = f"{span_day_month[1]:02d}" if span_day_month else None
                
                if span_month and span_month != month:
                    logger.warning("Exclu : mois CMS %s différent du mois cible %s : %s", span_month, month, label)
                    continue
                
                sort_day = span_day_month[0] if span_day_month else 99
                name = value.split("/")[-1] + ".pdf" if ".pdf" not in value else value.split("/")[-1]
                results.append((sort_day, name, url))
            except RaaError as e:
                logger.error("Erreur lors de la récupération du lien pour %s : %s", label, e)
        
        results.sort(key=lambda item: (item[0], item[1]))
        return [(url, name) for _, name, url in results]

    def download(self, url, dest_path, retries=4, backoff=10):
        """Télécharge le PDF."""
        return super().download(url, dest_path, retries, backoff)

