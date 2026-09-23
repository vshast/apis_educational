import os

import pytest
import requests

BASE_URL = "https://reqres.in"


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def api_key() -> str:
    # ReqRes test-mode API key. Not hardcoded here - must be provided via the
    # REQRES_API_KEY environment variable.
    key = os.environ.get("REQRES_API_KEY")
    if not key:
        pytest.skip("REQRES_API_KEY environment variable is not set")
    return key


@pytest.fixture
def api_session(api_key: str):
    session = requests.Session()
    session.headers.update({"x-api-key": api_key})
    yield session
    session.close()


STRIPE_BASE_URL = "https://api.stripe.com"


@pytest.fixture(scope="session")
def stripe_base_url() -> str:
    return STRIPE_BASE_URL


@pytest.fixture(scope="session")
def stripe_api_key() -> str:
    # Stripe test-mode secret key (starts with sk_test_). Not hardcoded here -
    # must be provided via the STRIPE_API_KEY environment variable, since it
    # is tied to a real Stripe account (even in test mode).
    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        pytest.skip("STRIPE_API_KEY environment variable is not set")
    return key


@pytest.fixture
def stripe_session(stripe_api_key: str):
    session = requests.Session()
    # Stripe authenticates via HTTP Basic Auth: secret key as username, empty password.
    session.auth = (stripe_api_key, "")
    yield session
    session.close()
