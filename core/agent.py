"""
core/agent.py — TelecomAI main pipeline (fictional demo)
============================================================
This file is part of a hackathon demo project. It orchestrates
the fictional AAA mock and diagnostics modules. No real operator
data is used anywhere.
"""

from .aaa_mock    import AAAMockClient
from .diagnostics import generer_diagnostic, identifier_zone


class TelecomAIAgent:

    def __init__(self):
        self.aaa = AAAMockClient()

    def traiter(self, numero: str) -> dict:
        """Full pipeline: subscriber number -> diagnosis"""

        # Step 1 - AAA status
        statut = self.aaa.consulter_statut(numero)
        status = statut.get("status", "")

        # Step 2 - Authentication log (if Normal)
        if status == "Normal":
            radius = self.aaa.consulter_radius(numero)
        else:
            radius = {"connecte": False, "codes_erreur": {},
                      "nb_successful": 0, "nb_failed": 0, "trafic_mb": 0}

        # Step 3 - Diagnosis
        diag = generer_diagnostic(statut, radius)

        return {
            "numero":           numero,
            "statut":           status,
            "zone":             diag.get("zone", {}),
            "categorie":        diag.get("categorie", "INCONNU"),
            "code_erreur":      diag.get("code_erreur"),
            "message":          diag.get("message", ""),
            "reponse_whatsapp": diag.get("reponse_whatsapp", ""),
            "action_required":  diag.get("action_required", "info_only"),
            "urgence":          "HIGH" if diag.get("action_required") == "reset_mdp" else "NORMAL",
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
