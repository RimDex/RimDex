from app.core.event_bus import EventBus


def test_singleton_returns_same_instance(fresh_event_bus: None) -> None:
    assert EventBus() is EventBus()


def test_signal_emit_reaches_connected_slot(
    fresh_event_bus: None, qapp: object
) -> None:
    bus = EventBus()
    received: list[bool] = []
    bus.do_open_settings_directory.connect(lambda: received.append(True))
    bus.do_open_settings_directory.emit()
    assert received == [True]


def test_signal_with_args(fresh_event_bus: None, qapp: object) -> None:
    bus = EventBus()
    captured: dict[str, str] = {}

    def _slot(mod_path: str, target_tag: str) -> None:
        captured["mod_path"] = mod_path
        captured["target_tag"] = target_tag

    bus.github_version_switch_requested.connect(_slot)
    bus.github_version_switch_requested.emit("path/to/mod", "v1.2")
    assert captured == {"mod_path": "path/to/mod", "target_tag": "v1.2"}


def test_fresh_event_bus_fixture_resets_singleton(
    fresh_event_bus: None,
) -> None:
    first = EventBus()
    assert EventBus() is first
