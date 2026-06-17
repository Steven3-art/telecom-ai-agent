"""
core/diagnostics.py — Version réelle CAMTEL
=============================================
Mapping COMPLET des codes d'erreur AAA → diagnostic → réponse.
Source : Dictionnaire CODES_ERREUR_AAA CAMTEL officiel.
Données fictives pour la démo — logique 100% réelle.
"""

import re

# ── Centraux téléphoniques ────────────────────────────────────
CENTRAUX = {
    "22": ("Zone Yaoundé Centre",     "CTN",           "Yaoundé",  "Centre"),
    "23": ("Zone Yaoundé Centre",     "CTN",           "Yaoundé",  "Centre"),
    "20": ("Zone Yaoundé Jamot",      "Central JMT",   "Yaoundé",  "Centre"),
    "21": ("Zone Yaoundé Jamot",      "Central JMT",   "Yaoundé",  "Centre"),
    "31": ("Zone Yaoundé Biyem-Assi", "Central BYM",   "Yaoundé",  "Centre"),
    "30": ("Zone Yaoundé Nkomo",      "Central NKM",   "Yaoundé",  "Centre"),
    "27": ("Zone Garoua",             "Central GRA",   "Garoua",   "Nord"),
    "29": ("Zone Maroua",             "Central Mra",   "Maroua",   "Extrême-Nord"),
    "44": ("Zone Bafoussam",          "Central Bfs",   "Bafoussam","Ouest"),
    "33": ("Zone Limbe",              "Central Limbe", "Limbe",    "Sud-Ouest"),
    "43": ("Zone Bertoua",            "Central Bertoua","Bertoua", "Est"),
    "28": ("Zone Ebolowa-Megong",     "Central Ebw",   "Ebolowa",  "Sud"),
    "46": ("Zone Kribi-Nyete",        "Central Kbi",   "Kribi",    "Sud"),
    "11": ("Zone Mbalmayo",           "Central MBY",   "Mbalmayo", "Centre"),
}

# ── Mapping officiel codes erreur AAA → diagnostic CAMTEL ────
CODES_ERREUR_AAA = {
    # MOT DE PASSE / BLACKLIST
    "109020102": {
        "message":          "Because of wrong username or password, CHAP authentication for common subscribers failed",
        "categorie":        "MOT_DE_PASSE",
        "reponse_whatsapp": "problème de mot passe CERAF doit faire le mail à crip.yaounde@camtel.cm pour avoir un nouveau",
        "action_crip":      "reset_mdp",
    },
    "109022520": {
        "message":          "Authentication fails because the subscriber is blacklisted",
        "categorie":        "MOT_DE_PASSE",
        "reponse_whatsapp": "problème de mot passe CERAF doit faire le mail à crip.yaounde@camtel.cm pour avoir un nouveau",
        "action_crip":      "reset_mdp",
    },
    "109020109": {
        "message":          "The subscriber has been online",
        "categorie":        "MOT_DE_PASSE",
        "reponse_whatsapp": "problème de mot passe CERAF doit faire le mail à crip.yaounde@camtel.cm pour avoir un nouveau",
        "action_crip":      "reset_mdp",
    },
    # SUSPENSION
    "109020122": {
        "message":          "The subscriber is suspended due to arrears",
        "categorie":        "SUSPENDU",
        "reponse_whatsapp": "Suspendu",
        "action_crip":      "info_only",
    },
    "109020106": {
        "message":          "Incorrect subscriber status",
        "categorie":        "SUSPENDU",
        "reponse_whatsapp": "Suspendu",
        "action_crip":      "info_only",
    },
    # ÉCHEC AUTHENTIFICATION
    "109020207": {
        "message":          "No record is found in the subscriber-terminal binding table",
        "categorie":        "ECHEC_AUTH",
        "reponse_whatsapp": "Actif AAA... Echec d'authentification B/V contacter CRAF_DCRA@camtel.cm",
        "action_crip":      "info_only",
    },
    # BLOCAGE CRM/OSS
    "109129999": {
        "message":          "Undefined OCS result code in AAA",
        "categorie":        "BLOCAGE_CRM",
        "reponse_whatsapp": "Actif AAA... Suspendu pour impayé ou autre blocage dans CRM / OSS .. B/V vouloir vérifier que le client est à jour dans CBS... si ok Contacter SPIF@camtel.local",
        "action_crip":      "info_only",
    },
    # ABSENCE AUTHENTIFICATION
    "109020018": {
        "message":          "There is no Accounting message received",
        "categorie":        "ABSENCE_AUTH",
        "reponse_whatsapp": "Actif dans AAA. Absence d'authentification. CERAF pour investigations",
        "action_crip":      "info_only",
    },
}

# ── Libellés des catégories ───────────────────────────────────
LABELS_CATEGORIES = {
    "MOT_DE_PASSE":  "Problème mot de passe (CHAP/Blacklist)",
    "SUSPENDU":      "Compte suspendu (arrêté de service)",
    "ECHEC_AUTH":    "Échec d'authentification (terminal/liaison)",
    "BLOCAGE_CRM":   "Blocage CRM/OSS (impayé ou autre)",
    "ABSENCE_AUTH":  "Actif AAA — Absence d'authentification",
    "NORMAL":        "Connecté avec trafic actif (Internet OK)",
    "NORMAL_SANS_TRAFIC": "Connecté sans trafic (problème équipement)",
    "INEXISTANT":    "Inexistant dans AAA",
    "INCONNU":       "Diagnostic non catégorisé",
}

