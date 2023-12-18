import enum
import os
import pickle
from typing import Any

# Missing typed stubs
from google.auth.transport.requests import Request  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore


class GoogleService(enum.Enum):
    GCAL = "calendar"
    GMAIL = "gmail"


SERVICE_TO_VERSION: dict[GoogleService, str] = {
    GoogleService.GCAL: "v3",
    GoogleService.GMAIL: "v1",
}


def get_google_service(
    service_name: GoogleService,
    client_config: dict[str, dict[str, str | list[str]]],
    scopes: list[str],
    use_cache: bool = True,
) -> Any:
    """Get a Google API service.

    Args:
        client_config (dict[str, dict[str, str  |  list[str]]]): Dictionary with the client configuration credentials.
        scopes (list[str]): List of scopes to request during the authorization flow.
        service (GoogleService): The Google service to get.

    Returns:
        The Google API service.
    """
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle") and use_cache:
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(client_config, scopes)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build(
        service_name.value, SERVICE_TO_VERSION[service_name], credentials=creds
    )
