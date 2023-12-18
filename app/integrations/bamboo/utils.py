import base64
from dataclasses import dataclass
from typing import Any

import numpy as np
import requests

from app.config import settings


@dataclass
class RequestMethods:
    GET: str = "GET"
    POST: str = "POST"
    PUT: str = "PUT"


def send_bamboo_request(url_path: str, method: str, data: Any = None) -> Any:
    headers = {
        "Authorization": "Basic "
        + base64.b64encode(f"{settings.BAMBOO_HR_API_KEY}:x".encode()).decode(),
        "accept": "application/json",
    }

    url = settings.BAMBOO_HR_BASE_URL + url_path

    response = requests.request(method, url, headers=headers, json=data)
    return response


def count_working_days(start_date: str, end_date: str) -> int:
    # Convert the dates to numpy datetime64
    start_date = np.datetime64(start_date)  # type: ignore
    end_date = np.datetime64(end_date)  # type: ignore

    # Get the total days array between start_date and end_date
    total_days: np.ndarray = np.arange(start_date, end_date)

    # Count the weekdays (monday to friday) only
    weekdays = np.isin(
        total_days.astype("datetime64[D]").view("int64") % 7, [0, 1, 2, 3, 4]
    )

    return np.count_nonzero(weekdays)
