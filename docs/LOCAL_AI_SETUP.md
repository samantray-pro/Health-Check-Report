# 🦙 Local Offline AI Setup Guide (Ollama)

This guide provides step-by-step instructions to configure **100% private, offline AI inference** for the Health Checkup Tracker using [Ollama](https://ollama.com/).

When using Local AI, your medical data **never leaves your computer**. All prompt ingestion, health record summarization, and token streaming happen directly on your CPU/GPU/NPU.

---

## Table of Contents
- [1. System Requirements](#1-system-requirements)
- [2. Installing Ollama](#2-installing-ollama)
- [3. Downloading a Recommended Model](#3-downloading-a-recommended-model)
- [4. Verifying Ollama Service](#4-verifying-ollama-service)
- [5. Configuring Health Checkup Tracker](#5-configuring-health-checkup-tracker)
- [6. Performance Tuning & Optimizations](#6-performance-tuning--optimizations)
- [7. Troubleshooting & FAQs](#7-troubleshooting--faqs)

---

## 1. System Requirements

| Hardware Component | Minimum Requirement | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11, macOS 12+, Ubuntu 22.04+ | Windows 11 (with WSL2 or native Ollama) |
| **RAM** | 8 GB System RAM | 16 GB+ System RAM |
| **CPU** | 4-Core x86_64 or Apple Silicon (M1/M2/M3) | Intel Core Ultra / AMD Ryzen AI / Apple M-series |
| **GPU / NPU** | Optional (runs fine on modern CPUs) | Dedicated NVIDIA GPU (4GB+ VRAM) or Integrated NPU |
| **Disk Space** | ~4 GB free disk space | SSD with 10 GB+ free space |

---

## 2. Installing Ollama

### Windows
1. Download the official installer from [ollama.com/download/windows](https://ollama.com/download/windows).
2. Run `OllamaSetup.exe` and complete the installation wizard.
3. Ollama will automatically start and run in your system tray (near your clock).

### macOS
1. Download from [ollama.com/download/mac](https://ollama.com/download/mac) or install via Homebrew:
   ```bash
   brew install ollama
   ```
2. Launch the Ollama application.

### Linux
Run the official one-line installation script:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

## 3. Downloading a Recommended Model

Open your terminal (**PowerShell** or **Command Prompt** on Windows, or **Terminal** on macOS/Linux) and pull one of the recommended models below:

### Option A: Microsoft Phi-3 Mini 3.8B (Default & Recommended)
Microsoft's `phi3:3.8b` is the default model tuned for medical terminology, dense numerical data analysis, and running smoothly on standard laptop CPUs without dedicated GPUs:
```bash
ollama pull phi3:3.8b
```
* Download size: ~2.2 GB
* Context window: 4K (clamped in app settings to prevent memory crashes)

### Option B: Meta Llama 3.2 3B (Fast & High Capability)
Meta's latest ultra-compact model:
```bash
ollama pull llama3.2:3b
```
* Download size: ~2.0 GB
* Great conversational reasoning and fast token generation.

### Option C: Google Gemma 2 2B (Ultra Lightweight)
Ideal for older laptops or systems with only 8 GB of RAM:
```bash
ollama pull gemma2:2b
```
* Download size: ~1.6 GB

---

## 4. Verifying Ollama Service

Verify that Ollama is actively running and responding to local API requests:

### 1. Check in Terminal:
```bash
ollama list
```
You should see `phi3:3.8b` (or your chosen model) listed.

### 2. Test the Local REST API:
Open your browser or run in PowerShell:
```powershell
Invoke-RestMethod -Uri http://localhost:11434/api/tags
```
If Ollama is running, it returns a JSON list of installed models.

---

## 5. Configuring Health Checkup Tracker

Once Ollama is installed and the model is downloaded:

1. Start the Health Checkup Tracker by running `.\run.bat` (Windows) or `./run.sh` (Linux/Mac).
2. Open `http://localhost:8000` in your web browser.
3. Click the **"🤖 AI Config"** button in the navigation bar (top right).
4. Fill in the modal settings:
   - **AI Provider**: `Local Offline (Ollama / LM Studio)`
   - **Local API URL**: `http://localhost:11434`
   - **Local Model Name**: `phi3:3.8b` *(or the model tag you downloaded, e.g. `llama3.2:3b`)*
5. Click **Save Settings**.
6. Open the floating chat widget (💬 icon at bottom right) and ask a question:
   > *"What are my recent abnormal test results?"*
   > *"How has my cholesterol changed over time?"*

---

## 6. Performance Tuning & Optimizations

### Automatic Context Clamping (OOM Protection)
Models with large native context windows (such as `phi3:3.8b` with 128k context) can attempt to allocate up to 26GB of system RAM for the KV cache if left unconstrained, causing system out-of-memory crashes on consumer laptops.

The Health Checkup Tracker backend automatically clamps inference parameters:
* **Context Limit**: Clamped to `num_ctx: 2048` tokens.
* **Prediction Length**: Capped to `num_predict: 180` tokens for concise clinical answers.
* **Temperature**: Set to `0.2` for deterministic, grounded medical data extraction.

### CPU Generation Speeds
* On consumer laptop CPUs (e.g. 15W Intel Core Ultra or AMD Ryzen), initial prompt evaluation takes **2 to 8 seconds**, followed by streaming generation at **8 to 15 tokens/sec**.
* The chat widget displays a **pulsing blue animation** and shimmering progress text so you know inference is progressing.
* The application uses extended client timeouts (`read=240.0s`) to ensure local CPU generation never aborts prematurely.

---

## 7. Troubleshooting & FAQs

### Error: `Failed to connect to Local AI (http://localhost:11434)`
* **Cause**: Ollama service is not running.
* **Fix**: Search for **Ollama** in your Windows Start menu or launch it from terminal:
  ```bash
  ollama serve
  ```

### Error: `Local AI request timed out`
* **Cause**: Heavy system load or background processes throttling CPU inference.
* **Fix**: Close resource-heavy apps (e.g., video editing tools, games). Alternatively, try pulling a smaller model like `gemma2:2b`.

### Accessing Local AI from Mobile on LAN
* If you access the dashboard from your phone via Wi-Fi (`http://192.168.x.x:8000`), the browser sends chat requests to your PC's backend, which routes them internally to Ollama.
* **Your phone does NOT need to run Ollama!** The PC running the server handles all computation.

---

[← Back to Main README](../README.md)
