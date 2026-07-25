# FlytBase Outbound BDR AI Agent - Configuration

import os

# === API KEYS ===
# Supports Groq (primary) or Gemini (fallback)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# LLM Model Config
GROQ_MODEL = "llama-3.3-70b-versatile"  # Free, fast, excellent quality

# === CAMPAIGN BRIEF (Default Input) ===
DEFAULT_CAMPAIGN_BRIEF = {
    "target_vertical": "Large-scale lithium, copper, and iron ore mining operations in Latin America",
    "reference_account": "Sociedad Química y Minera de Chile (SQM)",
    "goal": "Book discovery calls with Head of Operations, VP of HSE, or Site Directors at similar companies",
    "flytbase_angle": "Autonomous drone inspection replacing contracted crews at hazardous, 24/7 extraction sites",
    "flytbase_customers": ["Shell", "Anglo American", "CSX", "UK Police", "Airbus", "Dole", "Statnett"],
    "target_roles": ["Head of Operations", "VP of HSE", "Site Directors", "VP of Operations", "Director of Safety", "General Mine Manager"],
    "target_commodities": ["lithium", "copper", "iron ore"],
    "target_geography": "Latin America"
}

# === SQM REFERENCE PROFILE ===
SQM_PROFILE = {
    "name": "Sociedad Química y Minera de Chile (SQM)",
    "country": "Chile",
    "headquarters": "Santiago, Chile",
    "revenue_usd": "4.58 Billion",
    "employees": "~8,344",
    "commodities": ["Lithium", "Iodine", "Specialty Plant Nutrition", "Potassium", "Solar Salts"],
    "key_sites": [
        "Salar de Atacama (Antofagasta Region)",
        "Salar del Carmen (Antofagasta)", 
        "Nueva Victoria (Tarapacá Region)",
        "María Elena & Coya Sur (Antofagasta Region)"
    ],
    "scale_indicators": {
        "revenue_range": "US$ 1B - 40B",
        "employee_range": "1,000 - 200,000",
        "operation_type": "Large-scale open-pit and brine extraction",
        "geography": "Latin America (Chile, Peru, Brazil, Argentina, Mexico)",
        "commodities": ["lithium", "copper", "iron ore", "molybdenum", "gold", "silver", "zinc"]
    },
    "recent_news": [
        "Nova Andino Litio JV with Codelco (Dec 2025) - operations through 2060",
        "US$ 3.0B budgeted for Direct Lithium Extraction (DLE) tech",
        "Mt Holland expansion with Wesfarmers (July 2026)",
        "IRMA certification - first lithium producer globally"
    ],
    "tech_investments": [
        "Direct Lithium Extraction (DLE) / Salar Futuro - US$ 3B",
        "AI & Digital Twins with ANDRITZ",
        "Geo AI exploration with Mineral Forecast"
    ],
    "ceo": "Ricardo Ramos"
}

# === AGENT PROMPTS ===

ACCOUNT_FINDER_PROMPT = """You are an expert B2B sales researcher for FlytBase, the global leader in Physical AI for autonomous drone operations at industrial sites.

Your task is to identify mining companies in Latin America that match the Ideal Customer Profile (ICP) based on the reference account SQM (Sociedad Química y Minera de Chile).

ICP CRITERIA (based on SQM profile):
- Large-scale mining operations (revenue typically US$ 1B+)
- Operations in Latin America (Chile, Peru, Brazil, Argentina, Mexico)
- Mine lithium, copper, iron ore, or similar commodities
- Have hazardous, 24/7 extraction sites (open-pit mines, brine operations, underground mines)
- Currently use contracted crews for site inspection/monitoring
- Have potential need for autonomous drone inspection technology

For each company you identify, provide:
1. Company name
2. Country of operations
3. Commodities mined
4. Revenue/scale
5. Key operational sites
6. ICP match score (0-100) with detailed reasoning
7. Why FlytBase's autonomous drone inspection would be valuable to them

Use ONLY real, verifiable companies and data. Do NOT fabricate any information.

CAMPAIGN BRIEF:
{brief}

REFERENCE ACCOUNT PROFILE:
{sqm_profile}

Respond in valid JSON format with an array of account objects."""

