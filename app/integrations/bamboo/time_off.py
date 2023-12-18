import datetime
from typing import Any
from urllib.parse import urlencode

from app.integrations.bamboo.utils import RequestMethods, send_bamboo_request

##################### TO SET UP USER TIME OFF POLICIES #####################


def add_time_off_policy(employee_id: str, accrual_start_date: str) -> None:
    """
    Adds a time off policy to an employee

    Args:
        employee_id (str)
        accrual_start_date (str): Date in format YYYY-MM-DD

    Raises:
        Exception: Error adding time off policy
    """
    data = [
        {
            "timeOffPolicyId": 3,  # Manual Vacation Policy See https://documentation.bamboohr.com/reference/get-time-off-policies
            "accrualStartDate": accrual_start_date,
        }
    ]

    res = send_bamboo_request(
        url_path=f"/employees/{employee_id}/time_off/policies",
        method=RequestMethods.PUT,
        data=data,
    )

    if res.status_code != 200:
        raise Exception("Error adding time off policy")


def add_time_off_balance(employee_id: str) -> None:
    """
    Adds the initial time off balance of an employee according to the HR policy

    Args:
        employee_id (str)

    Raises:
        Exception: Error modifying time off balance
    """
    res = send_bamboo_request(
        url_path=f"/employees/{employee_id}/time_off/balance_adjustment",
        method=RequestMethods.PUT,
        data={
            "timeOffTypeId": 78,  # Manual Vacation Policy See https://documentation.bamboohr.com/reference/get-time-off-policies
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "amount": 25
            * 8,  # 25 days of vacation per year from HR policy PDF, units in hours
        },
    )

    if res.status_code != 201:
        raise Exception("Error modifying time off balance")


##################### TO INTERACT WITH TIME OFF REQUESTS #####################


def get_time_off_requests(employee_id: str) -> dict[str, Any]:
    """
    Gets all time off requests for an employee

    Args:
        employee_id (str)

    Returns:
        dict[str, Any]: JSON response from BambooHR API
    """
    start_date = datetime.date.today().strftime("%Y-%m-%d")
    end_date = (datetime.date.today() + datetime.timedelta(days=365)).strftime(
        "%Y-%m-%d"
    )
    params = {"start": start_date, "end": end_date, "employeeId": employee_id}
    encoded_params = urlencode(params)
    res = send_bamboo_request(
        url_path=f"/time_off/requests/?{encoded_params}",
        method=RequestMethods.GET,
    )

    return res.json()


def add_time_off_request(employee_id: str, start_date: str, end_date: str) -> str:
    """
    Adds a time off request for an employee

    Args:
        employee_id (str):
        start_date (str): Start date in format YYYY-MM-DD
        end_date (str): End date in format YYYY-MM-DD

    Returns:
        str: Request ID
    """
    time_diff = datetime.datetime.strptime(
        end_date, "%Y-%m-%d"
    ) - datetime.datetime.strptime(start_date, "%Y-%m-%d")
    data = {
        "status": "requested",  # Options: "approved", "denied" (or "declined"), "requested"
        "start": start_date,
        "end": end_date,
        "amount": 8 * time_diff.days,  # 8h per working day (units are given in hours)
        "timeOffTypeId": 78,  # Indicates vacation, see: https://documentation.bamboohr.com/reference/get-time-off-types
    }

    res = send_bamboo_request(
        url_path=f"/employees/{employee_id}/time_off/request",
        method=RequestMethods.PUT,
        data=data,
    )

    if res.status_code != 201:
        raise Exception("Error creating time off request")

    request_id = res.headers["Location"].split("/")[-1]
    return request_id


def cancel_time_off_request(request_id: str) -> None:
    """
    Cancels a time off request

    Args:
        request_id (str)

    Raises:
        Exception: Error cancelling time off request
    """
    url_path = f"/time_off/requests/{request_id}/status"
    res = send_bamboo_request(
        url_path=url_path,
        method=RequestMethods.PUT,
        data={"status": "canceled"},
    )

    if res.status_code != 200:
        raise Exception("Error cancelling time off request")


def get_time_off_balance_estimate(employee_id: str, end_date: str) -> dict[str, Any]:
    """
    Estimates the time off balance for an employee

    Args:
        employee_id (str)
        end_date (str): Date in format YYYY-MM-DD

    Raises:
        Exception: Error getting time off balance

    Returns:
        dict[str, Any]: JSON response from BambooHR API
    """
    params_encoded = urlencode({"end": end_date})
    res = send_bamboo_request(
        url_path=f"/employees/{employee_id}/time_off/calculator/?{params_encoded}",
        method=RequestMethods.GET,
    )

    if res.status_code != 200:
        raise Exception("Error getting time off balance")

    return res.json()
