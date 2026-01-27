from app.core.generic import (
    check_valid_http_git_url,
    extract_git_dir_name,
    extract_git_user_or_org,
)

GIT_URLS = [
    "https://github.com/org/RimDex.git",
    "https://github.com/org/RimDex",
    "https://github.com/org/RimDex/",
    "http://github.com/org/RimDex.git",
    "github.com/org/RimDex.git",
    "github.com/org/RimDex",
    "github.com/org/RimDex/",
]


def test_get_git_dir_name() -> None:
    for url in GIT_URLS:
        assert extract_git_dir_name(url) == "RimDex"


def test_get_git_org_or_user() -> None:
    for url in GIT_URLS:
        assert extract_git_user_or_org(url) == "org"


def test_check_valid_http_git_url() -> None:
    assert check_valid_http_git_url("") is False

    assert check_valid_http_git_url("github.com/org/RimDex.git") is False

    assert check_valid_http_git_url("https://github.com/org/RimDex.git") is True

    assert check_valid_http_git_url("http://github.com/org/RimDex.git/") is True
