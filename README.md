# ⚛️ PKTron Agent
### Pakistan's First AI-Powered Quantum Circuit Agent

Built by [CETQAC](https://thecetqap.com) — Centre of Excellence for Technology, Quantum and AI.

PKTron Agent lets you build and simulate real quantum circuits using plain English. 
Type "make a bell state" and the agent writes the code, runs it on the PKTron 
simulator, validates the result, and explains it back to you in simple language.

---

## How It Works

```
Your Request → BRAIN (Gemini writes circuit code)
             → HANDS (PKTron runs the simulation)
             → EYES (validates the quantum result)
             → MOUTH (explains it in plain English)
```

---

## Circuits You Can Build

| Circuit | Example Request |
|--------|----------------|
| Superposition | "show me superposition" |
| Bell State | "make a bell state" |
| GHZ State | "create a 3-qubit GHZ state" |
| Deutsch-Jozsa | "run the Deutsch-Jozsa algorithm" |
| Grover's Search | "find a marked item using Grover" |
| Quantum Teleportation | "teleport a qubit" |
| Quantum Fourier Transform | "run the QFT" |
| Entanglement Swapping | "swap entanglement between two pairs" |

---

## Quick Start (Google Colab)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/pktron-agent/blob/main/PKTron_Agent.ipynb)

1. Click the button above
2. Go to the 🔑 Secrets panel in Colab
3. Add your key as `GOOGLE_API_KEY`
   → Get a free key at [aistudio.google.com](https://aistudio.google.com)
4. Run All cells
5. Start building quantum circuits

---

## Local Setup

```bash
git clone https://github.com/YOUR_USERNAME/pktron-agent
cd pktron-agent
pip install -r requirements.txt
export GOOGLE_API_KEY=your_key_here
python server.py
```
Then open `index.html` in your browser.

---

## Requirements

- Python 3.9+
- Google Gemini API key (free at aistudio.google.com)
- No quantum hardware needed — runs on simulation

---

## Note on Rate Limits

The free Gemini tier allows 5 requests per minute. Each agent run uses 2 requests. 
If you hit a rate limit error, wait 40 seconds and try again.

---

## Built With

- [PKTron](https://pypi.org/project/pktron/) — Pakistan's quantum computing SDK
- [Google Gemini](https://aistudio.google.com) — AI brain
- [Flask](https://flask.palletsprojects.com) — backend server

---

## About CETQAC

The Centre of Excellence for Technology, Quantum and AI (CETQAC) is Pakistan's 
pioneering private quantum computing institution, based in Islamabad.

---

## License

MIT License — free to use, modify and distribute.
