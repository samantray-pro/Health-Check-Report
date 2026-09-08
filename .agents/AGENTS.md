# Health Checkup Tracker - Agent Rules

These rules dictate the architectural guidelines for this repository. All agentic AI assistants working in this repository MUST follow these rules.

## 1. Database Architecture (CRITICAL)
- **NO ORMs allowed**: Do NOT use SQLAlchemy, Peewee, or any other Object-Relational Mapper.
- **Strictly Raw SQLite**: This repository uses the standard library `sqlite3` driver with `sqlite3.Row` for its database architecture.
- **Context Manager**: Database connections must always be handled via the `get_db()` context manager located in `app.database`.
- **Why**: This ensures the application remains entirely dependency-free at the persistence layer, maximizing speed and minimizing installation friction for a lightweight local tool.

## 2. Frontend Architecture
- **No Build Steps**: No Webpack, Vite, Babel, or Tailwind preprocessors.
- **Vanilla Everything**: HTML, CSS, and Vanilla JavaScript only. 
- **DOM Manipulation**: Use native `document.createElement` and string templates.

## 3. Local/Offline Priority
- All features should prioritize 100% offline functionality. If a cloud API is used (e.g. Gemini), it MUST be optional, and a local fallback (e.g. Ollama) must be supported.

## 4. Context Management
- **Compaction Rule**: Automatically compact the current context as a summary whenever the chat context reaches 70% of volume token capacity, to maintain performance and avoid context overflow.

## 5. Local AI & LLM Inference Architecture (CRITICAL)
- **Local LLM Inference Timeouts**: Local inference running on consumer CPUs or integrated GPUs/NPUs (e.g. Phi-3 3.8B on laptop hardware) takes 40-120+ seconds for prompt ingestion and token generation. NEVER set short timeouts (like `timeout=30.0`) on HTTP clients communicating with local Ollama/LM Studio endpoints. Always use `httpx.Timeout(connect=15.0, read=240.0, write=30.0, pool=15.0)` or higher to prevent premature socket aborts.
- **HTTPX Exception Formats**: In `httpx`, `str(e)` on `ReadTimeout` and `ConnectTimeout` evaluates to `""` (an empty string). NEVER format error messages as `f"Error: {str(e)}"` without a fallback. Always use `err_msg = str(e) or type(e).__name__` to prevent blank error messages in UI bubbles.
- **Ollama KV Cache Memory Clamping**: Models with massive context windows (e.g. `phi3:3.8b` with 128k context) will attempt to allocate up to 26GB of system RAM for the KV cache if not restricted, causing Ollama 500 Out-of-Memory crashes on consumer devices. ALWAYS pass an explicit context limit in the Ollama payload: `options: {"num_ctx": 4096}`.
- **SSE Stream Decoding in Vanilla JS**: Never use `chunk.split('\\n')`. A double-backslash in a JavaScript string literal searches for literal characters `\` and `n`, breaking event line separation. Always maintain an incoming stream buffer across `reader.read()` calls and split by actual newlines `'\n'`.

## 6. Gemini Cloud API Lifecycle & Asynchronous Streaming (CRITICAL)
- **Model Deprecation / Versioning**: Standard production models are `gemini-3.5-flash` and `gemini-3.5-flash-lite`. Never hardcode retired or restricted models (`gemini-2.0-flash` was retired on June 1, 2026; `gemini-2.5-flash-lite` is restricted to new users and returns `404 NOT_FOUND`; `gemini-1.5-flash` is retired).
- **Pre-emptive Deprecation Remapping**: Always intercept deprecated or retired model strings at both frontend (`localStorage`) and backend levels (`retired_model_map`), automatically upgrading stale requests (e.g., `gemini-2.5-flash-lite` -> `gemini-3.5-flash-lite`, `gemini-2.0-flash` -> `gemini-3.5-flash`) so that cached user settings never throw 404s.
- **Automated Fallback Cascade**: Always wrap model calls in an active candidate list (`['gemini-3.5-flash', 'gemini-3.5-flash-lite', 'gemini-3.6-flash', 'gemini-2.5-flash']`). If a model call returns `404 NOT_FOUND` or "no longer available", automatically catch the error before yielding any text and cascade to the next candidate model.
- **Immediate Stream Handshake**: Always yield an initial empty SSE payload `data: {"content": ""}\n\n` immediately upon establishing the stream so the browser's `fetch()` resolves in milliseconds and displays the "Thinking..." UI state instead of hanging in "Pending".
- **Async Streaming Interface**: When streaming responses inside FastAPI async generator functions, NEVER use the synchronous blocking `client.models.generate_content_stream`. Always use the official asynchronous `await client.aio.models.generate_content_stream(...)` to prevent event-loop starvation.

## 7. Frontend CSS Tokens & Chat UI Integrity (CRITICAL)
- **CSS Custom Property Strictness**: Never use unregistered CSS variables (such as `var(--primary-color)` or `var(--bg-color)`) without defining them in `:root` or supplying a solid fallback. Unregistered CSS variables on `background-color` evaluate to `transparent`, causing user chat bubbles and text to be invisible against dark container backgrounds.
- **Asset Versioning & Cache Busting**: In local vanilla setups without a build step, always append version query strings to `<script>` and `<link>` tags (`?v=2.x`) whenever modifying client-side logic or styles to prevent stale browser disk caches.

