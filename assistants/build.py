import asyncio
import os
import sys

from assistants.log import logger
from assistants.user_data.sqlite_backend import migrate


def main():
    backend = os.environ.get("ASSISTANTS_DATA_LAYER", "sqlite")
    if backend == "sqlite":
        from assistants.user_data.sqlite_backend import init_db, rebuild_db
    # elif backend == "postgres":   TODO: Implement Postgres backend
    #     from assistants.user_data.postgres_backend import init_db, rebuild_db
    else:
        raise ValueError(f"Unknown backend: {backend}")

    if len(sys.argv) > 1 and sys.argv[1] == "rebuild":
        confirm = input(
            "This will delete the existing database. Are you sure you want to continue? (y/n): "
        )
        if confirm.lower() != "y":
            logger.warning("Rebuild cancelled.")
            sys.exit(0)

        asyncio.run(rebuild_db())
        logger.info("Database has been rebuilt.")
    elif len(sys.argv) > 1 and sys.argv[1] == "migrate":
        asyncio.run(migrate())
        logger.info("Database ready.")
    else:
        asyncio.run(init_db())
        logger.info("Database ready.")


if __name__ == "__main__":
    main()
