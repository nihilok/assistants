import asyncio
import os
import sys
from pathlib import Path

from assistants.cli import cli
from assistants.user_data.sqlite_backend import init_db


def install():
    # Get the path to the current environment's bin directory
    bin_dir = Path(sys.prefix) / "bin"
    path_update = f"export PATH=$PATH:{bin_dir}\n"

    # Check that the bin directory is not in the PATH environment variable already
    # and has not already been added to the path by this script
    path = os.environ.get("PATH", "")
    if str(bin_dir) in path:
        print(f"{bin_dir} is already in PATH")
        return

    with open(Path.home() / ".profile", "r") as f:
        if path_update in f.read():
            print(f"{bin_dir} is already in PATH")
            return

    # Add the bin directory to the PATH environment variable in .profile
    print(f"Adding {bin_dir} to PATH in .profile")
    with open(Path.home() / ".profile", "a") as f:
        f.write(f"export PATH=$PATH:{bin_dir}\n")

    os.system("source ~/.profile")
    print("Done!")


def main():

    if len(sys.argv) > 1 and sys.argv[1] == "install":
        install()
        return

    asyncio.run(init_db())
    cli()


if __name__ == "__main__":
    main()
