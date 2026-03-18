import sys
from dotenv import load_dotenv

load_dotenv()

from browserflare.exceptions import MissingCredentialsError
from cli import run_cli
from prompts import interactive_menu


def main():
    try:
        # If CLI arguments provided, use argparse mode
        if len(sys.argv) > 1:
            handled = run_cli()
            if handled:
                return

        # Otherwise, interactive menu
        interactive_menu()
    except MissingCredentialsError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
