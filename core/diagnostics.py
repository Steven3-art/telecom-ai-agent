"""
core/diagnostics.py — Fictional demo version
================================================
Maps AAA-style error codes to a diagnosis and a recommended
next step. All company names, domains, and team acronyms in
this file are entirely fictional and created for this hackathon
demo only. No real operator, infrastructure, or staff data is
used anywhere in this project.
"""

import re

# ── Fictional network zones ────────────────────────────────────
CENTRAUX = {
    "22": ("Zone A — Capital Center",  "EX-01", "Capital City",   "Central"),
    "23": ("Zone A — Capital Center",  "EX-01", "Capital City",   "Central"),
    "20": ("Zone B — Capital North",   "EX-02", "Capital City",   "Central"),
    "21": ("Zone B — Capital North",   "EX-02", "Capital City",   "Central"),
    "31": ("Zone C — Capital South",   "EX-03", "Capital City",   "Central"),
    "30": ("Zone D — Capital East",    "EX-04", "Capital City",   "Central"),
    "27": ("Zone E — Northern Hub",    "EX-05", "Northern City",  "North"),
    "29": ("Zone F — Far North Hub",   "EX-06", "Far North City", "Far North"),
    "44": ("Zone G — Western Hub",     "EX-07", "Western City",   "West"),
    "33": ("Zone H — Coastal Hub",     "EX-08", "Coastal City",   "Southwest"),
    "43": ("Zone I — Eastern Hub",     "EX-09", "Eastern City",   "East"),
    "28": ("Zone J — Southern Hub",    "EX-10", "Southern City",  "South"),
    "46": ("Zone K — Coastal South",   "EX-11", "Port City",      "South"),
    "11": ("Zone L — Rural Center",    "EX-12", "Rural Town",     "Central"),
}

# ── Fictional support team contacts ──────────────────────────
NOC_EMAIL            = "noc@afritel-demo.com"
FIELD_OPS_EMAIL      = "field.ops@afritel-demo.com"
ACCESS_SUPPORT_EMAIL = "access.support@afritel-demo.com"
BILLING_OPS_EMAIL    = "billing.ops@afritel-demo.com"

# ── Fictional error-code mapping (illustrative, not real) ────
CODES_ERREUR_AAA = {
    # PASSWORD / BLACKLIST
    "109020102": {
        "message":          "Because of wrong username or password, CHAP authentication for common subscribers failed",
        "categorie":        "MOT_DE_PASSE",
        "reponse_whatsapp": f"Password issue detected. Field Ops must email {NOC_EMAIL} to request a new one.",
        "action_required":  "reset_mdp",
    },
    "109022520": {
        "message":          "Authentication fails because the subscriber is blacklisted",
        "categorie":        "MOT_DE_PASSE",
        "reponse_whatsapp": f"Password issue detected. Field Ops must email {NOC_EMAIL} to request a new one.",
        "action_required":  "reset_mdp",
    },
    "109020109": {
        "message":          "The subscriber has been online",
        "categorie":        "MOT_DE_PASSE",
        "reponse_whatsapp": f"Password issue detected. Field Ops must email {NOC_EMAIL} to request a new one.",
        "action_required":  "reset_mdp",
    },
    # SUSPENSION
    "109020122": {
        "message":          "The subscriber is suspended due to arrears",
        "categorie":        "SUSPENDU",
        "reponse_whatsapp": "Suspended",
        "action_required":  "info_only",
    },
    "109020106": {
        "message":          "Incorrect subscriber status",
        "categorie":        "SUSPENDU",
        "reponse_whatsapp": "Suspended",
        "action_required":  "info_only",
    },
    # AUTHENTICATION FAILURE
    "109020207": {
        "message":          "No record is found in the subscriber-terminal binding table",
        "categorie":        "ECHEC_AUTH",
        "reponse_whatsapp": f"Active in AAA... Authentication failure. Please contact {ACCESS_SUPPORT_EMAIL}.",
        "action_required":  "info_only",
    },
    # CRM/OSS BLOCK
    "109129999": {
        "message":          "Undefined OCS result code in AAA",
        "categorie":        "BLOCAGE_CRM",
        "reponse_whatsapp": f"Active in AAA... Suspended for unpaid invoice or other CRM/OSS block. Please verify billing status, then contact {BILLING_OPS_EMAIL}.",
        "action_required":  "info_only",
    },
    # NO AUTHENTICATION
    "109020018": {
        "message":          "There is no Accounting message received",
        "categorie":        "ABSENCE_AUTH",
        "reponse_whatsapp": f"Active in AAA. No authentication detected. {FIELD_OPS_EMAIL} should investigate.",
        "action_required":  "info_only",
    },
}

# ── Category labels ───────────────────────────────────────────
LABELS_CATEGORIES = {
    "MOT_DE_PASSE":       "Password issue (CHAP/blacklist)",
    "SUSPENDU":           "Suspended account (service stopped)",
    "ECHEC_AUTH":         "Authentication failure (terminal/link)",
    "BLOCAGE_CRM":        "CRM/OSS block (unpaid invoice or other)",
    "ABSENCE_AUTH":       "Active in AAA — no authentication",
    "NORMAL":             "Connected with active traffic (online)",
    "NORMAL_SANS_TRAFIC": "Connected, no traffic (equipment issue)",
    "INEXISTANT":         "Not found in AAA",
    "INCONNU":            "Uncategorized diagnosis",
}

