"""Tests for the pure URL/page-mode helpers used by the Steam browser."""

import pytest

from app.utils.steam.steambrowser.browser import (
    parse_publishedfileid_from_url,
    resolve_workshop_page_mode,
    toolbar_add_to_list_visible,
)

URL_PREFIX_STEAM = "https://steamcommunity.com"
URL_PREFIX_SHAREDFILES = f"{URL_PREFIX_STEAM}/sharedfiles/filedetails/?id="
URL_PREFIX_WORKSHOP = f"{URL_PREFIX_STEAM}/workshop/filedetails/?id="
SEARCHTEXT = "&searchtext="
SECTION_READYTOUSEITEMS = "section=readytouseitems"
SECTION_COLLECTIONS = "section=collections"
HUB_BROWSE_URL = (
    f"{URL_PREFIX_STEAM}/app/294100/workshop/browse/?{SECTION_READYTOUSEITEMS}"
)


def _pfid(url: str) -> str | None:
    return parse_publishedfileid_from_url(
        url,
        url_prefix_sharedfiles=URL_PREFIX_SHAREDFILES,
        url_prefix_workshop=URL_PREFIX_WORKSHOP,
        searchtext_string=SEARCHTEXT,
    )


def _mode(url: str) -> str:
    return resolve_workshop_page_mode(
        url,
        url_prefix_steam=URL_PREFIX_STEAM,
        url_prefix_sharedfiles=URL_PREFIX_SHAREDFILES,
        url_prefix_workshop=URL_PREFIX_WORKSHOP,
        section_readytouseitems=SECTION_READYTOUSEITEMS,
        section_collections=SECTION_COLLECTIONS,
    )


def _toolbar_visible(url: str) -> bool:
    return toolbar_add_to_list_visible(
        url,
        url_prefix_steam=URL_PREFIX_STEAM,
        url_prefix_sharedfiles=URL_PREFIX_SHAREDFILES,
        url_prefix_workshop=URL_PREFIX_WORKSHOP,
        searchtext_string=SEARCHTEXT,
    )


class TestParsePublishedfileidFromUrl:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            (f"{URL_PREFIX_SHAREDFILES}123456", "123456"),
            (f"{URL_PREFIX_WORKSHOP}123456", "123456"),
            (f"{URL_PREFIX_SHAREDFILES}123456#comment", "123456"),
            (f"{URL_PREFIX_SHAREDFILES}123456&searchtext=foo", "123456"),
            (f"{URL_PREFIX_SHAREDFILES}123456&searchtext=foo#bar", "123456"),
            (f"{URL_PREFIX_SHAREDFILES}123456?l=english", "123456"),
            (f"{URL_PREFIX_SHAREDFILES}123456&l=english", "123456"),
            (f"{URL_PREFIX_SHAREDFILES}123456/", "123456"),
            (URL_PREFIX_SHAREDFILES, None),
            (f"{URL_PREFIX_WORKSHOP}   ", None),
            ("https://example.com/nothing", None),
        ],
    )
    def test_extraction(self, url: str, expected: str | None) -> None:
        assert _pfid(url) == expected


class TestResolveWorkshopPageMode:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            (f"{URL_PREFIX_SHAREDFILES}1", "detail"),
            (f"{URL_PREFIX_WORKSHOP}1", "detail"),
            (f"{URL_PREFIX_STEAM}/app/294100/workshop/", "hub"),
            (f"{URL_PREFIX_STEAM}/app/294100/workshop/featured", "hub"),
            (f"{HUB_BROWSE_URL}", "browse"),
            (
                f"{URL_PREFIX_STEAM}/myworkshopfiles/?{SECTION_READYTOUSEITEMS}",
                "browse",
            ),
            (f"{URL_PREFIX_STEAM}/workshop/browse/?{SECTION_COLLECTIONS}", "browse"),
            (f"{URL_PREFIX_STEAM}/workshop/browse/?section=toprated", "browse"),
            ("https://example.com/workshop", "other"),
            (f"{URL_PREFIX_STEAM}/", "other"),
        ],
    )
    def test_classification(self, url: str, expected: str) -> None:
        assert _mode(url) == expected

    def test_hub_loses_to_browse(self) -> None:
        """A browse URL under the workshop hub path is a grid, not a hub."""
        assert _mode(HUB_BROWSE_URL) == "browse"

    def test_hub_loses_to_item_page(self) -> None:
        """A filedetails URL under the hub path is a detail page, not a hub."""
        url = f"{URL_PREFIX_STEAM}/app/294100/workshop/filedetails/?id=1"
        assert _mode(url) == "other"


class TestToolbarAddToListVisible:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            (f"{URL_PREFIX_SHAREDFILES}123456", True),
            (f"{URL_PREFIX_WORKSHOP}123456", True),
            (f"{URL_PREFIX_SHAREDFILES}123456#c", True),
            (URL_PREFIX_SHAREDFILES, False),
            (f"{URL_PREFIX_STEAM}/app/294100/workshop/", False),
            (f"{URL_PREFIX_STEAM}/workshop/browse/?{SECTION_READYTOUSEITEMS}", False),
            ("https://example.com/nothing", False),
        ],
    )
    def test_visibility(self, url: str, expected: bool) -> None:
        assert _toolbar_visible(url) is expected
