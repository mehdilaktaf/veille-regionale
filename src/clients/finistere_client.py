from src.raa_client import AnnualPageRaaClient

class FinistereRaaClient(AnnualPageRaaClient):
    """Client HTTP du RAA du Finistère.
    
    Navigation : page section -> cartes « Recueils publiés en YYYY » -> 
    page annuelle avec liens directs a.fr-link--download.
    """
    def __init__(self, base_url, timeout=60):
        super().__init__(
            base_url=base_url,
            card_needle="Recueils publiés en",
            timeout=timeout
        )
