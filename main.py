import asyncio
import argparse
from pathlib import Path
import platform

from ut import get_unchecked_locations


async def main():
    parser = argparse.ArgumentParser(
        prog="checks_mix",
        description="Query multiple slots for unchecked locations using Universal Tracker.",
    )
    parser.add_argument("server", help="Archipelago server to connect to.")
    parser.add_argument(
        "-p", "--password", default=None, help="Password to use when connecting."
    )
    parser.add_argument(
        "-s",
        "--slot",
        action="append",
        help="Slot to check. Can be passed multiple times.",
    )
    parser.add_argument(
        "-a",
        "--ap-launcher",
        default=None,
        type=Path,
        help="Path to the ArchipelagoLauncher executable. Attempts to autodetect by default.",
    )
    parser.add_argument(
        "-c",
        "--count",
        action="store_true",
        help="Print the number of unchecked locations only.",
    )
    parser.add_argument(
        "-t",
        "--total",
        action="store_true",
        help="Print total number of unchecked locations",
    )

    args = parser.parse_args()

    slots: list[str] = args.slot
    server: str = args.server
    launcher: Path | None = args.ap_launcher
    password: str = args.password
    count_only: bool = args.count
    print_total: bool = args.total

    location_data = await get_unchecked_locations(
        server, slots, ap_launcher=launcher, password=password
    )

    total_locs = 0
    for slot, slot_locs in location_data.items():
        total_locs += len(slot_locs)
        print(f"{len(slot_locs)} unchecked locations for '{slot}'")
        if slot_locs and not count_only:
            print(*[f"\t{loc}" for loc in slot_locs], sep="\n")

    if print_total:
        print(f"{total_locs} total unchecked locations")


if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
