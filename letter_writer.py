"""
Cover letter generator.
- LLM mode if ANTHROPIC_API_KEY is set
- Template mode otherwise
- Always reads resume_profile.json fresh per call
"""
import json
from pathlib import Path
import config
from models import Job

PROFILE_PATH = Path("resume_profile.json")


def _load_profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def write_letter(job: Job) -> str:
    profile = _load_profile()
    if config.USE_LLM_LETTERS:
        try:
            return _llm_letter(job, profile)
        except Exception as e:
            print(f"[letter] LLM failed ({e}); using template")
    return _template_letter(job, profile)


def _llm_letter(job: Job, profile: dict) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    highlights = "\n".join("  • " + h for h in profile["highlights"]) or "  • (none provided)"
    prompt = f"""You are writing a cover letter on behalf of a job applicant.

APPLICANT PROFILE:
- Name: {profile['name']}
- Years of experience: {profile['years']}
- Key skills: {', '.join(profile['skills'])}
- Background: {profile['summary']}
- Career highlights:
{highlights}

JOB DETAILS:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
- Description:
{job.description[:2500]}

Write a cover letter that:
1. Opens with a specific hook referencing this company/role
2. Highlights 2–3 of the applicant's real skills that match the job
3. Mentions one concrete achievement with a number
4. States remote/location fit if relevant
5. Closes with a clear call to action

Tone: professional, warm, confident, concise. Under 280 words.
No placeholders like [Company Name]. Address the reader as "you".
Return ONLY the letter body (no subject, no "Dear Hiring Manager")."""

    resp = client.messages.create(
        model=config.LLM_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    body = resp.content[0].text.strip()
    return _wrap(job, body, profile)


def _template_letter(job: Job, profile: dict) -> str:
    text = f"{job.title} {job.description}".lower()
    matching = [s for s in profile["skills"] if s in text][:3] \
        or profile["skills"][:3]
    highlight = profile["highlights"][0] if profile["highlights"] else ""
    skills_line = ", ".join(matching)
    title_line = profile["titles"][0] if profile["titles"] else "software development"

    body = f"""I came across the {job.title} role at {job.company} and it aligns closely with my work in {skills_line}.

Over the past {profile['years']} years I've focused on {title_line}. {"A recent example: " + highlight if highlight else ""}

I'd welcome the chance to discuss how I can contribute to your team. My resume is attached and I'm available for a call at your convenience.

Thank you for your time and consideration."""
    return _wrap(job, body, profile)


def _wrap(job: Job, body: str, profile: dict) -> str:
    return f"""Subject: Application — {job.title} at {job.company}

Dear Hiring Manager,

{body}

Sincerely,
{profile['name']}
{profile['email']}
"""