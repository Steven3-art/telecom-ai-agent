"""
core/agent.py — Pipeline principal TelecomAI
"""
from .aaa_mock    import AAAMockClient
from .diagnostics import generer_diagnostic, identifier_zone


class TelecomAIAgent:

    def __init__(self):
        self.aaa = AAAMockClient()

    def traiter(self, numero: str) -> dict:
        """Pipeline complet : numéro → diagnostic"""

        # Étape 1 — Statut AAA
        statut = self.aaa.consulter_statut(numero)
        status = statut.get("status", "")

        # Étape 2 — Radius (si Normal)
        if status == "Normal":
            radius = self.aaa.consulter_radius(numero)
        else:
            radius = {"connecte": False, "codes_erreur": {},
                      "nb_successful": 0, "nb_failed": 0, "trafic_mb": 0}

        # Étape 3 — Diagnostic
        diag = generer_diagnostic(statut, radius)

        return {
            "numero":           numero,
            "statut":           status,
            "zone":             diag.get("zone", {}),
            "categorie":        diag.get("categorie", "INCONNU"),
            "code_erreur":      diag.get("code_erreur"),
            "message":          diag.get("message", ""),
            "reponse_whatsapp": diag.get("reponse_whatsapp", ""),
            "action_crip":      diag.get("action_crip", "info_only"),
            "urgence":          "HAUTE" if diag.get("action_crip") == "reset_mdp" else "NORMALE",
        }

    def traiter_batch(self, numeros: list) -> list:
        return [self.traiter(n) for n in numeros]

    def rapport_zone(self, zone_nom: str) -> dict:
        import random
        return {
            "zone":         zone_nom,
            "total":        random.randint(20, 100),
            "normal":       random.randint(15, 70),
            "suspendu":     random.randint(5, 20),
            "inexistant":   random.randint(0, 10),
            "absence_auth": random.randint(3, 15),
        }