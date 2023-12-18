import datetime
import json
from pathlib import Path
from typing import Callable

from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool

from app.config import settings
from app.integrations.bamboo.employees import add_employee, edit_employee
from app.integrations.bamboo.time_off import (
    add_time_off_balance,
    add_time_off_policy,
    add_time_off_request,
    cancel_time_off_request,
    get_time_off_balance_estimate,
    get_time_off_requests,
)
from app.integrations.faiss import build_index
from app.integrations.gcal import schedule_event
from app.integrations.gmail import send_message
from app.integrations.google_auth import GoogleService, get_google_service

FAISS_INDEX = build_index("./assets/HR_policies.pdf")


class RespondTool(BaseTool):
    name = "respond_tool"
    description = "used to give an answer to the human. The input to this tool is a string with your response"

    def _run(self, query: str) -> str:
        return query


class WelcomeEmailTool(BaseTool):
    name = "welcome_email_tool"
    description = "useful to send a welcome email to a new employee. The input is the email address of the recipient."
    callback: Callable | None = None

    def _run(self, recipient_email: str) -> str:
        service = get_google_service(
            service_name=GoogleService.GMAIL,
            client_config=settings.GOOGLE_CLIENT_CONFIG,
            scopes=settings.GOOGLE_SCOPES,
        )

        send_message(
            service=service,
            recipient=recipient_email,
            subject="Welcome to the company!",
            body="Welcome to the company! We are very happy to have you here.",
        )

        if self.callback:
            self.callback()

        return f"\nA welcome email has been sent to {recipient_email}\n"


class HRPolicyEmailTool(BaseTool):
    name = "HR_policy_email_tool"
    description = "useful to send an email with the HR policies to the new employee. The only input is the email address of the recipient."
    callback: Callable | None = None

    def _run(self, recipient_email: str) -> str:
        service = get_google_service(
            service_name=GoogleService.GMAIL,
            client_config=settings.GOOGLE_CLIENT_CONFIG,
            scopes=settings.GOOGLE_SCOPES,
        )

        send_message(
            service=service,
            recipient=recipient_email,
            subject="HR policies",
            body="Please find attached the HR policies of the company",
            attachments=[Path("./assets/HR_policies.pdf").resolve().as_posix()],
        )

        if self.callback:
            self.callback()

        return f"\nAn email with the HR policies has been sent to {recipient_email}\n"


class SlackInviteTool(BaseTool):
    name = "slack_invite_tool"
    description = "useful to send a slack invite to a new employee via email. The only input is the email address of the recipient."
    callback: Callable | None = None

    def _run(self, recipient_email: str) -> str:
        service = get_google_service(
            service_name=GoogleService.GMAIL,
            client_config=settings.GOOGLE_CLIENT_CONFIG,
            scopes=settings.GOOGLE_SCOPES,
        )

        send_message(
            service=service,
            recipient=recipient_email,
            subject="Slack invite",
            body=f"Welcome to the company! \n\n Here is your Slack invitation: \n{settings.SLACK_INVITE_URL}",
        )

        if self.callback:
            self.callback()

        return f"\nAn email with a Slack invite has been sent to {recipient_email}\n"


class CreateCalendarEventTool(BaseTool):
    name = "calendar_event_tool"
    description = """useful to send a slack invite to a new employee via email. The input to this tool is a JSON with the following format:
    {
        title: str,
        start_iso_datetime: str,
        end_iso_datetime: str,
        attendees: list[str],
        timezone: Optional[str]  # Defaults to UTC
    }
    Make sure to confirm the details of the event with the user.
    """
    callback: Callable | None = None

    def _run(self, event: str) -> str:
        try:
            event_dict = json.loads(event)
        except json.JSONDecodeError:
            return "The event is not a valid JSON"

        service = get_google_service(
            service_name=GoogleService.GCAL,
            client_config=settings.GOOGLE_CLIENT_CONFIG,
            scopes=settings.GOOGLE_SCOPES,
        )

        # Parse datetime strings into datetime objects
        # Add a UTC to BST correction
        event_dict["start_iso_datetime"] = datetime.datetime.fromisoformat(
            event_dict["start_iso_datetime"]
        ) - datetime.timedelta(hours=1)

        event_dict["end_iso_datetime"] = datetime.datetime.fromisoformat(
            event_dict["end_iso_datetime"]
        ) - datetime.timedelta(hours=1)

        event_id = schedule_event(
            service=service,
            summary=event_dict["title"],
            start_time=event_dict["start_iso_datetime"].isoformat(),
            end_time=event_dict["end_iso_datetime"].isoformat(),
            attendees=event_dict["attendees"],
            timezone=event_dict.get("timezone", "UTC"),
        )

        if self.callback:
            self.callback()

        return f"\nA calendar event has been created with id {event_id}\n"


class AddEmployeeToHRTool(BaseTool):
    name = "add_employee_to_hr_tool"
    description = """useful to add a new employee to the HR system. The input to this tool is a JSON with the following format:
    {
        first_name: str,
        last_name: str,
        email_address: str,
    }
    """
    callback: Callable | None = None

    def _run(self, employee_str: str) -> str:
        try:
            employee_dict = json.loads(employee_str)
        except json.JSONDecodeError:
            return "The input is not a valid JSON"

        first_name = employee_dict["first_name"]
        last_name = employee_dict["last_name"]
        email_address = employee_dict["email_address"]
        hire_date = datetime.date.today().strftime("%Y-%m-%d")

        employee_id = add_employee(
            first_name=first_name,
            last_name=last_name,
            email_address=email_address,
            hire_date=hire_date,
        )
        add_time_off_policy(employee_id=employee_id, accrual_start_date=hire_date)
        add_time_off_balance(employee_id=employee_id)

        if self.callback:
            self.callback()

        return f"\nEmployee {first_name} {last_name} has been added to the HR system with employee_id {employee_id} (THIS NUMBER IS IMPORTANT!)\n"


