# 🧠 Local‑AI (Ollama + FastAPI + Web UI)

A fully local chatbot that runs on your own machine.  
No cloud. No API keys. No internet required after model download.
---

## How it works:

```
Browser UI → FastAPI backend → Ollama Engine → Local LLM → Response → Browser
```
The **browser** sends your message to a **FastAPI server** (Python), which forwards it to **Ollama** (the local AI engine), which runs the **LLM model** on your hardware and returns the response.

---

## Requirements

Before starting, make sure you have the following installed:

| Requirement | Notes |
|---|---|
| Python 3.10+ | Check with `python3 --version` |
| Ollama | Download at [ollama.com](https://ollama.com) |
| A local model | e.g. `llama3`, `mistral`, or `phi3` |
| Linux / macOS / Windows WSL | Native Windows not recommended |


---

## Project Structure

```
local-ai/
├── server.py       ← FastAPI backend (the bridge between UI and Ollama)
├── index.html      ← Browser-based chat interface
└── venv/           ← Python virtual environment (created in Step 1)
```

---

## Step 1 — Set Up the Python Environment
Navigate into the project folder and create an isolated Python enviroment:

```bash
cd local-ai
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn requests
```
> **Why a virtual enviroment?** It keeps project dependencies isolated from your system Python, avoiding version conflicts.
---

## Step 2 — Start Ollama (AI Engine)

Open Terminal #1:

```bash
ollama serve
```

Check installed models:

```bash
ollama list
```

If empty:

```bash
ollama run llama3
```

Wait for download then press CTRL+C

Ollama is now running locally at:

```
http://localhost:11434
```
> **Note:** Keep this terminal open. Ollama must be running for the rest of the steps to work.
---

## Step 3 — Test Ollama Directly
Before building anything else, confirm ollama is responding correctly. In a new terminal run:
```bash
curl http://localhost:11434/api/generate -d '{
  "model":"llama3",
  "prompt":"Say hello",
  "stream":false
}'
```

**Expected result :** A JSON response containing the `response` field with generated texts.

> If this fails, stop and fix ollama before continuing. The backend depends entirely on this working.

---

## Step 4 — Backend Server (FastAPI Bridge)

Create a file named `server.py` with the following content:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

class Message(BaseModel):
    text: str

@app.post("/chat")
def chat(msg: Message):
    r = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": msg.text,
        "stream": False
    })
    return {"reply": r.json()["response"]}
```
> **What this does:** FastAPI exposes a `/chat` endpoint. When the browser POSTs a message, this server forwards it to Ollama and returns a response.
---

## Step 5 — Run the Backend

Open Terminal #2:

```bash
source venv/bin/activate
uvicorn server:app --reload --port 8000
```

Server now available at:

```
http://127.0.0.1:8000/chat
```

---

## Step 6 — Test Backend (Important)

Open Terminal #3:

```bash
curl -X POST http://127.0.0.1:8000/chat \
-H "Content-Type: application/json" \
-d '{"text":"Explain recursion simply"}'
```

If this works → backend connected to model successfully.

---

## Step 7 — Launch UI

Open `index.html` in your browser.

Type a message and press Enter.

You should receive a response from the local model.

---
## Terminal Summary

At this point you should have these running simultaneously:

| Terminal | Command | Purpose |
|---|---|---|
| Terminal 1 | `ollama serve` | Runs the local AI engine |
| Terminal 2 | `uvicorn server:app --reload --port 8000` | Runs the FastAPI bridge |
| Terminal 3 | *(optional)* `curl` tests | Used only for verification |


---

## Troubleshooting

| Problem                 | Cause               | Fix                         |
| ----------------------- | ------------------- | --------------------------- |
| UI shows Offline        | FastAPI not running | Start uvicorn               |
| Backend error           | Ollama stopped      | Run `ollama serve`          |
| No model response       | Model not installed | `ollama run llama3`         |
| CORS error              | Missing middleware  | Check server.py             |
| curl works but UI fails | Wrong JSON keys     | Must use `text` and `reply` |

---

## How It Works Internally

1. Browser sends POST `/chat`
    
2. FastAPI receives JSON `{text}`
    
3. FastAPI forwards prompt to Ollama
    
4. Ollama runs the LLM
    
5. Response returned as `{reply}`
    
6. UI displays message bubble
    

---

## Ideas For Future Improvements

- **Conversation memory** — pass previous messages as context so the model remembers the conversation
- **Streaming responses** — display tokens in real time as the model generates them
- **System prompts / personas** — define a custom AI personality or role
- **File uploads** — allow the model to read and respond to documents
- **Voice I/O** — integrate speech-to-text and text-to-speech
- **Multi-agent workflows** — chain multiple models or tools together (great for n8n integration)

---

 > Built with ❤️ by CipherNex0

 **Author:** CipherNex0
 **Version:** 1.0
 

