"""Game launch — executable detection, process spawning, and validation.

Depends on ``app.ui.dialogue`` for user-facing warnings.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

from loguru import logger

import app.ui.dialogue as dialogue
from app.core.launch_command_parser import parse_launch_command


def get_executable_path(game_install_path: Path) -> str | None:
    """Determine the executable path for RimWorld based on the platform.

    :param game_install_path: Path to the game folder.
    :return: Executable path as string or None if not found.
    """
    system_name = platform.system()

    platform_checks = {
        "Darwin": lambda p: str(p) if p.suffix == ".app" and p.is_dir() else None,
        "Linux": lambda p: next(
            (
                str(exe)
                for exe in [
                    p / "RimWorldLinux",
                    p / "RimWorldWin64.exe",
                    p / "RimWorldWin.exe",
                ]
                if exe.exists()
                and (exe.name != "RimWorldLinux" or os.access(exe, os.X_OK))
            ),
            None,
        ),
        "Windows": lambda p: next(
            (
                str(exe)
                for exe in [p / "RimWorldWin64.exe", p / "RimWorldWin.exe"]
                if exe.exists()
            ),
            None,
        ),
    }

    check_func = platform_checks.get(system_name)
    if check_func:
        return check_func(game_install_path)
    else:
        logger.error(f"Unsupported platform for game launch: {system_name}")
        return None


def validate_game_executable(game_folder: str) -> bool:
    """Validate if the provided game folder contains a valid RimWorld executable.

    :param game_folder: Path to the game folder as a string.
    :return: True if a valid executable is found, False otherwise.
    """
    if not game_folder or not game_folder.strip():
        logger.info("Game folder path is empty or None")
        return False

    game_install_path = Path(game_folder)
    if not game_install_path.exists() or not game_install_path.is_dir():
        logger.info(
            f"Game folder does not exist or is not a directory: {game_install_path}"
        )
        return False

    executable_path = get_executable_path(game_install_path)
    if executable_path:
        logger.debug(f"Valid RimWorld executable found: {executable_path}")
        return True

    system_name = platform.system()
    logger.info(
        f"No valid RimWorld executable found for {system_name} in: {game_install_path}"
    )
    return False


def launch_game_process(game_install_path: Path, run_args: str = "") -> None:
    """Start the RimWorld game process in its own process.

    :param game_install_path: is a path to the game folder
    :param run_args: a launch command string with optional Steam-style
                     %command% syntax
    """
    from PySide6.QtCore import QCoreApplication

    if not game_install_path:
        logger.error("The path to the game folder is empty")
        dialogue.show_warning(
            title=QCoreApplication.translate(
                "launch_game_process", "Game launch failed"
            ),
            text=QCoreApplication.translate(
                "launch_game_process", "Unable to launch RimWorld"
            ),
            information=(
                QCoreApplication.translate(
                    "launch_game_process",
                    "RimDex could not start RimWorld as the game folder is empty or invalid: [{game_install_path}] "
                    "Please check that the game folder is properly set and that the RimWorld executable exists in it.",
                ).format(game_install_path=game_install_path)
            ),
        )
        return

    logger.info(f"Attempting to launch the game from folder {game_install_path}")

    executable_path = get_executable_path(game_install_path)
    if not executable_path:
        logger.error("Game executable validation failed - no valid executable found")
        dialogue.show_warning(
            title=QCoreApplication.translate(
                "launch_game_process", "Invalid game folder"
            ),
            text=QCoreApplication.translate(
                "launch_game_process", "Unable to launch RimWorld"
            ),
            information=(
                QCoreApplication.translate(
                    "launch_game_process",
                    "RimDex could not validate the RimWorld executable in the specified folder: {game_install_path}. Please check that this directory is correct and contains a valid RimWorld game executable.",
                ).format(game_install_path=game_install_path)
            ),
        )
        return

    if run_args:
        logger.info(f"Parsing launch command: {run_args}")
        parsed = parse_launch_command(run_args)
        env_vars = parsed.env_vars
        wrapper_commands = parsed.wrapper_commands
        game_args = parsed.game_args
    else:
        env_vars = {}
        wrapper_commands = []
        game_args = []

    logger.info(
        f"Launching the game with subprocess.Popen(): `{executable_path}` "
        f"with env_vars: {list(env_vars.keys())}, wrappers: {wrapper_commands}, args: {game_args}"
    )
    pid, popen_args = launch_process(
        executable_path,
        game_args,
        str(game_install_path),
        env_vars=env_vars,
        wrapper_commands=wrapper_commands,
    )
    logger.info(
        f"Launched independent RimWorld game process with PID {pid} using args {popen_args}"
    )


def launch_process(
    executable_path: str,
    args: list[str],
    cwd: str,
    env_vars: dict[str, str] | None = None,
    wrapper_commands: list[str] | None = None,
) -> tuple[int, list[str]]:
    """Launch a process with optional environment variables and wrapper executables.

    Platform-specific behavior:
    - macOS: Uses 'open' command; wrapper executables are NOT supported
    - Linux/Windows: Directly launches executable with wrapper commands prepended
    """
    pid = -1

    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
        logger.info(f"Setting environment variables: {list(env_vars.keys())}")

    wrappers = wrapper_commands or []

    if platform.system() == "Darwin":
        if wrappers:
            logger.warning(
                f"Wrapper commands are not supported on macOS: {wrappers}. "
                "These will be ignored. Use environment variables instead."
            )
        popen_args = ["open", executable_path, "--args"]
        popen_args.extend(args)
        p = subprocess.Popen(popen_args, env=env)
        pid = p.pid
    else:
        popen_args = wrappers + [executable_path]
        popen_args.extend(args)

        if sys.platform == "win32":
            p = subprocess.Popen(
                popen_args,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                shell=True,
                cwd=cwd,
                env=env,
            )
            pid = p.pid
        else:
            p = subprocess.Popen(popen_args, start_new_session=True, cwd=cwd, env=env)
            pid = p.pid
    return pid, popen_args
