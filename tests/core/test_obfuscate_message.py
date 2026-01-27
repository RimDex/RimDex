from app.core.obfuscate_message import obfuscate_message


def test_no_path_unchanged() -> None:
    msg = "Operation completed successfully"
    assert obfuscate_message(msg) == msg


def test_windows_user_path_anonymized() -> None:
    msg = r"C:\Users\Alice\AppData\RimWorld\Mods"
    assert obfuscate_message(msg) == r"C:\Users\...\AppData\RimWorld\Mods"


def test_windows_user_path_at_end_anonymized() -> None:
    msg = "C:\\Users\\Alice\\"
    assert obfuscate_message(msg) == "C:\\Users\\...\\"
    # Trailing username segment with no trailing content is still masked.
    assert "Alice" not in obfuscate_message(msg)


def test_linux_user_path_anonymized() -> None:
    msg = "/home/bob/steam/workshop/123"
    assert obfuscate_message(msg) == "/home/.../steam/workshop/123"


def test_non_user_path_unchanged() -> None:
    msg = r"C:\Program Files\RimWorld\Mods"
    assert obfuscate_message(msg) == msg


def test_anonymize_path_disabled_keeps_username() -> None:
    msg = r"C:\Users\Alice\AppData"
    assert obfuscate_message(msg, anonymize_path=False) == msg
