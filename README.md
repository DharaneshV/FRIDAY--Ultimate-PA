# F.R.I.D.A.Y. — Ultimate Command Center

> *"Fully Responsive Intelligent Digital Assistant for You"*

F.R.I.D.A.Y. is a high-performance, Stark-inspired AI ecosystem that bridges the gap between voice interaction and immersive visual telemetry. This "Ultimate" version upgrades the assistant's brain to Gemini 1.5 Pro and introduces a real-time React-based Visual HUD.

## 🏗️ The Three-Tier Architecture

Friday operates as a distributed system across three dedicated layers:

| Component | What it is | Transport |
|-----------|-----------|-----------|
| **The Brain** (`agent_friday.py`) | LiveKit Voice Agent powered by **Gemini 1.5 Pro**. It listens, reasons, and speaks while orchestrating all other systems. | WebSockets (LiveKit) |
| **The Nexus** (`dashboard_server.py`) | A FastAPI server that hosts the **Visual HUD** and provides a real-time WebSocket relay for telemetry. | WebSockets & HTTP |
| **The Armor** (`server.py`) | An MCP (Model Context Protocol) server that exposes deep system tools (Search, Lab Scan, Diagnostics, Memory). | SSE (Port 8000) |

---

## 🚀 Key Features

### 🧠 Advanced "Pro" Intelligence
Friday is now powered by **Gemini 1.5 Pro**, providing superior reasoning, complex tool-calling capabilities, and deep code understanding. She can handle multi-step requests like "Scan my projects, find all TODOs, and brief me on the most urgent one."

### 🖥️ Cinematic Visual HUD
A premium **React + Tailwind + Framer Motion** dashboard that opens in your browser.
*   **Animated Arc Reactor**: A central SVG core that visualizes Friday's processing state.
*   **Real-Time Telemetry**: Live gauges for CPU load, Memory pressure, and Session uptime.
*   **Communication Uplink**: A scrolling terminal showing Friday's internal logs and search results.
*   **Glassmorphism**: High-end translucent UI with blurred backgrounds and neon accents.

### 🔬 Lab Intelligence & Memory
*   **Lab Scan**: Friday can recursively scan your workspace to answer "What are we working on?".
*   **Git Uplink**: Real-time git status, branch analysis, and recent commit summaries.
*   **Persistent Memory**: Long-term session memory and a Task Board system persisted to local storage.
*   **Armor Diagnostics**: Deep system health monitoring via `psutil`.

---

## 🛠️ Quick Start

### 1. Prerequisites
- Python ≥ 3.11
- Node.js & npm (for building the HUD)
- A [LiveKit Cloud](https://cloud.livekit.io) project
- API Keys: Sarvam (STT), Gemini (LLM), Tavily/Serper (Search)

### 2. Installation & Setup
```bash
git clone https://github.com/DharaneshV/FRIDAY--Ultimate-PA.git
cd FRIDAY--Ultimate-PA
python -m pip install -r requirements.txt  # Or use uv sync
```

### 3. Running the System (3 Terminals)

**Terminal 1: THE NEXUS (Visuals)**
```bash
python dashboard_server.py
```
*Initializes the WebSocket relay and hosts the Command Center at `http://localhost:8000`.*

**Terminal 2: THE ARMOR (Tools)**
```bash
python server.py
```
*Starts the MCP server on port 8000.*

**Terminal 3: THE BRAIN (Voice)**
```bash
python agent_friday.py dev
```
*Starts the voice pipeline. Open the [LiveKit Playground](https://agents-playground.livekit.io) to start the session.*

---

## 🎙️ Command Guidelines

| Category | Commands | Friday's Action |
|----------|----------|-----------------|
| **Systems** | *"Initiate HUD"* / *"Bring up the interface"* | Opens the Visual Command Center in your browser. |
| **Diagnostics** | *"Check armor status"* / *"Run diagnostics"* | Performs a deep system scan and updates the HUD gauges. |
| **Intelligence** | *"Scan the lab"* / *"Recall the latest project notes"* | Searches the filesystem and pulls data from persistent memory. |
| **Global** | *"Brief me on the world"* / *"Search for XYZ"* | Pulls news/search results and scrolls them in the HUD terminal. |

---

## 🛠️ Tech Stack
- **LLM**: Google Gemini 1.5 Pro
- **STT**: Sarvam Saaras v3 (High-accuracy Indian English)
- **TTS**: Sarvam Bulbul / OpenAI Nova
- **Frontend**: React 18, Tailwind CSS, Framer Motion, Vite
- **Backend**: FastAPI, Uvicorn, Python MCP SDK, LiveKit Agents
- **monitoring**: psutil

---

## License
MIT
