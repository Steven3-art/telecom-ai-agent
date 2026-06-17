"""
qwen_interface/client_interface.py — Client-facing interface (fictional demo)
================================================================================
TelecomAI Agent — Client interface (WhatsApp-style simulation)
Track 4: Autopilot Agent

This file is part of a hackathon demo project. The company name
"AfriTel" and all contact details are entirely fictional, created
for this demo only. No real operator or customer data is used.

Reuses the same core (aaa_mock + diagnostics + agent) but produces
SIMPLIFIED responses for end customers, with zero technical jargon
or error codes.
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

# ── Simplified messages per category (zero technical jargon) ──
MESSAGES_CLIENT = {
    "NORMAL": {
        "emoji": "[OK]",
        "resume": "Your line is working normally and well connected",
        "conseil": "If you still feel the speed is low while the line is "
                   "active, this usually comes from a local factor: many "
                   "devices connected at once, router placement (walls, "
                   "distance), background downloads, or a WiFi password "
                   "shared with others. A wired (Ethernet) speed test is "
                   "usually more reliable than WiFi."
    },
    "NORMAL_SANS_TRAFIC": {
        "emoji": "[WARNING]",
        "resume": "Your line is active but no data is flowing",
        "conseil": "Please check your router (ONT) indicator lights and "
                   "restart it. If the issue continues, a technician will "
                   "be sent."
    },
    "ABSENCE_AUTH": {
        "emoji": "[TECH]",
        "resume": "A technical issue was detected on your line",
        "conseil": "Our technical team has been automatically notified "
                   "and is investigating. Estimated time: 2 to 4 hours."
    },
    "MOT_DE_PASSE": {
        "emoji": "[KEY]",
        "resume": "An identification issue was detected on your line",
        "conseil": "Our technical team is resolving this. Your connection "
                   "will be restored shortly without any action needed "
                   "from you."
    },
    "ECHEC_AUTH": {
        "emoji": "[TECH]",
        "resume": "Your equipment is not identifying correctly on the network",
        "conseil": "Please check that your router (ONT) is properly "
                   "connected and powered. Contact support if needed."
    },
    "BLOCAGE_CRM": {
        "emoji": "[NOTICE]",
        "resume": "An administrative check is needed on your account",
        "conseil": "Please check your account status (billing up to date) "
                   "with your nearest AfriTel agency."
    },
    "SUSPENDU": {
        "emoji": "[SUSPENDED]",
        "resume": "Your line is currently suspended",
        "conseil": "Please contact your AfriTel agency to settle your "
                   "account and reactivate your connection."
    },
    "INEXISTANT": {
        "emoji": "[UNKNOWN]",
        "resume": "This number is not recognized in our system",
        "conseil": "Please double check the number provided, or contact "
                   "your AfriTel agency for help."
    },
    "INCONNU": {
        "emoji": "[UNKNOWN]",
        "resume": "Further verification is needed",
        "conseil": "Our support team will get back to you shortly."
    },
}


def generer_ticket() -> str:
    """Generate a tracking ticket number"""
    date_str = datetime.now().strftime("%Y%m%d")
    suffix   = "".join(random.choices(string.digits, k=4))
    return f"FTTH-{date_str}-{suffix}"


def extraire_numero_client(texte: str) -> str | None:
    """Extract the subscriber number from a client message"""
    m = re.search(r'\b\d{9}\b', texte)
    if m:
        return m.group()
    try:
        r = client.chat.completions.create(
            model=MODEL, max_tokens=30,
            messages=[
                {"role":"system","content":"Extract the 9-digit subscriber "
                 "number mentioned in this customer message. Reply ONLY "
                 "with the number or NONE."},
                {"role":"user","content":texte}
            ])
        res = r.choices[0].message.content.strip()
        m2 = re.search(r'\d{9}', res)
        return m2.group() if m2 else None
    except Exception:
        return None


def generer_reponse_client(numero: str, resultat: dict, ticket: str) -> str:
    """
    Use Qwen to craft a warm, simplified response for the end customer
    (zero technical jargon).
    """
    cat  = resultat.get("categorie", "INCONNU")
    info = MESSAGES_CLIENT.get(cat, MESSAGES_CLIENT["INCONNU"])

    prompt = (
        f"You are AfriTel's FTTH support assistant, replying directly "
        f"to customers on WhatsApp. Your tone is warm, clear, and "
        f"reassuring. NEVER use technical jargon, error codes, or "
        f"internal terms (AAA, NOC, CHAP...).\n\n"
        f"Customer number : {numero}\n"
        f"Finding         : {info['resume']}\n"
        f"Advice/action   : {info['conseil']}\n"
        f"Reference       : {ticket}\n\n"
        f"Write a short WhatsApp message (6-8 lines max), explaining "
        f"possible causes where relevant, with the advice. End with "
        f"the reference ticket."
    )
    try:
        r = client.chat.completions.create(
            model=MODEL, max_tokens=220,
            messages=[{"role":"user","content":prompt}]
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return (
            f"Hello,\n\n"
            f"Regarding your line {numero}: {info['resume']}.\n\n"
            f"{info['conseil']}\n\n"
            f"Tracking reference: {ticket}\n"
            f"The AfriTel team"
        )


def traiter_message_client(texte: str) -> dict:
    """Full client-side pipeline"""
    print(f"\n{'='*60}")
    print(f"Client message: {texte[:60]}")
    print(f"{'='*60}")

    numero = extraire_numero_client(texte)
    if not numero:
        reponse_demande = ("Hello! To check your line, please share your "
                           "subscriber (FTTH) number with us.")
        print(f"\n{'-'*60}")
        print("RESPONSE SENT TO CLIENT (WhatsApp):")
        print(f"{'-'*60}")
        print(reponse_demande)
        print(f"{'-'*60}\n")
        return {"succes": False, "reponse": reponse_demande}
    print(f"   Number: {numero}")

    agent    = TelecomAIAgent()
    resultat = agent.traiter(numero)
    cat      = resultat.get("categorie", "INCONNU")
    print(f"   Internal diagnosis: {cat}")

    ticket = generer_ticket()
    print(f"   Ticket: {ticket}")

    reponse = generer_reponse_client(numero, resultat, ticket)

    print(f"\n{'-'*60}")
    print("RESPONSE SENT TO CLIENT (WhatsApp):")
    print(f"{'-'*60}")
    print(reponse)
    print(f"{'-'*60}\n")

    return {
        "succes":    True,
        "numero":    numero,
        "ticket":    ticket,
        "categorie": cat,
        "reponse":   reponse
    }


# ── CLI simulating WhatsApp ────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TELECOMAI AGENT — Client space (WhatsApp simulation)")
    print("  Track 4: Autopilot Agent — Qwen Cloud")
    print("="*60)
    print("\nSimulates an incoming customer message on WhatsApp Business")
    print("Examples:")
    print("  -> 'Hello my fiber has not been working since this morning, "
          "my number is 222233811'")
    print("  -> 'Internet down 222311395'")
    print("  -> '222270004 no internet'")
    print("\nType 'quit' to exit\n")

    while True:
        try:
            texte = input("Client: ").strip()
            if texte.lower() in ("quit","exit","q"):
                print("\nSession ended\n"); break
            if not texte:
                continue
            traiter_message_client(texte)
        except KeyboardInterrupt:
            print("\n\nSession ended\n"); break
        except Exception as e:
            print(f"Error: {e}")
