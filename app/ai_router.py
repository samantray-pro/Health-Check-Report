import json
import logging
import sqlite3
from typing import List, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

class AIChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    provider: str = "local"  # 'local' or 'gemini'
    api_key: Optional[str] = None
    local_url: str = "http://localhost:11434"
    local_model: str = "phi3:3.8b"
    gemini_model: str = "gemini-3.5-flash"
    profile_id: int

def build_health_context(profile_id: int, conn: sqlite3.Connection) -> str:
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
    profile = cursor.fetchone()
    if not profile:
        return "No health profile found."

    # Aggregated stats to directly answer count/trend questions
    cursor.execute("SELECT COUNT(*) as total_records, COUNT(DISTINCT test_name) as unique_tests FROM test_records WHERE profile_id = ?", (profile_id,))
    stats = cursor.fetchone()
    total_records = stats['total_records'] if stats else 0
    unique_tests = stats['unique_tests'] if stats else 0

    cursor.execute("""
        SELECT test_name, COUNT(*) as cnt 
        FROM test_records 
        WHERE profile_id = ? 
        GROUP BY test_name 
        HAVING cnt > 1 
        ORDER BY cnt DESC
    """, (profile_id,))
    multi_records = cursor.fetchall()

    # Get abnormal/flagged records
    cursor.execute("""
        SELECT test_name, value, unit, flag 
        FROM test_records 
        WHERE profile_id = ? AND flag IS NOT NULL AND flag != 'NORMAL'
        ORDER BY test_date DESC 
        LIMIT 15
    """, (profile_id,))
    abnormal_records = cursor.fetchall()

    # Get recent normal records
    cursor.execute("""
        SELECT test_name, value, unit 
        FROM test_records 
        WHERE profile_id = ? AND (flag IS NULL OR flag = 'NORMAL')
        ORDER BY test_date DESC 
        LIMIT 10
    """, (profile_id,))
    normal_records = cursor.fetchall()

    context = f"Patient: {profile['name']} (Age: {profile['age']}, Gender: {profile['gender']}). Total records: {total_records} across {unique_tests} unique tests.\n"
    if multi_records:
        multi_str = ", ".join([f"{r['test_name']} ({r['cnt']} entries)" for r in multi_records])
        context += f"Tests with multiple historical entries ({len(multi_records)} tests): {multi_str}.\n"
    else:
        context += "Tests with multiple historical entries: None.\n"

    if abnormal_records:
        abn_str = "; ".join([f"{r['test_name']}: {r['value']} {r['unit']} [{r['flag']}]" for r in abnormal_records])
        context += f"Out-of-range flagged tests: {abn_str}.\n"
        
    if normal_records:
        norm_str = "; ".join([f"{r['test_name']}: {r['value']} {r['unit']}" for r in normal_records])
        context += f"Recent normal tests: {norm_str}.\n"

    context += "Instructions: Provide direct, clear, concise answers (1-3 sentences). Answer questions about test counts or multiple entries directly using the statistics provided above."
    return context

