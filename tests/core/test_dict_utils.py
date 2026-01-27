from typing import Any

from app.core.dict_utils import recursively_update_dict


def test_merge_nested_dicts() -> None:
    a = {"x": 1, "nested": {"a": 1, "b": 2}}
    b: dict[str, Any] = {"nested": {"b": 3, "c": 4}}
    recursively_update_dict(a, b)
    assert a == {"x": 1, "nested": {"a": 1, "b": 3, "c": 4}}


def test_top_level_new_keys() -> None:
    a = {"keep": True}
    b: dict[str, Any] = {"added": 1, "nested": {"x": 1}}
    recursively_update_dict(a, b)
    assert a == {"keep": True, "added": 1, "nested": {"x": 1}}


def test_recurse_exceptions_overwrite_directly() -> None:
    a = {"cfg": {"deep": {"k": 1}}}
    b: dict[str, Any] = {"cfg": {"other": 2}}
    # "cfg" in recurse_exceptions: b["cfg"] replaces a["cfg"] wholesale.
    recursively_update_dict(a, b, recurse_exceptions=("cfg",))
    assert a == {"cfg": {"other": 2}}


def test_purge_keys_removes_unconditionally() -> None:
    # purge_keys removes matching keys only at the top level.
    a = {"keep": 1, "drop": 2, "nested": {"drop": 3}}
    b: dict[str, Any] = {}
    recursively_update_dict(a, b, purge_keys=("drop",))
    assert a == {"keep": 1, "nested": {"drop": 3}}


def test_empty_subdicts_pruned_by_default() -> None:
    a = {"empty": {}, "keep": {"x": 1}}
    b: dict[str, Any] = {}
    recursively_update_dict(a, b)
    assert "empty" not in a
    assert a == {"keep": {"x": 1}}


def test_prune_exceptions_keeps_empty_subdict() -> None:
    a: dict[str, Any] = {"empty": {}}
    b: dict[str, Any] = {}
    recursively_update_dict(a, b, prune_exceptions=("empty",))
    assert "empty" in a and a["empty"] == {}


def test_original_untouched_keys_preserved() -> None:
    a = {"a": 1, "b": {"c": 2}}
    b: dict[str, Any] = {"b": {"d": 3}}
    recursively_update_dict(a, b)
    assert a == {"a": 1, "b": {"c": 2, "d": 3}}


def test_mutates_in_place() -> None:
    a = {"x": 1}
    b: dict[str, Any] = {"y": 2}
    recursively_update_dict(a, b)
    assert a == {"x": 1, "y": 2}
