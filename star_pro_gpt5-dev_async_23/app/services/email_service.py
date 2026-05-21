import smtplib
import logging
from email.message import EmailMessage
from typing import Optional
from app.core.config import settings


class EmailService:
    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.use_tls = settings.smtp_use_tls
        self.from_email = settings.smtp_from_email or (self.username or "no-reply@localhost")
        self.logger = logging.getLogger(__name__)

    def is_configured(self) -> bool:
        return bool(self.host and self.port and self.from_email)

    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None):
        if not self.is_configured():
            raise RuntimeError("SMTP is not configured")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = to_email
        if text_body:
            msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        # Log attempt without exposing credentials
        self.logger.info(
            f"Sending email via SMTP host={self.host} port={self.port} tls={self.use_tls} to={to_email} subject='{subject}'"
        )

        try:
            if self.use_tls:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls()
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.host, self.port) as server:
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.send_message(msg)
            self.logger.info(
                f"Email sent successfully to={to_email} subject='{subject}'"
            )
        except Exception as e:
            # Log error without leaking sensitive data
            self.logger.error(
                f"Failed to send email to={to_email} subject='{subject}': {e}"
            )
            raise


email_service = EmailService()