async def stream_local_ollama(url: str, model: str, system_prompt: str, messages: List[Dict[str, str]]):
    clean_model = model.strip() if model else "phi3:3.8b"
    clean_url = url.strip().rstrip('/')
    logger.info(f"Connecting to Local Ollama at {clean_url} with model {clean_model}")
    
    # Flush immediate connection confirmation to client
    yield f"data: {json.dumps({'content': ''})}\n\n"

    formatted_messages = [{"role": "system", "content": system_prompt}] + messages
    payload = {
        "model": clean_model,
        "messages": formatted_messages,
        "stream": True,
        "options": {
            "num_ctx": 2048,
            "num_predict": 180,
            "temperature": 0.2
        }
    }
    api_endpoint = f"{clean_url}/api/chat"
    
    timeout_config = httpx.Timeout(
        connect=15.0,
        read=240.0,
        write=30.0,
        pool=15.0
    )
    
    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            async with client.stream("POST", api_endpoint, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_decoded = error_text.decode('utf-8', errors='ignore')
                    logger.error(f"Local AI server returned status {response.status_code}: {error_decoded}")
                    yield f"data: [ERROR] Local AI server returned status {response.status_code}: {error_decoded}\n\n"
                    return
                
                async for chunk in response.aiter_lines():
                    if chunk:
                        try:
                            data = json.loads(chunk)
                            if data.get("done"):
                                break
                            if "message" in data and "content" in data["message"]:
                                content = data["message"]["content"]
                                if content:
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                        except json.JSONDecodeError:
                            pass
    except httpx.TimeoutException as e:
        logger.error(f"Local AI request timed out: {type(e).__name__}")
        yield f"data: [ERROR] Local AI request timed out. The local model is taking longer than expected on your CPU/GPU. Please try again or close background apps to free CPU power.\n\n"
    except httpx.RequestError as e:
        err_msg = str(e) or type(e).__name__
        logger.error(f"Failed to connect to Local AI: {err_msg}")
        yield f"data: [ERROR] Failed to connect to Local AI ({api_endpoint}). Ensure Ollama is running. Error: {err_msg}\n\n"

async def stream_gemini(api_key: str, system_prompt: str, messages: List[Dict[str, str]], requested_model: str = "gemini-3.5-flash"):
    try:
        from google import genai
        from google.genai import types
        
        # Flush immediate connection confirmation to client
        yield f"data: {json.dumps({'content': ''})}\n\n"

        clean_key = api_key.strip()
        client = genai.Client(api_key=clean_key)
        
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_messages.append({"role": role, "parts": [{"text": msg["content"]}]})

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
        )

        clean_model = requested_model.strip() if requested_model else "gemini-3.5-flash"
        
        # Pre-emptively remap retired or restricted models to active Gemini 3.5 production models
        retired_model_map = {
            "gemini-2.5-flash-lite": "gemini-3.5-flash-lite",
            "gemini-2.0-flash": "gemini-3.5-flash",
            "gemini-2.0-flash-001": "gemini-3.5-flash",
            "gemini-2.0-flash-lite": "gemini-3.5-flash-lite",
            "gemini-1.5-flash": "gemini-3.5-flash",
            "gemini-1.5-pro": "gemini-3.5-flash"
        }
        if clean_model in retired_model_map:
            mapped_model = retired_model_map[clean_model]
            logger.info(f"Remapping deprecated model '{clean_model}' -> '{mapped_model}'")
            clean_model = mapped_model

        # Candidate models to try in order of preference (current Gemini 3 production models)
        models_to_try = [clean_model, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-2.5-flash"]
        models_to_try = list(dict.fromkeys(models_to_try))  # Remove duplicates preserving order

        last_error = None
        for mod in models_to_try:
            try:
                logger.info(f"Attempting Gemini generation with model: {mod}")
                response_stream = await client.aio.models.generate_content_stream(
                    model=mod,
                    contents=gemini_messages,
                    config=config
                )
                yielded_token = False
                async for chunk in response_stream:
                    if chunk.text:
                        yielded_token = True
                        yield f"data: {json.dumps({'content': chunk.text})}\n\n"
                return  # Generation completed successfully
            except Exception as ex:
                last_error = ex
                err_str = str(ex)
                if not yielded_token and ("404" in err_str or "NOT_FOUND" in err_str or "no longer available" in err_str):
                    logger.warning(f"Gemini model '{mod}' not found or deprecated, attempting fallback: {err_str}")
                    continue
                else:
                    raise ex

        if last_error:
            raise last_error
                
    except Exception as e:
        err_msg = str(e) or type(e).__name__
        logger.error(f"Gemini API Error: {err_msg}")
        yield f"data: [ERROR] Gemini API Error: {err_msg}\n\n"

@router.post("/chat")
async def chat_endpoint(req: AIChatRequest):
    with get_db() as db:
        system_prompt = build_health_context(req.profile_id, db)

    if req.provider == "gemini":
        if not req.api_key:
            raise HTTPException(status_code=400, detail="Gemini API Key is required when using the Gemini provider.")
        return StreamingResponse(
            stream_gemini(req.api_key, system_prompt, req.messages, req.gemini_model),
            media_type="text/event-stream"
        )
    else:
        return StreamingResponse(
            stream_local_ollama(req.local_url, req.local_model, system_prompt, req.messages),
            media_type="text/event-stream"
        )
