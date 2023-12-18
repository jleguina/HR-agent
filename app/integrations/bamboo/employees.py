from typing import Any
from urllib.parse import urlencode

from app.integrations.bamboo.utils import RequestMethods, send_bamboo_request


def get_employee(
    employee_id: str,
    fields: list[str] = [
        "firstName",
        "lastName",
        "homeEmail",
        "location",
        "hireDate",
    ],
) -> dict[str, Any]:
    """
    Gets an employee from Bamboo HR

    Args:
        employee_id (str)
        fields (list[str], optional): Fields to be retrieved from the employee profile. Defaults to [ "firstName", "lastName", "homeEmail", "location", "hireDate", ].

    Raises:
        Exception: Error getting employee

    Returns:
        dict[str, Any]: Employee profile JSON object with requested fields
    """
    fields_str = ",".join(fields)
    encoded_fields = urlencode({"fields": fields_str})

    res = send_bamboo_request(
        url_path=f"/employees/{employee_id}/?{encoded_fields}",
        method=RequestMethods.GET,
    )

    if res.status_code != 200:
        raise Exception("Error getting employee")

    return res.json()


def add_employee(
    first_name: str, last_name: str, email_address: str, hire_date: str
) -> str:
    """
    Adds an employee to Bamboo HR

    Args:
        first_name (str)
        last_name (str)
        email_address (str)
        hire_date (str): Format YYYY-MM-DD

    Raises:
        Exception: Error creating employee

    Returns:
        str: Employee ID
    """
    res = send_bamboo_request(
        url_path="/employees",
        method=RequestMethods.POST,
        data={
            "firstName": first_name,
            "lastName": last_name,
            "homeEmail": email_address,
            "location": "London, UK",
            "hireDate": hire_date,
        },
    )
    if res.status_code != 201:
        raise Exception("Error creating employee")

    employee_id = res.headers["Location"].split("/")[-1]
    return employee_id


def edit_employee(
    employee_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    email_address: str | None = None,
) -> None:
    """
    Edits an employee in Bamboo HR

    Args:
        employee_id (str):
        first_name (str | None, optional): Defaults to None.
        last_name (str | None, optional): Defaults to None.
        email_address (str | None, optional): Defaults to None.

    Raises:
        Exception: At least one field must be provide
        Exception: Error editing employee
    """
    if not any([first_name, last_name, email_address]):
        raise Exception("At least one field must be provided")

    data = {}
    if first_name:
        data["firstName"] = first_name
    if last_name:
        data["lastName"] = last_name
    if email_address:
        data["homeEmail"] = email_address

    res = send_bamboo_request(
        url_path=f"/employees/{employee_id}/",
        method=RequestMethods.POST,
        data=data,
    )

    if res.status_code != 200:
        raise Exception("Error editing employee")


# Employee useful fields
# useful_fields = [
#     {"id": 3991, "name": "Country", "type": "country", "alias": "country"},
#     {"id": 1, "name": "First Name", "type": "text", "alias": "firstName"},
#     {"id": 3, "name": "Hire Date", "type": "date", "alias": "hireDate"},
#     {"id": 1357, "name": "Home Email", "type": "email", "alias": "homeEmail"},
#     {"id": 14, "name": "Home Phone", "type": "phone", "alias": "homePhone"},
#     {"id": 17, "name": "Job Title", "type": "list", "alias": "jobTitle"},
#     {"id": 2, "name": "Last Name", "type": "text", "alias": "lastName"},
#     {"id": 5, "name": "Middle Name", "type": "text", "alias": "middleName"},
#     {"id": 13, "name": "Mobile Phone", "type": "phone", "alias": "mobilePhone"},
#     {"id": 19, "name": "Pay rate", "type": "currency", "alias": "payRate"},
#     {"id": 91, "name": "Reporting to", "type": "employee"},
#     {
#         "id": 4357,
#         "name": "Vacation - Policy Assigned",
#         "type": "time_off_type_exists",
#     },
#     {"id": "4357.3", "name": "Vacation - Available Balance", "type": "int"},
#     {"id": "4357.7", "name": "Vacation - Current balance", "type": "time_off_type"},
#     {"id": "4357.5", "name": "Vacation - Hours scheduled", "type": "int"},
#     {"id": "4357.4", "name": "Vacation - Hours taken (YTD)", "type": "int"},
#     {"id": "4357.2", "name": "Vacation - Policy", "type": "text"},
# ]
