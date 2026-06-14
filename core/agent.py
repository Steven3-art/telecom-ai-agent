"""
agent.py — Core du TelecomAI Agent
====================================
Logique commune aux interfaces Qwen et Slack.
Aucune donnée confidentielle ici.
"""

from .aaa_mock    import AAAMockClient
from .diagnostics import generer_diagnostic, identifier_zone


class TelecomAIAgent:
    """
    Agent IA de support FTTH pour opérateurs télécoms africains.
    Architecture :
      Input  → AAAMock (statut + radius)
             → Diagnostic (catégorisation)
             → Réponse formatée
    """

    def __init__(self):
        self.aaa = AAAMockClient()

    def traiter(self, numero: str, include_cdr: bool = False,
                mois: int = None, annee: int = None) -> dict:
        """
        Pipeline complet de traitement.

        Args:
            numero      : Numéro FTTH à consulter (ex: 222230001)
            include_cdr : Inclure l'historique CDR si True
            mois, annee : Mois CDR à interroger

        Returns:
            dict avec diagnostic complet + recommandation
        """
        # Étape 1 — Consultation statut
        statut = self.aaa.consulter_statut(numero)

        # Étape 2 — Consultation Radius (si pas suspendu/inexistant)
        if statut["status"] in ("Normal",):
            radius = self.aaa.consulter_radius(numero)
        else:
            radius = {"connecte": False, "nb_echecs": 0, "trafic_mb": 0}

        # Étape 3 — Diagnostic
        diag = generer_diagnostic(statut, radius)

        # Étape 4 — CDR si demandé
        cdr = None
        if include_cdr and mois and annee:
            cdr = self.aaa.consulter_cdr(numero, mois, annee)

        return {
            "numero":    numero,
            "statut":    statut["status"],
            "zone":      diag["zone"],
            "categorie": diag["categorie"],
            "message":   diag["message"],
            "action":    diag["action"],
            "urgence":   diag["urgence"],
            "cdr":       cdr,
        }

    def traiter_batch(self, numeros: list) -> list:
        """Traiter plusieurs numéros d'un coup"""
        return [self.traiter(n) for n in numeros]

    def rapport_zone(self, zone_nom: str) -> dict:
        """Générer un rapport de supervision pour une zone"""
        # En production : requête sur la vraie base ETL
        # En mock : simulation statistique
        import random
        return {
            "zone":         zone_nom,
            "total":        random.randint(20, 100),
            "normal":       random.randint(15, 70),
            "suspendu":     random.randint(5, 20),
            "inexistant":   random.randint(0, 10),
            "absence_auth": random.randint(3, 15),
            "alerte":       random.random() > 0.7,
        }
