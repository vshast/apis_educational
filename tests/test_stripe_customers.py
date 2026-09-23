"""Automated coverage for TestRail case C46 - "Stripe API test1" (Stripe APIs section).

Precondition: a valid Stripe test-mode secret key (sk_test_...) is provided via
the STRIPE_API_KEY environment variable and used as HTTP Basic Auth username.
Step: GET https://api.stripe.com/v1/customers.
Expected: 200 OK with a JSON list response.
"""


def test_get_customers_returns_list(stripe_base_url, stripe_session):
    response = stripe_session.get(f"{stripe_base_url}/v1/customers")

    assert response.status_code == 200, response.text

    body = response.json()
    assert body.get("object") == "list", f"Unexpected 'object' value: {body}"
    assert isinstance(body.get("data"), list), f"'data' is not a list: {body}"
    assert "has_more" in body, f"Missing 'has_more' in response body: {body}"
    assert "url" in body, f"Missing 'url' in response body: {body}"