# ── Actions CRIP par catégorie ────────────────────────────────
ACTIONS_CRIP = {
    "MOT_DE_PASSE":  "reset_mdp",   # CRIP change le MDP dans AAA
    "SUSPENDU":      "info_only",   # Juste informer
    "ECHEC_AUTH":    "info_only",
    "BLOCAGE_CRM":   "info_only",
    "ABSENCE_AUTH":  "info_only",
    "NORMAL":        "info_only",
    "INEXISTANT":    "info_only",
}


def identifier_zone(numero: str) -> dict:
    """Identifier la zone/central depuis l'indicatif (digits[3:5])"""
    num = re.sub(r"[^\d]", "", str(numero))
    if len(num) == 9:
        ind = num[3:5]
        if ind in CENTRAUX:
            z, c, v, r = CENTRAUX[ind]
            return {"indicatif":ind,"zone":z,"central":c,"ville":v,"region":r}
    return {"indicatif":"??","zone":"Inconnu","central":"?","ville":"?","region":"?"}


def get_info_code(code_erreur: str) -> dict:
    """Obtenir les informations d'un code erreur AAA"""
    return CODES_ERREUR_AAA.get(code_erreur, {
        "message":          f"Code inconnu : {code_erreur}",
        "categorie":        "INCONNU",
        "reponse_whatsapp": f"Erreur AAA (code {code_erreur}). Contacter support technique.",
        "action_crip":      "info_only",
    })


def generer_diagnostic(statut_aaa: dict, radius: dict) -> dict:
    """
    Générer le diagnostic complet basé sur les données AAA.
    Utilise CODES_ERREUR_AAA pour les réponses exactes CAMTEL.
    """
    statut = statut_aaa.get("status", "")
    numero = statut_aaa.get("numero", "?")
    zone   = identifier_zone(numero)

    # ── CAS 1 : Inexistant ───────────────────────────────────
    if statut == "No record found":
        return {
            "categorie":        "INEXISTANT",
            "code_erreur":      None,
            "message":          f"{numero} — Inexistant dans AAA.",
            "reponse_whatsapp": "Inexistant dans AAA",
            "action_crip":      "info_only",
            "zone":             zone,
        }

    # ── CAS 2 : Suspendu (statut AAA direct) ─────────────────
    if statut in ("Suspend", "Suspended"):
        return {
            "categorie":        "SUSPENDU",
            "code_erreur":      None,
            "message":          f"{numero} — Compte suspendu dans AAA (arrêté de service).",
            "reponse_whatsapp": "Suspendu",
            "action_crip":      "info_only",
            "zone":             zone,
        }

    # ── CAS 3 : Normal — analyser les codes erreur radius ────
    if statut == "Normal":
        codes = radius.get("codes_erreur", {})
        connecte = radius.get("connecte", False)
        trafic   = radius.get("trafic_mb", 0) or 0
        nb_succ  = radius.get("nb_successful", 0)

        # Connecté avec trafic
        if connecte and trafic > 0:
            return {
                "categorie":        "NORMAL",
                "code_erreur":      None,
                "message":          f"{numero} — Connecté avec trafic actif ({trafic} MB).",
                "reponse_whatsapp": "Connecté avec trafic (Internet OK)",
                "action_crip":      "info_only",
                "zone":             zone,
            }

        # Connecté sans trafic
        if connecte and trafic == 0:
            return {
                "categorie":        "NORMAL_SANS_TRAFIC",
                "code_erreur":      None,
                "message":          f"{numero} — Session AAA active mais 0 MB transféré. Problème équipement probable.",
                "reponse_whatsapp": "Connecté SANS trafic",
                "action_crip":      "info_only",
                "zone":             zone,
            }

        # Codes erreur présents → utiliser CODES_ERREUR_AAA
        if codes:
            # Prendre le code le plus fréquent
            code_principal = max(codes.items(), key=lambda x: x[1])[0]
            info = get_info_code(code_principal)

            # Si Successful quand même → absence auth (connexion intermittente)
            if nb_succ > 0 and info["categorie"] in ("MOT_DE_PASSE",):
                return {
                    "categorie":        "ABSENCE_AUTH",
                    "code_erreur":      code_principal,
                    "message":          f"{numero} — Actif AAA. Authentification réussie ce mois mais problème intermittent.",
                    "reponse_whatsapp": CODES_ERREUR_AAA["109020018"]["reponse_whatsapp"],
                    "action_crip":      "info_only",
                    "zone":             zone,
                }

            return {
                "categorie":        info["categorie"],
                "code_erreur":      code_principal,
                "message":          f"{numero} — {info['message']}",
                "reponse_whatsapp": info["reponse_whatsapp"],
                "action_crip":      info["action_crip"],
                "zone":             zone,
            }

        # Aucun code erreur ET pas de connexion → Absence auth
        return {
            "categorie":        "ABSENCE_AUTH",
            "code_erreur":      "109020018",
            "message":          f"{numero} — Actif dans AAA. Absence d'authentification.",
            "reponse_whatsapp": CODES_ERREUR_AAA["109020018"]["reponse_whatsapp"],
            "action_crip":      "info_only",
            "zone":             zone,
        }

    # ── CAS INCONNU ───────────────────────────────────────────
    return {
        "categorie":        "INCONNU",
        "code_erreur":      None,
        "message":          f"{numero} — Statut inattendu : {statut}.",
        "reponse_whatsapp": f"Statut inattendu ({statut}). Contacter support technique.",
        "action_crip":      "info_only",
        "zone":             zone,
    }
