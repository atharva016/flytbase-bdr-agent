"""
Stage 4: Personalized Email Generation Agent
Generates hyper-personalized outbound emails for each contact.
Emails are specific, human-sounding, and reference real research.
"""

import json
from config import EMAIL_COMPOSER_PROMPT
from llm_client import call_llm, parse_json_response


def run_email_composer(
    contacts: list[dict],
    research_briefs: list[dict],
    accounts: list[dict]
) -> dict:
    """
    Stage 4: Generate personalized outbound emails.
    
    Args:
        contacts: List of contact dictionaries from Stage 2
        research_briefs: List of research briefs from Stage 3
        accounts: List of account dictionaries from Stage 1
    
    Returns:
        Dictionary with generated emails and metadata
    """
    print("[Stage 4] Email Generation - Starting...")
    
    # Step 1: Merge contacts with their company research
    research_by_company = {}
    for brief in research_briefs:
        company = brief.get("company_name", "")
        research_by_company[company] = brief
    
    account_by_company = {}
    for account in accounts:
        company = account.get("company_name", "")
        account_by_company[company] = account
    
    contacts_with_research = []
    for contact in contacts:
        company = contact.get("company", "")
        enriched_contact = {
            **contact,
            "company_research": research_by_company.get(company, {}),
            "company_info": account_by_company.get(company, {})
        }
        contacts_with_research.append(enriched_contact)
    
    # Step 2: Build prompt
    prompt = EMAIL_COMPOSER_PROMPT.format(
        contacts_with_research=json.dumps(contacts_with_research, indent=2)
    )
    
    augmented_prompt = f"""{prompt}

CRITICAL RULES:
1. Each email MUST be unique - no two emails should read the same
2. Reference SPECIFIC details from the company research (recent news, projects, challenges)
3. Subject lines must be compelling and specific to the company
4. Keep emails to 4-6 sentences - BDRs don't write essays
5. The CTA should ask for a specific 15-minute call
6. Sign off as: Atharva Jamdar, Business Development Representative, FlytBase
7. Output ONLY valid JSON - no markdown, no code blocks
8. Use this exact JSON structure:
{{
  "emails": [
    {{
      "contact_name": "...",
      "contact_title": "...",
      "company": "...",
      "subject": "...",
      "body": "...",
      "personalization_notes": "What specific research was used to personalize this email",
      "quality_score": 85,
      "key_hooks": ["Specific elements that make this email personalized"]
    }}
  ],
  "total_emails": 20,
  "methodology": "..."
}}"""
    
    # Step 3: Call LLM
    print("[Stage 4] Generating personalized emails with AI...")
    try:
        response_text = call_llm(augmented_prompt)
        result = parse_json_response(response_text)
        
        print(f"[Stage 4] Generated {len(result.get('emails', []))} emails")
        return result
        
    except Exception as e:
        print(f"[Stage 4] Error: {e}")
        return {"emails": [], "error": str(e)}
