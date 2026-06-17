"""
qwen_interface/main.py — Version finale
========================================
TelecomAI Agent — CRIP Yaoundé / Qwen Cloud
Track 4 : Autopilot Agent

3 types de requêtes détectés automatiquement :
  STATUT       → Consulte AAA → 1 mail diagnostic
  MOT_DE_PASSE → Reset MDP   → 2 mails (CERAF + nouveau MDP)
  CDR          → Historique  → 1 mail avec dates connexions
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
MODEL        = "qwen-plus"
CRIP_EMAIL   = "crip.yaounde@camtel.cm"
CHEF_CERAF   = os.getenv("CHEF_CERAF_EMAIL", "chef.ceraf@camtel.cm")
CATEGORIES_MDP = ("MOT_DE_PASSE", "ECHEC_AUTH")

MOIS_FR = {
    "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,
    "mai":5,"juin":6,"juillet":7,"août":8,"aout":8,
    "septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12
}
MOIS_NOMS = {
    1:"Janvier",2:"Février",3:"Mars",4:"Avril",5:"Mai",6:"Juin",
    7:"Juillet",8:"Août",9:"Septembre",10:"Octobre",11:"Novembre",12:"Décembre"
}

# ── Utilitaires ───────────────────────────────────────────────
def generer_mdp() -> str:
    p = (random.choices(string.ascii_uppercase,k=4) +
         random.choices(string.digits,k=4) +
         random.choices("@#!*",k=2))
    random.shuffle(p); return "".join(p)
    
def simuler_capture_radius(numero: str, code_erreur: str, message: str) -> str:
    """Simuler la capture d'écran Radius Login Log collée dans le mail"""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not code_erreur:
        return ""
    return (
        f"\n"
        f"[Capture Radius Login Log — AAA Platform]\n"
        f"┌─────────────────────────────────────────────────────┐\n"
        f"│  User Name  : {numero}@camnet.cm\n"
        f"│  Date/Heure : {now}\n"
        f"│  Résultat   : Failed({code_erreur})\n"
        f"│  Message    : {message}\n"
        f"└─────────────────────────────────────────────────────┘\n"
    )


def simuler_capture_subscriber(numero: str, statut: str) -> str:
    """Simuler la capture Subscriber Information"""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"\n"
        f"[Capture Subscriber Information — AAA Platform]\n"
        f"┌─────────────────────────────────────────────────────┐\n"
        f"│  Login Name : {numero}@camnet.cm\n"
        f"│  Status     : {statut}\n"
        f"│  Date/Heure : {now}\n"
        f"└─────────────────────────────────────────────────────┘\n"
    )    

def extraire_numero(texte: str) -> str | None:
    m = re.search(r'\b\d{9}\b', texte)
    if m: return m.group()
    try:
        r = client.chat.completions.create(
            model=MODEL, max_tokens=30,
            messages=[
                {"role":"system","content":"Extrais le numéro abonné FTTH 9 chiffres. Réponds UNIQUEMENT avec le numéro ou AUCUN."},
                {"role":"user","content":texte}
            ])
        res = r.choices[0].message.content.strip()
        m2 = re.search(r'\d{9}', res)
        return m2.group() if m2 else None
    except: return None

