"""
Stage 1: Account Identification Agent
Finds mining companies in Latin America matching the SQM ICP profile.
Uses Gemini LLM + DuckDuckGo web search for real-time data.
"""

import json
from duckduckgo_search import DDGS
from llm_client import call_llm, parse_json_response
from config import ACCOUNT_FINDER_PROMPT, SQM_PROFILE


def search_mining_companies(query: str, max_results: int = 10) -> list[dict]:
    """Search the web for mining companies using DuckDuckGo."""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "href": r.get("href", "")
                })
    except Exception as e:
        print(f"[Account Finder] Search error: {e}")
    return results


def gather_web_intelligence(brief: dict) -> str:
    """Gather web search results to augment LLM knowledge with real-time data."""
    search_queries = [
        "largest mining companies Latin America 2025 2026",
        "lithium mining companies Chile Argentina Peru",
        "copper mining companies Latin America largest",
        "iron ore mining companies Brazil Chile",
        "mining companies Latin America autonomous technology drones",
        "SQM competitors lithium mining South America",
        "Codelco Antofagasta Vale Southern Copper operations",
        "mining companies Latin America safety technology investment 2026"
    ]
    
    all_results = []
    for query in search_queries:
        results = search_mining_companies(query, max_results=5)
        all_results.extend(results)
    
    # Format results as context for the LLM
    context_parts = []
    for i, r in enumerate(all_results[:40]):  # Limit to 40 results
        context_parts.append(f"[{i+1}] {r['title']}: {r['body']} (Source: {r['href']})")
    
    return "\n".join(context_parts)


def run_account_finder(brief: dict) -> dict:
    """
    Stage 1: Identify target accounts matching the ICP.
    
    Args:
        brief: Campaign brief dictionary
    
    Returns:
        Dictionary with accounts list and metadata
    """
    print("[Stage 1] Account Identification - Starting...")
    
    # Step 1: Gather real-time web intelligence
    print("[Stage 1] Searching web for mining companies...")
    web_context = gather_web_intelligence(brief)
    
    # Step 2: Build the prompt with web context and brief
    prompt = ACCOUNT_FINDER_PROMPT.format(
        brief=json.dumps(brief, indent=2),
        sqm_profile=json.dumps(SQM_PROFILE, indent=2)
    )
    
    augmented_prompt = f"""{prompt}

ADDITIONAL WEB RESEARCH CONTEXT (use this to verify and enrich your knowledge):
{web_context}

IMPORTANT INSTRUCTIONS:
1. Identify 8-12 real mining companies in Latin America
2. Each must be a REAL company with verifiable data
3. Include ICP match reasoning for each
4. Output ONLY valid JSON - no markdown, no code blocks
5. Use this exact JSON structure:
{{
  "accounts": [
    {{
      "company_name": "...",
      "country": "...",
      "commodities": ["..."],
      "revenue_usd": "...",
      "employees": "...",
      "key_sites": ["..."],
      "icp_match_score": 85,
      "icp_match_reasoning": "...",
      "flytbase_value_prop": "...",
      "recent_news": ["..."],
      "stock_ticker": "..."
    }}
  ],
  "total_accounts": 10,
  "methodology": "..."
}}"""

    # Step 3: Call LLM
    print("[Stage 1] Analyzing companies with AI...")
    try:
        response_text = call_llm(augmented_prompt)
        result = parse_json_response(response_text)
        
        print(f"[Stage 1] Found {len(result.get('accounts', []))} accounts")
        return result
        
    except Exception as e:
        print(f"[Stage 1] Error: {e}")
        return {"accounts": [], "error": str(e)}
