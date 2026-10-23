"""Centralized FastAPI HTTP client for LedgerBud."""

import os
from typing import Any
import httpx
import streamlit as st


def resolve_backend_url(custom_url: str | None = None) -> str:
    """Resolve and validate the FastAPI backend base URL from secrets or environment.

    Priority:
    1. Explicit custom_url argument.
    2. Streamlit secrets (for Streamlit Community Cloud deployments).
    3. FASTAPI_BASE_URL environment variable.
    4. Default to http://localhost:8000 only in local development.
    """
    url = custom_url

    if not url:
        # 1. Check Streamlit secrets (supported in Streamlit Cloud and local .streamlit/secrets.toml)
        try:
            if hasattr(st, "secrets") and "FASTAPI_BASE_URL" in st.secrets:
                url = str(st.secrets["FASTAPI_BASE_URL"]).strip()
        except Exception:
            pass

    if not url:
        # 2. Check environment variable
        raw_env = os.environ.get("FASTAPI_BASE_URL")
        if raw_env:
            url = raw_env.strip()

    env = os.environ.get("ENVIRONMENT", "")
    try:
        if hasattr(st, "secrets") and not env and "ENVIRONMENT" in st.secrets:
            env = str(st.secrets["ENVIRONMENT"]).strip()
    except Exception:
        pass
    env = env.lower() or "development"
    is_prod = env in ("production", "prod", "staging")

    if not url:
        if is_prod:
            raise ValueError(
                "FASTAPI_BASE_URL is not configured. In production/Streamlit Community Cloud, "
                "you must configure FASTAPI_BASE_URL in Streamlit Secrets or environment variables "
                "(e.g., FASTAPI_BASE_URL = 'https://api.yourdomain.com')."
            )
        url = "http://localhost:8000"

    url = url.rstrip("/")

    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError(
            f"Invalid FASTAPI_BASE_URL: '{url}'. The URL must start with http:// or https://."
        )

    if is_prod and any(h in url for h in ("localhost", "127.0.0.1", "0.0.0.0")):
        raise ValueError(
            f"FASTAPI_BASE_URL is configured as a local loopback address ('{url}') in a {env} environment. "
            "Please configure the public HTTPS URL of your deployed FastAPI backend."
        )

    return url


class APIClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = resolve_backend_url(base_url)
        self.api_prefix = "/api/v1"

    @property
    def headers(self) -> dict[str, str]:
        """Build headers with JWT bearer token if user is authenticated."""
        headers: dict[str, str] = {}
        token = st.session_state.get("token")
        if token and isinstance(token, str):
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        """Parse response and handle common HTTP error codes."""
        if response.status_code == 401:
            # Session expired / unauthorized — trigger logout and navigate cleanly to sign in
            from ui.state import logout_user
            logout_user()
            st.query_params["auth"] = "true"
            try:
                st.switch_page("ui/pages/auth_page.py")
            except Exception:
                st.rerun()

        if response.is_error:
            try:
                err_data = response.json()
                detail = err_data.get("detail", "API Request Failed") if isinstance(err_data, dict) else str(err_data)
            except Exception:
                detail = f"Error {response.status_code}: {response.text}"
            raise httpx.HTTPStatusError(detail, request=response.request, response=response)

        if response.status_code == 204:
            return None

        try:
            return response.json()
        except Exception as exc:
            raise ValueError(
                f"Failed to decode API JSON response from {response.request.url} (status {response.status_code}): {exc}"
            ) from exc

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Perform raw HTTP request with auth header attached."""
        clean_path = "/" + path.lstrip("/")
        url = f"{self.base_url}{self.api_prefix}{clean_path}"
        try:
            with httpx.Client(timeout=30.0) as client:
                req_headers: dict[str, str] = {**self.headers}
                extra_headers = kwargs.pop("headers", None)
                if isinstance(extra_headers, dict):
                    req_headers.update(extra_headers)
                response = client.request(method, url, headers=req_headers, **kwargs)
                return self._handle_response(response)
        except httpx.RequestError as exc:
            raise httpx.RequestError(f"API Server unavailable: {exc}") from exc

    def _request_dict(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Perform HTTP request and validate that the response is a JSON dictionary."""
        data = self._request(method, path, **kwargs)
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict response from {path}, got {type(data).__name__}")
        return data

    def _request_list(self, method: str, path: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Perform HTTP request and validate that the response is a JSON list of dictionaries."""
        data = self._request(method, path, **kwargs)
        if not isinstance(data, list):
            raise TypeError(f"Expected list response from {path}, got {type(data).__name__}")
        return data

    def _request_int(self, method: str, path: str, **kwargs: Any) -> int:
        """Perform HTTP request and validate that the response is an integer."""
        data = self._request(method, path, **kwargs)
        if not isinstance(data, int) or isinstance(data, bool):
            raise TypeError(f"Expected int response from {path}, got {type(data).__name__}")
        return data

    def _request_empty(self, method: str, path: str, **kwargs: Any) -> None:
        """Perform HTTP request expecting an empty/204 response."""
        self._request(method, path, **kwargs)

    # --- AUTH ENDPOINTS ---

    def get_me(self) -> dict[str, Any]:
        return self._request_dict("GET", "/auth/me")

    def update_name(self, full_name: str) -> dict[str, Any]:
        return self._request_dict("PUT", "/auth/me/name", json={"full_name": full_name})

    def delete_profile(self) -> None:
        self._request_empty("DELETE", "/auth/me")

    # --- WALLET ENDPOINTS ---

    def list_wallets(self, include_archived: bool = False) -> list[dict[str, Any]]:
        return self._request_list("GET", "/wallets", params={"include_archived": str(include_archived).lower()})

    def wallet_summary(self) -> dict[str, Any]:
        return self._request_dict("GET", "/wallets/summary")

    def create_wallet(self, name: str, type: str, balance: float) -> dict[str, Any]:
        return self._request_dict(
            "POST",
            "/wallets",
            json={"wallet_name": name, "wallet_type": type, "balance": balance},
        )

    def update_wallet(self, wallet_id: int, name: str, type: str, balance: float) -> dict[str, Any]:
        return self._request_dict(
            "PUT",
            f"/wallets/{wallet_id}",
            json={"wallet_name": name, "wallet_type": type, "balance": balance},
        )

    def delete_wallet(self, wallet_id: int) -> None:
        self._request_empty("DELETE", f"/wallets/{wallet_id}")

    def archive_wallet(self, wallet_id: int) -> None:
        self._request_empty("POST", f"/wallets/{wallet_id}/archive")

    def transfer_funds(
        self,
        from_wallet_id: int,
        to_wallet_id: int,
        amount: float,
        notes: str | None = None,
        transaction_date: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "from_wallet_id": from_wallet_id,
            "to_wallet_id": to_wallet_id,
            "amount": amount,
        }
        if notes:
            payload["notes"] = notes
        if transaction_date:
            payload["transaction_date"] = transaction_date
        return self._request_dict("POST", "/wallets/transfer", json=payload)

    # --- TRANSACTION ENDPOINTS ---

    def list_transactions(
        self,
        wallet_id: int | None = None,
        search: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        is_transfer: bool | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if wallet_id is not None:
            params["wallet_id"] = wallet_id
        if search:
            params["search"] = search
        if category:
            params["category"] = category
        if transaction_type:
            params["type"] = transaction_type
        if is_transfer is not None:
            params["is_transfer"] = str(is_transfer).lower()
        return self._request_dict("GET", "/transactions", params=params)

    def create_transaction(
        self,
        wallet_id: int,
        merchant_name: str,
        category: str | None,
        amount: float,
        transaction_type: str,
        transaction_date: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        return self._request_dict(
            "POST",
            "/transactions",
            json={
                "wallet_id": wallet_id,
                "merchant_name": merchant_name,
                "category": category,
                "amount": amount,
                "transaction_type": transaction_type,
                "transaction_date": transaction_date,
                "notes": notes,
            },
        )

    def update_transaction(self, transaction_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_dict("PUT", f"/transactions/{transaction_id}", json=payload)

    def delete_transaction(self, transaction_id: int) -> None:
        self._request_empty("DELETE", f"/transactions/{transaction_id}")

    def delete_all_transactions(self) -> dict[str, Any]:
        return self._request_dict("DELETE", "/transactions/all")

    # --- DASHBOARD & INTELLIGENCE ---

    def get_dashboard(self) -> dict[str, Any]:
        return self._request_dict("GET", "/dashboard")

    def get_health_score(self) -> dict[str, Any]:
        return self._request_dict("GET", "/dashboard/health-score")

    def get_insights(self) -> list[dict[str, Any]]:
        return self._request_list("GET", "/insights")

    # --- ADVISOR ---

    def ask_advisor(self, question: str, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"question": question}
        if history:
            payload["history"] = history
        return self._request_dict("POST", "/advisor/ask", json=payload)

    def get_advisor_context(self) -> dict[str, Any]:
        return self._request_dict("GET", "/advisor/context")

    # --- NET WORTH ---

    def get_net_worth_summary(self) -> dict[str, Any]:
        return self._request_dict("GET", "/net-worth/summary")
        
    def list_net_worth_items(self) -> list[dict[str, Any]]:
        return self._request_list("GET", "/net-worth/items")

    def create_net_worth_item(
        self,
        name: str,
        item_type: str,
        category: str,
        amount: float,
        notes: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "item_type": item_type, "category": category, "amount": amount}
        if notes:
            payload["notes"] = notes
        return self._request_dict("POST", "/net-worth/items", json=payload)

    def update_net_worth_item(self, item_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_dict("PUT", f"/net-worth/items/{item_id}", json=payload)

    def delete_net_worth_item(self, item_id: int) -> None:
        self._request_empty("DELETE", f"/net-worth/items/{item_id}")

    def take_net_worth_snapshot(self) -> dict[str, Any]:
        return self._request_dict("POST", "/net-worth/snapshot")

    def list_net_worth_snapshots(self) -> list[dict[str, Any]]:
        return self._request_list("GET", "/net-worth/history")

    # --- BUDGETS ---

    def list_budgets(self) -> list[dict[str, Any]]:
        return self._request_list("GET", "/budgets")

    def create_budget(
        self,
        name: str,
        category: str,
        amount: float,
        period: str = "monthly",
        start_date: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "category": category, "amount": amount, "period": period}
        if start_date:
            payload["start_date"] = start_date
        return self._request_dict("POST", "/budgets", json=payload)

    def update_budget(self, budget_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_dict("PUT", f"/budgets/{budget_id}", json=payload)

    def delete_budget(self, budget_id: int) -> None:
        self._request_empty("DELETE", f"/budgets/{budget_id}")

    # --- GOALS ---

    def list_goals(self) -> list[dict[str, Any]]:
        return self._request_list("GET", "/goals")

    def create_goal(
        self,
        name: str,
        target_amount: float,
        current_amount: float = 0.0,
        description: str | None = None,
        target_date: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "target_amount": target_amount, "current_amount": current_amount}
        if description:
            payload["description"] = description
        if target_date:
            payload["target_date"] = target_date
        return self._request_dict("POST", "/goals", json=payload)

    def update_goal(self, goal_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_dict("PUT", f"/goals/{goal_id}", json=payload)

    def contribute_goal(self, goal_id: int, amount: float) -> dict[str, Any]:
        return self._request_dict("POST", f"/goals/{goal_id}/contribute", json={"amount": amount})

    def delete_goal(self, goal_id: int) -> None:
        self._request_empty("DELETE", f"/goals/{goal_id}")

    # --- SUBSCRIPTIONS ---

    def list_subscriptions(self, confirmed_only: bool = False) -> list[dict[str, Any]]:
        return self._request_list("GET", "/subscriptions", params={"confirmed_only": confirmed_only})

    def create_subscription(
        self,
        name: str,
        amount: float,
        frequency: str = "monthly",
        merchant_name: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "amount": amount, "frequency": frequency}
        if merchant_name:
            payload["merchant_name"] = merchant_name
        if category:
            payload["category"] = category
        return self._request_dict("POST", "/subscriptions", json=payload)

    def update_subscription(self, sub_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_dict("PUT", f"/subscriptions/{sub_id}", json=payload)

    def confirm_subscription(self, sub_id: int) -> dict[str, Any]:
        return self._request_dict("POST", f"/subscriptions/{sub_id}/confirm")

    def dismiss_subscription(self, sub_id: int) -> None:
        self._request_empty("DELETE", f"/subscriptions/{sub_id}")

    def detect_subscriptions(self) -> int:
        return self._request_int("POST", "/subscriptions/detect")

    # --- IMPORTS ---

    def list_import_jobs(self) -> list[dict[str, Any]]:
        return self._request_list("GET", "/imports")

    def get_import_job(self, job_id: int) -> dict[str, Any]:
        return self._request_dict("GET", f"/imports/{job_id}")

    def upload_statement(self, wallet_id: int, filename: str, file_bytes: bytes) -> dict[str, Any]:
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        data = {"wallet_id": str(wallet_id)}
        return self._request_dict("POST", "/imports/upload", data=data, files=files)

    def commit_import(self, job_id: int) -> dict[str, Any]:
        return self._request_dict("POST", f"/imports/{job_id}/commit")

    # --- ANALYTICS ---

    def get_trends(self, months: int = 6) -> list[dict[str, Any]]:
        return self._request_list("GET", "/analytics/trends", params={"months": months})

    def get_categories(self, year: int | None = None, month: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, int] = {}
        if year:
            params["year"] = year
        if month:
            params["month"] = month
        return self._request_list("GET", "/analytics/categories", params=params)

    def get_merchants(self, limit: int = 10) -> list[dict[str, Any]]:
        return self._request_list("GET", "/analytics/merchants", params={"limit": limit})

    def run_whatif(
        self,
        category: str | None,
        reduce_by: float,
        years: int = 10,
        interest_rate: float = 12.0,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"reduce_by": reduce_by, "years": years, "interest_rate": interest_rate}
        if category:
            payload["category"] = category
        return self._request_dict("POST", "/analytics/whatif", json=payload)

    # --- FIRE INTELLIGENCE ENGINE ---

    def get_fire_dashboard(self) -> dict[str, Any]:
        """Fetch the latest stored FIRE dashboard (has_data=False if no calc yet)."""
        return self._request_dict("GET", "/fire")

    def calculate_fire(self, settings: dict[str, Any]) -> dict[str, Any]:
        """
        Run the full 10-step FIRE engine.
        settings keys: current_age, retirement_target_age, investment_return,
                       inflation_rate, lifestyle
        """
        return self._request_dict("POST", "/fire/calculate", json=settings)

    def get_fire_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return historical FIRE analysis records."""
        return self._request_list("GET", "/fire/history", params={"limit": limit})

    def ask_fire_coach(
        self,
        question: str,
        history: list[dict[str, Any]] | None = None,
        fire_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Ask the FIRE Coach AI — delegates to Groq with FIRE-specific system prompt."""
        payload: dict[str, Any] = {"question": question}
        if history:
            payload["history"] = history
        if fire_context:
            payload["fire_context"] = fire_context
        return self._request_dict("POST", "/fire/ai", json=payload)


# Single shared client instance
api_client = APIClient()
