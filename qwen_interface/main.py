"""
qwen_interface/main.py — Internal team interface (fictional demo)
====================================================================
TelecomAI Agent — NOC internal interface
Track 4: Autopilot Agent

This file is part of a hackathon demo project. All company names,
domains, and team identifiers are entirely fictional. No real
operator, infrastructure, or staff information is used anywhere.

3 request types are detected automatically:
  STATUS    -> Query AAA -> 1 diagnostic email
  PASSWORD  -> Reset password -> 2 emails (NOC + Field Ops, new password)
  CDR       -> Connection history -> 1 email with connection dates
"""

import os, sys, re, random, string
from datetime import date
from openai import OpenAI
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.agent import TelecomAIAgent
from core.aaa_mock import AAAMockClient

load_dotenv()

client = OpenAI(
    api_key=os.getenv("QWEN_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)
MODEL = "qwen-plus"

# ── Fictional internal team contacts ───────────────────────────
NOC_EMAIL      = "noc@afritel-demo.com"
FIELD_OPS_LEAD = os.getenv("FIELD_OPS_LEAD_EMAIL", "field.ops.lead@afritel-demo.com")
CATEGORIES_MDP = ("MOT_DE_PASSE", "ECHEC_AUTH")

MOIS_FR = {
    "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,
    "mai":5,"juin":6,"juillet":7,"août":8,"aout":8,
    "septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12
}
MOIS_NOMS = {
    1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
    7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"
}

# ── Utilities ────────────────────────────────────────────────
def generer_mdp() -> str:
    p = (random.choices(string.ascii_uppercase,k=4) +
         random.choices(string.digits,k=4) +
         random.choices("@#!*",k=2))
    random.shuffle(p); return "".join(p)


def simuler_capture_radius(numero: str, code_erreur: str, message: str) -> str:
    """Simulate the Radius/Auth log screenshot pasted into the email body"""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not code_erreur:
        return ""
    return (
        f"\n"
        f"[Auth log capture — AAA platform]\n"
        f"+-------------------------------------------------------+\n"
        f"|  User name  : {numero}@demo-isp.net\n"
        f"|  Timestamp  : {now}\n"
        f"|  Result     : Failed({code_erreur})\n"
        f"|  Message    : {message}\n"
        f"+-------------------------------------------------------+\n"
    )


def simuler_capture_subscriber(numero: str, statut: str) -> str:
    """Simulate the Subscriber Information screenshot pasted into the email body"""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"\n"
        f"[Subscriber info capture — AAA platform]\n"
        f"+-------------------------------------------------------+\n"
        f"|  Login name : {numero}@demo-isp.net\n"
        f"|  Status     : {statut}\n"
        f"|  Timestamp  : {now}\n"
        f"+-------------------------------------------------------+\n"
    )


def analyser_mail(objet: str, corps: str) -> dict:
    """
    Use Qwen to analyze the full email (subject + body) and extract
    the subscriber number, the request type, and any mentioned months.
    """
    prompt = f"""You analyze emails received by a fictional ISP's
internal Network Operations Center (NOC). These emails come from
sales agencies and field teams about fiber (FTTH) subscriber lines.

SUBJECT: {objet or '(empty)'}
BODY: {corps}

Extract this information and respond ONLY with valid JSON:
{{
  "numero": "the 9-digit subscriber number (e.g. 222311395) or null",
  "type": "STATUS if asking about status or connection issue, CDR if asking about dates/history/last connection/authentication, UNKNOWN otherwise",
  "mois": ["May 2026", "June 2026"] if specific months are mentioned, else null
}}

The number may appear after words like 'line', 'subscriber', 'number', in the subject, or anywhere else.
Respond ONLY with the JSON, no explanation."""

    try:
        r = client.chat.completions.create(
            model=MODEL, max_tokens=100,
            messages=[{"role":"user","content":prompt}]
        )
        import json
        texte_json = r.choices[0].message.content.strip()
        texte_json = texte_json.replace("```json","").replace("```","").strip()
        data = json.loads(texte_json)
        return {
            "numero": data.get("numero"),
            "type":   data.get("type","STATUS"),
            "mois":   data.get("mois")
        }
    except Exception:
        m = re.search(r'\b\d{9}\b', f"{objet} {corps}")
        return {"numero": m.group() if m else None, "type": "STATUS", "mois": None}


def convertir_mois(mois_texte: list) -> list:
    """Convert ["May 2026","June 2026"] -> [(2026,5),(2026,6)]"""
    if not mois_texte:
        return None
    MOIS_EN = {
        "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
        "july":7,"august":8,"september":9,"october":10,"november":11,"december":12
    }
    resultat = []
    for m in mois_texte:
        ml = m.lower()
        for nom, num in MOIS_EN.items():
            if nom in ml:
                annees = re.findall(r'20\d{2}', m)
                annee = int(annees[0]) if annees else date.today().year
                if (annee, num) not in resultat:
                    resultat.append((annee, num))
    return resultat or None


# ── Email preparation ──────────────────────────────────────────
def mail_statut(numero, resultat, expediteur):
    zone        = resultat.get("zone", {})
    recommande  = resultat.get("reponse_whatsapp", "")
    code_erreur = resultat.get("code_erreur", "")
    categorie   = resultat.get("categorie", "")

    if categorie in ("BLOCAGE_CRM", "ECHEC_AUTH", "ABSENCE_AUTH", "MOT_DE_PASSE"):
        capture = simuler_capture_radius(numero, code_erreur, resultat.get("message",""))
    elif categorie in ("SUSPENDU", "INEXISTANT"):
        capture = simuler_capture_subscriber(numero, resultat.get("statut","?"))
    elif categorie == "NORMAL_SANS_TRAFIC":
        capture = simuler_capture_subscriber(numero, "Normal — active session, 0 MB")
    else:
        capture = ""

    prompt = (f"You work at the NOC of a fictional ISP. Write a SHORT, "
              f"PROFESSIONAL email for line {numero} ({zone.get('zone','?')}).\n"
              f"AAA status     : {resultat.get('statut','?')}\n"
              f"Recommendation : {recommande}\n\n"
              f"IMPORTANT: include the recommendation as-is. "
              f"Do NOT include any closing or signature (no 'Best regards', "
              f"no name) — that will be added separately. "
              f"Be professional and concise.")
    try:
        r = client.chat.completions.create(model=MODEL, max_tokens=200,
            messages=[{"role":"user","content":prompt}])
        corps = r.choices[0].message.content.strip()
    except Exception:
        corps = f"Hello,\n\nRegarding line {numero}:\n\n{recommande}"

    corps_final = corps + "\n" + capture + f"\nBest regards,\nNOC — AfriTel"

    return {"type":"statut","mails":[{
        "a":expediteur,"cc":"",
        "objet":f"[NOC] AAA diagnosis — {numero} — {zone.get('ville','Capital City')}",
        "corps":corps_final}]}


def mail_mdp(numero, resultat, expediteur):
    zone = resultat.get("zone", {})
    mdp  = generer_mdp()
    try:
        r = client.chat.completions.create(model=MODEL, max_tokens=150,
            messages=[{"role":"user","content":
                f"You work at the NOC of a fictional ISP. Write a SHORT email: "
                f"password issue (CHAP failed or blacklist) on line {numero}. "
                f"Field Ops must email {NOC_EMAIL} for a new password. Be brief."}])
        corps1 = r.choices[0].message.content.strip()
    except Exception:
        corps1 = (f"Hello,\n\nA password issue was detected on line {numero}.\n"
                  f"Field Ops must email {NOC_EMAIL} to request a new password.\n\n"
                  f"Best regards,\nNOC — AfriTel")

    capture_radius = simuler_capture_radius(
        numero, "109020102", "CHAP authentication failed / subscriber blacklisted"
    )
    corps1 = corps1 + "\n" + capture_radius

    corps2 = (f"Hello,\n\nFollowing your request for line {numero} "
              f"({zone.get('zone','?')}):\n\n"
              f"The password has been reset on the AAA platform.\n\n"
              f"-------------------------------\n"
              f"  Number      : {numero}\n"
              f"  New password: {mdp}\n"
              f"-------------------------------\n\n"
              f"Please configure this password on the customer's line "
              f"via the provisioning tool.\n"
              f"The customer should restart their equipment afterward.\n\n"
              f"Best regards,\nNOC — AfriTel ({NOC_EMAIL})")

    return {"type":"mot_de_passe","nouveau_mdp":mdp,"mails":[
        {"a":expediteur,"cc":"","objet":f"[NOC] Password issue — {numero}","corps":corps1},
        {"a":expediteur,"cc":FIELD_OPS_LEAD,"objet":f"[NOC] New AAA password — {numero}","corps":corps2}
    ]}


def mail_cdr(numero, zone, mois_liste, expediteur):
    aaa = AAAMockClient()
    if not mois_liste:
        auj = date.today()
        mois_liste = [(auj.year, auj.month)]
    lignes = []
    for (annee, mois) in mois_liste:
        cdr = aaa.consulter_cdr(numero, mois, annee)
        nom = f"{MOIS_NOMS[mois]} {annee}"
        if cdr["total"] == 0:
            lignes.append(f"- {nom} = No authentication on record")
        else:
            p = cdr["premiere"].replace(" "," at ",1) if cdr["premiere"] else "N/A"
            d = cdr["derniere"].replace(" "," at ",1) if cdr["derniere"] else "N/A"
            lignes.append(f"- {nom} = First authentication on {p}. "
                          f"Last authentication on {d}")
    mois_str = " / ".join(f"{MOIS_NOMS[m]} {a}" for a,m in mois_liste)
    corps = (f"Hello,\n\nFollowing your request for line "
             f"{numero} ({zone.get('zone','?')}):\n\n"
             + "\n".join(lignes) +
             f"\n\nBest regards,\nNOC — AfriTel ({NOC_EMAIL})")
    return {"type":"cdr","mails":[{
        "a":expediteur,"cc":"",
        "objet":f"[NOC] Connection history — {numero} — {mois_str}",
        "corps":corps}]}


# ── Display ──────────────────────────────────────────────────
def afficher(prep):
    mails = prep.get("mails",[])
    print(f"\n{'='*60}")
    icons  = {"statut":"[STATUS]","mot_de_passe":"[PASSWORD]","cdr":"[CDR]"}
    labels = {"statut":"STATUS","mot_de_passe":"PASSWORD","cdr":"CDR HISTORY"}
    t = prep.get("type","?")
    print(f"{icons.get(t,'[MAIL]')} CASE {labels.get(t,'?')} — {len(mails)} email(s)")
    if t == "mot_de_passe":
        print(f"   Reminder: reset the password in AAA before sending!")
        print(f"   New password: {prep.get('nouveau_mdp','?')}")
    print(f"{'='*60}")
    for i,mail in enumerate(mails,1):
        print(f"\n{'-'*60}  EMAIL {i}/{len(mails)}")
        print(f"  To     : {mail['a']}")
        if mail.get("cc"): print(f"  CC     : {mail['cc']}")
        print(f"  Subject: {mail['objet']}")
        print(f"{'-'*60}")
        print(mail["corps"])
    print(f"\n{'='*60}")


# ── Main pipeline ────────────────────────────────────────────
def traiter(corps: str, objet: str = "", expediteur: str = "agency@afritel-demo.com") -> dict:
    print(f"\n{'='*60}")
    print(f"Email: {corps[:60]}")
    print(f"{'='*60}")

    print("Analyzing email with Qwen...")
    analyse  = analyser_mail(objet, corps)
    numero   = analyse.get("numero")
    type_req = analyse.get("type","STATUS")
    mois     = analyse.get("mois")

    print(f"   Number: {numero}")
    print(f"   Type  : {type_req}")
    if mois: print(f"   Months: {mois}")

    if not numero:
        print("Number not found")
        return {"succes":False,"erreur":"Subscriber number not found"}

    agent = TelecomAIAgent()

    if type_req == "CDR":
        mois_liste = convertir_mois(mois) if mois else None
        res  = agent.traiter(numero)
        prep = mail_cdr(numero, res.get("zone",{}), mois_liste, expediteur)
    else:
        res = agent.traiter(numero)
        cat = res.get("categorie","INCONNU")
        print(f"   AAA -> {cat}")
        if cat in CATEGORIES_MDP:
            prep = mail_mdp(numero, res, expediteur)
        else:
            prep = mail_statut(numero, res, expediteur)

    afficher(prep)
    prep.update({"succes":True,"numero":numero})
    return prep


# ── CLI ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n"+"="*60)
    print("  TELECOMAI AGENT — NOC internal interface / Qwen Cloud")
    print("  Track 4: Autopilot Agent")
    print("="*60)
    print("\nExample requests:")
    print("  -> 'Please check the status of line 222230906'")
    print("  -> 'subscriber 222316544 has a password issue'")
    print("  -> 'last authentication dates for May and June 2026 - line 222302628'")
    print("\nType 'quit' to exit\n")

    while True:
        try:
            texte = input("Email body: ").strip()
            if texte.lower() in ("quit","exit","q"):
                print("\nSession ended\n"); break
            if not texte: continue
            objet = input("Email subject (ENTER if empty): ").strip()
            exp   = input("Sender (ENTER = agency@afritel-demo.com): ").strip()
            traiter(texte, objet, exp or "agency@afritel-demo.com")
        except KeyboardInterrupt:
            print("\n\nSession ended\n"); break
