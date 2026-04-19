from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import os
import smtplib

import httpx


@dataclass(frozen=True)
class DeliveryPayload:
    utilisateur: str
    destination: str
    subject: str
    body: str


class EmailSender:
    def send(self, payload: DeliveryPayload) -> None:
        raise NotImplementedError


class SmsSender:
    def send(self, payload: DeliveryPayload) -> None:
        raise NotImplementedError


class ConsoleEmailSender(EmailSender):
    def send(self, payload: DeliveryPayload) -> None:
        # Placeholder transport for local/dev environments.
        print(
            "[EMAIL] to={dest} user={user} subject={subject} body={body}".format(
                dest=payload.destination,
                user=payload.utilisateur,
                subject=payload.subject,
                body=payload.body,
            )
        )


class ConsoleSmsSender(SmsSender):
    def send(self, payload: DeliveryPayload) -> None:
        # Placeholder transport for local/dev environments.
        print(
            "[SMS] to={dest} user={user} body={body}".format(
                dest=payload.destination,
                user=payload.utilisateur,
                body=payload.body,
            )
        )


class SmtpEmailSender(EmailSender):
    def __init__(
        self,
        host: str,
        port: int,
        from_email: str,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.from_email = from_email
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def send(self, payload: DeliveryPayload) -> None:
        msg = EmailMessage()
        msg["From"] = self.from_email
        msg["To"] = payload.destination
        msg["Subject"] = payload.subject
        msg.set_content(payload.body)

        with smtplib.SMTP(self.host, self.port, timeout=15) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.username and self.password:
                smtp.login(self.username, self.password)
            smtp.send_message(msg)


class TwilioSmsSender(SmsSender):
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send(self, payload: DeliveryPayload) -> None:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        response = httpx.post(
            url,
            data={
                "To": payload.destination,
                "From": self.from_number,
                "Body": payload.body,
            },
            auth=(self.account_sid, self.auth_token),
            timeout=20.0,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Twilio error {response.status_code}: {response.text}")


def build_email_sender_from_env() -> EmailSender:
    provider = os.getenv("EMAIL_PROVIDER", "console").strip().lower()
    if provider != "smtp":
        return ConsoleEmailSender()

    host = os.getenv("SMTP_HOST", "").strip()
    port_raw = os.getenv("SMTP_PORT", "587").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
    username = os.getenv("SMTP_USERNAME", "").strip() or None
    password = os.getenv("SMTP_PASSWORD", "").strip() or None
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes"}

    if not host or not from_email:
        return ConsoleEmailSender()

    try:
        port = int(port_raw)
    except ValueError:
        return ConsoleEmailSender()

    return SmtpEmailSender(
        host=host,
        port=port,
        from_email=from_email,
        username=username,
        password=password,
        use_tls=use_tls,
    )


def build_sms_sender_from_env() -> SmsSender:
    provider = os.getenv("SMS_PROVIDER", "console").strip().lower()
    if provider != "twilio":
        return ConsoleSmsSender()

    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv("TWILIO_FROM_NUMBER", "").strip()
    if not account_sid or not auth_token or not from_number:
        return ConsoleSmsSender()

    return TwilioSmsSender(
        account_sid=account_sid,
        auth_token=auth_token,
        from_number=from_number,
    )
