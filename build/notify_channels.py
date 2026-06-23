#!/usr/bin/env python3
"""Deliver alerts via email, SMS, ntfy, and optional webhook.

Defaults (override with env):
  MUSK_ALERT_EMAIL=kiran@wattsadvisor.com
  MUSK_ALERT_SMS=+12792692780

Email (SMTP):
  MUSK_SMTP_HOST, MUSK_SMTP_PORT (587), MUSK_SMTP_USER, MUSK_SMTP_PASS
  MUSK_SMTP_FROM (defaults to MUSK_SMTP_USER)

SMS (Twilio):
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM (+1...)

Optional:
  MUSK_WATCH_NTFY, MUSK_WATCH_WEBHOOK, MUSK_NOTIFY_DISABLED=1
"""
import json
import os
import smtplib
import ssl
import urllib.parse
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

UA = "Watts Advisor research kiran@wattsadvisor.com"
DEFAULT_EMAIL = "kiran@wattsadvisor.com"
DEFAULT_SMS = "+12792692780"


def _disabled():
    return os.environ.get("MUSK_NOTIFY_DISABLED", "0") == "1"


def send_email(subject, body, to=None):
    if _disabled():
        return False
    to = to or os.environ.get("MUSK_ALERT_EMAIL", DEFAULT_EMAIL)
    host = os.environ.get("MUSK_SMTP_HOST")
    user = os.environ.get("MUSK_SMTP_USER")
    password = os.environ.get("MUSK_SMTP_PASS")
    if not all([host, user, password]):
        print("email skipped: set MUSK_SMTP_HOST, MUSK_SMTP_USER, MUSK_SMTP_PASS")
        return False
    port = int(os.environ.get("MUSK_SMTP_PORT", "587"))
    from_addr = os.environ.get("MUSK_SMTP_FROM", user)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject[:250]
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls(context=ctx)
            smtp.login(user, password)
            smtp.sendmail(from_addr, [to], msg.as_string())
        print(f"email sent to {to}")
        return True
    except Exception as e:
        print(f"email failed: {e}")
        return False


def send_sms(body, to=None):
    if _disabled():
        return False
    to = to or os.environ.get("MUSK_ALERT_SMS", DEFAULT_SMS)
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_num = os.environ.get("TWILIO_FROM")
    if not all([sid, token, from_num]):
        print("sms skipped: set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM")
        return False
    text = body[:1500]
    data = urllib.parse.urlencode({"To": to, "From": from_num, "Body": text}).encode()
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    req = urllib.request.Request(url, data=data, method="POST")
    creds = f"{sid}:{token}".encode()
    import base64
    req.add_header("Authorization", "Basic " + base64.b64encode(creds).decode())
    req.add_header("User-Agent", UA)
    try:
        urllib.request.urlopen(req, timeout=30)
        print(f"sms sent to {to}")
        return True
    except Exception as e:
        print(f"sms failed: {e}")
        return False


def send_ntfy(title, body, priority="default", tags=""):
    if _disabled():
        return False
    ntfy = os.environ.get("MUSK_WATCH_NTFY")
    if not ntfy:
        return False
    headers = {"User-Agent": UA, "Title": title[:250], "Priority": priority}
    if tags:
        headers["Tags"] = tags
    try:
        req = urllib.request.Request(ntfy, data=body.encode("utf-8"), headers=headers)
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:
        print(f"ntfy failed: {e}")
        return False


def send_webhook(text):
    if _disabled():
        return False
    hook = os.environ.get("MUSK_WATCH_WEBHOOK")
    if not hook:
        return False
    try:
        req = urllib.request.Request(
            hook, data=json.dumps({"text": text}).encode(),
            headers={"Content-Type": "application/json", "User-Agent": UA})
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:
        print(f"webhook failed: {e}")
        return False


def alert_all(title, body, *, priority="high", tags="sec", email=True, sms=True, ntfy=True):
    """Fan out to every configured channel."""
    if ntfy:
        send_ntfy(title, body, priority=priority, tags=tags)
    if email:
        send_email(title, body)
    if sms:
        short = f"{title}\n{body[:320]}"
        send_sms(short)
    send_webhook(f"*{title}*\n{body}")
    return True


if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "Musk dossier alert test"
    ok_email = send_email("Dossier alert test", msg)
    ok_sms = send_sms(f"Dossier alert test\n{msg[:320]}")
    ok_ntfy = send_ntfy("Dossier alert test", msg, priority="high", tags="test")
    print(f"results: email={ok_email} sms={ok_sms} ntfy={ok_ntfy}")
    if not (ok_email and ok_sms):
        sys.exit(1)
