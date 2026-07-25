import sys

from app.cli.bootstrap import bootstrap


def main() -> None:

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "  python -m app.cli bootstrap"
        )

        sys.exit(1)

    command = sys.argv[1]

    if command == "bootstrap":

        bootstrap()

    else:

        print(
            f"Unknown command: {command}"
        )

        sys.exit(1)


if __name__ == "__main__":

    main()