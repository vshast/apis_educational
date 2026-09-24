"""End-to-end coverage for the Stripe customer creation lifecycle.

Exercises the full flow for creating customers with idempotency keys against
https://api.stripe.com:

1. Create a customer supplying all fields treated as mandatory for this
   scenario, sending an idempotency key.

   Stripe's "Create a customer" endpoint does not enforce any strictly
   required parameters - every field is technically optional. For this
   scenario, `email` and `name` are treated as the customer's mandatory
   identifying fields.
2. Confirm the customer exists via a direct GET.
3. Repeat the exact same creation request with the SAME idempotency key and
   the SAME parameters - Stripe must return the cached response for the
   original customer (no new resource is created).
4. Repeat creation of the same customer data with a DIFFERENT idempotency
   key - Stripe treats this as an unrelated request and creates a second,
   distinct customer even though the submitted data matches.
5. Create a genuinely different customer (different data) with yet another
   idempotency key.
6. Ask for the customer list and confirm all three created customers are
   present in it.

Precondition: a valid Stripe test-mode secret key (sk_test_...) is provided
via the STRIPE_API_KEY environment variable (see the stripe_session fixture
in conftest.py).

Every customer created during the test is deleted again in a `finally` block
so the test-mode account does not accumulate leftover data.
"""

import json
import uuid


def _show(label: str, response) -> None:
    """Print a step's status code and JSON body for -v -s runs."""
    print(f"\n--- {label} (status {response.status_code}) ---")
    try:
        print(json.dumps(response.json(), indent=2, sort_keys=True))
    except ValueError:
        print(response.text)


def _unique_email() -> str:
    return f"qure.e2e.{uuid.uuid4().hex}@example.com"


def _idempotency_key() -> str:
    return f"qure-e2e-{uuid.uuid4()}"


def test_customer_creation_lifecycle_with_idempotency_keys(stripe_base_url, stripe_session):
    customers_url = f"{stripe_base_url}/v1/customers"
    created_customer_ids = []

    try:
        # 1. Create a customer with all mandatory fields, using an idempotency key.
        key_1 = _idempotency_key()
        customer_1_data = {
            "email": _unique_email(),
            "name": "Qure E2E Customer One",
        }
        response = stripe_session.post(
            customers_url, data=customer_1_data, headers={"Idempotency-Key": key_1}
        )
        assert response.status_code == 200, response.text
        customer_1 = response.json()
        _show("1. Create customer 1", response)
        assert customer_1.get("object") == "customer", customer_1
        assert customer_1.get("email") == customer_1_data["email"], customer_1
        assert customer_1.get("name") == customer_1_data["name"], customer_1
        customer_1_id = customer_1["id"]
        created_customer_ids.append(customer_1_id)

        # 2. Check the customer exists.
        response = stripe_session.get(f"{customers_url}/{customer_1_id}")
        assert response.status_code == 200, response.text
        fetched_customer_1 = response.json()
        _show("2. Fetch customer 1", response)
        assert fetched_customer_1.get("id") == customer_1_id, fetched_customer_1
        assert fetched_customer_1.get("email") == customer_1_data["email"], fetched_customer_1
        assert fetched_customer_1.get("name") == customer_1_data["name"], fetched_customer_1

        # 3. Repeat creation of the same customer using the SAME idempotency
        # key -> Stripe must return the cached response for the same customer,
        # not create a new one.
        response = stripe_session.post(
            customers_url, data=customer_1_data, headers={"Idempotency-Key": key_1}
        )
        assert response.status_code == 200, response.text
        replayed_customer = response.json()
        _show("3. Replay creation with SAME idempotency key", response)
        assert replayed_customer.get("id") == customer_1_id, (
            f"Replaying the same idempotency key created a new customer: {replayed_customer}"
        )
        assert replayed_customer == customer_1, (
            "Cached idempotent response body differs from the original creation response: "
            f"{replayed_customer} != {customer_1}"
        )

        # 4. Repeat creation of the same customer data using a DIFFERENT
        # idempotency key -> Stripe treats it as an unrelated request and
        # creates a second, distinct customer even though the data matches.
        key_2 = _idempotency_key()
        response = stripe_session.post(
            customers_url, data=customer_1_data, headers={"Idempotency-Key": key_2}
        )
        assert response.status_code == 200, response.text
        customer_2 = response.json()
        _show("4. Repeat creation with DIFFERENT idempotency key", response)
        assert customer_2.get("object") == "customer", customer_2
        customer_2_id = customer_2["id"]
        created_customer_ids.append(customer_2_id)
        assert customer_2_id != customer_1_id, (
            "A different idempotency key should create a distinct customer resource, "
            f"but the same id ({customer_1_id}) was returned again"
        )
        assert customer_2.get("email") == customer_1_data["email"], customer_2
        assert customer_2.get("name") == customer_1_data["name"], customer_2

        # 5. Create a genuinely different customer with all mandatory fields,
        # using another idempotency key.
        key_3 = _idempotency_key()
        customer_3_data = {
            "email": _unique_email(),
            "name": "Qure E2E Customer Two",
        }
        response = stripe_session.post(
            customers_url, data=customer_3_data, headers={"Idempotency-Key": key_3}
        )
        assert response.status_code == 200, response.text
        customer_3 = response.json()
        _show("5. Create a different customer", response)
        assert customer_3.get("object") == "customer", customer_3
        customer_3_id = customer_3["id"]
        created_customer_ids.append(customer_3_id)
        assert customer_3_id not in (customer_1_id, customer_2_id), customer_3
        assert customer_3.get("email") == customer_3_data["email"], customer_3
        assert customer_3.get("name") == customer_3_data["name"], customer_3

        # 6. Ask for the customer list and confirm all three created
        # customers are present in it.
        response = stripe_session.get(customers_url, params={"limit": 100})
        assert response.status_code == 200, response.text
        customer_list = response.json()
        _show("6. Customer list", response)
        assert customer_list.get("object") == "list", customer_list
        assert isinstance(customer_list.get("data"), list), customer_list
        listed_ids = {item.get("id") for item in customer_list["data"]}
        assert customer_1_id in listed_ids, (
            f"Customer {customer_1_id} missing from customer list: {listed_ids}"
        )
        assert customer_2_id in listed_ids, (
            f"Customer {customer_2_id} missing from customer list: {listed_ids}"
        )
        assert customer_3_id in listed_ids, (
            f"Customer {customer_3_id} missing from customer list: {listed_ids}"
        )
    finally:
        # Clean up every customer created during the test so the test-mode
        # account does not accumulate leftover data.
        for customer_id in created_customer_ids:
            stripe_session.delete(f"{customers_url}/{customer_id}")
