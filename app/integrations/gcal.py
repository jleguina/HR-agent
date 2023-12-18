import datetime
from typing import Any

from app.config import settings
from app.integrations.google_auth import GoogleService, get_google_service


def schedule_event(
    service: Any,
    summary: str,
    start_time: str,
    end_time: str,
    attendees: list[str] = [],
    timezone: str = "UTC",
) -> str:
    """
    Schedule and event in Google Calendar.

    Args:
        service (Any): Google Calendar API service object
        summary (str): Title of the event
        start_time (str): Start time of the event in ISO format
        end_time (str): End time of the event in ISO format
        attendees (list[str], optional): list of attendees emails. Defaults to [].
        timezone (str, optional): timezone. Defaults to "UTC".

    Returns:
        str: event ID
    """
    event = {
        "summary": summary,
        "start": {
            "dateTime": start_time,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_time,
            "timeZone": timezone,
        },
        "attendees": [{"email": attendee} for attendee in attendees],
    }

    if attendees:
        event["conferenceData"] = {
            "createRequest": {
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
                "requestId": "randomString",
            }
        }

    event = (
        service.events()
        .insert(calendarId="primary", body=event, conferenceDataVersion=1)
        .execute()
    )

    return event["id"]  # type: ignore


def delete_event(service: Any, event_id: str) -> None:
    """Deletes a calendar event by ID. Requires to be logged in.

    Args:
        service (Any): Google Calendar API service object
        event_id (str): event ID
    """
    service.events().delete(calendarId="primary", eventId=event_id).execute()


if __name__ == "__main__":
    # Authenticate with Google Calendar API
    service = get_google_service(
        service_name=GoogleService.GCAL,
        client_config=settings.GOOGLE_CLIENT_CONFIG,
        scopes=settings.GOOGLE_SCOPES,
    )
    # Schedule an event for tomorrow at 2:30 PM
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=30, second=0, microsecond=0)
    end_time = start_time + datetime.timedelta(hours=1)
    summary = "Dummy meeting"

    event_id = schedule_event(
        service,
        summary,
        start_time.isoformat(),
        end_time.isoformat(),
        attendees=["javierleguina98@gmail.com", "aalixmeunier@gmail.com"],
    )

    delete_event(service, event_id)
