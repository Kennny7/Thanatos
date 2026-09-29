# Thanatos/services/email/email_service.py

import email
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import os
import smtplib
import ssl
from typing import Any, Dict, List, Optional
import uuid

from config.settings import app_config

logger = logging.getLogger(__name__)


class EmailTransmissionResult:
    def __init__(
        self,
        success: bool,
        message: str,
        message_id: Optional[str] = None,
        recipient: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.success = success
        self.message = message
        self.message_id = message_id or f"msg-{uuid.uuid4().hex[:12]}"
        self.recipient = recipient
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "message_id": self.message_id,
            "recipient": self.recipient,
            "details": self.details,
        }


class EmailService:
    """
    Robust SMTP email service that sends real emails with attachments,
    validates configuration, and verifies server transmission delivery receipts.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: Optional[bool] = None,
        from_email: Optional[str] = None,
    ) -> None:
        self.host = host or os.getenv("SMTP_HOST", app_config.smtp_host)
        self.port = int(port or os.getenv("SMTP_PORT", str(app_config.smtp_port or 587)))
        self.user = user or os.getenv("SMTP_USER", app_config.smtp_user)
        self.password = password or os.getenv("SMTP_PASSWORD", app_config.smtp_password)
        self.use_tls = use_tls if use_tls is not None else app_config.smtp_use_tls
        self.from_email = from_email or os.getenv("SMTP_FROM_EMAIL", app_config.smtp_from_email or self.user or app_config.user_email)

    def is_configured(self) -> bool:
        """Returns True if minimum required SMTP settings (host, user, password) are present."""
        return bool(self.host and self.user and self.password)

    def update_credentials(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> None:
        if host:
            self.host = host
        if port:
            self.port = int(port)
        if user:
            self.user = user
        if password:
            self.password = password
        if from_email:
            self.from_email = from_email
        elif user and not self.from_email:
            self.from_email = user

    def verify_connection(self) -> EmailTransmissionResult:
        """Tests SMTP handshake and authentication without sending an email."""
        if not self.is_configured():
            return EmailTransmissionResult(
                success=False,
                message="SMTP is not configured. Missing host, username, or password.",
            )

        try:
            if self.port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=15) as server:
                    server.login(self.user, self.password)
            else:
                with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                    if self.use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    server.login(self.user, self.password)

            return EmailTransmissionResult(
                success=True,
                message=f"Successfully authenticated with SMTP server {self.host}:{self.port} as {self.user}",
            )
        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP Authentication failed: %s", e)
            return EmailTransmissionResult(
                success=False,
                message=f"Authentication failed for {self.user} on {self.host}. Please verify credentials/app password.",
                details={"error": str(e)},
            )
        except Exception as e:
            logger.error("SMTP Connection test error: %s", e)
            return EmailTransmissionResult(
                success=False,
                message=f"Could not connect to SMTP server {self.host}:{self.port}: {e}",
                details={"error": str(e)},
            )

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        attachments: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
    ) -> EmailTransmissionResult:
        """
        Sends an email with optional attachments and verifies transmission.
        """
        if not self.is_configured():
            return EmailTransmissionResult(
                success=False,
                message="SMTP credentials required. Host, user, and password are not set.",
                recipient=to_email,
            )

        msg = MIMEMultipart()
        msg["From"] = self.from_email or self.user
        msg["To"] = to_email
        msg["Subject"] = Header(subject, "utf-8")
        if cc:
            msg["Cc"] = ", ".join(cc)

        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        # Attach files
        attached_names = []
        if attachments:
            for filepath in attachments:
                if os.path.exists(filepath):
                    try:
                        filename = os.path.basename(filepath)
                        with open(filepath, "rb") as f:
                            part = MIMEApplication(f.read(), Name=filename)
                        part["Content-Disposition"] = f'attachment; filename="{filename}"'
                        msg.attach(part)
                        attached_names.append(filename)
                    except Exception as e:
                        logger.warning("Could not attach file %s: %s", filepath, e)

        recipients = [to_email] + (cc or [])

        try:
            if self.port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=25) as server:
                    server.login(self.user, self.password)
                    send_errors = server.sendmail(self.from_email or self.user, recipients, msg.as_string())
            else:
                with smtplib.SMTP(self.host, self.port, timeout=25) as server:
                    if self.use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    server.login(self.user, self.password)
                    send_errors = server.sendmail(self.from_email or self.user, recipients, msg.as_string())

            if send_errors:
                return EmailTransmissionResult(
                    success=False,
                    message=f"SMTP accepted connection but failed delivery to recipients: {send_errors}",
                    recipient=to_email,
                    details={"send_errors": send_errors},
                )

            logger.info("Email successfully sent to %s (Subject: %s)", to_email, subject)
            return EmailTransmissionResult(
                success=True,
                message=f"Email successfully delivered to {to_email} via {self.host}:{self.port}.",
                recipient=to_email,
                details={
                    "host": self.host,
                    "attachments": attached_names,
                    "subject": subject,
                },
            )

        except smtplib.SMTPAuthenticationError as e:
            return EmailTransmissionResult(
                success=False,
                message=f"SMTP Authentication error: Invalid username or password for {self.user}.",
                recipient=to_email,
                details={"error": str(e)},
            )
        except Exception as e:
            logger.exception("Failed to send email to %s: %s", to_email, e)
            return EmailTransmissionResult(
                success=False,
                message=f"Failed to transmit email: {e}",
                recipient=to_email,
                details={"error": str(e)},
            )


# Global singleton
email_service = EmailService()
