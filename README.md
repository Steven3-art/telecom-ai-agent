# TelecomAI Agent 🌍📡

> AI-powered FTTH subscriber support automation for African telecom operators.

Built for the **Qwen Cloud Hackathon** (Track 4: Autopilot Agent)
and the **Slack Agent Builder Challenge** (Slack Agent for Organizations).

## 🎯 Problem

African telecom operators receive hundreds of FTTH support requests daily
via email. Each request requires manual portal access, diagnosis, and response
— taking 5–15 minutes per case.

## 💡 Solution

TelecomAI Agent automates the full support pipeline:

```
Email / Slack request
        ↓
AI Agent identifies subscriber number
        ↓
Automated AAA portal consultation
        ↓
Intelligent diagnosis (6 categories)
        ↓
Instant response + ETL recording
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│             TELECOMAI AGENT                 │
│                                             │
│  core/                                      │
│  ├── agent.py        ← Main pipeline        │
│  ├── aaa_mock.py     ← AAA simulation       │
│  └── diagnostics.py  ← AI categorization   │
│                                             │
│  qwen_interface/     ← Alibaba Cloud        │
│  slack_interface/    ← Slack Bot            │
└─────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python core/agent.py
```

## 📊 Diagnostic Categories

| Category | Description | Action |
|----------|-------------|--------|
| NORMAL_EN_LIGNE | Active with traffic | No action needed |
| ABSENCE_AUTH | Active in AAA, no connection | CERAF investigation |
| ECHEC_AUTH | Authentication failures | Password reset |
| SUSPENDU | Account suspended | Commercial contact |
| INEXISTANT | Not in AAA | Check contract |

## 🌍 Impact

Targeting 45+ million FTTH subscribers across Sub-Saharan Africa.
Reduces support response time from 15 minutes to under 30 seconds.

## 📄 License

MIT License — Open Source
