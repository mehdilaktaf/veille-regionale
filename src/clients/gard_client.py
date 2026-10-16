from src.raa_client import AnnualPageRaaClient

class GardRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA du Gard.
    
    Structure : page publications -> cartes « Recueil des actes administratifs - YYYY »
    -> page annuelle de liens directs.
    """
    def __init__(self, base_url, timeout=60):
        super().__init__(
            base_url=base_url,
            card_needle="Recueil des actes administratifs",
            timeout=timeout
        )
