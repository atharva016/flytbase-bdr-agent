"""
Unified LLM Client
Supports Groq (primary, free) and Google Gemini (fallback).
Abstracts the LLM provider so agents don't need to know the details.
"""

import os
import json

# Determine which provider to use
_provider = None
_client = None


def get_provider():
    """Detect and initialize the LLM provider."""
    global _provider, _client
    
    if _provider:
        return _provider, _client
    
    # Try Groq first (primary - free and fast)
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        try:
            from groq import Groq
            _client = Groq(api_key=groq_key)
            _provider = "groq"
            print("[LLM] Using Groq (Llama 3.3 70B) - Free & Fast")
            return _provider, _client
        except Exception as e:
            print(f"[LLM] Groq init failed: {e}")
    
    # Try Gemini as fallback
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            from google import genai
            _client = genai.Client(api_key=gemini_key)
            _provider = "gemini"
            print("[LLM] Using Google Gemini 2.0 Flash")
            return _provider, _client
        except Exception as e:
            print(f"[LLM] Gemini init failed: {e}")
    
    raise ValueError(
        "No LLM API key found! Set GROQ_API_KEY or GEMINI_API_KEY environment variable.\n"
        "Get a free Groq key at: https://console.groq.com"
    )


def call_llm(prompt: str, temperature: float = 0.3) -> str:
    """
    Call the LLM with a prompt and return the response text.
    Works with both Groq and Gemini.
    """
    provider, client = get_provider()
    
    if provider == "groq":
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert B2B sales researcher and BDR for FlytBase. Always respond with valid JSON when asked for JSON output. Never include markdown code blocks in your response - output raw JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=8000,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    
    elif provider == "gemini":
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "temperature": temperature,
                "response_mime_type": "application/json"
            }
        )
        return response.text
    
    else:
        raise ValueError(f"Unknown provider: {provider}")


def parse_json_response(response_text: str) -> dict:
    """Safely parse a JSON response from the LLM."""
    text = response_text.strip()
    
    # Remove markdown code blocks if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        try:
            start = text.index('{')
            end = text.rindex('}') + 1
            return json.loads(text[start:end])
        except:
            return {"error": f"Failed to parse JSON response", "raw": text[:500]}
