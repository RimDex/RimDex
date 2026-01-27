from typing import Any
from unittest.mock import MagicMock, patch

import requests

from app.utils.steam.webapi.wrapper import (
    ISteamRemoteStorage_GetPublishedFileDetails,
)

PFIDS = ["111", "222", "333"]

VALID_RESPONSE_JSON = {
    "response": {
        "result": 1,
        "resultcount": 3,
        "publishedfiledetails": [
            {"publishedfileid": "111", "time_created": 100, "time_updated": 200},
            {"publishedfileid": "222", "time_created": 100, "time_updated": 300},
            {"publishedfileid": "333", "time_created": 100, "time_updated": 400},
        ],
    }
}


def _make_mock_response(
    status_code: int = 200, json_data: dict[str, Any] | None = None
) -> MagicMock:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = requests.exceptions.JSONDecodeError(
            "Expecting value", "", 0
        )
    return resp


class TestGetPublishedFileDetailsReturn:
    """Verify the function returns (metadata, failed_pfids, errors) tuple."""

    @patch("app.utils.steam.webapi.wrapper.http.post")
    def test_success_returns_three_tuple(self, mock_post: MagicMock) -> None:
        mock_post.return_value = _make_mock_response(200, VALID_RESPONSE_JSON)
        result = ISteamRemoteStorage_GetPublishedFileDetails(PFIDS)
        assert isinstance(result, tuple)
        assert len(result) == 3
        metadata, failed_pfids, errors = result
        assert len(metadata) == 3
        assert failed_pfids == []
        assert errors == []

    @patch("app.utils.steam.webapi.wrapper.http.post")
    def test_empty_pfids_returns_empty_tuple(self, mock_post: MagicMock) -> None:
        metadata, failed_pfids, errors = ISteamRemoteStorage_GetPublishedFileDetails([])
        assert metadata == []
        assert failed_pfids == []
        assert errors == []
        mock_post.assert_not_called()


class TestGetPublishedFileDetailsRetry:
    """Verify the wrapper delegates retries to http.post and handles results.

    Retry logic (exponential backoff, status codes) is handled internally by
    http.post(retry=True) and tested in test_http.py.
    """

    @patch("app.utils.steam.webapi.wrapper.http.post")
    def test_calls_post_with_retry_enabled(self, mock_post: MagicMock) -> None:
        """http.post is called with retry=True for every chunk."""
        mock_post.return_value = _make_mock_response(200, VALID_RESPONSE_JSON)
        ISteamRemoteStorage_GetPublishedFileDetails(PFIDS)
        for call in mock_post.call_args_list:
            assert call.kwargs.get("retry") is True

    @patch("app.utils.steam.webapi.wrapper.http.post")
    def test_timeout_records_failure(self, mock_post: MagicMock) -> None:
        """When http.post raises, the chunk is recorded as failed."""
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")
        metadata, failed_pfids, errors = ISteamRemoteStorage_GetPublishedFileDetails(
            PFIDS
        )
        assert metadata == []
        assert set(failed_pfids) == set(PFIDS)
        assert len(errors) == 1

    @patch("app.utils.steam.webapi.wrapper.http.post")
    def test_connection_error_records_failure(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )
        metadata, failed_pfids, errors = ISteamRemoteStorage_GetPublishedFileDetails(
            PFIDS
        )
        assert metadata == []
        assert set(failed_pfids) == set(PFIDS)

    @patch("app.utils.steam.webapi.wrapper.http.post")
    def test_http_503_records_failure(self, mock_post: MagicMock) -> None:
        """Retryable status after retries exhausted → recorded as failed."""
        mock_post.return_value = _make_mock_response(503)
        metadata, failed_pfids, errors = ISteamRemoteStorage_GetPublishedFileDetails(
            PFIDS
        )
        assert metadata == []
        assert set(failed_pfids) == set(PFIDS)

    @patch("app.utils.steam.webapi.wrapper.http.post")
    def test_http_429_records_failure(self, mock_post: MagicMock) -> None:
        mock_post.return_value = _make_mock_response(429)
        metadata, failed_pfids, errors = ISteamRemoteStorage_GetPublishedFileDetails(
            PFIDS
        )
        assert metadata == []
        assert set(failed_pfids) == set(PFIDS)


class TestGetPublishedFileDetailsNonRetryable:
    """Verify non-retryable errors fail immediately without retry."""

    @patch("app.utils.steam.webapi.wrapper.sleep")
    @patch("app.utils.steam.webapi.wrapper.http.post")
    def test_json_decode_error_no_retry(
        self, mock_post: MagicMock, mock_sleep: MagicMock
    ) -> None:
        mock_post.return_value = _make_mock_response(200, json_data=None)
        metadata, failed_pfids, errors = ISteamRemoteStorage_GetPublishedFileDetails(
            PFIDS
        )
        assert metadata == []
        assert set(failed_pfids) == set(PFIDS)
        assert len(errors) == 1
        assert mock_post.call_count == 1  # no retry
        mock_sleep.assert_not_called()

    @patch("app.utils.steam.webapi.wrapper.sleep")
    @patch("app.utils.steam.webapi.wrapper.http.post")
    def test_http_400_no_retry(
        self, mock_post: MagicMock, mock_sleep: MagicMock
    ) -> None:
        mock_post.return_value = _make_mock_response(400)
        metadata, failed_pfids, errors = ISteamRemoteStorage_GetPublishedFileDetails(
            PFIDS
        )
        assert metadata == []
        assert set(failed_pfids) == set(PFIDS)
        assert mock_post.call_count == 1
        mock_sleep.assert_not_called()
