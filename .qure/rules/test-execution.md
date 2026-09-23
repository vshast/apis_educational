---
name: Test execution
status: active
---
This repository is a Python + pytest + `requests` API test project (no Playwright/JS setup).

- Working directory: repository root.
- Install dependencies: `pip install -r requirements.txt`
- Run all tests: `pytest`
- Run one test: `pytest tests/test_reqres_users.py -v`
- Discover tests without running them: `pytest --collect-only -q`
  - Qure's `qure_pytest.collect_only` discovery plugin is not installed in this
    environment (`ModuleNotFoundError: No module named 'qure_pytest'`), so
    verify collection with the plain command above.
- The ReqRes API key used by tests defaults to a value in
  `tests/conftest.py` and can be overridden with the `REQRES_API_KEY`
  environment variable.
- The Stripe test-mode secret key used by `tests/test_stripe_customers.py`
  is NOT hardcoded anywhere in the repo. It must be provided via the
  `STRIPE_API_KEY` environment variable (a real Stripe test-mode key,
  starts with `sk_test_`); without it, that test is skipped.
