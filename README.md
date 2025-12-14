# SOLACE

**Your refuge when you need it** | **Seu refúgio quando você precisar**

An AI-powered emotional support companion that provides conversations, advice, and comfort with 100% encrypted privacy.

---

## Overview

Solace is an AI companion app designed to provide emotional support through meaningful conversations. Using advanced AI (Claude by Anthropic), Solace offers a safe, private space for users to express themselves and receive thoughtful, empathetic responses.

### Key Features

- **24/7 Availability** - Always there when you need someone to talk to
- **100% Private** - End-to-end encrypted conversations
- **Empathetic AI** - Powered by Claude for nuanced, caring responses
- **No Judgment** - A safe space for your thoughts and feelings

---

## Project Structure

```
solace/
├── backend.py              # FastAPI backend with Claude API integration
├── PROTOTIPO.html          # Interactive app prototype
├── pitch-deck-solace-pt.html   # Investor pitch deck (Portuguese)
├── pitch-deck-solace-en.html   # Investor pitch deck (English)
├── solace-modelo-negocio.md    # Business model documentation
├── INSTRUCOES.md           # Development instructions
└── requirements.txt        # Python dependencies
```

---

## Tech Stack

- **Backend**: Python + FastAPI
- **AI**: Anthropic Claude API (Sonnet 4 / Haiku 3.5)
- **Frontend**: React Native + Expo (planned)
- **Payments**: Stripe, Google Play Billing, Apple In-App Purchase

---

## Business Model

| Metric | Value |
|--------|-------|
| Subscription | $5.99/month |
| Free Trial | 7 days (20 messages) |
| Break-even | ~3,800 subscribers |
| Target Margin | 62-73% |

See [solace-modelo-negocio.md](solace-modelo-negocio.md) for detailed financial projections.

---

## Getting Started

### Prerequisites

- Python 3.9+
- Anthropic API key

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/solace.git
cd solace

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export ANTHROPIC_API_KEY="your-api-key"

# Run the backend
uvicorn backend:app --reload
```

---

## Demo

Open `PROTOTIPO.html` in a browser to see the interactive prototype.

View the pitch decks:
- [English Version](pitch-deck-solace-en.html)
- [Portuguese Version](pitch-deck-solace-pt.html)

---

## Investment

We're seeking **$200,000** for 10-15% equity to:
- Complete iOS/Android app development
- Fund 12 months of operations
- Marketing and user acquisition

**Projected returns at 1M users:** $45M+ annual profit

---

## Contact

- Email: contact@solace.app
- Website: [solace.app](https://solace.app)

---

## License

This project is proprietary. All rights reserved.

---

*Solace - Your refuge when you need it*
