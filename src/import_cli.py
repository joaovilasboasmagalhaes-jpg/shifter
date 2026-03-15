import argparse

try:
    from loader.loader import load_file
except ModuleNotFoundError:
    from src.loader.loader import load_file

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load shifts from a file")
    parser.add_argument("file_path", help="Path of the file to load")
    parser.add_argument("config_path", help="Path of the configuration file")
    parser.add_argument(
        "-t",
        "--file-type",
        dest="file_type",
        help="Type/format of the file being loaded",
    )
    return parser.parse_args()


def main() -> None:
    # Parse CLI arguments and pass them to the loader entrypoint.
    args = parse_args()
    load_file(args)


if __name__ == "__main__":
    main()
