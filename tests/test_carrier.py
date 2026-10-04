from shipping.carrier import client


def test_headers_carry_the_account():
    c = client.CarrierClient()
    headers = c._headers()
    assert headers["X-Account-Id"] == client.ACCOUNT_ID
    assert headers["Authorization"].startswith("Bearer ")


def test_base_url_is_versioned():
    assert client.BASE_URL.endswith("/v2")
