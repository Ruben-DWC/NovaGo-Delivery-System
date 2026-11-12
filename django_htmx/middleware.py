from __future__ import annotations

from typing import Callable
from django.http import HttpRequest, HttpResponse
from django_htmx.http import HtmxDetails


class HtmxMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.htmx = HtmxDetails(request)
        return self.get_response(request)

