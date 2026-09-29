"""DeepSeek account operations that never expose credentials in the report."""

from __future__ import annotations

import json
from typing import Any, Callable
from urllib import request


class DeepSeekBalanceClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        request_json: Callable[[str, str, dict[str, str]], dict[str, Any]]
        | None = None,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.request_json = request_json or self._request_json

    def query(self) -> dict[str, Any]:
        return self.request_json(
            "GET",
            f"{self.base_url}/user/balance",
            {"Authorization": f"Bearer {self.api_key}"},
        )

    def safe_summary(self) -> dict[str, Any]:
        data = self.query()
        infos = data.get("balance_infos")
        currencies = []
        if isinstance(infos, list):
            currencies = [
                str(item.get("currency"))
                for item in infos
                if isinstance(item, dict) and item.get("currency")
            ]
        return {
            "is_available": bool(data.get("is_available")),
            "currencies": currencies,
        }

    @staticmethod
    def _request_json(
        method: str,
        url: str,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        req = request.Request(url, method=method, headers=headers)
        with request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
