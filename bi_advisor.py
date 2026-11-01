# bi_advisor.py
"""
Per-organization BI improvement recommendations.

- LLM mode when ANTHROPIC_API_KEY is set (USE_LLM_BI = True)
- Template fallback using category-specific playbooks
- Reads resume_profile.json fresh per call

Public entry point:
    write_bi_recommendation(org_name, jobs) -> str
"""
import json
from pathlib import Path

import config
from models import Job

PROFILE_PATH = Path("resume_profile.json")


# ── Category playbooks for the template fallback ────────────
PLAYBOOK = {
    "pharmacy": {
        "pain": "expired stock and till-level M-Pesa reconciliation",
        "data": [
            "Daily M-Pesa + cash receipts by branch and till operator",
            "Stock levels by SKU with expiry dates",
            "Prescription refill rates per chronic customer",
        ],
        "bi": [
            "Expiry-risk dashboard — tracks stock within 60 days "
            "of expiry by branch; used by the pharmacist-in-charge; "
            "drives weekly markdown or inter-branch transfer decisions",
            "Till-variance report — flags operators with >2% "
            "cash-to-M-Pesa mismatch by shift; used by branch "
            "managers; drives daily cash-handling coaching",
            "Refill-reminder automation — SMS to chronic-medication "
            "customers whose cycle is due; drives repeat revenue",
        ],
        "quick": "expiry-risk dashboard cutting write-offs by 25%",
    },
    "medical supply store": {
        "pain": "stockouts on critical items and slow-moving inventory",
        "data": [
            "Weekly consumption by SKU and by client facility",
            "Supplier lead times and price history",
            "Stock-on-hand vs. reorder point per item",
        ],
        "bi": [
            "Reorder-alert dashboard — flags SKUs below reorder "
            "point; used by the procurement officer; drives daily "
            "purchase orders",
            "Client-consumption report — shows each clinic's monthly "
            "usage trend; drives quarterly contract renewal talks",
            "Supplier price tracker — flags >5% weekly increases",
        ],
        "quick": "reorder-alert dashboard cutting stockouts by 40%",
    },
    "supermarket": {
        "pain": "shrinkage and reorder timing",
        "data": [
            "Per-till basket size and item mix",
            "Stock-on-hand vs. reorder point per SKU",
            "Footfall by hour vs. revenue by hour",
        ],
        "bi": [
            "Daily reorder-alert dashboard — flags SKUs below "
            "reorder point; used by the procurement lead; drives "
            "morning purchase orders",
            "Shrinkage heatmap — shows loss by aisle and shift; "
            "used by the store manager; drives weekly loss-prevention "
            "focus",
            "Basket-affinity report — shows what sells together; "
            "drives shelf layout and cross-promotion",
        ],
        "quick": "reorder-alert dashboard cutting stockouts by 30%",
    },
    "grocery store": {
        "pain": "perishable waste and reorder timing",
        "data": [
            "Daily sales by SKU and shelf location",
            "Waste log by item and reason (expiry, damage)",
            "Supplier delivery reliability",
        ],
        "bi": [
            "Waste-tracking dashboard — logs daily spoilage by item; "
            "used by the shop manager; drives markdown timing",
            "Reorder-alert dashboard for perishables and staples",
            "Supplier scorecard — rates delivery punctuality and "
            "fill-rate; drives negotiation",
        ],
        "quick": "waste-tracking dashboard cutting spoilage by 20%",
    },
    "logistics service": {
        "pain": "route inefficiency and delivery-proof tracking",
        "data": [
            "Per-route distance, time, and fuel",
            "Delivery success rate by driver and vehicle",
            "Client billing vs. actual cost per shipment",
        ],
        "bi": [
            "Route-profitability dashboard — shows margin per route; "
            "used by the ops manager; drives route redesign",
            "Driver scorecard — on-time %, damage rate, fuel/km; "
            "used by the fleet supervisor; drives monthly coaching",
            "COD reconciliation report — matches cash collected to "
            "invoices; used by finance; drives daily cash controls",
        ],
        "quick": "route-profitability dashboard finding 15% margin leaks",
    },
    "courier service": {
        "pain": "delivery-proof tracking and COD reconciliation",
        "data": [
            "Per-courier deliveries, distance, and time",
            "Failed-delivery rate by reason",
            "COD cash collected vs. invoices",
        ],
        "bi": [
            "Courier scorecard — success rate, on-time %, COD "
            "accuracy; used by the dispatcher; drives weekly "
            "route assignments",
            "Failed-delivery dashboard — reasons and repeat addresses",
            "COD reconciliation report — daily cash matching",
        ],
        "quick": "courier scorecard cutting failed deliveries by 25%",
    },
    "freight forwarder": {
        "pain": "shipment-margin visibility and customs-clearance delays",
        "data": [
            "Per-shipment revenue vs. cost (customs, transport, doc)",
            "Clearance time by port and by clearing agent",
            "Client payment ageing",
        ],
        "bi": [
            "Shipment-margin dashboard — shows margin per container; "
            "used by the director; drives quote revisions",
            "Clearance-time tracker — average days by port and agent",
            "Receivables dashboard — ageing report by client",
        ],
        "quick": "shipment-margin dashboard finding loss-making lanes",
    },
    "clearing agent": {
        "pain": "customs-clearance delays and client receivables",
        "data": [
            "Clearance time per shipment and per customs officer",
            "Revenue vs. duty/VAT disbursements per file",
            "Client payment ageing",
        ],
        "bi": [
            "Clearance-cycle dashboard — average days by port, "
            "client, and commodity; drives prioritization",
            "File-margin report — revenue vs. disbursements per file",
            "Receivables ageing dashboard",
        ],
        "quick": "clearance-cycle dashboard cutting dwell time by 2 days",
    },
    "warehouse": {
        "pain": "space utilization and picking efficiency",
        "data": [
            "Occupancy % by zone and by client",
            "Pick-rate per worker-hour",
            "Inbound-to-shelf cycle time",
        ],
        "bi": [
            "Occupancy dashboard — utilization by zone and client; "
            "drives pricing and layout decisions",
            "Pick-rate scorecard — units per hour by picker",
            "Inbound-cycle tracker — dock to shelf in hours",
        ],
        "quick": "occupancy dashboard unlocking 20% more billable space",
    },
    "delivery service": {
        "pain": "per-drop profitability and rider utilization",
        "data": [
            "Drops per rider per day",
            "Revenue vs. fuel and time per drop",
            "Failed or repeat deliveries per address",
        ],
        "bi": [
            "Rider scorecard — drops, revenue, fuel cost per rider",
            "Drop-profitability heatmap — margin by zone",
            "Address-quality dashboard — repeat failed deliveries",
        ],
        "quick": "rider scorecard raising utilization by 20%",
    },
    "garage": {
        "pain": "job-card tracking and parts inventory",
        "data": [
            "Open job cards by status and technician",
            "Parts used vs. parts billed per job",
            "Average turnaround time by job type",
        ],
        "bi": [
            "Job-card pipeline dashboard — shows each vehicle's "
            "stage; used by the workshop manager; drives daily "
            "scheduling",
            "Parts-variance report — flags missing parts between "
            "issued and billed",
            "Turnaround-time dashboard — by job type and technician",
        ],
        "quick": "job-card pipeline cutting turnaround by 20%",
    },
    "car repair": {
        "pain": "job-card tracking and parts variance",
        "data": [
            "Open job cards by stage",
            "Parts issued vs. parts billed",
            "Repeat customers and their vehicle history",
        ],
        "bi": [
            "Job-card pipeline dashboard",
            "Parts-variance report",
            "Customer-history dashboard — service intervals",
        ],
        "quick": "job-card dashboard cutting turnaround by 20%",
    },
    "car wash": {
        "pain": "throughput at peak hours and repeat-customer tracking",
        "data": [
            "Vehicles washed per hour per bay",
            "Revenue by service type",
            "Repeat-customer frequency",
        ],
        "bi": [
            "Throughput dashboard — vehicles per hour per bay",
            "Service-mix report — revenue by wash type",
            "Loyalty dashboard — repeat customer rate",
        ],
        "quick": "throughput dashboard cutting peak-hour waits by 30%",
    },
    "auto parts store": {
        "pain": "stockouts on fast-movers and dead stock",
        "data": [
            "Sales by part number and vehicle model",
            "Stock-on-hand vs. reorder point",
            "Dead-stock ageing",
        ],
        "bi": [
            "Fast-mover dashboard — top 100 SKUs by velocity",
            "Dead-stock report — no sales in 90 days",
            "Reorder-alert system for fast-movers",
        ],
        "quick": "fast-mover dashboard cutting stockouts by 25%",
    },
    "tire shop": {
        "pain": "stock mix and fitting-bay utilization",
        "data": [
            "Sales by tire size and brand",
            "Fitting-bay utilization per hour",
            "Repeat-customer alignment intervals",
        ],
        "bi": [
            "Stock-mix dashboard — sales by size/brand",
            "Bay-utilization dashboard",
            "Customer-reminder automation for alignment/rotation",
        ],
        "quick": "stock-mix dashboard cutting dead stock by 30%",
    },
    "restaurant": {
        "pain": "food-cost variance and table turnover",
        "data": [
            "Recipe-level food cost per dish",
            "Table turnover by hour and day",
            "Delivery-platform reconciliation (Glovo, Uber Eats)",
        ],
        "bi": [
            "Food-cost dashboard — cost per dish vs. menu price; "
            "used by the chef and owner; drives menu repricing",
            "Turnover dashboard — tables per hour by shift",
            "Platform reconciliation — orders vs. payouts by app",
        ],
        "quick": "food-cost dashboard cutting waste by 20%",
    },
    "cafe": {
        "pain": "waste and peak-hour throughput",
        "data": [
            "Daily sales by item",
            "Waste log by item",
            "Peak-hour customer counts",
        ],
        "bi": [
            "Item-margin dashboard — top and bottom sellers",
            "Waste-tracking log",
            "Peak-hour staffing report",
        ],
        "quick": "item-margin dashboard doubling margin on top 5 items",
    },
    "bakery": {
        "pain": "production planning vs. actual demand",
        "data": [
            "Baked quantities vs. sold quantities per item",
            "Waste by item and time of day",
            "Standing orders vs. walk-in sales",
        ],
        "bi": [
            "Demand-forecast dashboard — yesterday's data feeds "
            "today's bake plan",
            "Waste-tracking log",
            "Standing-order dashboard",
        ],
        "quick": "demand-forecast dashboard cutting waste by 25%",
    },
    "solar energy company": {
        "pain": "lead-to-install conversion and after-sales service",
        "data": [
            "Lead source and conversion rate by channel",
            "Project cost vs. quote per installation",
            "Warranty/service tickets by product",
        ],
        "bi": [
            "Sales-pipeline dashboard — leads by source and stage; "
            "used by the sales lead; drives weekly follow-up",
            "Project-margin tracker — cost vs. quote per install",
            "Service-ticket analytics — issue frequency by product",
        ],
        "quick": "lead-source dashboard doubling conversion from best channel",
    },
    "water supplier": {
        "pain": "route density and tanker-return tracking",
        "data": [
            "Deliveries per tanker per day",
            "Distance and fuel per route",
            "Customer churn and prepaid balances",
        ],
        "bi": [
            "Route-density dashboard — stops per km per route",
            "Tanker-return tracker — dispatch to return in hours",
            "Churn-risk dashboard — customers with falling order "
            "frequency",
        ],
        "quick": "route-density dashboard raising stops/day by 15%",
    },
    "insurance agency": {
        "pain": "policy-renewal tracking and claim cycle time",
        "data": [
            "Policies due for renewal in next 90 days",
            "Claim cycle time by type",
            "Commission tracking per agent",
        ],
        "bi": [
            "Renewal-pipeline dashboard — policies by renewal date",
            "Claim-cycle dashboard — average days by claim type",
            "Agent-scorecard — commission and retention rate",
        ],
        "quick": "renewal-pipeline dashboard cutting lapse rate by 20%",
    },
    "sacco": {
        "pain": "loan portfolio risk and deposit-mix visibility",
        "data": [
            "Loan book by cohort and default rate",
            "Deposit mix — fixed vs. savings",
            "Member activity and dormancy",
        ],
        "bi": [
            "Loan-portfolio dashboard — default rate by cohort",
            "Deposit-mix report — funding cost trend",
            "Member-activity dashboard — active vs. dormant",
        ],
        "quick": "loan-portfolio dashboard cutting NPL ratio by 2 points",
    },
    "real estate agency": {
        "pain": "viewing-to-close ratio and rent-roll visibility",
        "data": [
            "Viewings per listing and conversion rate",
            "Rent-roll collection rate by property",
            "Days-on-market per property",
        ],
        "bi": [
            "Listing-funnel dashboard — views → viewings → offers",
            "Rent-roll dashboard — collection rate by unit",
            "Days-on-market report",
        ],
        "quick": "listing-funnel dashboard cutting days-on-market by 30%",
    },
    "private school": {
        "pain": "enrolment funnel and fee-collection rate",
        "data": [
            "Enquiries → applications → enrolments by source",
            "Fee-collection rate by class and by term",
            "Attendance and teacher-class ratios",
        ],
        "bi": [
            "Enrolment-funnel dashboard",
            "Fee-collection dashboard — outstanding by family",
            "Attendance analytics",
        ],
        "quick": "fee-collection dashboard cutting arrears by 25%",
    },
}


