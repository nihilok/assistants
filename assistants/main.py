import asyncio
import getpass
import os
import sys
from pathlib import Path

from assistants.cli import cli
from assistants.user_data.sqlite_backend import init_db


def install():
    # Get the path to the current environment's bin directory
    bin_dir = Path(sys.prefix) / "bin"
    path_update = f"export PATH=$PATH:{bin_dir}\n"

    # Check if we need to update PATH
    path = os.environ.get("PATH", "")
    path_needs_update = str(bin_dir) not in path

    # Get API keys if not in environment variables
    openai_key = os.environ.get("OPENAI_API_KEY")
    openai_key_to_add = None
    if not openai_key:
        if (
            input("Would you like to set your OpenAI API key now? (y/N): ").lower()
            == "y"
        ):
            openai_key_to_add = getpass.getpass("Enter your OpenAI API key: ")

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    anthropic_key_to_add = None
    if not anthropic_key:
        if (
            input("Would you like to set your Anthropic API key now? (y/N): ").lower()
            == "y"
        ):
            anthropic_key_to_add = getpass.getpass("Enter your Anthropic API key: ")

    # Only proceed with RC file operations if we have something to update
    if path_needs_update or openai_key_to_add or anthropic_key_to_add:
        # Detect user's shell
        shell = os.environ.get("SHELL", "")
        if not shell:
            print("Could not determine shell type. Using ~/.profile as default")
            rc_file = Path.home() / ".profile"
        elif "zsh" in shell:
            rc_file = Path.home() / ".zshrc"
        elif "bash" in shell:
            # Check for .bash_profile first, then .bashrc
            if (Path.home() / ".bash_profile").exists():
                rc_file = Path.home() / ".bash_profile"
            else:
                rc_file = Path.home() / ".bashrc"
        else:
            # Default to .profile for other shells
            rc_file = Path.home() / ".profile"

        # Create or read the file
        if not rc_file.exists():
            rc_file.touch()
            print(f"Created {rc_file}")
            rc_content = "\n\n# Added by assistants-framework:\n"
        else:
            rc_content = rc_file.read_text()

        # Update PATH if needed
        if path_needs_update and path_update not in rc_content:
            print(f"Adding {bin_dir} to PATH in {rc_file}")
            rc_content += f"\n{path_update}"
        elif path_needs_update:
            print(f"{bin_dir} is already configured in {rc_file}")
        else:
            print(f"{bin_dir} is already in PATH")

        # Add API keys only if they were newly provided
        if openai_key_to_add:
            rc_content += f"\nexport OPENAI_API_KEY={openai_key_to_add}\n"
            print("Added OpenAI API key to configuration")
        if anthropic_key_to_add:
            rc_content += f"\nexport ANTHROPIC_API_KEY={anthropic_key_to_add}\n"
            print("Added Anthropic API key to configuration")

        # Write back to the file
        rc_file.write_text(rc_content)
        print(f"Updated {rc_file}")
        os.system("source " + str(rc_file))
    else:
        print(
            "Binaries are already on the PATH, and API keys were either not provided, or are already available."
        )
        print("No changes have been made.")

    print("Done!")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "install":
            try:
                install()
                return
            except (KeyboardInterrupt, EOFError):
                print("\nInstallation cancelled.")
                sys.exit(1)
        elif sys.argv[1] in {"build", "rebuild"}:
            from assistants.build import main as build_main

            build_main()
            return

    asyncio.run(init_db())
    cli()


if __name__ == "__main__":
    main()
