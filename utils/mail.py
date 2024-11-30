from __future__ import annotations

from email.message import EmailMessage

import aiosmtplib

from config import (
    MAIL_HOST,
    MAIL_PORT,
    MAIL_USE_SSL,
    MAIL_USE_TLS,
    MAIL_PASSWORD,
    MAIL_USERNAME,
    MAIL_DEFAULT_SENDER,
)


async def send_email(to: str, subject: str, template: str) -> None:
    """
    Sends an email using the configured SMTP server.

    Args:
        to (str): The recipient's email address.
        subject (str): The subject of the email.
        template (str): The HTML content of the email.

    Raises:
        SMTPException: If there is an error while sending the email.
    """
    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = MAIL_DEFAULT_SENDER
    msg["To"] = to

    msg.add_alternative(template, subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=MAIL_HOST,
            port=MAIL_PORT,
            username=MAIL_USERNAME,
            password=MAIL_PASSWORD,
            use_tls=MAIL_USE_SSL,
            start_tls=MAIL_USE_TLS,
        )

    except aiosmtplib.SMTPException:
        return
