"""
Stage 4: Personalized Email Generation Agent
Generates hyper-personalized outbound emails for each contact.
Emails are specific, human-sounding, and reference real research.
Processes contacts in small batches to stay within token limits.
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
    Processes contacts in batches of 3 to avoid token limits.
    """
    print("[Stage 4] Email Generation - Starting...")
    
    # Step 1: Merge contacts with their company research (compact version)
    research_by_company = {}
    for brief in research_briefs:
        company = brief.get("company_name", "")
        # Keep only essential research fields to reduce token count
        research_by_company[company] = {
            "company_name": company,
            "executive_summary": brief.get("executive_summary", ""),
            "recent_news": brief.get("recent_news", [])[:3],
            "technology_signals": brief.get("technology_signals", [])[:2],
            "flytbase_angle": brief.get("flytbase_angle", {})
        }
    
    account_by_company = {}
    for account in accounts:
        company = account.get("company_name", "")
        account_by_company[company] = {
            "company_name": company,
            "country": account.get("country", ""),
            "commodities": account.get("commodities", []),
            "revenue_usd": account.get("revenue_usd", ""),
            "key_sites": account.get("key_sites", [])[:3]
        }
    
    contacts_with_research = []
    for contact in contacts:
        company = contact.get("company", "")
        enriched_contact = {
            "name": contact.get("name", ""),
            "title": contact.get("title", ""),
            "company": company,
            "company_research": research_by_company.get(company, {}),
            "company_info": account_by_company.get(company, {})
        }
        contacts_with_research.append(enriched_contact)
    
    # Step 2: Process in batches of 3 contacts to stay within token limits
    all_emails = []
    batch_size = 3
    
    for i in range(0, len(contacts_with_research), batch_size):
        batch = contacts_with_research[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(contacts_with_research) + batch_size - 1) // batch_size
        
        print(f"[Stage 4] Generating emails batch {batch_num}/{total_batches} ({len(batch)} contacts)...")
        
        prompt = EMAIL_COMPOSER_PROMPT.format(
            contacts_with_research=json.dumps(batch, indent=2, ensure_ascii=False)
        )
        
        augmented_prompt = f"""{prompt}

CRITICAL RULES:
1. Each email MUST be unique - no two emails should read the same
2. Reference SPECIFIC details from the company research (recent news, projects, challenges)
3. Subject lines must be compelling and specific to the company
4. Keep emails to 4-6 sentences max
5. The CTA should ask for a specific 15-minute call
6. Sign off as: Atharva Jamdar, Business Development Representative, FlytBase
7. Output ONLY valid JSON
8. Use this JSON structure:
{{
  "emails": [
    {{
      "contact_name": "...",
      "contact_title": "...",
      "company": "...",
      "subject": "...",
      "body": "...",
      "personalization_notes": "What research was used",
      "quality_score": 85,
      "key_hooks": ["..."]
    }}
  ]
}}"""
        
        try:
            response_text = call_llm(augmented_prompt)
            result = parse_json_response(response_text)
            batch_emails = result.get("emails", [])
            all_emails.extend(batch_emails)
            print(f"[Stage 4] Batch {batch_num}: Generated {len(batch_emails)} emails")
        except Exception as e:
            print(f"[Stage 4] Batch {batch_num} error: {e}")
            # Continue with next batch even if one fails
    
    print(f"[Stage 4] Total emails generated: {len(all_emails)}")
    return {
        "emails": all_emails,
        "total_emails": len(all_emails),
        "methodology": "Contacts processed in batches of 3 with enriched company research. Each email uses specific research hooks and company context."
    }
