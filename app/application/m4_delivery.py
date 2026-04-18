from __future__ import annotations

from dataclasses import dataclass


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
