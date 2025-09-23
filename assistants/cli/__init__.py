from assistants.cli.cli import CLI


def run_cli():
    """CLI entry point."""
    cli_instance = CLI()
    cli_instance.run()


__all__ = ["run_cli"]
