"""
core/aaa_mock.py — Version réelle CAMTEL
==========================================
Simulation du portail AAA avec les vrais codes erreur.
Données abonnés 100% fictives — logique 100% réelle.
"""

import random
from datetime import datetime, timedelta
from .diagnostics import CODES_ERREUR_AAA

# ── Profils abonnés fictifs avec codes erreur réels ──────────
ABONNES_FICTIFS = {
    # Normal connecté avec trafic
    "222230001": {
        "statut": "Normal", "connecte": True, "trafic_mb": 245.3,
        "codes_erreur": {}, "nb_successful": 15, "nb_failed": 0,
        "zone": "22"
    },
    # Absence d'authentification (code 109020018)
    "222230003": {
        "statut": "Normal", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {}, "nb_successful": 0, "nb_failed": 0,
        "zone": "22"
    },
    # Problème mot de passe CHAP (code 109020102)
    "222310002": {
        "statut": "Normal", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {"109020102": 8}, "nb_successful": 0, "nb_failed": 8,
        "zone": "31"
    },
    # Blacklisté (code 109022520)
    "222316544": {
        "statut": "Normal", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {"109022520": 3}, "nb_successful": 0, "nb_failed": 3,
        "zone": "31"
    },
    # Suspendu (code 109020122)
    "222311395": {
        "statut": "Suspend", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {}, "nb_successful": 0, "nb_failed": 0,
        "zone": "31"
    },
    # Échec auth terminal (code 109020207)
    "222270004": {
        "statut": "Normal", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {"109020207": 5}, "nb_successful": 0, "nb_failed": 5,
        "zone": "27"
    },
    # Blocage CRM (code 109129999)
    "222230906": {
        "statut": "Normal", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {"109129999": 2}, "nb_successful": 0, "nb_failed": 2,
        "zone": "23"
    },
    # Suspendu impayé (code 109020106)
    "222201181": {
        "statut": "Suspend", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {}, "nb_successful": 0, "nb_failed": 0,
        "zone": "20"
    },
    # Inexistant
    "222990999": {
        "statut": "No record found", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {}, "nb_successful": 0, "nb_failed": 0,
        "zone": None
    },
    # Normal sans trafic (équipement client)
    "222302375": {
        "statut": "Normal", "connecte": True, "trafic_mb": 0,
        "codes_erreur": {}, "nb_successful": 3, "nb_failed": 0,
        "zone": "30"
    },
    # CDR disponible
    "222302628": {
        "statut": "Normal", "connecte": True, "trafic_mb": 180.5,
        "codes_erreur": {}, "nb_successful": 22, "nb_failed": 0,
        "zone": "30"
    },
}


class AAAMockClient:
    """
    Simulation du portail AAA CAMTEL.
    Reproduit la structure et la logique réelle.
    """

    def consulter_statut(self, numero: str) -> dict:
        """Simuler Subscriber Information"""
        abonne = self._get_abonne(numero)
        return {
            "numero":  numero,
            "login":   f"{numero}@camnet.cm",
            "status":  abonne["statut"],
            "zone":    abonne.get("zone"),
        }

    def consulter_radius(self, numero: str) -> dict:
        """Simuler Radius Login Log"""
        abonne = self._get_abonne(numero)
        if abonne["statut"] != "Normal":
            return {"connecte": False, "codes_erreur": {},
                    "nb_successful": 0, "nb_failed": 0, "trafic_mb": 0}
        return {
            "connecte":     abonne.get("connecte", False),
            "trafic_mb":    abonne.get("trafic_mb", 0),
            "codes_erreur": abonne.get("codes_erreur", {}),
            "nb_successful": abonne.get("nb_successful", 0),
            "nb_failed":    abonne.get("nb_failed", 0),
        }

    def consulter_cdr(self, numero: str, mois: int, annee: int) -> dict:
        """Simuler Query CDRs"""
        abonne = self._get_abonne(numero)
        if abonne["statut"] != "Normal" or abonne.get("nb_successful", 0) == 0:
            return {"total": 0, "premiere": None, "derniere": None}

        total = random.randint(8, 45)
        from datetime import datetime, timedelta
        debut = datetime(annee, mois, 1)
        import calendar
        fin   = datetime(annee, mois, calendar.monthrange(annee, mois)[1])
        prem  = debut + timedelta(hours=random.randint(0, 12))
        dern  = fin   - timedelta(days=random.randint(1, 5))
        return {
            "total":    total,
            "premiere": prem.strftime("%Y-%m-%d %H:%M:%S"),
            "derniere": dern.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _get_abonne(self, numero: str) -> dict:
        """Récupérer ou générer un profil abonné fictif"""
        if numero in ABONNES_FICTIFS:
            return ABONNES_FICTIFS[numero]

        # Générer aléatoirement pour numéros non définis
        # Distribution réaliste terrain CAMTEL
        r = random.random()
        if r < 0.45:   # 45% Normal connecté
            return {"statut":"Normal","connecte":True,"trafic_mb":random.uniform(10,500),
                    "codes_erreur":{},"nb_successful":random.randint(5,30),"nb_failed":0}
        elif r < 0.65: # 20% Absence auth
            return {"statut":"Normal","connecte":False,"trafic_mb":0,
                    "codes_erreur":{},"nb_successful":0,"nb_failed":0}
        elif r < 0.78: # 13% Problème mot de passe
            code = random.choice(["109020102","109022520"])
            return {"statut":"Normal","connecte":False,"trafic_mb":0,
                    "codes_erreur":{code:random.randint(2,10)},"nb_successful":0,"nb_failed":5}
        elif r < 0.90: # 12% Suspendu
            return {"statut":"Suspend","connecte":False,"trafic_mb":0,
                    "codes_erreur":{},"nb_successful":0,"nb_failed":0}
        elif r < 0.96: # 6% Blocage CRM
            return {"statut":"Normal","connecte":False,"trafic_mb":0,
                    "codes_erreur":{"109129999":random.randint(1,5)},"nb_successful":0,"nb_failed":3}
        else:          # 4% Inexistant
            return {"statut":"No record found","connecte":False,"trafic_mb":0,
                    "codes_erreur":{},"nb_successful":0,"nb_failed":0}
