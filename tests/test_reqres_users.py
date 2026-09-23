"""Automated coverage for TestRail case C47 - "Simple GET request" (ReqRes APIs section).

Precondition: a valid ReqRes API key is sent as the `x-api-key` header.
Step: GET https://reqres.in/api/users with pagination.
Expected: 200 OK with a paginated list of user objects.
"""


def test_get_users_returns_paginated_list(base_url, api_session):
    response = api_session.get(f"{base_url}/api/users", params={"page": 2})

    assert response.status_code == 200, response.text

    body = response.json()
    for field in ("page", "per_page", "total", "total_pages", "data"):
        assert field in body, f"Missing '{field}' in response body: {body}"

    users = body["data"]
    assert isinstance(users, list)
    assert len(users) > 0

    for user in users:
        print(user)
        for field in ("id", "email", "first_name", "last_name", "avatar"):
            print(field)
            assert field in user, f"Missing '{field}' in user object: {user}"

if __name__ == "__main__":
    # 3. Call the function here
    test_get_users_returns_paginated_list("https://reqres.in", api_session)