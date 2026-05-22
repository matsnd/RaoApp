import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import settings


class EmailService:
    async def send_password_reset(self, to_email: str, reset_link: str, user_name: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "RAO — Resetowanie hasła"
        msg["From"] = settings.RAO_SMTP_FROM
        msg["To"] = to_email

        html = f"""
        <html><body style="font-family: Montserrat, sans-serif; color: #1D2B53;">
        <h2>Resetowanie hasła</h2>
        <p>Cześć {user_name},</p>
        <p>Otrzymaliśmy prośbę o resetowanie hasła do Twojego konta w systemie RAO.</p>
        <p><a href="{reset_link}"
           style="background:#1D2B53;color:white;padding:12px 32px;
                  border-radius:24px;text-decoration:none;display:inline-block;">
           Ustaw nowe hasło
        </a></p>
        <p style="color:#718096;font-size:13px;">Link jest ważny przez 1 godzinę.</p>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(settings.RAO_SMTP_HOST, settings.RAO_SMTP_PORT) as server:
                if settings.RAO_SMTP_TLS:
                    server.starttls()
                if settings.RAO_SMTP_USER:
                    server.login(settings.RAO_SMTP_USER, settings.RAO_SMTP_PASSWORD)
                server.send_message(msg)
        except Exception:
            pass


email_service = EmailService()