def analyser_mail(objet: str, corps: str) -> dict:
    """
    Qwen analyse le mail complet et extrait toutes les infos.
    Retourne : {"numero": "...", "type": "...", "mois": [...]}
    """
    prompt = f"""Tu analyses des mails reçus au CRIP CAMTEL Yaoundé 
(Centre Régional IP/Internet). Ces mails viennent d'agences 
commerciales et de CERAF concernant des lignes FTTH.

OBJET DU MAIL : {objet or '(vide)'}
CORPS DU MAIL : {corps}

Extrais ces informations et réponds UNIQUEMENT en JSON valide :
{{
  "numero": "le numéro abonné FTTH à 9 chiffres (ex: 222311395) ou null",
  "type": "STATUT si on demande le statut ou problème connexion, CDR si on demande dates/historique/dernière connexion/authentification, INCONNU sinon",
  "mois": ["Mai 2026", "Juin 2026"] si des mois sont mentionnés sinon null
}}

Exemples de numéros : après 'du', 'LIGNE:', 'ABONNEMENT:', 'le', numéro en objet...
Réponds UNIQUEMENT avec le JSON, sans explication."""

    try:
        r = client.chat.completions.create(
            model=MODEL, max_tokens=100,
            messages=[{"role":"user","content":prompt}]
        )
        import json
        texte_json = r.choices[0].message.content.strip()
        # Nettoyer si Qwen ajoute des backticks
        texte_json = texte_json.replace("```json","").replace("```","").strip()
        data = json.loads(texte_json)
        return {
            "numero": data.get("numero"),
            "type":   data.get("type","STATUT"),
            "mois":   data.get("mois")
        }
    except Exception as e:
        # Fallback regex si Qwen échoue
        import re
        m = re.search(r'\b\d{9}\b', f"{objet} {corps}")
        return {
            "numero": m.group() if m else None,
            "type":   "STATUT",
            "mois":   None
        }

def extraire_mois(texte: str) -> list:
    t = texte.lower()
    annees = re.findall(r'20\d{2}', texte)
    annee = int(annees[0]) if annees else date.today().year
    res = []
    for nom,num in MOIS_FR.items():
        if nom in t and (annee,num) not in res:
            res.append((annee,num))
    return res or None

# ── Préparation mails ─────────────────────────────────────────
def mail_statut(numero, resultat, expediteur):
    zone        = resultat.get("zone",{})
    recommande  = resultat.get("reponse_whatsapp","")
    code_erreur = resultat.get("code_erreur","")
    categorie   = resultat.get("categorie","")
    # Générer la capture simulée selon le cas
    if categorie in ("BLOCAGE_CRM","ECHEC_AUTH","ABSENCE_AUTH","MOT_DE_PASSE"):
        capture = simuler_capture_radius(
            numero, code_erreur, resultat.get("message","")
        )
    elif categorie in ("SUSPENDU","INEXISTANT"):
        capture = simuler_capture_subscriber(
            numero, resultat.get("statut","?")
        )
    elif categorie == "NORMAL_SANS_TRAFIC":
        capture = simuler_capture_subscriber(numero, "Normal — Session active, 0 MB")
    else:
        capture = ""

    prompt = (f"Tu es CRIP CAMTEL Yaoundé. Rédige un mail COURT et PROFESSIONNEL "
              f"pour la ligne {numero} ({zone.get('zone','?')}).\n"
              f"Statut AAA       : {resultat.get('statut','?')}\n"
              f"Recommandation   : {recommande}\n\n"
              f"IMPORTANT : Inclus la recommandation telle quelle. "
              f"Termine le mail avant 'Cordialement'. "
              f"Sois professionnel et concis.")
    try:
        r = client.chat.completions.create(model=MODEL, max_tokens=200,
            messages=[{"role":"user","content":prompt}])
        corps = r.choices[0].message.content.strip()
    except:
        corps = (f"Bonjour,\n\nConcernant la ligne {numero} :\n\n"
                 f"{recommande}\n\nCordialement,\nCRIP Yaoundé")

    # Ajouter la capture DANS le corps du mail
    corps_final = corps + "\n" + capture + f"\nCordialement,\nCRIP Yaoundé — {CRIP_EMAIL}"

    return {"type":"statut","mails":[{
        "a":expediteur,"cc":"",
        "objet":f"[CRIP] Diagnostic AAA — {numero} — {zone.get('ville','Yaoundé')}",
        "corps":corps_final}]}
    try:
        r = client.chat.completions.create(model=MODEL,max_tokens=200,
            messages=[{"role":"user","content":prompt}])
        corps = r.choices[0].message.content.strip()
    except:
        corps = (f"Bonjour,\n\nConcernant la ligne {numero} :\n\n"
                 f"{resultat.get('message','?')}\n\nCordialement,\nCRIP Yaoundé")
    return {"type":"statut","mails":[{
        "a":expediteur,"cc":"",
        "objet":f"[CRIP] Diagnostic AAA — {numero} — {zone.get('ville','Yaoundé')}",
        "corps":corps}]}

