import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_password_reset_code(self, email: str, code: str, ttl_minutes: int) -> None:
        if not self.settings.smtp_host or not self.settings.smtp_from_email:
            logger.info("SMTP is not configured; password reset email was not sent")
            return

        message = EmailMessage()
        message["Subject"] = "TicketRush password reset code"
        message["From"] = self.settings.smtp_from_email
        message["To"] = email
        message.set_content(
            "\n".join(
                [
                    "Use this verification code to reset your TicketRush password:",
                    "",
                    code,
                    "",
                    f"This code expires in {ttl_minutes} minutes.",
                ]
            )
        )

        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=10) as smtp:
                if self.settings.smtp_use_tls:
                    smtp.starttls()
                if self.settings.smtp_username:
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise ConnectionError("unable to send password reset email") from exc
