import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.io.json_utils import atomic_json_dump


def test_atomic_json_dump_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "out.json"
    data = {"name": "RimDex", "nested": {"ids": [1, 2, 3]}, "flag": True}
    atomic_json_dump(data, str(target), indent=2)
    assert target.is_file()
    assert json.loads(target.read_text(encoding="utf-8")) == data


def test_atomic_json_dump_passes_kwargs(tmp_path: Path) -> None:
    target = tmp_path / "compact.json"
    atomic_json_dump({"a": 1}, str(target), separators=(",", ":"))
    assert target.read_text(encoding="utf-8") == '{"a":1}'


def test_atomic_json_dump_nested_target_with_existing_parent(tmp_path: Path) -> None:
    parent = tmp_path / "nested" / "dir"
    parent.mkdir(parents=True)
    target = parent / "data.json"
    atomic_json_dump({"v": 1}, str(target))
    assert target.is_file()


def test_atomic_json_dump_cleans_up_temp_on_error(tmp_path: Path) -> None:
    target = tmp_path / "bad.json"

    class _Bad:
        pass

    try:
        atomic_json_dump({"x": _Bad()}, str(target))
    except TypeError:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("expected TypeError")

    # The target must not have been created (temp was unlinked + replaced only on success).
    assert not target.exists()
    # No stray temp files left behind.
    assert not list(tmp_path.glob("*.json*"))


def test_atomic_json_dump_retries_transient_replace_permission_error(
    tmp_path: Path,
) -> None:
    target = tmp_path / "settings.json"
    real_replace = os.replace
    attempts = 0

    def flaky_replace(source: str, destination: str) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise PermissionError("temporarily locked")
        real_replace(source, destination)

    with (
        patch("app.io.json_utils.os.replace", side_effect=flaky_replace),
        patch("app.io.json_utils.time.sleep") as sleep,
    ):
        atomic_json_dump({"language": "en"}, str(target))

    assert attempts == 2
    sleep.assert_called_once_with(0.05)
    assert json.loads(target.read_text(encoding="utf-8")) == {"language": "en"}


def test_atomic_json_dump_cleans_temp_file_after_persistent_permission_error(
    tmp_path: Path,
) -> None:
    target = tmp_path / "settings.json"

    with (
        patch(
            "app.io.json_utils.os.replace",
            side_effect=PermissionError("still locked"),
        ),
        patch("app.io.json_utils.time.sleep") as sleep,
        pytest.raises(PermissionError, match="still locked"),
    ):
        atomic_json_dump({"language": "en"}, str(target))

    assert list(tmp_path.iterdir()) == []
    assert sleep.call_count == 4