def mail_mdp(numero, resultat, expediteur):
    zone = resultat.get("zone",{})
    mdp  = generer_mdp()
    try:
        r = client.chat.completions.create(model=MODEL,max_tokens=150,
            messages=[{"role":"user","content":
                f"CRIP CAMTEL Yaoundé. Mail COURT : problème mot de passe "
                f"(CHAP failed ou Blacklist) sur ligne {numero}. "
                f"CERAF doit envoyer mail à {CRIP_EMAIL} pour nouveau MDP. "
                f"Ajouter en fin : 'NB : Capture d'écran Radius Login Log "
                f"en pièce jointe (erreur visible).' Sois bref."}])
        corps1 = r.choices[0].message.content.strip()
    except:
        corps1 = (f"Bonjour,\n\nProblème de mot de passe détecté sur la ligne {numero}.\n"
                  f"Le CERAF doit envoyer un mail à {CRIP_EMAIL} pour demander un nouveau mot de passe.\n\n"
                  f"Cordialement,\nCRIP Yaoundé")
    corps2 = (f"Bonjour,\n\nSuite à votre demande pour la ligne {numero} "
              f"({zone.get('zone','?')}) :\n\n"
              f"Nous avons réinitialisé le mot de passe dans la plateforme AAA.\n\n"
              f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
              f"  Numéro      : {numero}\n"
              f"  Nouveau MDP : {mdp}\n"
              f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
              f"Merci de configurer ce mot de passe côté client via NCE.\n"
              f"Le client devra redémarrer son équipement ensuite.\n\n"
              f"Cordialement,\nCRIP Yaoundé — {CRIP_EMAIL}")
              # Ajouter capture Radius Login Log dans mail 1
    capture_radius = simuler_capture_radius(
        numero, "109020102", "CHAP authentication failed / Subscriber blacklisted"
    )
    corps1 = corps1 + "\n" + capture_radius
    return {"type":"mot_de_passe","nouveau_mdp":mdp,"mails":[
        {"a":expediteur,"cc":"","objet":f"[CRIP] Problème mot de passe — {numero}","corps":corps1},
        {"a":expediteur,"cc":CHEF_CERAF,"objet":f"[CRIP] Nouveau mot de passe AAA — {numero}","corps":corps2}
    ]}

def mail_cdr(numero, zone, mois_liste, expediteur):
    aaa = AAAMockClient()
    if not mois_liste:
        auj = date.today()
        mois_liste = [(auj.year, auj.month)]
    lignes = []
    for (annee,mois) in mois_liste:
        cdr = aaa.consulter_cdr(numero, mois, annee)
        nom = f"{MOIS_NOMS[mois]} {annee}"
        if cdr["total"] == 0:
            lignes.append(f"- {nom} = Aucune authentification à ce jour")
        else:
            p = cdr["premiere"].replace(" "," à ",1) if cdr["premiere"] else "N/A"
            d = cdr["derniere"].replace(" "," à ",1) if cdr["derniere"] else "N/A"
            lignes.append(f"- {nom} = Première authentification le {p}. "
                          f"Dernière authentification le {d}")
    mois_str = " / ".join(f"{MOIS_NOMS[m]} {a}" for a,m in mois_liste)
    corps = (f"Bonjour,\n\nSuite à votre demande pour la ligne "
             f"{numero} ({zone.get('zone','?')}) :\n\n"
             + "\n".join(lignes) +
             f"\n\nCordialement,\nCRIP Yaoundé — {CRIP_EMAIL}")
    return {"type":"cdr","mails":[{
        "a":expediteur,"cc":"",
        "objet":f"[CRIP] Historique connexions — {numero} — {mois_str}",
        "corps":corps}]}

# ── Affichage ─────────────────────────────────────────────────