# ── Profile loader ──────────────────────────────────────────
def _load_profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


# ── Extract category and snippets from jobs ────────────────
def _extract_context(jobs: list[Job]) -> tuple[str, list[str]]:
    """
    Job.description has shape: "Category: X | snippet"
    Returns (category, list_of_snippets)
    """
    category = ""
    snippets: list[str] = []

    for j in jobs:
        desc = (j.description or "").strip()
        if desc.startswith("Category:"):
            head, _, rest = desc.partition("|")
            cat = head.replace("Category:", "").strip()
            if cat and not category:
                category = cat
            if rest.strip():
                snippets.append(rest.strip())
        elif desc:
            snippets.append(desc)

    # Dedupe + cap
    seen: set[str] = set()
    unique: list[str] = []
    for s in snippets:
        key = s[:80].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(s[:400])
        if len(unique) >= 3:
            break

    return category, unique


# ── Public ──────────────────────────────────────────────────
def write_bi_recommendation(org: str, jobs: list[Job]) -> str:
    profile = _load_profile()
    if config.USE_LLM_BI and config.ANTHROPIC_API_KEY:
        try:
            return _llm_recommendation(org, jobs, profile)
        except Exception as e:
            print(f"[BI] LLM failed ({e}); using template")
    return _template_recommendation(org, jobs, profile)