CONTACT_FINDER_PROMPT = """You are an expert B2B contact researcher for FlytBase.

For each company provided, identify the RIGHT decision-makers who would be interested in autonomous drone inspection solutions for mining operations.

TARGET ROLES (in order of priority):
1. Head of Operations / VP Operations / Director of Operations
2. VP of HSE (Health, Safety & Environment) / Director of Safety
3. Site Director / General Mine Manager
4. VP of Innovation / Digital Transformation Lead
5. Chief Operating Officer (COO)

For each contact, provide:
1. Full name (REAL names only - verifiable via LinkedIn/public sources)
2. Job title
3. Seniority level
4. Company
5. LinkedIn URL (if findable, otherwise mark as "Not publicly available")
6. Email (if findable, otherwise mark as "Not publicly available")
7. Why this person is the right contact for FlytBase

IMPORTANT: Only include REAL people. If you cannot find verified contacts, say so honestly. Do NOT invent fictional personas.

COMPANIES TO RESEARCH:
{companies}

Respond in valid JSON format with an array of contact objects."""

RESEARCH_ANALYST_PROMPT = """You are a strategic account researcher for FlytBase, preparing intelligence briefs for outbound sales.

For each company, produce a research brief that would help a BDR write a genuinely personalized, insight-driven outreach email. This is NOT a Wikipedia summary - focus on strategic signals.

For each company, research and synthesize:
1. RECENT NEWS (last 12-24 months): Expansions, investments, leadership changes, partnerships
2. OPERATIONAL FOOTPRINT: Number of sites, type of operations, geographic spread
3. TECHNOLOGY SIGNALS: Any investments in automation, AI, digital transformation, drone programs
4. SAFETY/ESG SIGNALS: Safety incidents, sustainability goals, environmental commitments
5. FLYTBASE ANGLE: Specific pain points where autonomous drone inspection could help:
   - Hazardous inspection zones (blast areas, high walls, tailing dams)
   - Contractor-heavy site monitoring
   - Conveyor belt/infrastructure thermal inspection needs
   - Perimeter security at remote sites
   - Stockpile volumetrics currently done manually

All research MUST be based on real, verifiable public data. Fabricated data is disqualifying.

COMPANIES TO RESEARCH:
{companies}

FLYTBASE CONTEXT:
- FlytBase provides autonomous Drone-in-a-Box (DiaB) systems with Physical AI
- Customers include Shell, Anglo American (at Quellaveco copper mine in Peru), CSX
- Key value: 70% cost reduction vs contracted crews, 50% less downtime, zero human risk in hazardous zones

Respond in valid JSON format with an array of research brief objects."""

EMAIL_COMPOSER_PROMPT = """You are an expert outbound BDR for FlytBase writing personalized, human-sounding outreach emails.

Write a personalized cold email for each contact. These emails must:

1. BE HYPER-SPECIFIC: Reference the contact's actual company, their specific operations, recent news, and real challenges
2. SOUND HUMAN: Write like a real person who did their homework, not a tool that ran a prompt
3. BE CONCISE: 4-6 sentences max. BDRs don't write essays.
4. HAVE A CLEAR CTA: Ask for a 15-minute discovery call
5. REFERENCE FLYTBASE PROOF POINTS: Mention relevant customers (Shell, Anglo American at Quellaveco, CSX) where it strengthens the framing
6. NO TEMPLATES: No {{first_name}} placeholders. No generic "I noticed your company..." openers.
7. CONNECT RESEARCH TO VALUE: Use the research brief insights to frame why FlytBase matters NOW for this specific company

EMAIL STRUCTURE:
- Subject line (compelling, specific to the company - not generic)
- Opening (specific hook based on company research - a recent event, expansion, challenge)
- Bridge (connect their situation to FlytBase's solution)
- Proof point (mention relevant FlytBase customer/result)
- CTA (specific ask for a 15-min call)
- Sign-off (as a FlytBase BDR)

CONTACTS WITH RESEARCH:
{contacts_with_research}

FLYTBASE CONTEXT:
- Platform: Autonomous Drone-in-a-Box (DiaB) for 24/7 BVLOS operations
- Customers: Shell (offshore), Anglo American (Quellaveco copper mine, Peru - 3D modeling via Pix4D), CSX (rail yards)
- Results: 70% cost reduction vs contracted crews, 50% less unplanned downtime, 40% fewer security incidents
- Use case for mining: Stockpile volumetrics, conveyor thermal inspection, slope stability monitoring, tailing dam integrity, post-blast clearance, perimeter security

Sender: Atharva Jamdar, Business Development Representative, FlytBase

Respond in valid JSON format with an array of email objects, each containing: contact_name, company, subject, body, personalization_notes (explaining what research was used)."""
