from src.raa_client import AnnualPageRaaClient

class AllierRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA de l'Allier.
    Page annuelle de liens directs, span CMS faisant foi.
    """
    def __init__(self, base_url, année):
        super().__init__(
            base_url=base_url,
            card_needle="Recueil des actes administratifs de l'année",
        )
        self.année = année
        # On force l'URL de la page annuelle pour éviter de scanner la page publications à chaque fois
        # Le pattern est : /Publications/Recueil-des-actes-administratifs-arretes/Recueil-des-actes-administratifs-de-l-annee-YYYY
        self.annual_page_url = f"{base_url}/Recueil-des-actes-administratifs-de-l-annee-{année}"
