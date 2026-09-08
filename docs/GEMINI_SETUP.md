# ⚡ Google Gemini Cloud AI Setup Guide

This guide walks you through configuring **Google Gemini Cloud AI** for the Health Checkup Tracker. 

If you prefer lightning-fast, zero-setup AI responses without utilizing your computer's local CPU/GPU hardware, Google Gemini's generous free tier provides real-time streaming answers in milliseconds.

---

## Table of Contents
- [1. Why Use Gemini Cloud AI?](#1-why-use-gemini-cloud-ai)
- [2. Privacy & Key Security Architecture](#2-privacy--key-security-architecture)
- [3. Obtaining a Free Gemini API Key](#3-obtaining-a-free-gemini-api-key)
- [4. Supported Models & Versioning](#4-supported-models--versioning)
- [5. Configuring Health Checkup Tracker](#5-configuring-health-checkup-tracker)
- [6. Automated Fallback Cascade & Remapping](#6-automated-fallback-cascade--remapping)
- [7. Troubleshooting & FAQs](#7-troubleshooting--faqs)

---

## 1. Why Use Gemini Cloud AI?

* **Instant Response Times**: Delivers initial tokens in under 400 milliseconds.
* **Zero Hardware Impact**: Does not consume CPU, GPU, or system memory on your machine.
* **High Clinical Acumen**: Gemini models possess vast medical training data, providing detailed explanations of complex biomarker relationships (e.g., Lipid profiles, Thyroid panels, HbA1c).
* **Generous Free Tier**: Google AI Studio provides free access for personal projects with high rate limits (up to 15 Requests Per Minute / 1 million tokens per day).

---

## 2. Privacy & Key Security Architecture

The Health Checkup Tracker was built with privacy as its first principle:

1. **Client-Side Key Storage**: Your Gemini API Key is stored **strictly in your local browser's `localStorage`**. It is never written to `health_tracker.db` or persisted to server disk logs.
2. **Ephemeral In-Memory Routing**: When you ask a question, the API Key is transmitted over the local connection to the backend, held ephemerally in Python memory for the streaming request, and immediately discarded upon stream completion.
3. **No Training on Your Data**: Personal prompts sent via paid or free standard AI Studio keys are subject to Google's standard enterprise API data governance policies.

---

## 3. Obtaining a Free Gemini API Key

1. Navigate to **Google AI Studio**: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
2. Sign in with your standard Google Account.
3. Click **"Create API Key"** (or **"Get API key"**).
4. Select a Google Cloud project (or let AI Studio automatically create a default project for you).
5. Copy the generated API key (it starts with `AIzaSy...`).

> [!TIP]
> Keep your API key private. Do not commit it to public Git repositories.

---

## 4. Supported Models & Versioning

The Health Checkup Tracker is configured with the latest production Gemini models:

| Model Identifier | Tier | Description | Recommended For |
| :--- | :--- | :--- | :--- |
| **`gemini-3.5-flash`** | **Default** | Balanced flagship speed and clinical reasoning | General health queries, deep trend comparisons |
| **`gemini-3.5-flash-lite`** | Fast | Ultra-lightweight, lowest latency | Quick biomarker lookups and instant answers |
| **`gemini-3.6-flash`** | Advanced | High-capacity multimodal reasoning | Complex multi-report historical synthesis |
| **`gemini-2.5-flash`** | Stable | Proven stable fallback | Backup inference |

### ⚠️ Deprecated Models Notice
* **`gemini-2.0-flash`**: Retired on June 1, 2026.
* **`gemini-2.5-flash-lite`**: Restricted to legacy accounts; returns `404 NOT_FOUND` for new users.
* **`gemini-1.5-flash`**: Retired legacy model.

> [!NOTE]
> If an older model string is entered or stored in your browser settings, the application automatically remaps it to an active model (e.g. `gemini-3.5-flash-lite` or `gemini-3.5-flash`) so requests never fail with 404 errors.

---

## 5. Configuring Health Checkup Tracker

1. Start the application (`.\run.bat` on Windows or `./run.sh` on Linux/macOS).
2. Open `http://localhost:8000` in your web browser.
3. Click the **"🤖 AI Config"** button in the top navigation bar.
4. Select **"Google Gemini (Cloud)"** from the **AI Provider** dropdown.
5. In the **Gemini API Key** field, paste your key (`AIzaSy...`).
6. In the **Gemini Model** dropdown, select **`gemini-3.5-flash (Fast & Recommended)`**.
7. Click **Save Settings**.
8. Open the floating chat widget (💬 icon at bottom right) and test with:
   > *"Explain my latest blood test results and suggest lifestyle improvements."*

---

## 6. Automated Fallback Cascade & Remapping

To ensure 100% service uptime even if Google updates or sunsets a model version upstream, the Health Checkup Tracker includes an automated fallback cascade:

```
User Query
    │
    ▼
Check Model Name (Auto-remap retired models)
    │
    ▼
Attempt: gemini-3.5-flash ───────► Success? ──► Stream to UI
    │ (if 404 NOT_FOUND)
    ▼
Attempt: gemini-3.5-flash-lite ──► Success? ──► Stream to UI
    │ (if 404 NOT_FOUND)
    ▼
Attempt: gemini-3.6-flash ───────► Success? ──► Stream to UI
    │ (if 404 NOT_FOUND)
    ▼
Attempt: gemini-2.5-flash ───────► Success? ──► Stream to UI
```

If an error is returned before any content is yielded, the backend seamlessly cascades to the next candidate model without dropping your chat session.

---

## 7. Troubleshooting & FAQs

### Error: `Gemini API Error: 400 API_KEY_INVALID`
* **Cause**: The API key pasted in the settings modal contains a typo, extra spaces, or has been revoked in Google AI Studio.
* **Fix**: Re-open **🤖 AI Config**, clear the API Key field, copy a fresh key from [Google AI Studio](https://aistudio.google.com/app/apikey), and click **Save Settings**.

### Error: `Gemini API Error: 429 RESOURCE_EXHAUSTED`
* **Cause**: You have exceeded the free tier quota (typically 15 requests/minute).
* **Fix**: Wait 60 seconds before sending your next query, or switch your model to `gemini-3.5-flash-lite` in **🤖 AI Config** for higher rate allowance.

### Error: `Gemini API Error: 404 NOT_FOUND`
* **Cause**: An outdated model identifier was requested.
* **Fix**: Hard refresh your browser with **`Ctrl + F5`** (or `Cmd + Shift + R`) to load the updated settings interface, open **🤖 AI Config**, and select **`gemini-3.5-flash`**.

---

[← Back to Main README](../README.md)
