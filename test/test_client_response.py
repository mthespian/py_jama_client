from unittest.mock import Mock

import pytest

from py_jama_client.client import JamaClient
from py_jama_client.exceptions import TooManyRequestsException
from py_jama_client.response import ClientResponse


def test_client_response(get_example_client_response):
    assert "pageInfo" in get_example_client_response.meta


def test_client_to_dict(get_example_client_response):
    assert "pageInfo" in get_example_client_response.to_dict()["meta"]


def test_client_combination(get_example_client_response):
    new_response = ClientResponse(
        meta={"new": "meta"},
        links={"new": "links"},
        linked={"new": "linked"},
        data=[{"id": 1}],
    )
    combined_response = get_example_client_response + new_response
    assert "pageInfo" in combined_response.meta
    assert "new" in combined_response.meta
    assert "data" in combined_response.to_dict()
    assert len(combined_response.data) == 3
    assert combined_response.data[0]["id"] == 50621
    assert combined_response.data[2]["id"] == 1


def test_get_all_uses_short_page_when_page_info_is_missing():
    client = JamaClient.__new__(JamaClient)
    client.get_page = Mock(side_effect=[
        ClientResponse({}, {}, {}, [{"id": 1}, {"id": 2}]),
        ClientResponse({}, {}, {}, [{"id": 3}]),
    ])

    response = client.get_all(
        "items", params={"omitCount": "true"}, allowed_results_per_page=2
    )

    assert response.data == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert [call.args[1] for call in client.get_page.call_args_list] == [0, 2]


def test_get_all_ignores_zero_total_results_when_page_has_data():
    client = JamaClient.__new__(JamaClient)
    client.get_page = Mock(side_effect=[
        ClientResponse(
            {"pageInfo": {"startIndex": 0, "totalResults": 0}},
            {},
            {},
            [{"id": 1}, {"id": 2}],
        ),
        ClientResponse(
            {"pageInfo": {"startIndex": 2, "totalResults": 0}},
            {},
            {},
            [{"id": 3}],
        ),
    ])

    response = client.get_all(
        "items", params={"omitCount": "true"}, allowed_results_per_page=2
    )

    assert response.data == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert [call.args[1] for call in client.get_page.call_args_list] == [0, 2]


def test_too_many_requests_exception_includes_response_headers():
    response = Mock(
        status_code=429,
        text='{"meta": {"message": "rate limited"}}',
        headers={"Retry-After": "17"},
    )

    with pytest.raises(TooManyRequestsException) as exc_info:
        JamaClient.handle_response_status(response)

    assert exc_info.value.headers["Retry-After"] == "17"