# ── LLM path ────────────────────────────────────────────────
def _llm_recommendation(org: str, jobs: list[Job], profile: dict) -> str:
    import anthropic
    kwargs = {"api_key": config.ANTHROPIC_API_KEY}
    if config.ANTHROPIC_BASE_URL:
        kwargs["base_url"] = config.ANTHROPIC_BASE_URL
    client = anthropic.Anthropic(**kwargs)

    category, snippets = _extract_context(jobs)

    context_block = "\n".join(
        f"  - {s}" for s in snippets
    ) or "  (no description available)"

    roles = "\n".join(
        f"  • {j.title}" for j in jobs
        if j.source != "brightdata_maps"
    ) or "  (no open roles on job boards — cold outreach)"

    skills = ", ".join(profile.get("skills", []))

    prompt = f"""You are a Business Intelligence consultant writing a
short, practical, SPECIFIC improvement memo for a Kenyan organization.

ORGANIZATION: {org}
CATEGORY / SECTOR: {category or "unknown — infer from name and snippets"}

WHAT WE KNOW ABOUT THIS ORGANIZATION:
{context_block}

OPEN ROLES THEY ARE HIRING FOR:
{roles}

CONSULTANT'S SKILLS:
{skills}

Write a memo with EXACTLY these five sections, no more than 280 words:

1. Snapshot — In 2 sentences, state what {org} actually does
   (use the category and snippets above — do NOT guess if the
   info is there). Then name ONE concrete operational pain
   point specific to a {category or "Kenyan"} business of this
   size and type.

2. Data they should be capturing — 3 specific data points
   relevant to a {category or "similar"} business. Be concrete:
   not "sales data" but "daily M-Pesa receipts by branch and
   by till operator".

3. BI improvements — 3 dashboards or automations this specific
   business needs. Each one must include: WHAT it tracks,
   WHO uses it, and WHAT decision it drives.

4. Quick win in 2 weeks — pick the single highest-ROI change
   from the list above and describe it in one sentence that
   includes a metric.

5. How I can help — one sentence linking the consultant's
   skills ({skills}) to delivering that quick win.

Rules:
- NO generic filler like "businesses in this space typically..."
- Every claim must relate to the category ({category}) or
  the snippets provided.
- Reference Kenya-specific context (M-Pesa, boda, county
  licensing, WhatsApp) only where it fits naturally.
- Do NOT use placeholders like [Name], [Company], [metric].
- Return ONLY the memo body — no headings like "Memo:".
"""

    resp = client.messages.create(
        model=config.BI_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    body = resp.content[0].text.strip()
    return _wrap(org, body, profile)


# ── Template fallback ───────────────────────────────────────
def _template_recommendation(org: str, jobs: list[Job], profile: dict) -> str:
    category, _snippets = _extract_context(jobs)

    # Pick playbook entry, falling back to a generic one
    playbook = PLAYBOOK.get(category.lower() if category else "")
    if not playbook:
        for key, entry in PLAYBOOK.items():
            if key in (category or "").lower():
                playbook = entry
                break
    if not playbook:
        playbook = {
            "pain": "manual record-keeping and untracked supplier prices",
            "data": [
                "Daily transactions (M-Pesa + cash) reconciled per shift",
                "Customer requests and their resolution time",
                "Supplier price history for top 10 inputs",
            ],
            "bi": [
                "Daily ops dashboard — revenue, footfall, top item",
                "Supplier price tracker — flags >5% weekly jumps",
                "WhatsApp order pipeline — logs every inbound "
                "message to a sheet",
            ],
            "quick": "M-Pesa ledger automation surfacing 5–10% leakage",
        }

    data_bullets = "\n".join(f"- {d}" for d in playbook["data"])
    bi_bullets = "\n".join(f"- {b}" for b in playbook["bi"])

    body = f"""1. Snapshot
{org} operates in {category or "a Kenyan local business"}. Its main
operational pain point is {playbook['pain']}.

2. Data to capture
{data_bullets}

3. BI improvements
{bi_bullets}

4. Quick win (2 weeks)
{playbook['quick'].capitalize()}.

5. How I can help
I build scraping, dashboards, and ETL pipelines — and can deliver
the quick win while training your staff."""

    return _wrap(org, body, profile)


def _wrap(org: str, body: str, profile: dict) -> str:
    return (
        f"BI Improvement Memo — {org}\n"
        f"Prepared by: {profile.get('name', 'Consultant')} "
        f"({profile.get('email', '')})\n"
        + "─" * 60 + "\n\n"
        + body + "\n"
    )