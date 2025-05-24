from assistants.cli.cli import CLI


def cli():
    """CLI entry point."""
    cli_instance = CLI()
    cli_instance.run()


__all__ = ["cli"]
