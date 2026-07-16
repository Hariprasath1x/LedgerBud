"""Centralized FastAPI HTTP client for LedgerBud."""

import os
import httpx
import streamlit as st


class APIClient:
    def __init__(self):
        # Read base URL from environment or default to localhost:8000
        self.base_url = os.environ.get("FASTAPI_BASE_URL", "http://localhost:8000").rstrip("/")
        self.api_prefix = "/api/v1"

    @property
    def headers(self) -> dict[str, str]:
        """Build headers with JWT bearer token if user is authenticated."""
        headers = {}
        if st.session_state.get("token"):
            headers["Authorization"] = f"Bearer {st.session_state.token}"
        return headers

    def _handle_response(self, response: httpx.Response):
        """Parse response and handle common HTTP error codes."""
        if response.status_code == 401:
            # Session expired / unauthorized — trigger logout
            from ui.state import logout_user
            logout_user()
            st.rerun()

        if response.is_error:
            try:
                detail = response.json().get("detail", "API Request Failed")
            except Exception:
                detail = f"Error {response.status_code}: {response.text}"
            raise httpx.HTTPStatusError(detail, request=response.request, response=response)

        if response.status_code == 204:
            return None

        try:
            return response.json()
        except Exception:
            return response.text

    def _request(self, method: str, path: str, **kwargs):
        """Perform raw HTTP request with auth header attached."""
        url = f"{self.base_url}{self.api_prefix}{path}"
        try:
            with httpx.Client(timeout=30.0) as client:
                headers = {**self.headers, **kwargs.pop("headers", {})}
                response = client.request(method, url, headers=headers, **kwargs)
                return self._handle_response(response)
        except httpx.RequestError as exc:
            raise httpx.RequestError(f"API Server unavailable: {exc}") from exc

    # --- AUTH ENDPOINTS ---

    def register(self, email: str, password: str, full_name: str) -> dict:
        return self._request(
            "POST",
            "/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )

    def login(self, email: str, password: str) -> dict:
        return self._request(
            "POST",
            "/auth/login",
            json={"email": email, "password": password},
        )

    def get_me(self) -> dict:
        return self._request("GET", "/auth/me")

    # --- WALLET ENDPOINTS ---

    def list_wallets(self, include_archived: bool = False) -> list[dict]:
        return self._request("GET", "/wallets", params={"include_archived": str(include_archived).lower()})

    def wallet_summary(self) -> dict:
        return self._request("GET", "/wallets/summary")

    def create_wallet(self, name: str, type: str, balance: float) -> dict:
        return self._request(
            "POST",
            "/wallets",
            json={"wallet_name": name, "wallet_type": type, "balance": balance},
        )

    def update_wallet(self, wallet_id: int, name: str, type: str, balance: float) -> dict:
        return self._request(
            "PUT",
            f"/wallets/{wallet_id}",
            json={"wallet_name": name, "wallet_type": type, "balance": balance},
        )

    def delete_wallet(self, wallet_id: int) -> None:
        self._request("DELETE", f"/wallets/{wallet_id}")

    def archive_wallet(self, wallet_id: int) -> None:
        self._request("POST", f"/wallets/{wallet_id}/archive")

    def transfer_funds(self, from_wallet_id: int, to_wallet_id: int, amount: float, notes: str | None = None, transaction_date: str | None = None) -> dict:
        payload = {
            "from_wallet_id": from_wallet_id,
            "to_wallet_id": to_wallet_id,
            "amount": amount,
        }
        if notes:
            payload["notes"] = notes
        if transaction_date:
            payload["transaction_date"] = transaction_date
        return self._request("POST", "/wallets/transfer", json=payload)

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
    ) -> dict:
        params = {"page": page, "per_page": per_page}
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
        return self._request("GET", "/transactions", params=params)

    def create_transaction(
        self,
        wallet_id: int,
        merchant_name: str,
        category: str | None,
        amount: float,
        transaction_type: str,
        transaction_date: str,
        notes: str | None = None,
    ) -> dict:
        return self._request(
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

    def update_transaction(self, transaction_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/transactions/{transaction_id}", json=payload)

    def delete_transaction(self, transaction_id: int) -> None:
        self._request("DELETE", f"/transactions/{transaction_id}")

    # --- DASHBOARD & INTELLIGENCE ---

    def get_dashboard(self) -> dict:
        return self._request("GET", "/dashboard")

    def get_health_score(self) -> dict:
        return self._request("GET", "/dashboard/health-score")

    def get_insights(self) -> list[dict]:
        return self._request("GET", "/insights")

    # --- ADVISOR ---

    def ask_advisor(self, question: str, history: list[dict] | None = None) -> dict:
        payload = {"question": question}
        if history:
            payload["history"] = history
        return self._request("POST", "/advisor/ask", json=payload)

    def get_advisor_context(self) -> dict:
        return self._request("GET", "/advisor/context")

    # --- NET WORTH ---

    def get_net_worth_summary(self) -> dict:
        return self._request("GET", "/net-worth/summary")
        
    def list_net_worth_items(self) -> list[dict]:
        return self._request("GET", "/net-worth/items")

    def create_net_worth_item(self, name: str, item_type: str, category: str, amount: float, notes: str | None = None) -> dict:
        payload = {"name": name, "item_type": item_type, "category": category, "amount": amount}
        if notes:
            payload["notes"] = notes
        return self._request("POST", "/net-worth/items", json=payload)

    def update_net_worth_item(self, item_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/net-worth/items/{item_id}", json=payload)

    def delete_net_worth_item(self, item_id: int) -> None:
        self._request("DELETE", f"/net-worth/items/{item_id}")

    def take_net_worth_snapshot(self) -> dict:
        return self._request("POST", "/net-worth/snapshot")

    def list_net_worth_snapshots(self) -> list[dict]:
        return self._request("GET", "/net-worth/history")

    # --- BUDGETS ---

    def list_budgets(self) -> list[dict]:
        return self._request("GET", "/budgets")

    def create_budget(self, name: str, category: str, amount: float, period: str = "monthly", start_date: str | None = None) -> dict:
        payload = {"name": name, "category": category, "amount": amount, "period": period}
        if start_date:
            payload["start_date"] = start_date
        return self._request("POST", "/budgets", json=payload)

    def update_budget(self, budget_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/budgets/{budget_id}", json=payload)

    def delete_budget(self, budget_id: int) -> None:
        self._request("DELETE", f"/budgets/{budget_id}")

    # --- GOALS ---

    def list_goals(self) -> list[dict]:
        return self._request("GET", "/goals")

    def create_goal(self, name: str, target_amount: float, current_amount: float = 0.0, description: str | None = None, target_date: str | None = None) -> dict:
        payload = {"name": name, "target_amount": target_amount, "current_amount": current_amount}
        if description:
            payload["description"] = description
        if target_date:
            payload["target_date"] = target_date
        return self._request("POST", "/goals", json=payload)

    def update_goal(self, goal_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/goals/{goal_id}", json=payload)

    def contribute_goal(self, goal_id: int, amount: float) -> dict:
        return self._request("POST", f"/goals/{goal_id}/contribute", json={"amount": amount})

    def delete_goal(self, goal_id: int) -> None:
        self._request("DELETE", f"/goals/{goal_id}")

    # --- SUBSCRIPTIONS ---

    def list_subscriptions(self, confirmed_only: bool = False) -> list[dict]:
        return self._request("GET", "/subscriptions", params={"confirmed_only": confirmed_only})

    def create_subscription(self, name: str, amount: float, frequency: str = "monthly", merchant_name: str | None = None, category: str | None = None) -> dict:
        payload = {"name": name, "amount": amount, "frequency": frequency}
        if merchant_name:
            payload["merchant_name"] = merchant_name
        if category:
            payload["category"] = category
        return self._request("POST", "/subscriptions", json=payload)

    def update_subscription(self, sub_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/subscriptions/{sub_id}", json=payload)

    def confirm_subscription(self, sub_id: int) -> dict:
        return self._request("POST", f"/subscriptions/{sub_id}/confirm")

    def dismiss_subscription(self, sub_id: int) -> None:
        self._request("DELETE", f"/subscriptions/{sub_id}")

    def detect_subscriptions(self) -> int:
        return self._request("POST", "/subscriptions/detect")

    # --- IMPORTS ---

    def list_import_jobs(self) -> list[dict]:
        return self._request("GET", "/imports")

    def get_import_job(self, job_id: int) -> dict:
        return self._request("GET", f"/imports/{job_id}")

    def upload_statement(self, wallet_id: int, filename: str, file_bytes: bytes) -> dict:
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        data = {"wallet_id": str(wallet_id)}
        return self._request("POST", "/imports/upload", data=data, files=files)

    def commit_import(self, job_id: int) -> dict:
        return self._request("POST", f"/imports/{job_id}/commit")

    # --- ANALYTICS ---

    def get_trends(self, months: int = 6) -> list[dict]:
        return self._request("GET", "/analytics/trends", params={"months": months})

    def get_categories(self, year: int | None = None, month: int | None = None) -> list[dict]:
        params = {}
        if year:
            params["year"] = year
        if month:
            params["month"] = month
        return self._request("GET", "/analytics/categories", params=params)

    def get_merchants(self, limit: int = 10) -> list[dict]:
        return self._request("GET", "/analytics/merchants", params={"limit": limit})

    def run_whatif(self, category: str | None, reduce_by: float, years: int = 10, interest_rate: float = 12.0) -> dict:
        payload = {"reduce_by": reduce_by, "years": years, "interest_rate": interest_rate}
        if category:
            payload["category"] = category
        return self._request("POST", "/analytics/whatif", json=payload)

    # --- FIRE INTELLIGENCE ENGINE ---

    def get_fire_dashboard(self) -> dict:
        """Fetch the latest stored FIRE dashboard (has_data=False if no calc yet)."""
        return self._request("GET", "/fire")

    def calculate_fire(self, settings: dict) -> dict:
        """
        Run the full 10-step FIRE engine.
        settings keys: current_age, retirement_target_age, investment_return,
                       inflation_rate, lifestyle
        """
        return self._request("POST", "/fire/calculate", json=settings)

    def get_fire_history(self, limit: int = 20) -> list[dict]:
        """Return historical FIRE analysis records."""
        return self._request("GET", "/fire/history", params={"limit": limit})

    def ask_fire_coach(
        self,
        question: str,
        history: list[dict] | None = None,
        fire_context: dict | None = None,
    ) -> dict:
        """Ask the FIRE Coach AI — delegates to Groq with FIRE-specific system prompt."""
        payload: dict = {"question": question}
        if history:
            payload["history"] = history
        if fire_context:
            payload["fire_context"] = fire_context
        return self._request("POST", "/fire/ai", json=payload)


# Single shared client instance
api_client = APIClient()
