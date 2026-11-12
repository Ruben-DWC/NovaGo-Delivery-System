from __future__ import annotations

import json
from typing import Any
from django.http import HttpRequest


class HtmxDetails:
    def __init__(self, request: HttpRequest) -> None:
        self.request = request

    def __bool__(self) -> bool:
        return self.request.headers.get("HX-Request", "").lower() == "true"

    @property
    def boosted(self) -> bool:
        return self.request.headers.get("HX-Boosted", "").lower() == "true"

    @property
    def current_url(self) -> str | None:
        return self.request.headers.get("HX-Current-URL")

    @property
    def history_restore_request(self) -> bool:
        return self.request.headers.get("HX-History-Restore-Request", "").lower() == "true"

    @property
    def prompt(self) -> str | None:
        return self.request.headers.get("HX-Prompt")

    @property
    def target(self) -> str | None:
        return self.request.headers.get("HX-Target")

    @property
    def trigger(self) -> str | None:
        return self.request.headers.get("HX-Trigger")

    @property
    def trigger_name(self) -> str | None:
        return self.request.headers.get("HX-Trigger-Name")

    @property
    def triggering_event(self) -> Any | None:
        raw = self.request.headers.get("HX-Triggering-Event")
        if raw:
            try:
                return json.loads(raw)
            except Exception:
                return None
        return None