class HRPolicyQATool(BaseTool):
    name = "HR_policy_QA_tool"
    description = "useful to answer questions about the HR policies. The input to this tool is a string with the question."

    def _run(self, query: str) -> str:
        docs = FAISS_INDEX.similarity_search("what is the holiday policy?", k=5)
        clean_docs = [doc.page_content for doc in docs]

        llm = ChatOpenAI(temperature=0.1, model=settings.OPENAI_MODEL)

        result = llm.predict(
            f"""You are a helpful question-answering assistant. You are asked the following question:\n\n
            "{query}"\n

            You have to answer the question. You can use the following information:\n\n
            {clean_docs}\n

            Answer:"
            """
        )

        return f"\n{result}\n"


class ModifyEmployeeTool(BaseTool):
    name = "modify_employee_tool"
    description = """useful to modify an employee in the HR system. The input to this tool is a JSON with the following format:
    {
        employee_id: str,
        first_name: Optional[str],
        last_name: Optional[str],
        email_address: Optional[str],
    }
    """

    def _run(self, employee_str: str) -> str:
        try:
            employee_dict = json.loads(employee_str)
        except json.JSONDecodeError:
            return "The input is not a valid JSON"

        edit_employee(**employee_dict)

        return f"\nEmployee {employee_dict['employee_id']} has been modified successfully\n"


class ViewTimeOffRequestsTool(BaseTool):
    name = "view_time_off_requests_tool"
    description = """useful to view all time off requests for an employee. The input to this tool is the employee_id of the employee to view."""

    def _run(self, employee_id: str) -> str:
        return f"\nTime off requests for employee {employee_id}:\n{get_time_off_requests(employee_id)}\n"


class MakeTimeOffRequestTool(BaseTool):
    name = "make_time_off_request_tool"
    description = """useful to make a time off request. The input to this tool is a JSON with the following format:
    {
        employee_id: str,
        start_date: str,  # Format YYYY-MM-DD
        end_date: str,  # Format YYYY-MM-DD
    }
    """

    def _run(self, time_off_request_str: str) -> str:
        try:
            time_off_request_dict = json.loads(time_off_request_str)
        except json.JSONDecodeError:
            return "The input is not a valid JSON"
        request_id = add_time_off_request(**time_off_request_dict)

        return f"\nTime off request with id {request_id} for employee {time_off_request_dict['employee_id']} has been made successfully\n"


class CancelTimeOffRequestTool(BaseTool):
    name = "cancel_time_off_request_tool"
    description = """useful to cancel a time off request. The input to this tool is the request_id of the request to cancel."""

    def _run(self, request_id: str) -> str:
        cancel_time_off_request(request_id=request_id)
        return (
            f"\nTime off request with id {request_id} has been cancelled successfully\n"
        )


class EstimateTimeOffBalanceTool(BaseTool):
    name = "estimate_time_off_balance_tool"
    description = "useful to estimate the time off balance for an employee. The input to this tool is the employee_id of the employee to view."

    def _run(self, employee_id: str) -> str:
        end_date = (datetime.date.today() + datetime.timedelta(days=365)).strftime(
            "%Y-%m-%d"
        )
        future_balance = get_time_off_balance_estimate(
            employee_id=employee_id, end_date=end_date
        )
        return f"\nTime off balance for employee {employee_id}:\n{future_balance}\n"


def get_all_tools() -> list[BaseTool]:
    return [
        RespondTool(),  # type: ignore
        WelcomeEmailTool(),  # type: ignore
        HRPolicyEmailTool(),  # type: ignore
        SlackInviteTool(),  # type: ignore
        CreateCalendarEventTool(),  # type: ignore
        HRPolicyQATool(),  # type: ignore
        AddEmployeeToHRTool(),  # type: ignore
        ModifyEmployeeTool(),  # type: ignore
        ViewTimeOffRequestsTool(),  # type: ignore
        MakeTimeOffRequestTool(),  # type: ignore
        CancelTimeOffRequestTool(),  # type: ignore
        EstimateTimeOffBalanceTool(),  # type: ignore
    ]


# if __name__ == "__main__":
# Test tools
# AddEmployeeToHRTool()._run(
#     employee_str='{"first_name": "test2", "last_name": "McTest2", "email_address": "test2@test.com"}'
# )
# ModifyEmployeeTool()._run(
#     employee_str='{"employee_id": "215", "first_name": "test3", "last_name": "McTest3"}'
# )
# MakeTimeOffRequestTool()._run(
#     time_off_request_str='{"employee_id": "215", "start_date": "2023-10-26", "end_date": "2023-10-27"}'
# )

# ViewTimeOffRequestsTool()._run(employee_id="215")

# EstimateTimeOffBalanceTool()._run(employee_id="215")

# CancelTimeOffRequestTool()._run(request_id="1650")
