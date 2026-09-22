"""Email transports for the Mailer.

- "outlook": the desktop Outlook signed in on this machine — Windows via
  COM (pywin32), macOS via AppleScript. No app registration, no
  passwords; the mail appears in your own Sent Items.
- "smtp": Office 365 / any SMTP server with STARTTLS (needs SMTP AUTH
  enabled by your admin).
"""
import platform
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class SendError(Exception):
    pass


def send(cfg, to, cc, bcc, subject, html_body, review=False):
    if not to:
        raise SendError("no recipients")
    if cfg.get("transport") == "smtp":
        return _send_smtp(cfg, to, cc, bcc, subject, html_body)
    return _send_desktop(to, cc, bcc, subject, html_body, review)


def _send_desktop(to, cc, bcc, subject, html_body, review):
    system = platform.system()
    if system == "Windows":
        try:
            import win32com.client  # pywin32
        except ImportError as exc:
            raise SendError("pywin32 is not installed — run: pip install pywin32") from exc
        try:
            app = win32com.client.Dispatch("Outlook.Application")
            mail = app.CreateItem(0)
            mail.To = "; ".join(to)
            if cc:
                mail.CC = "; ".join(cc)
            if bcc:
                mail.BCC = "; ".join(bcc)
            mail.Subject = subject
            mail.HTMLBody = html_body
            if review:
                mail.Display()
                return "opened in Outlook for review"
            mail.Send()
            return "sent via desktop Outlook"
        except Exception as exc:  # COM errors are not a clean hierarchy
            raise SendError(f"Outlook (Windows) refused: {exc}") from exc
    if system == "Darwin":
        def q(s):
            return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'
        lines = ['tell application "Microsoft Outlook"',
                 f'set msg to make new outgoing message with properties {{subject:{q(subject)}, content:{q(html_body)}}}']
        for kind, addrs in (("to recipient", to), ("cc recipient", cc), ("bcc recipient", bcc)):
            for a in addrs:
                lines.append(f'make new {kind} at msg with properties {{email address:{{address:{q(a)}}}}}')
        lines.append("open msg" if review else "send msg")
        lines.append("end tell")
        proc = subprocess.run(["osascript", "-e", "\n".join(lines)], capture_output=True, text=True)
        if proc.returncode != 0:
            raise SendError(f"Outlook (macOS) refused: {proc.stderr.strip() or proc.stdout.strip()}")
        return "opened in Outlook for review" if review else "sent via desktop Outlook"
    raise SendError(f"desktop Outlook sending is not available on {system}; use SMTP")


def _send_smtp(cfg, to, cc, bcc, subject, html_body):
    user = cfg.get("smtp_user", "")
    if not user:
        raise SendError("SMTP user (your mailbox) is not configured")
    msg = MIMEMultipart("alternative")
    sender = f'{cfg.get("from_name")} <{user}>' if cfg.get("from_name") else user
    msg["From"], msg["To"], msg["Subject"] = sender, ", ".join(to), subject
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        with smtplib.SMTP(cfg.get("smtp_host", "smtp.office365.com"), int(cfg.get("smtp_port") or 587), timeout=60) as s:
            s.ehlo()
            s.starttls()
            s.login(user, cfg.get("smtp_password", ""))
            s.sendmail(user, to + cc + bcc, msg.as_string())
    except Exception as exc:
        raise SendError(f"SMTP failed: {exc}") from exc
    return "sent via SMTP"
