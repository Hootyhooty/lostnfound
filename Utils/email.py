import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_reset_email(to_email, reset_url):
    sender = os.getenv("EMAIL_SENDER", "noreply@lostfound.com")
    subject = "Reset your Lost&Found password"
    body = f"""
    Hello,
    You requested to reset your password. Click the link below to reset it:
    {reset_url}

    This link will expire in 15 minutes.
    """

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Use local SMTP debug server
        smtp_host = os.getenv("SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", 1025))

        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.sendmail(sender, to_email, msg.as_string())

        print(f"📤 [DEBUG] Reset email sent to {to_email} via {smtp_host}:{smtp_port}")
    except Exception as e:
        print(f"❌ Error sending reset email: {e}")