# ── Recommended internal action per category ──────────────────
INTERNAL_ACTIONS = {
    "MOT_DE_PASSE":  "reset_mdp",   # support team resets the password in AAA
    "SUSPENDU":      "info_only",
    "ECHEC_AUTH":    "info_only",
    "BLOCAGE_CRM":   "info_only",
    "ABSENCE_AUTH":  "info_only",
    "NORMAL":        "info_only",
    "INEXISTANT":    "info_only",
}


def identifier_zone(numero: str) -> dict:
    """Identify the network zone from the subscriber number (digits[3:5])"""
    num = re.sub(r"[^\d]", "", str(numero))
    if len(num) == 9:
        ind = num[3:5]
        if ind in CENTRAUX:
            z, c, v, r = CENTRAUX[ind]
            return {"indicatif": ind, "zone": z, "central": c, "ville": v, "region": r}
    return {"indicatif": "??", "zone": "Unknown", "central": "?", "ville": "?", "region": "?"}


def get_info_code(code_erreur: str) -> dict:
    """Look up the diagnosis info for a given error code"""
    return CODES_ERREUR_AAA.get(code_erreur, {
        "message":          f"Unknown code: {code_erreur}",
        "categorie":        "INCONNU",
        "reponse_whatsapp": f"AAA error (code {code_erreur}). Please contact technical support.",
        "action_required":  "info_only",
    })


def generer_diagnostic(statut_aaa: dict, radius: dict) -> dict:
    """
    Generate the full diagnosis based on the mocked AAA platform data.
    """
    statut = statut_aaa.get("status", "")
    numero = statut_aaa.get("numero", "?")
    zone   = identifier_zone(numero)

    # ── CASE 1: Not found ─────────────────────────────────────
    if statut == "No record found":
        return {
            "categorie":        "INEXISTANT",
            "code_erreur":      None,
            "message":          f"{numero} — Not found in AAA.",
            "reponse_whatsapp": "Not found in AAA",
            "action_required":  "info_only",
            "zone":             zone,
        }

    # ── CASE 2: Suspended (direct AAA status) ─────────────────
    if statut in ("Suspend", "Suspended"):
        return {
            "categorie":        "SUSPENDU",
            "code_erreur":      None,
            "message":          f"{numero} — Suspended in AAA (service stopped).",
            "reponse_whatsapp": "Suspended",
            "action_required":  "info_only",
            "zone":             zone,
        }

    # ── CASE 3: Normal — analyze radius error codes ───────────
    if statut == "Normal":
        codes    = radius.get("codes_erreur", {})
        connecte = radius.get("connecte", False)
        trafic   = radius.get("trafic_mb", 0) or 0
        nb_succ  = radius.get("nb_successful", 0)

        if connecte and trafic > 0:
            return {
                "categorie":        "NORMAL",
                "code_erreur":      None,
                "message":          f"{numero} — Connected with active traffic ({trafic} MB).",
                "reponse_whatsapp": "Connected with traffic (online)",
                "action_required":  "info_only",
                "zone":             zone,
            }

        if connecte and trafic == 0:
            return {
                "categorie":        "NORMAL_SANS_TRAFIC",
                "code_erreur":      None,
                "message":          f"{numero} — AAA session active but 0 MB transferred. Likely equipment issue.",
                "reponse_whatsapp": "Connected with NO traffic",
                "action_required":  "info_only",
                "zone":             zone,
            }

        if codes:
            code_principal = max(codes.items(), key=lambda x: x[1])[0]
            info = get_info_code(code_principal)

            if nb_succ > 0 and info["categorie"] in ("MOT_DE_PASSE",):
                return {
                    "categorie":        "ABSENCE_AUTH",
                    "code_erreur":      code_principal,
                    "message":          f"{numero} — Active in AAA. Successful auth this month but intermittent issue.",
                    "reponse_whatsapp": CODES_ERREUR_AAA["109020018"]["reponse_whatsapp"],
                    "action_required":  "info_only",
                    "zone":             zone,
                }

            return {
                "categorie":        info["categorie"],
                "code_erreur":      code_principal,
                "message":          f"{numero} — {info['message']}",
                "reponse_whatsapp": info["reponse_whatsapp"],
                "action_required":  info["action_required"],
                "zone":             zone,
            }

        return {
            "categorie":        "ABSENCE_AUTH",
            "code_erreur":      "109020018",
            "message":          f"{numero} — Active in AAA. No authentication detected.",
            "reponse_whatsapp": CODES_ERREUR_AAA["109020018"]["reponse_whatsapp"],
            "action_required":  "info_only",
            "zone":             zone,
        }

    # ── UNKNOWN CASE ────────────────────────────────────────────
    return {
        "categorie":        "INCONNU",
        "code_erreur":      None,
        "message":          f"{numero} — Unexpected status: {statut}.",
        "reponse_whatsapp": f"Unexpected status ({statut}). Please contact technical support.",
        "action_required":  "info_only",
        "zone":             zone,
    }
