"""
Stage 3: Account Research Agent
Produces deep research briefs on each target company using real public data.
Connects findings to FlytBase's autonomous drone inspection angle.
"""

import json
from duckduckgo_search import DDGS
from config import RESEARCH_ANALYST_PROMPT
from llm_client import call_llm, parse_json_response


def deep_research_company(company_name: str) -> list[dict]:
    """Perform deep web research on a specific company."""
    results = []
    search_queries = [
        f"{company_name} mining news 2025 2026",
        f"{company_name} technology investment automation drones",
        f"{company_name} safety incidents ESG sustainability",
        f"{company_name} expansion operations new mine project",
        f"{company_name} annual report revenue production 2025",
        f"{company_name} contracted crews inspection maintenance mining"
    ]
    
    try:
        with DDGS() as ddgs:
            for query in search_queries:
                for r in ddgs.text(query, max_results=4):
                    results.append({
                        "title": r.get("title", ""),
                        "body": r.get("body", ""),
                        "href": r.get("href", ""),
                        "query": query
                    })
    except Exception as e:
        print(f"[Research Analyst] Search error for {company_name}: {e}")
    
    return results


def run_research_analyst(accounts: list[dict]) -> dict:
    """
    Stage 3: Deep research on each target account.
    
    Args:
        accounts: List of account dictionaries from Stage 1
    
    Returns:
        Dictionary with research briefs and metadata
    """
    print("[Stage 3] Account Research - Starting...")
    
    # Step 1: Deep research each company
    all_research = {}
    for account in accounts:
        company_name = account.get("company_name", "")
        if company_name:
            print(f"[Stage 3] Researching {company_name}...")
            results = deep_research_company(company_name)
            all_research[company_name] = results
    
    # Format research as context
    research_context = ""
    for company, results in all_research.items():
        research_context += f"\n=== RESEARCH FOR {company.upper()} ===\n"
        for i, r in enumerate(results[:10]):
            research_context += f"[{i+1}] {r['title']}: {r['body']} (Source: {r['href']})\n"
    
    if not research_context.strip():
        research_context = "Web search unavailable. Use your training knowledge to produce research briefs with publicly known information about these companies. Focus on well-documented facts: revenue, operations, recent major projects, leadership, and safety/ESG initiatives."
    
    # Step 2: Build prompt
    companies_json = json.dumps(accounts, indent=2)
    prompt = RESEARCH_ANALYST_PROMPT.format(companies=companies_json)
    
    augmented_prompt = f"""{prompt}

LIVE WEB RESEARCH DATA (synthesize these real sources into your briefs):
{research_context}

IMPORTANT INSTRUCTIONS:
1. Produce a research brief for EACH company
2. ALL data must be real and verifiable - cite sources where possible
3. Focus on strategic insights, not generic summaries
4. Connect every brief to FlytBase's specific value proposition
5. Highlight pain points where autonomous drone inspection solves real problems
6. Output ONLY valid JSON - no markdown, no code blocks
7. Use this exact JSON structure:
{{
  "research_briefs": [
    {{
      "company_name": "...",
      "executive_summary": "2-3 sentence strategic overview",
      "recent_news": [
        {{
          "headline": "...",
          "detail": "...",
          "source": "...",
          "date": "..."
        }}
      ],
      "operational_footprint": {{
        "sites": ["..."],
        "scale": "...",
        "geography": "..."
      }},
      "technology_signals": [
        {{
          "signal": "...",
          "detail": "...",
          "relevance_to_flytbase": "..."
        }}
      ],
      "safety_esg_signals": [
        {{
          "signal": "...",
          "detail": "..."
        }}
      ],
      "flytbase_angle": {{
        "primary_use_case": "...",
        "pain_points_addressed": ["..."],
        "estimated_impact": "...",
        "competitor_context": "..."
      }},
      "research_quality_score": 85,
      "sources_cited": ["..."]
    }}
  ],
  "methodology": "..."
}}"""
    
    # Step 3: Call LLM
    print("[Stage 3] Synthesizing research with AI...")
    try:
        response_text = call_llm(augmented_prompt)
        result = parse_json_response(response_text)
        
        print(f"[Stage 3] Produced {len(result.get('research_briefs', []))} research briefs")
        return result
        
    except Exception as e:
        print(f"[Stage 3] Error: {e}")
        return {"research_briefs": [], "error": str(e)}
