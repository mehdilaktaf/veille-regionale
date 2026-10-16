from src.raa_client import AnnualPageRaaClient

class IlleEtVilaineRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA d'Ille-et-Vilaine.
    
    Navigation : page section -> cartes « Recueil des actes administratifs YYYY » -> 
    page annuelle avec liens directs a.fr-link--download.
    """
    def __init__(self, base_url, timeout=60):
        super().__init__(
            base_url=base_url,
            card_needle="Recueil des actes administratifs",
            timeout=timeout
        )
