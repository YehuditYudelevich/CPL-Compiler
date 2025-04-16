import sys
import argparse
from typing import Optional, Tuple

from main_process import Compiler  # Main compiler class


def parse_arguments() -> Tuple[str, str]:
    # Parse command-line arguments and validate the input file
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=str, help="CPL program file", default=None)
    filename = parser.parse_args().input
    validate_filename(filename, parser.prog)
    return load_source_code(filename), filename.replace(".ou", ".qud")


def validate_filename(filename: str, prog: str) -> None:
    if not filename:
        # No file provided
        sys.stderr.write(
            f"ERROR (No Input File): An input file must be provided.\n"
            f"Usage: {prog} <filename.ou>\n"
        )
        sys.exit(0)

    if not filename.endswith(".ou"):
        # Wrong file extension
        sys.stderr.write(
            'ERROR (Invalid Filename): Filenames must end with ".ou"\n'
        )
        sys.exit(0)


def load_source_code(filename: str) -> Optional[str]:
    try:
        with open(filename, "r") as file:
            return file.read()
    except IOError:
        # File not found or unreadable
        sys.stderr.write(
            f"ERROR (Input File Does Not Exist): {filename} is not a valid path.\n"
        )
        sys.exit(0)


def compile_cpl_program(source_code: str, destination_file: str) -> None:
    sys.stderr.write("Yehudit Yudelevich\n")  # Required stamp in stderr

    try:
        with Compiler(source_code, destination_file) as instance:
            output = instance.compiled_output
            if output:
                print(output, end="")  # Echo result to stdout
    except Exception as err:
        # Unexpected failure during compilation
        sys.stderr.write(f"\nAn unexpected error has occurred:\n{err}")


def main():
    try:
        code_input, output_path = parse_arguments()
        compile_cpl_program(code_input, output_path)
    except KeyboardInterrupt:
        sys.stderr.write("Process interrupted by user (CTRL+C). Terminating...\n")


if __name__ == "__main__":
    main()
