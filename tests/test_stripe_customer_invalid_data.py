"""Automated coverage for TestRail cases C51-C54 (Stripe APIs section):
invalid-data / error-path scenarios against the Stripe test-mode account.

- C52: GET /v1/customers with an invalid API key returns 401 Unauthorized.
- C53: GET /v1/customers/{id} with a non-existent id returns 404 Not Found.
- C51: POST /v1/customers with a malformed email returns 400 Bad Request.
- C54: Reusing an Idempotency-Key with different parameters returns a
  400 idempotency error.

Precondition (C51, C53, C54): a valid Stripe test-mode secret key
(sk_test_...) is provided via the STRIPE_API_KEY environment variable (see
the stripe_session fixture in conftest.py). C52 intentionally uses a
fabricated key and does not require STRIPE_API_KEY.

Every customer created during these tests is deleted again in a `finally`
block so the test-mode account does not accumulate leftover data.
"""

import json
import uuid

import requests


def _unique_email() -> str:
    return f"qure.e2e.{uuid.uuid4().hex}@example.com"


def _idempotency_key() -> str:
    return f"qure-e2e-{uuid.uuid4()}"


def test_get_customers_invalid_api_key_returns_401(stripe_base_url):
    """C52: an invalid secret key must be rejected with 401, not customer data."""
    session = requests.Session()
    session.auth = ("sk_test_invalid_key_0000", "")

    try:
        response = session.get(f"{stripe_base_url}/v1/customers")

        assert response.status_code == 401, response.text
        body = response.json()
        assert "error" in body, f"Missing 'error' in response body: {body}"
        assert "data" not in body, f"Unexpected customer data returned: {body}"
    finally:
        session.close()


def test_create_customer_invalid_email_returns_400(stripe_base_url, stripe_session):
    """C51: creating a customer with a malformed email must be rejected."""
    customers_url = f"{stripe_base_url}/v1/customers"

    response = stripe_session.post(
        customers_url,
        data={"email": "not-an-email", "name": "Invalid Email Customer"},
    )

    assert response.status_code == 400, response.text
    body = response.json()
    error = body.get("error", {})
    assert error.get("type") == "invalid_request_error", body
    assert "email" in json.dumps(error).lower(), (
        f"Expected the validation error to reference the 'email' field: {error}"
    )
    assert "object" not in body, f"A customer object should not have been created: {body}"


def test_get_nonexistent_customer_returns_404(stripe_base_url, stripe_session):
    """C53: retrieving a syntactically valid but non-existent customer id."""
    response = stripe_session.get(
        f"{stripe_base_url}/v1/customers/cus_doesnotexist000000"
    )

    assert response.status_code == 404, response.text
    body = response.json()
    error = body.get("error", {})
    assert error.get("type") == "invalid_request_error", body
    assert error.get("code") == "resource_missing", body


def test_idempotency_key_reuse_with_different_params_conflicts(
    stripe_base_url, stripe_session
):
    """C54: replaying an Idempotency-Key with different parameters must
    fail with an idempotency_error instead of creating a second customer or
    silently returning the first customer's response.
    """
    customers_url = f"{stripe_base_url}/v1/customers"
    key = _idempotency_key()
    created_customer_id = None

    try:
        data_a = {"email": _unique_email(), "name": "Idempotency Customer A"}
        response = stripe_session.post(
            customers_url, data=data_a, headers={"Idempotency-Key": key}
        )
        assert response.status_code == 200, response.text
        customer_a = response.json()
        created_customer_id = customer_a["id"]

        data_b = {"email": _unique_email(), "name": "Idempotency Customer B"}
        response = stripe_session.post(
            customers_url, data=data_b, headers={"Idempotency-Key": key}
        )

        assert response.status_code == 400, response.text
        body = response.json()
        error = body.get("error", {})
        assert error.get("type") == "idempotency_error", body
    finally:
        if created_customer_id:
            stripe_session.delete(f"{customers_url}/{created_customer_id}")
