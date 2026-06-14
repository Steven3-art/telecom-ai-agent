"""
diagnostics.py — Moteur de diagnostic FTTH
==========================================
Reproduit la logique de diagnostic réelle.
Aucune donnée confidentielle.
"""

CENTRAUX = {
    "22": ("Zone Yaoundé Centre",     "CTN",          "Yaoundé",  "Centre"),
    "23": ("Zone Yaoundé Centre",     "CTN",          "Yaoundé",  "Centre"),
    "31": ("Zone Yaoundé Biyem-Assi", "Central BYM",  "Yaoundé",  "Centre"),
    "30": ("Zone Yaoundé Nkomo",      "Central NKM",  "Yaoundé",  "Centre"),
    "27": ("Zone Garoua",             "Central GRA",  "Garoua",   "Nord"),
    "29": ("Zone Maroua",             "Central Mra",  "Maroua",   "Extrême-Nord"),
    "44": ("Zone Bafoussam",          "Central Bfs",  "Bafoussam","Ouest"),
    "33": ("Zone Limbe",              "Central Limbe","Limbe",    "Sud-Ouest"),
    "43": ("Zone Bertoua",            "Central Bertoua","Bertoua","Est"),
    "28": ("Zone Ebolowa-Megong",     "Central Ebw",  "Ebolowa",  "Sud"),
}


def identifier_zone(numero: str) -> dict:
    """Extraire zone/central depuis l'indicatif (digits[3:5])"""
    num = "".join(c for c in str(numero) if c.isdigit())
    if len(num) == 9:
        ind = num[3:5]
        if ind in CENTRAUX:
            z, c, v, r = CENTRAUX[ind]
            return {"indicatif": ind, "zone": z,
                    "central": c, "ville": v, "region": r}
    return {"indicatif": "??", "zone": "Inconnu",
            "central": "?", "ville": "?", "region": "?"}


def generer_diagnostic(statut_aaa: dict, radius: dict) -> dict:
    """
    Générer le diagnostic et l'action recommandée.
    Logique métier identique à la réalité terrain.
    """
    statut = statut_aaa.get("status", "")
    zone   = identifier_zone(statut_aaa.get("numero", ""))

    # ── Cas 1 : Inexistant ────────────────────────────────────
    if statut == "No record found":
        return {
            "categorie": "INEXISTANT",
            "message":   f"❌ {statut_aaa['numero']} — Inexistant dans AAA.",
            "action":    "Vérifier le numéro et le contrat client.",
            "urgence":   "FAIBLE",
            "zone":      zone,
        }

    # ── Cas 2 : Suspendu ─────────────────────────────────────
    if statut in ("Suspend", "Suspended"):
        return {
            "categorie": "SUSPENDU",
            "message":   f"🔴 {statut_aaa['numero']} — Compte suspendu (arrêté de service).",
            "action":    "Contacter le service commercial pour régularisation.",
            "urgence":   "HAUTE",
            "zone":      zone,
        }

    # ── Cas 3 : Normal mais absence d'auth ───────────────────
    connecte = radius.get("connecte", False)
    nb_echecs = radius.get("nb_echecs", 0)
    derniere = radius.get("derniere")

    if not connecte and nb_echecs == 0:
        return {
            "categorie": "ABSENCE_AUTH",
            "message":   (f"🟡 {statut_aaa['numero']} — Actif dans AAA. "
                         f"Absence d'authentification.\n"
                         f"Zone : {zone['zone']} | Central : {zone['central']}"),
            "action":    "CERAF doit investiguer la liaison. Mail à crip.yaounde@camtel.cm",
            "urgence":   "MOYENNE",
            "zone":      zone,
        }

    # ── Cas 4 : Échecs d'authentification ────────────────────
    if not connecte and nb_echecs > 0:
        return {
            "categorie": "ECHEC_AUTH",
            "message":   (f"🟠 {statut_aaa['numero']} — Échecs d'authentification "
                         f"({nb_echecs} tentatives échouées).\n"
                         f"Dernière tentative : {derniere}"),
            "action":    "Vérifier mot de passe. CERAF → mail crip.yaounde@camtel.cm",
            "urgence":   "HAUTE",
            "zone":      zone,
        }

    # ── Cas 5 : Connecté avec trafic ─────────────────────────
    trafic = radius.get("trafic_mb", 0)
    if connecte and trafic > 0:
        return {
            "categorie": "NORMAL_EN_LIGNE",
            "message":   (f"✅ {statut_aaa['numero']} — En ligne et actif.\n"
                         f"IP : {radius.get('ip')} | Trafic : {trafic} MB\n"
                         f"Zone : {zone['zone']}"),
            "action":    "Aucune action requise. Ligne fonctionnelle.",
            "urgence":   "AUCUNE",
            "zone":      zone,
        }

    return {
        "categorie": "INCONNU",
        "message":   f"⚪ {statut_aaa['numero']} — Statut indéterminé.",
        "action":    "Diagnostic manuel requis.",
        "urgence":   "MOYENNE",
        "zone":      zone,
    }
