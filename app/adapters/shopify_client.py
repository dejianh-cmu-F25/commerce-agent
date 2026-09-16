"""Shopify Admin GraphQL client: a thin transport (feature 045).

Auth header, JSON GraphQL, cost extraction, and loud errors. Domain mapping lives
in ``shopify_post_purchase.py``. The ``httpx.AsyncClient`` is injectable, so tests
run keylessly with a ``MockTransport``.
"""

from __future__ import annotations

from typing import Any

import httpx


class ShopifyError(RuntimeError):
    """A Shopify transport or GraphQL error."""


class ShopifyAdminClient:
    """Issues GraphQL requests against one shop's Admin API."""

    def __init__(
        self,
        shop: str,
        access_token: str,
        api_version: str = "2025-07",
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 20.0,
    ) -> None:
        if not shop or not access_token:
            raise ValueError(
                "Shopify shop/access_token is empty; set SHOPIFY_SHOP and SHOPIFY_ACCESS_TOKEN"
            )
        self._url = f"https://{shop}/admin/api/{api_version}/graphql.json"
        self._headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }
        self._client = client
        self._timeout = timeout
        self.last_cost: dict[str, Any] | None = None

    async def query(self, graphql: str, variables: dict[str, Any] | None = None) -> dict:
        """Run a GraphQL query/mutation and return its ``data`` object."""
        payload = {"query": graphql, "variables": variables or {}}
        if self._client is not None:
            response = await self._client.post(self._url, json=payload, headers=self._headers)
        else:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._url, json=payload, headers=self._headers)

        if response.status_code >= 400:
            raise ShopifyError(f"Shopify HTTP {response.status_code}: {response.text[:200]}")
        body = response.json()
        if body.get("errors"):
            raise ShopifyError(f"Shopify GraphQL errors: {body['errors']}")
        cost = body.get("extensions", {}).get("cost")
        if cost:
            self.last_cost = cost
        data = body.get("data")
        if not isinstance(data, dict):
            raise ShopifyError("Shopify response has no data object")
        return data
