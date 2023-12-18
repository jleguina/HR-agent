import copy
import os
import os.path
import warnings
from base64 import urlsafe_b64encode
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mimetypes import guess_type as guess_mime_type
from pathlib import Path
from typing import Any

from app.config import settings
from app.integrations.google_auth import GoogleService, get_google_service


# Adds the attachment with the given filename to the given message
def add_attachment(
    message: MIMEText | MIMEMultipart, filepath: str
) -> MIMEText | MIMEMultipart:
    """Add an attachment to an email message.

    Args:
        message (MIMEText | MIMEMultipart): MIME message to attach to
        filepath (str): path to the file to attach

    Returns:
        MIMEText | MIMEMultipart: MIME message with the attachment
    """
    content_type, encoding = guess_mime_type(filepath)
    if content_type is None or encoding is not None:
        content_type = "application/octet-stream"
    main_type, sub_type = content_type.split("/", 1)

    msg: MIMEText | MIMEImage | MIMEAudio | MIMEApplication | MIMEBase
    with open(filepath, "rb") as fp:
        if main_type == "text":
            msg = MIMEText(fp.read().decode(), _subtype=sub_type)
        elif main_type == "image":
            msg = MIMEImage(fp.read(), _subtype=sub_type)
        elif main_type == "audio":
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
        elif main_type == "application":
            msg = MIMEApplication(fp.read(), _subtype=sub_type)
        else:
            warnings.warn(f"Unknown attachment type {main_type}/{sub_type}")
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())

    filename = os.path.basename(filepath)
    msg.add_header("Content-Disposition", "attachment", filename=filename)

    # Avoid side effects
    message_copy = copy.deepcopy(message)
    message_copy.attach(msg)
    return message_copy


def build_message(
    recipient: str,
    subject: str,
    body: str,
    attachments: list[str] = [],
) -> dict[str, str]:
    """Build a message to send via Gmail API.

    Args:
        recipient (str): email address of the recipient
        subject (str): subject of the email
        body (str): body of the email
        attachments (list[str], optional): list of paths to attachment files. Defaults to [].

    Raises:
        FileNotFoundError: if any of the attachment files does not exist

    Returns:
        dict[str, str]: message payload to send via Gmail API
    """
    message: MIMEText | MIMEMultipart
    if not attachments:
        message = MIMEText(body)
    else:
        message = MIMEMultipart()
        message.attach(MIMEText(body))
        for filepath in attachments:
            # Verify that the file exists
            if not os.path.isfile(filepath):
                raise FileNotFoundError(f"File {filepath} not found")
            message = add_attachment(message, filepath)

    message["to"] = recipient
    message["from"] = settings.SYSTEM_EMAIL
    message["subject"] = subject

    return {"raw": urlsafe_b64encode(message.as_bytes()).decode()}


def send_message(
    service: Any,
    recipient: str,
    subject: str,
    body: str,
    attachments: list[str] = [],
) -> dict[str, str]:
    """Send an email message via Gmail API.

    Args:
        service (Any): Gmail API service object
        recipient (str): email address of the recipient
        subject (str): subject of the email
        body (str): body of the email
        attachments (list[str], optional): list of paths to attachment files. Defaults to [].

    Returns:
        dict[str, str]: Gmail API response
    """
    return (
        service.users()
        .messages()
        .send(
            userId="me",
            body=build_message(recipient, subject, body, attachments),
        )
        .execute()
    )


if __name__ == "__main__":
    service = get_google_service(
        service_name=GoogleService.GMAIL,
        client_config=settings.GOOGLE_CLIENT_CONFIG,
        scopes=settings.GOOGLE_SCOPES,
    )
    attachment_path = Path("./assets/HR_policies.pdf").resolve().as_posix()
    send_message(
        service=service,
        recipient="javierleguina98@gmail.com",
        subject="This is a subject",
        body="This is the body of the email",
        attachments=["./assets/HR_policies.pdf"],
    )
