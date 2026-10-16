from src.raa_client import MonthCardsRaaClient

class ArdecheRaaClient(MonthCardsRaaClient):
    """Client HTTP du RAA de l'Ardèche.
    
    Navigation : page annuelle (cartes mois) -> pages de mois -> liens PDF.
    Le mois CMS fait foi (span.fr-link__detail).
    """
    pass
