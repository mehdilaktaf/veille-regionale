from src.raa_client import AnnualPageRaaClient

class PasDeCalaisRaaClient(AnnualPageRaaClient):
    """Client pour le RAA du Pas-de-Calais.
    Structure : section -> page annuelle -> PDF directs.
    """
    def __init__(self, base_url, timeout=60):
        # La carte annuelle est identifiée par le texte "2026 - Recueils des actes administratifs"
        # On utilise un needle générique "Recueils des actes administratifs" pour matcher toutes les années.
        super().__init__(
            base_url=base_url,
            card_needle="Recueils des actes administratifs",
            timeout=timeout
        )
