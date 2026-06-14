"""
aaa_mock.py — Simulation du portail AAA FTTH
=============================================
Données 100% fictives pour la démo hackathon.
Aucune donnée réelle CAMTEL n'est utilisée ici.
L'architecture est identique au système réel.
"""

import random
from datetime import datetime, timedelta


# ── Faux abonnés fictifs (structure identique à la réalité) ──
ABONNES_FICTIFS = {
    "222230001": {
        "statut":    "Normal",
        "login":     "222230001@camnet.cm",
        "zone":      "Zone Yaoundé Centre",
        "central":   "CTN",
        "historique": True,   # a des sessions récentes
        "derniere_session": "2026-06-13 08:45:00",
    },
    "222310002": {
        "statut":    "Suspend",
        "login":     "222310002@camnet.cm",
        "zone":      "Zone Yaoundé Biyem-Assi",
        "central":   "Central BYM",
        "historique": False,
        "derniere_session": None,
    },
    "222230003": {
        "statut":    "Normal",
        "login":     "222230003@camnet.cm",
        "zone":      "Zone Yaoundé Centre",
        "central":   "CTN",
        "historique": False,  # pas de session = absence auth
        "derniere_session": "2026-04-02 14:22:00",
    },
    "222270004": {
        "statut":    "Normal",
        "login":     "222270004@camnet.cm",
        "zone":      "Zone Garoua",
        "central":   "Central GRA",
        "historique": True,
        "derniere_session": "2026-06-12 20:11:00",
    },
    "222440005": {
        "statut":    "Normal",
        "login":     "222440005@camnet.cm",
        "zone":      "Zone Bafoussam",
        "central":   "Central Bfs",
        "historique": False,
        "derniere_session": "2026-05-15 09:00:00",
    },
    "222990999": {
        "statut":    "No record found",
        "login":     None,
        "zone":      None,
        "central":   None,
        "historique": False,
        "derniere_session": None,
    },
}


class AAAMockClient:
    """
    Client de simulation du portail AAA.
    Reproduit fidèlement la structure des réponses réelles
    sans exposer aucune donnée confidentielle.
    """

    def consulter_statut(self, numero: str) -> dict:
        """Simuler la consultation Subscriber Information"""
        abonne = ABONNES_FICTIFS.get(numero)
        if not abonne:
            # Numéro inconnu → générer une réponse aléatoire réaliste
            abonne = self._generer_abonne_fictif(numero)

        return {
            "numero":  numero,
            "login":   abonne.get("login") or f"{numero}@camnet.cm",
            "status":  abonne["statut"],
            "zone":    abonne.get("zone",    "Zone inconnue"),
            "central": abonne.get("central", "Central inconnu"),
        }

    def consulter_radius(self, numero: str) -> dict:
        """Simuler la consultation Radius Login Log"""
        abonne = ABONNES_FICTIFS.get(numero, {})
        has_hist = abonne.get("historique", False)
        last_sess = abonne.get("derniere_session")

        if abonne.get("statut") == "Suspend":
            return {"success": False, "raison": "Compte suspendu"}

        if not has_hist or not last_sess:
            return {
                "success":   True,
                "connecte":  False,
                "derniere":  last_sess,
                "nb_echecs": random.randint(0, 3),
            }

        return {
            "success":    True,
            "connecte":   True,
            "ip":         f"10.1.{random.randint(1,254)}.{random.randint(1,254)}",
            "derniere":   last_sess,
            "trafic_mb":  round(random.uniform(10, 500), 2),
            "nb_echecs":  0,
        }

    def consulter_cdr(self, numero: str, mois: int, annee: int) -> dict:
        """Simuler la consultation Query CDRs"""
        abonne = ABONNES_FICTIFS.get(numero, {})
        if not abonne.get("historique"):
            return {"total": 0, "premiere": None, "derniere": None}

        # Générer des données CDR fictives cohérentes
        total = random.randint(8, 45)
        debut = datetime(annee, mois, 1, 0, 0, 0)
        fin   = datetime(annee, mois, 28, 23, 59, 59)
        premiere = debut + timedelta(hours=random.randint(0, 12))
        derniere  = fin  - timedelta(days=random.randint(1, 5),
                                     hours=random.randint(0, 23))
        return {
            "total":    total,
            "premiere": premiere.strftime("%Y-%m-%d %H:%M:%S"),
            "derniere": derniere.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _generer_abonne_fictif(self, numero: str) -> dict:
        """Générer un abonné fictif cohérent pour les numéros non définis"""
        # Tirage réaliste basé sur les statistiques terrain
        poids = ["Normal"] * 65 + ["Suspend"] * 25 + ["No record found"] * 10
        statut = random.choice(poids)
        return {
            "statut":          statut,
            "historique":      statut == "Normal" and random.random() > 0.3,
            "derniere_session": (
                (datetime.now() - timedelta(days=random.randint(1, 30))
                 ).strftime("%Y-%m-%d %H:%M:%S")
                if statut == "Normal" else None
            ),
        }


# ── Test rapide ────────────────────────────────────────────────
if __name__ == "__main__":
    client = AAAMockClient()
    for num in ["222230001", "222310002", "222230003", "222990999"]:
        st = client.consulter_statut(num)
        rx = client.consulter_radius(num)
        print(f"\n{num} → Statut: {st['status']} | Zone: {st['zone']}")
        print(f"  Radius → Connecté: {rx.get('connecte')} | Trafic: {rx.get('trafic_mb')} MB")
