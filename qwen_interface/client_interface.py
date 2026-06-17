"""
qwen_interface/client_interface.py
====================================
TelecomAI Agent — Interface CLIENT (WhatsApp simulé)
Track 4 : Autopilot Agent

Réutilise le même core (aaa_mock + diagnostics + agent)
mais génère des réponses SIMPLIFIÉES pour les clients finaux,
sans jargon technique ni codes d'erreur.
"""

import os, sys, re, random, string
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.agent import TelecomAIAgent

load_dotenv()

client = OpenAI(
    api_key=os.getenv("QWEN_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)
MODEL = "qwen-plus"

# ── Messages simplifiés par catégorie (zéro jargon technique) ──
MESSAGES_CLIENT = {
    "NORMAL": {
        "emoji": "✅",
        "resume": "Votre ligne fonctionne normalement et est bien connectée",
        "conseil": "Si vous ressentez un débit faible alors que la ligne "
                   "est active, cela vient généralement d'un facteur local : "
                   "trop d'appareils connectés en même temps, position du "
                   "routeur (murs, distance), téléchargements en arrière-plan, "
                   "ou mot de passe WiFi partagé par d'autres personnes. "
                   "Un test de débit en filaire (câble Ethernet) donne souvent "
                   "un résultat plus fiable qu'en WiFi."
    },
    "NORMAL_SANS_TRAFIC": {
        "emoji": "⚠️",
        "resume": "Votre ligne est active mais aucune donnée ne circule",
        "conseil": "Merci de vérifier les voyants de votre routeur (ONT) "
                   "et de le redémarrer. Si le problème persiste, un "
                   "technicien sera envoyé."
    },
    "ABSENCE_AUTH": {
        "emoji": "🔧",
        "resume": "Un problème technique a été détecté sur votre ligne",
        "conseil": "Notre équipe technique a été automatiquement notifiée "
                   "et va investiguer. Délai estimé : 2 à 4 heures."
    },
    "MOT_DE_PASSE": {
        "emoji": "🔑",
        "resume": "Un problème d'identification a été détecté sur votre ligne",
        "conseil": "Nos équipes techniques procèdent à la régularisation. "
                   "Votre connexion sera rétablie sous peu sans action de "
                   "votre part."
    },
    "ECHEC_AUTH": {
        "emoji": "🔧",
        "resume": "Votre équipement n'arrive pas à s'identifier sur le réseau",
        "conseil": "Merci de vérifier que votre routeur (ONT) est bien "
                   "connecté et alimenté. Si besoin, contactez notre support."
    },
    "BLOCAGE_CRM": {
        "emoji": "📋",
        "resume": "Une vérification administrative est nécessaire sur votre compte",
        "conseil": "Merci de vérifier votre situation (facturation à jour) "
                   "auprès de votre agence CAMTEL la plus proche."
    },
    "SUSPENDU": {
        "emoji": "🔴",
        "resume": "Votre ligne est actuellement suspendue",
        "conseil": "Merci de vous rapprocher de votre agence CAMTEL pour "
                   "régulariser votre situation et réactiver votre connexion."
    },
    "INEXISTANT": {
        "emoji": "❓",
        "resume": "Ce numéro n'est pas reconnu dans notre système",
        "conseil": "Merci de vérifier le numéro fourni ou de contacter "
                   "votre agence CAMTEL pour assistance."
    },
    "INCONNU": {
        "emoji": "❓",
        "resume": "Une vérification supplémentaire est nécessaire",
        "conseil": "Notre équipe support va vous recontacter rapidement."
    },
}


def generer_ticket() -> str:
    """Générer un numéro de ticket de suivi"""
    date_str = datetime.now().strftime("%Y%m%d")
    suffix   = "".join(random.choices(string.digits, k=4))
    return f"FTTH-{date_str}-{suffix}"


def extraire_numero_client(texte: str) -> str | None:
    """Extraire le numéro FTTH d'un message client"""
    m = re.search(r'\b\d{9}\b', texte)
    if m:
        return m.group()
    try:
        r = client.chat.completions.create(
            model=MODEL, max_tokens=30,
            messages=[
                {"role":"system","content":"Extrais le numéro abonné FTTH "
                 "à 9 chiffres mentionné dans ce message d'un client. "
                 "Réponds UNIQUEMENT avec le numéro ou AUCUN."},
                {"role":"user","content":texte}
            ])
        res = r.choices[0].message.content.strip()
        m2 = re.search(r'\d{9}', res)
        return m2.group() if m2 else None
    except:
        return None


def generer_reponse_client(numero: str, resultat: dict, ticket: str) -> str:
    """
    Utiliser Qwen pour formuler une réponse chaleureuse et
    simplifiée destinée au client final (zéro jargon technique).
    """
    cat = resultat.get("categorie", "INCONNU")
    info = MESSAGES_CLIENT.get(cat, MESSAGES_CLIENT["INCONNU"])

    prompt = (
        f"Tu es l'assistant support FTTH de CAMTEL, qui répond "
        f"directement aux clients sur WhatsApp. Ton ton est chaleureux, "
        f"clair et rassurant. JAMAIS de jargon technique, codes d'erreur, "
        f"ou termes internes (AAA, CERAF, CRIP, CHAP...).\n\n"
        f"Numéro client : {numero}\n"
        f"Constat       : {info['resume']}\n"
        f"Conseil/action: {info['conseil']}\n"
        f"Référence     : {ticket}\n\n"
        f"Rédige un message WhatsApp clair (6-8 lignes max), "
        f"qui rassure tout en expliquant les causes possibles "
        f"si pertinent, "
        f"avec l'emoji {info['emoji']} en début, qui informe le client "
        f"et lui donne le conseil. Termine par la référence ticket."
    )
    try:
        r = client.chat.completions.create(
            model=MODEL, max_tokens=200,
            messages=[{"role":"user","content":prompt}]
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return (
            f"{info['emoji']} Bonjour,\n\n"
            f"Concernant votre ligne {numero} : {info['resume']}.\n\n"
            f"{info['conseil']}\n\n"
            f"Référence de suivi : {ticket}\n"
            f"L'équipe CAMTEL"
        )


def traiter_message_client(texte: str) -> dict:
    """Pipeline complet côté client"""
    print(f"\n{'═'*60}")
    print(f"💬 Message client : {texte[:60]}")
    print(f"{'═'*60}")

    # Étape 1 — Extraire numéro
    numero = extraire_numero_client(texte)
    if not numero:
        reponse_demande = ("❓ Bonjour ! Pour pouvoir vérifier votre ligne, "
                           "merci de nous indiquer le numéro de votre "
                           "abonnement (ligne FTTH).")
        print(f"\n{'─'*60}")
        print("📤 RÉPONSE ENVOYÉE AU CLIENT (WhatsApp) :")
        print(f"{'─'*60}")
        print(reponse_demande)
        print(f"{'─'*60}\n")
        return {"succes": False, "reponse": reponse_demande}
    print(f"   ✅ Numéro : {numero}")

    # Étape 2 — Consultation AAA (même core que l'interne !)
    agent    = TelecomAIAgent()
    resultat = agent.traiter(numero)
    cat      = resultat.get("categorie", "INCONNU")
    print(f"   🔍 Diagnostic interne : {cat}")

    # Étape 3 — Générer ticket de suivi
    ticket = generer_ticket()
    print(f"   🎫 Ticket : {ticket}")

    # Étape 4 — Réponse simplifiée pour le client
    reponse = generer_reponse_client(numero, resultat, ticket)

    print(f"\n{'─'*60}")
    print("📤 RÉPONSE ENVOYÉE AU CLIENT (WhatsApp) :")
    print(f"{'─'*60}")
    print(reponse)
    print(f"{'─'*60}\n")

    return {
        "succes":   True,
        "numero":   numero,
        "ticket":   ticket,
        "categorie": cat,
        "reponse":  reponse
    }


# ── CLI simulant WhatsApp ──────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  💬 TELECOMAI AGENT — Espace CLIENT (WhatsApp simulé)")
    print("  Track 4 : Autopilot Agent — Qwen Cloud")
    print("="*60)
    print("\nSimule un message client entrant sur WhatsApp Business")
    print("Exemples :")
    print("  → 'Bonjour ma fibre ne marche plus depuis ce matin "
          "mon numéro est 222233811'")
    print("  → 'Internet coupé 222311395'")
    print("  → '222270004 plus internet'")
    print("\nTapez 'quit' pour quitter\n")

    while True:
        try:
            texte = input("💬 Client : ").strip()
            if texte.lower() in ("quit","exit","q"):
                print("\n👋 Session terminée\n"); break
            if not texte:
                continue
            traiter_message_client(texte)
        except KeyboardInterrupt:
            print("\n\n👋 Session terminée\n"); break
        except Exception as e:
            print(f"❌ Erreur : {e}")
