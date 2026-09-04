"""Client HTTP (sans navigateur) du RAA de l'Orne.

Trois niveaux (2 intermédiaires avant la page annuelle) :
- la page section (…/Recueil-des-Actes-Administratifs-RAA) porte une carte
  « Le Recueil des Actes Administratifs (RAA) » ;
- la page RAA porte les années en liens du **menu latéral**
  (`a.fr-sidemenu__link`) : « Le Recueil des Actes Administratifs 2026 »
  (majuscules) et « Le Recueil des actes administratifs YYYY » (minuscules,
  2025→2017) — les cartes h2 de cette page portent le même texte mais un
  href cassé (renvoi vers la page elle-même) : les ignorer ;
- la page annuelle (…/Le-Recueil-des-Actes-Administratifs-2026, slug en
  minuscule pour les autres années) liste des cartes mois à nom seul
  (Janvier…Décembre) + des cartes thématiques à nom de mois
  (« Spéciaux du mois de juillet ») : matching par `month_of_text`.

Page de carte : des `<ul>` de liens dont les **classes sont corrompues par
le CMS** (« <a fr-link--download="" id='class="fr-link'... ») — le
sélecteur `a.fr-link--download` ne matche pas : `a[href$='.pdf']` en
remplace. Le `span.fr-link__detail` est en revanche intact sur tous les
liens (source de vérité, 100 % — annexes comprises) ; le texte du lien le
reprise (« PDF - 0,43 Mb - 02/02/2026 ») en repli.

Les noms de fichier portent la date de l'acte ancrée « du » (« Spécial n° 1
du lundi 2 février 2026.pdf », double espaces tolérés), « du <mois> » sans
jour pour certains, ou aucune date pour les annexes (« Spécial n° 8 - DDT -
SHC -Annexe 1 de l'arrêté n° 2330-2025-037.pdf ») : le nom est un contrôle,
le mois CMS faisant foi (dérogation Manche non nécessaire : pas de
« RAA mensuel » dans l'Orne). L'Orne ne publie pas de recueil composé :
le « fusionné » = les spécialités + annexes du mois.
"""

import logging
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup
from unidecode import unidecode

from raa_client import (
    RaaError,
    RaaHttpClient,
    dedupe_documents,
    du_day_month,
    find_annual_href,
    link_day_month,
    month_of_text,
    parse_day_month,
    relaxed_day_month,
    select_month_documents,
)

logger = logging.getLogger(__name__)


class OrneRaaClient(RaaHttpClient):
    """Client HTTP du RAA de l'Orne."""

    # Classes corrompues par le CMS : le sélecteur par href est le seul
    # fiable (tous les liens de la plateforme pointent sur un .pdf).
    LINK_SELECTOR = "a[href$='.pdf']"

    def __init__(self, base_url, year, timeout=60):
        super().__init__(base_url, timeout)
        self.year = year
        self.annual_page_url = None

    def _year_href(self, soup):
        """Href du lien « Le Recueil des Actes Administratifs YYYY » (menu
        latéral d'abord : les cartes h2 de la page RAA portent le même
        texte mais un href cassé vers la page elle-même)."""
        needle = f"le recueil des actes administratifs {self.year}"
        for selector in ("a.fr-sidemenu__link", "a"):
            for link in soup.select(selector):
                href = link.get("href")
                if not href:
                    continue
                text = " ".join(unidecode(link.get_text(" ", strip=True)).lower().split())
                if text == needle:
                    return href
        return None

    def find_annual_page(self):
        """Retourne l'URL absolue de la page annuelle (ou None)."""
        soup = BeautifulSoup(self._get(self.base_url).text, "html.parser")
        href = self._year_href(soup)
        if href is None:
            # Niveau intermédiaire : carte « Le Recueil des Actes
            # Administratifs (RAA) ».
            card_href = find_annual_href(soup, "Le Recueil des Actes Administratifs")
            if card_href is None:
                return None
            raa_soup = BeautifulSoup(
                self._get(urljoin(self.base_url, card_href)).text, "html.parser"
            )
            href = self._year_href(raa_soup)
        return urljoin(self.base_url, href) if href else None

    @staticmethod
    def _card_month(text):
        """Mois (« MM ») d'une carte (« Février ») ou None."""
        return month_of_text(text)

    def _annual_cards(self):
        """(mois_carte, href) des cartes de la page annuelle (sans
        pagination observée) ; mois_carte = None pour une carte sans mois."""
        soup = BeautifulSoup(self._get(self.annual_page_url).text, "html.parser")
        cards = []
        for h2 in soup.select("h2.fr-card__title"):
            link = h2.find("a")
            if link is None or not link.get("href"):
                continue
            cards.append(
                (
                    self._card_month(link.get_text(" ", strip=True)),
                    link["href"],
                )
            )
        return cards

    def _collect_page(self, url, documents):
        """Collecte les documents d'une page de carte :
        (url, nom, jour_mois_cms, jour_mois_nom)."""
        soup = BeautifulSoup(self._get(url).text, "html.parser")
        for link in soup.select(self.LINK_SELECTOR):
            href = link.get("href")
            if not href:
                continue
            name = unquote(href.split("/")[-1])
            # Span fr-link__detail intact (source de vérité) ; le texte du
            # lien le reprise en repli.
            publication = link_day_month(link) or parse_day_month(
                link.get_text(" ", strip=True)
            )
            documents.append(
                (
                    urljoin(self.base_url, href),
                    name,
                    publication,
                    du_day_month(name) or relaxed_day_month(name),
                )
            )

    def list_documents(self, month):
        """Retourne les documents du mois : cartes du mois (et les cartes
        thématiques portant le même mois, ex. « Spéciaux du mois de
        juillet » pour 07) + cartes sans mois au balayeur.
        (url, nom, jour_mois_cms, jour_mois_nom)."""
        if self.annual_page_url is None:
            self.annual_page_url = self.find_annual_page()
            if self.annual_page_url is None:
                raise RaaError(
                    f"Page annuelle {self.year} introuvable sur {self.base_url}"
                )
        documents = []
        cards = self._annual_cards()
        month_cards = [href for m, href in cards if m == month]
        other_cards = [href for m, href in cards if m is None]
        if not cards:
            # Années anciennes éventuelles : liens directs sur la page
            # annuelle (sans carte).
            self._collect_page(self.annual_page_url, documents)
        else:
            for href in month_cards + other_cards:
                self._collect_page(urljoin(self.annual_page_url, href), documents)
        return dedupe_documents(documents)

    def documents_for_month(self, month):
        """Retourne les liens des RAA du mois, en ordre chronologique
        croissant : (url_absolue, nom_de_fichier)."""
        return select_month_documents(
            self.list_documents(month), month, secondary_source="nom de fichier"
        )
