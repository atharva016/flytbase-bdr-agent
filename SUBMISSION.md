# Submission: FlytBase Outbound BDR AI Agent

## Candidate
- **Name:** Atharva Jamdar
- **Role Applied:** Business Development Representative — Outbound
- **Date:** 25th July 2026

---

## System Overview

An autonomous AI-powered outbound sales pipeline that takes a campaign brief as input and produces real account lists, verified contacts, research intelligence, and hyper-personalized outreach emails — the same workflow a human BDR would perform, but systematized and scalable.

### What It Does
1. **Account Identification** — Searches the web for Latin American mining companies matching SQM's ICP profile, scores them on fit, and explains why each qualifies
2. **Contact Discovery** — Finds real decision-makers (Head of Ops, VP HSE, Site Directors) at each company using live web search
3. **Account Research** — Produces strategic intelligence briefs from real public data: recent news, tech signals, ESG commitments, FlytBase-specific pain points
4. **Email Generation** — Writes unique, human-sounding outbound emails for each contact, referencing their company's specific situation

### Architecture
```
Campaign Brief (JSON Input)
        │
        ▼
┌──────────────────┐    DuckDuckGo
│  Agent 1:         │◄──── Web Search ────► Real-time company data
│  Account Finder   │
└────────┬─────────┘
         │ Accounts (8-12 companies)
         ▼
┌──────────────────┐    DuckDuckGo
│  Agent 2:         │◄──── Web Search ────► LinkedIn / leadership pages
│  Contact Hunter   │
└────────┬─────────┘
         │ Contacts (2-3 per company)
         ▼
┌──────────────────┐    DuckDuckGo
│  Agent 3:         │◄──── Web Search ────► News, reports, press releases
│  Research Analyst │
└────────┬─────────┘
         │ Research Briefs
         ▼
┌──────────────────┐
│  Agent 4:         │
│  Email Composer   │──► Personalized emails (batched, 3 at a time)
└──────────────────┘
```

### Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Backend | Python / Flask | Fast development, excellent AI library ecosystem |
| AI Engine | Groq (Llama 3.3 70B) | Free tier, blazing fast inference, strong JSON output |
| Web Search | DuckDuckGo Search | No API key required, real-time web data, no rate limits |
| Frontend | HTML / CSS / JavaScript | Premium dark-themed dashboard with SSE streaming |
| Deployment | Render | Free tier, auto-deploys from GitHub |
| Version Control | GitHub | Public repo with full commit history |

### Key Design Decisions

1. **Multi-agent over single-agent**: Each stage requires different skills (web search vs. analysis vs. creative writing). Separating them improves quality and makes each independently testable.

2. **Web search augmentation**: Rather than relying solely on LLM training data, every agent performs live DuckDuckGo searches first, then feeds real results to the LLM for synthesis. This ensures data is current and verifiable.

3. **Batched email generation**: Contacts are processed in groups of 3 to stay within token limits while maintaining quality. Each batch includes the contact's enriched company research.

4. **SSE streaming**: The frontend receives real-time Server-Sent Events as each stage completes, so users can watch the pipeline progress live.

5. **Provider abstraction**: A unified LLM client (`llm_client.py`) supports both Groq and Gemini, making it easy to switch providers or add fallbacks.

---

## Deliverables

| Deliverable | Link |
|-------------|------|
| **Live System** | [Deployed on Render] |
| **GitHub Repo** | https://github.com/atharva016/flytbase-bdr-agent |
| **Mind Map** | `mindmap.html` (self-contained HTML file in repo) |
| **This File** | `SUBMISSION.md` |

---

## How to Run Locally

```bash
# Clone
git clone https://github.com/atharva016/flytbase-bdr-agent.git
cd flytbase-bdr-agent

# Install dependencies
pip install -r requirements.txt

# Set API key
export GROQ_API_KEY=your_groq_api_key  # Get free at https://console.groq.com

# Run
python app.py

# Open http://localhost:5000 and click "Run Pipeline"
```

---

## What I'd Improve With More Time

- **Multi-LLM fallback chain**: Groq → Gemini → Claude for redundancy
- **LinkedIn API integration**: Verified contact data instead of web scraping
- **Email A/B variants**: Generate 2-3 variants per contact for testing
- **CRM push**: Direct integration with Salesforce/HubSpot
- **Follow-up sequences**: Automated multi-touch cadence generation
- **Feedback loop**: Track email engagement to improve personalization

---

## Failure Transparency

The system handles failures honestly:
- If web search returns limited results → logs the issue and continues with available data
- If a contact can't be verified → marked as "Contact research needed" (never fabricated)
- If LLM returns invalid JSON → fallback parser extracts JSON from response
- If token limit exceeded → emails processed in smaller batches
- All errors surfaced in the dashboard with clear explanations
