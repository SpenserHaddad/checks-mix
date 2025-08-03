from pathlib import Path
import asyncio
from os import path
import platform

import logging

_logger = logging.getLogger("checks_mix.ut")

FILTER_LINES: set[str] = {"found cached multiworld!"}


class ApLauncherNotFoundError(Exception):
    message: str = "Could not find Archipelago Launcher"


def find_ap_launcher_path() -> Path | None:
    launcher_sub_path = Path("Archipelago") / "ArchipelagoLauncher"
    guessed_path: Path | None = None
    match platform.system():
        case "Windows":
            guessed_path = Path(path.expandvars("%PROGRAMDATA%")) / launcher_sub_path
        case "Linux":
            linux_home_ap = Path.home() / launcher_sub_path

            if linux_home_ap.is_file():
                guessed_path = linux_home_ap
            else:
                # Wild guess, try the AUR path
                guessed_path = Path("/opt") / launcher_sub_path
        case e:
            _logger.debug(f"Don't know how to find AP for {e}, giving up.")

    if guessed_path is not None and guessed_path.is_file():
        return guessed_path
    else:
        return None


async def _run_ut_command(command: list[str]) -> list[str]:
    proc = await asyncio.subprocess.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=3.0)
    except asyncio.TimeoutError as e:
        raise asyncio.TimeoutError("Failed to connect to server or slot.") from e

    return [
        line for line in stdout.decode().splitlines()[1::] if line not in FILTER_LINES
    ]


async def get_unchecked_locations(
    server: str,
    slots: list[str],
    ap_launcher: Path | None = None,
    password: str | None = None,
) -> dict[str, list[str]]:
    if not ap_launcher:
        ap_launcher = find_ap_launcher_path()
        if not ap_launcher:
            raise ApLauncherNotFoundError()

    base_command: list[str] = [
        str(ap_launcher),
        "Universal Tracker",
        "--",
        f"--connect={server}",
        "--nogui",
        "--list",
    ]

    if password:
        base_command.append(f"--password={password}")

    async with asyncio.TaskGroup() as tg:
        slot_tasks: dict[str, asyncio.Task[list[str]]] = {}
        for slot in slots:
            player_command: list[str] = base_command + [f"--name={slot}"]
            slot_tasks[slot] = tg.create_task(_run_ut_command(player_command))

    checks_per_slot: dict[str, list[str]] = {
        slot: task.result() for slot, task in slot_tasks.items()
    }
    return checks_per_slot
