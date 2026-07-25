"""
Stage 2: Contact Discovery Agent
Finds key decision-makers (Head of Ops, VP HSE, Site Directors) at target companies.
Uses Gemini LLM + DuckDuckGo web search to find real contacts.
"""

import json
from duckduckgo_search import DDGS
from config import CONTACT_FINDER_PROMPT
from llm_client import call_llm, parse_json_response


def search_company_contacts(company_name: str, roles: list[str]) -> list[dict]:
    """Search for key contacts at a specific company."""
    results = []
    search_queries = [
        f"{company_name} Head of Operations VP Operations LinkedIn",
        f"{company_name} VP HSE safety director mining",
        f"{company_name} site director general mine manager",
        f"{company_name} COO chief operating officer mining",
        f"{company_name} digital transformation innovation director mining",
        f"{company_name} leadership team executives mining"
    ]
    
    try:
        with DDGS() as ddgs:
            for query in search_queries[:4]:  # Limit searches per company
                for r in ddgs.text(query, max_results=3):
                    results.append({
                        "title": r.get("title", ""),
                        "body": r.get("body", ""),
                        "href": r.get("href", ""),
                        "company": company_name
                    })
    except Exception as e:
        print(f"[Contact Hunter] Search error for {company_name}: {e}")
    
    return results


def run_contact_hunter(accounts: list[dict]) -> dict:
    """
    Stage 2: Discover contacts at identified accounts.
    
    Args:
        accounts: List of account dictionaries from Stage 1
    
    Returns:
        Dictionary with contacts list and metadata
    """
    print("[Stage 2] Contact Discovery - Starting...")
    
    # Step 1: Search for contacts at each company
    all_search_results = []
    for account in accounts:
        company_name = account.get("company_name", "")
        if company_name:
            print(f"[Stage 2] Searching contacts at {company_name}...")
            results = search_company_contacts(company_name, [
                "Head of Operations", "VP HSE", "Site Director"
            ])
            all_search_results.extend(results)
    
    # Format search results as context
    search_context = ""
    for i, r in enumerate(all_search_results[:60]):
        search_context += f"[{i+1}] {r['title']}: {r['body']} ({r['href']})\n"
    
    # Step 2: Build prompt
    companies_json = json.dumps([{
        "company_name": a.get("company_name"),
        "country": a.get("country"),
        "commodities": a.get("commodities", [])
    } for a in accounts], indent=2)
    
    prompt = CONTACT_FINDER_PROMPT.format(companies=companies_json)
    
    augmented_prompt = f"""{prompt}

WEB SEARCH RESULTS (use these to find REAL contacts - verify names are real):
{search_context}

IMPORTANT INSTRUCTIONS:
1. Find 2-3 contacts per company (prioritize Head of Ops, VP HSE, Site Directors)
2. ONLY include REAL, verifiable people - no invented names
3. If you cannot find a specific person, note "Contact research needed" for that role
4. Include LinkedIn URLs where you found them in search results
5. Output ONLY valid JSON - no markdown, no code blocks
6. Use this exact JSON structure:
{{
  "contacts": [
    {{
      "name": "...",
      "title": "...",
      "seniority": "VP / Director / C-Suite",
      "company": "...",
      "linkedin_url": "... or Not publicly available",
      "email": "... or Not publicly available",
      "relevance": "Why this person is the right contact for FlytBase",
      "verified": true
    }}
  ],
  "total_contacts": 20,
  "methodology": "..."
}}"""
    
    # Step 3: Call LLM
    print("[Stage 2] Analyzing contacts with AI...")
    try:
        response_text = call_llm(augmented_prompt)
        result = parse_json_response(response_text)
        
        print(f"[Stage 2] Found {len(result.get('contacts', []))} contacts")
        return result
        
    except Exception as e:
        print(f"[Stage 2] Error: {e}")
        return {"contacts": [], "error": str(e)}
