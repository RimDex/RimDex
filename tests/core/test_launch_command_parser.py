from app.core.launch_command_parser import (
    ParsedLaunchCommand,
    parse_launch_command,
)


def test_empty_string() -> None:
    assert parse_launch_command("") == ParsedLaunchCommand()


def test_only_whitespace() -> None:
    assert parse_launch_command("   ") == ParsedLaunchCommand()


def test_env_var_before_command() -> None:
    result = parse_launch_command("PROTON_LOG=1 %command%")
    assert result.env_vars == {"PROTON_LOG": "1"}
    assert result.wrapper_commands == []
    assert result.game_args == []


def test_wrapper_before_command() -> None:
    result = parse_launch_command("gamemoderun %command%")
    assert result.env_vars == {}
    assert result.wrapper_commands == ["gamemoderun"]
    assert result.game_args == []


def test_env_and_wrapper_before_command() -> None:
    result = parse_launch_command("DXVK_HUD=1 gamemoderun %command% -logfile /tmp/log")
    assert result.env_vars == {"DXVK_HUD": "1"}
    assert result.wrapper_commands == ["gamemoderun"]
    assert result.game_args == ["-logfile", "/tmp/log"]


def test_game_args_after_command() -> None:
    result = parse_launch_command("%command% -logfile /tmp/log")
    assert result.env_vars == {}
    assert result.wrapper_commands == []
    assert result.game_args == ["-logfile", "/tmp/log"]


def test_no_placeholder_treated_as_game_args() -> None:
    result = parse_launch_command("--verbose --foo bar")
    assert result.env_vars == {}
    assert result.wrapper_commands == []
    assert result.game_args == ["--verbose", "--foo", "bar"]


def test_multiple_placeholders_later_are_literal_args() -> None:
    result = parse_launch_command("wrapper %command% a %command% b")
    assert result.wrapper_commands == ["wrapper"]
    assert result.game_args == ["a", "%command%", "b"]


def test_quoted_env_value_with_spaces() -> None:
    result = parse_launch_command('VAR="value with spaces" %command%')
    assert result.env_vars == {"VAR": "value with spaces"}


def test_unclosed_quote_falls_back_to_game_args() -> None:
    result = parse_launch_command('a "b')
    assert result.game_args == ['a "b']