def convertir_mois(mois_texte: list) -> list:
    """Convertir ["Mai 2026","Juin 2026"] → [(2026,5),(2026,6)]"""
    if not mois_texte: return None
    resultat = []
    for m in mois_texte:
        for nom,num in MOIS_FR.items():
            if nom in m.lower():
                annees = re.findall(r'20\d{2}', m)
                annee = int(annees[0]) if annees else date.today().year
                if (annee,num) not in resultat:
                    resultat.append((annee,num))
    return resultat or None

def afficher(prep):
    mails = prep.get("mails",[])
    print(f"\n{'═'*60}")
    icons = {"statut":"📋","mot_de_passe":"🔑","cdr":"📅"}
    labels = {"statut":"STATUT","mot_de_passe":"MOT DE PASSE","cdr":"CDR HISTORIQUE"}
    t = prep.get("type","?")
    print(f"{icons.get(t,'📧')} CAS {labels.get(t,'?')} — {len(mails)} mail(s)")
    if t == "mot_de_passe":
        print(f"   ⚠️  Changer MDP dans AAA avant d'envoyer !")
        print(f"   🔑 Nouveau MDP : {prep.get('nouveau_mdp','?')}")
    print(f"{'═'*60}")
    for i,mail in enumerate(mails,1):
        print(f"\n{'─'*60}  📧 MAIL {i}/{len(mails)}")
        print(f"  À      : {mail['a']}")
        if mail.get("cc"): print(f"  CC     : {mail['cc']}")
        print(f"  Objet  : {mail['objet']}")
        print(f"{'─'*60}")
        print(mail["corps"])
    print(f"\n{'═'*60}")

# ── Pipeline principal ────────────────────────────────────────
def traiter(corps: str, objet: str = "", expediteur: str = "agence@camtel.cm") -> dict:
    print(f"\n{'═'*60}")
    print(f"📨 Mail : {corps[:60]}...")
    print(f"{'═'*60}")

    # Qwen analyse tout le mail
    print("🤖 Analyse Qwen du mail...")
    analyse = analyser_mail(objet, corps)
    numero  = analyse.get("numero")
    type_req = analyse.get("type","STATUT")
    mois    = analyse.get("mois")

    print(f"   ✅ Numéro : {numero}")
    print(f"   ✅ Type   : {type_req}")
    if mois: print(f"   ✅ Mois   : {mois}")

    if not numero:
        print("❌ Numéro introuvable")
        return {"succes":False,"erreur":"Numéro FTTH introuvable"}

    agent = TelecomAIAgent()

    if type_req == "CDR":
        # Convertir mois texte en liste (annee, mois)
        mois_liste = convertir_mois(mois) if mois else None
        res  = agent.traiter(numero)
        prep = mail_cdr(numero, res.get("zone",{}), mois_liste, expediteur)

    else:  # STATUT — AAA décide du vrai diagnostic
        res  = agent.traiter(numero)
        cat  = res.get("categorie","INCONNU")
        print(f"   🔍 AAA → {cat}")
        if cat in CATEGORIES_MDP:
            prep = mail_mdp(numero, res, expediteur)
        else:
            prep = mail_statut(numero, res, expediteur)

    afficher(prep)
    prep.update({"succes":True,"numero":numero})
    return prep
# ── CLI ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n"+"="*60)
    print("  🤖 TELECOMAI AGENT — CRIP Yaoundé / Qwen Cloud")
    print("  Track 4 : Autopilot Agent")
    print("="*60)
    print("\nExemples réels :")
    print("  → 'Prière vérifier le statut du 222230906'")
    print("  → 'le numero 222316544 a un problème de mot de passe'")
    print("  → 'date de la dernière authentification Mai Juin 2026 LIGNE: 222302628'")
    print("\nTapez 'quit' pour quitter\n")

    while True:
        try:
            texte = input("📨 Contenu du mail : ").strip()
            if texte.lower() in ("quit","exit","q"):
                print("\n👋 Au revoir !\n"); break
            if not texte: continue
            objet = input("📌 Objet du mail (ENTER si vide) : ").strip()
            exp   = input("📧 Expéditeur (ENTER = agence@camtel.cm) : ").strip()
            traiter(texte, objet, exp or "agence@camtel.cm")
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir !\n"); break
