"""
core/aaa_mock.py — Fictional demo version
=============================================
Mock of an AAA-style subscriber platform with illustrative
error codes. All subscriber data, domains, and identifiers in
this file are entirely fictional and created for this hackathon
demo only. No real operator or customer data is used anywhere.
"""

import random
import calendar
from datetime import datetime, timedelta

# ── Fictional subscriber profiles ──────────────────────────────
ABONNES_FICTIFS = {
    # Normal, connected with traffic
    "222230001": {
        "statut": "Normal", "connecte": True, "trafic_mb": 245.3,
        "codes_erreur": {}, "nb_successful": 15, "nb_failed": 0,
        "zone": "22"
    },
    # No authentication (code 109020018)
    "222230003": {
        "statut": "Normal", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {}, "nb_successful": 0, "nb_failed": 0,
        "zone": "22"
    },
    # CHAP password issue (code 109020102)
    "222310002": {
        "statut": "Normal", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {"109020102": 8}, "nb_successful": 0, "nb_failed": 8,
        "zone": "31"
    },
    # Blacklisted (code 109022520)
    "222316544": {
        "statut": "Normal", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {"109022520": 3}, "nb_successful": 0, "nb_failed": 3,
        "zone": "31"
    },
    # Suspended (code 109020122)
    "222311395": {
        "statut": "Suspend", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {}, "nb_successful": 0, "nb_failed": 0,
        "zone": "31"
    },
    # Terminal auth failure (code 109020207)
    "222270004": {
        "statut": "Normal", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {"109020207": 5}, "nb_successful": 0, "nb_failed": 5,
        "zone": "27"
    },
    # CRM block (code 109129999)
    "222230906": {
        "statut": "Normal", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {"109129999": 2}, "nb_successful": 0, "nb_failed": 2,
        "zone": "23"
    },
    # Suspended for unpaid invoice (code 109020106)
    "222201181": {
        "statut": "Suspend", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {}, "nb_successful": 0, "nb_failed": 0,
        "zone": "20"
    },
    # Not found
    "222990999": {
        "statut": "No record found", "connecte": False, "trafic_mb": 0,
        "codes_erreur": {}, "nb_successful": 0, "nb_failed": 0,
        "zone": None
    },
    # Normal, no traffic (customer equipment issue)
    "222302375": {
        "statut": "Normal", "connecte": True, "trafic_mb": 0,
        "codes_erreur": {}, "nb_successful": 3, "nb_failed": 0,
        "zone": "30"
    },
    # CDR history available
    "222302628": {
        "statut": "Normal", "connecte": True, "trafic_mb": 180.5,
        "codes_erreur": {}, "nb_successful": 22, "nb_failed": 0,
        "zone": "30"
    },
}


class AAAMockClient:
    """
    Mock client for a fictional AAA-style subscriber platform.
    Mirrors the general structure and logic of such systems,
    without using any real operator's data or infrastructure.
    """

    def consulter_statut(self, numero: str) -> dict:
        """Simulate a subscriber-information lookup"""
        abonne = self._get_abonne(numero)
        return {
            "numero":  numero,
            "login":   f"{numero}@demo-isp.net",
            "status":  abonne["statut"],
            "zone":    abonne.get("zone"),
        }

    def consulter_radius(self, numero: str) -> dict:
        """Simulate an authentication log lookup"""
        abonne = self._get_abonne(numero)
        if abonne["statut"] != "Normal":
            return {"connecte": False, "codes_erreur": {},
                    "nb_successful": 0, "nb_failed": 0, "trafic_mb": 0}
        return {
            "connecte":      abonne.get("connecte", False),
            "trafic_mb":     abonne.get("trafic_mb", 0),
            "codes_erreur":  abonne.get("codes_erreur", {}),
            "nb_successful": abonne.get("nb_successful", 0),
            "nb_failed":     abonne.get("nb_failed", 0),
        }

    def consulter_cdr(self, numero: str, mois: int, annee: int) -> dict:
        """Simulate a connection-history (CDR) lookup"""
        abonne = self._get_abonne(numero)
        if abonne["statut"] != "Normal" or abonne.get("nb_successful", 0) == 0:
            return {"total": 0, "premiere": None, "derniere": None}

        total = random.randint(8, 45)
        debut = datetime(annee, mois, 1)
        fin   = datetime(annee, mois, calendar.monthrange(annee, mois)[1])
        prem  = debut + timedelta(hours=random.randint(0, 12))
        dern  = fin   - timedelta(days=random.randint(1, 5))
        return {
            "total":    total,
            "premiere": prem.strftime("%Y-%m-%d %H:%M:%S"),
            "derniere": dern.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _get_abonne(self, numero: str) -> dict:
        """Retrieve or randomly generate a fictional subscriber profile"""
        if numero in ABONNES_FICTIFS:
            return ABONNES_FICTIFS[numero]

        # Random generation for undefined numbers, using an
        # illustrative distribution for demo purposes.
        r = random.random()
        if r < 0.45:   # 45% normal, connected
            return {"statut":"Normal","connecte":True,"trafic_mb":random.uniform(10,500),
                    "codes_erreur":{},"nb_successful":random.randint(5,30),"nb_failed":0}
        elif r < 0.65: # 20% no authentication
            return {"statut":"Normal","connecte":False,"trafic_mb":0,
                    "codes_erreur":{},"nb_successful":0,"nb_failed":0}
        elif r < 0.78: # 13% password issue
            code = random.choice(["109020102","109022520"])
            return {"statut":"Normal","connecte":False,"trafic_mb":0,
                    "codes_erreur":{code:random.randint(2,10)},"nb_successful":0,"nb_failed":5}
        elif r < 0.90: # 12% suspended
            return {"statut":"Suspend","connecte":False,"trafic_mb":0,
                    "codes_erreur":{},"nb_successful":0,"nb_failed":0}
        elif r < 0.96: # 6% CRM block
            return {"statut":"Normal","connecte":False,"trafic_mb":0,
                    "codes_erreur":{"109129999":random.randint(1,5)},"nb_successful":0,"nb_failed":3}
        else:          # 4% not found
            return {"statut":"No record found","connecte":False,"trafic_mb":0,
                    "codes_erreur":{},"nb_successful":0,"nb_failed":0}
