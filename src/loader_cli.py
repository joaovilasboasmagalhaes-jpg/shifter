import argparse

from src.loader.loader import load_file
from src.model.config import Config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import shifts from a file")
    parser.add_argument("file_path", help="Path of the file to import")
    parser.add_argument("config_path", help="Path of the configuration file")
    parser.add_argument(
        "-t",
        "--file-type",
        dest="file_type",
        help="Type/format of the file being imported",
    )
    return parser.parse_args()


def main() -> None:
    # Parse CLI arguments and pass them to the loader entrypoint.
    args = parse_args()
    Config.load_from_file(args.config_path, required_root_keys=("import",))
    load_file(args)


if __name__ == "__main__":
    main()
