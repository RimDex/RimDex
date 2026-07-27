from pathlib import Path

from loguru import logger

from app.utils.log_setup import (
    _anonymize_path,
    _obfuscate_message,
    _rotate_session_logs,
    setup_logging,
)


def test_anonymize_path_windows() -> None:
    assert (
        _anonymize_path(r"C:\Users\john\Documents\file.txt")
        == r"C:\Users\...\Documents\file.txt"
    )
    assert (
        _anonymize_path(r"D:\Users\abc\Documents\file.txt")
        == r"D:\Users\...\Documents\file.txt"
    )


def test_anonymize_path_linux() -> None:
    assert (
        _anonymize_path("/home/john/Documents/file.txt")
        == "/home/.../Documents/file.txt"
    )


def test_anonymize_path_macos() -> None:
    assert (
        _anonymize_path("/Users/john/Documents/file.txt")
        == "/Users/.../Documents/file.txt"
    )


def test_anonymize_path_no_path() -> None:
    assert _anonymize_path("no path here") == "no path here"


def test_obfuscate_message_delegates_to_anonymize_path() -> None:
    assert _obfuscate_message("/home/john/file.txt") == "/home/.../file.txt"


def test_rotate_no_existing_logs(tmp_path: Path) -> None:
    _rotate_session_logs(tmp_path, "RimDex.log")
    assert list(tmp_path.iterdir()) == []


def test_rotate_current_becomes_1(tmp_path: Path) -> None:
    current = tmp_path / "RimDex.log"
    current.write_text("session A")
    _rotate_session_logs(tmp_path, "RimDex.log")
    assert not current.exists()
    assert (tmp_path / "RimDex.1.log").read_text() == "session A"


def test_rotate_cascade(tmp_path: Path) -> None:
    (tmp_path / "RimDex.log").write_text("session C")
    (tmp_path / "RimDex.1.log").write_text("session B")
    (tmp_path / "RimDex.2.log").write_text("session A")
    _rotate_session_logs(tmp_path, "RimDex.log")
    assert (tmp_path / "RimDex.1.log").read_text() == "session C"
    assert (tmp_path / "RimDex.2.log").read_text() == "session B"
    assert (tmp_path / "RimDex.3.log").read_text() == "session A"


def test_rotate_overflow_deleted(tmp_path: Path) -> None:
    (tmp_path / "RimDex.log").write_text("current")
    for i in range(1, 6):
        (tmp_path / f"RimDex.{i}.log").write_text(f"session {i}")
    _rotate_session_logs(tmp_path, "RimDex.log")
    assert not (tmp_path / "RimDex.6.log").exists()
    assert not (tmp_path / "RimDex.7.log").exists()
    assert (tmp_path / "RimDex.1.log").read_text() == "current"
    assert (tmp_path / "RimDex.5.log").exists()


def test_setup_logging_creates_log_file(tmp_path: Path) -> None:
    setup_logging(log_dir=tmp_path, debug=False)
    logger.info("test message")
    logger.complete()
    log_file = tmp_path / "RimDex.log"
    assert log_file.exists()
    assert "test message" in log_file.read_text()
    logger.remove()


def test_setup_logging_debug_level(tmp_path: Path) -> None:
    setup_logging(log_dir=tmp_path, debug=True)
    logger.debug("debug msg")
    logger.complete()
    assert "debug msg" in (tmp_path / "RimDex.log").read_text()
    logger.remove()


def test_setup_logging_info_level_no_debug(tmp_path: Path) -> None:
    setup_logging(log_dir=tmp_path, debug=False)
    logger.debug("should not appear")
    logger.info("should appear")
    logger.complete()
    content = (tmp_path / "RimDex.log").read_text()
    assert "should not appear" not in content
    assert "should appear" in content
    logger.remove()


def test_setup_logging_obfuscates_paths(tmp_path: Path) -> None:
    setup_logging(log_dir=tmp_path, debug=False)
    logger.info("File at /home/john/Documents/mod.xml")
    logger.complete()
    content = (tmp_path / "RimDex.log").read_text()
    assert "/home/john/" not in content
    assert "/home/.../" in content
    logger.remove()


def test_setup_logging_rotates_existing(tmp_path: Path) -> None:
    (tmp_path / "RimDex.log").write_text("old session")
    setup_logging(log_dir=tmp_path, debug=False)
    assert (tmp_path / "RimDex.1.log").read_text() == "old session"
    logger.remove()


def test_setup_logging_exception_rendered(tmp_path: Path) -> None:
    setup_logging(log_dir=tmp_path, debug=True)
    try:
        raise ValueError("test error")
    except ValueError:
        logger.exception("caught error")
    logger.complete()
    content = (tmp_path / "RimDex.log").read_text()
    assert "ValueError" in content
    assert "test error" in content
    logger.remove()
