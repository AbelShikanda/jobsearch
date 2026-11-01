import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config
from models import Job


def build_html(jobs: list[Job]) -> str:
    rows = []
    for j in jobs:
        letter_html = ""
        if j.letter:
            safe = (
                j.letter
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            letter_html = (
                "<details><summary>📝 Show cover letter</summary>"
                f"<pre style='white-space:pre-wrap;font-family:inherit;"
                f"background:#f7f7f7;padding:10px;border-radius:6px'>{safe}</pre>"
                "</details>"
            )
        rows.append(f"""
        <tr>
          <td><b>{j.title}</b><br>
              <small>{j.company} — {j.location}</small></td>
          <td><a href="{j.apply_url or j.url}">Apply</a><br>
              <small>{j.email or ''}</small></td>
          <td>{j.score}<br>
              <small>{'; '.join(j.reasons)}</small></td>
          <td>{letter_html}</td>
        </tr>""")
    return f"""
    <html><body style="font-family:sans-serif">
      <h2>Job Leads ({len(jobs)})</h2>
      <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse">
        <tr>
          <th align="left">Job</th>
          <th align="left">Apply</th>
          <th align="left">Score</th>
          <th align="left">Cover Letter</th>
        </tr>
        {''.join(rows)}
      </table>
    </body></html>
    """


def send_report(jobs: list[Job]) -> None:
    if not jobs:
        print("No qualifying jobs — skipping email.")
        return
    if not config.GMAIL_USER or not config.GMAIL_APP_PASSWORD:
        print("Gmail credentials missing — skipping email.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Job Leads — {len(jobs)} new matches"
    msg["From"] = config.GMAIL_USER
    msg["To"] = config.REPORT_TO
    msg.attach(MIMEText(build_html(jobs), "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
        server.send_message(msg)
    print(f"📧 Report sent to {config.REPORT_TO}")