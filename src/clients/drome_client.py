from src.raa_client import MonthCardsRaaClient

class DromeRaaClient(MonthCardsRaaClient):
    """Client HTTP du RAA de la Drôme.
    
    Navigation : page annuelle (cartes mois) -> pages de mois -> liens PDF.
    Le mois CMS fait foi (span.fr-link__detail).
    """
    pass
