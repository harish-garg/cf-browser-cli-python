import sys

from core.cli import run_cli
from core.prompts import interactive_menu


def main():
    # If CLI arguments provided, use argparse mode
    if len(sys.argv) > 1:
        handled = run_cli()
        if handled:
            return

    # Otherwise, interactive menu
    interactive_menu()


if __name__ == "__main__":
    main()
