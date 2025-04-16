import sys
from typing import List

from lexer import *      # lexer
from parser import *      # parser & codegen


class Compiler:
    def __init__(self, source_code: str, target_file: str):
        self._src = source_code                # Source CPL code
        self._target = target_file             # Target .qud file path
        self._lexer = CPLScanner()
        self._parser = CPLParser()
        self._compiled_code = ""

    def __enter__(self):
        self._compile()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # If exception occurred during compilation
            sys.stderr.write(
                f"Compilation failed for {self.target_path}.\n"
                f"Refer to stderr for error details.\n"
            )
            return

        if self.compiled_output == "":
            # Compilation completed but produced no output
            sys.stderr.write(
                "Compilation did not produce output. Skipping file creation.\n"
                "Check logs for potential errors.\n"
            )
            return

        self._write_output()

    def _compile(self):
        lexed = self._lexer.tokenize(self._src)
        self._compiled_code = self._parser.parse(lexed)

    def _write_output(self):
        with open(self.target_path, "w") as out_file:
            out_file.write(self.compiled_output)
            out_file.write("\nYehudit Yudelevich, ID: 325905628")  # Footer for identification

    @property
    def compiled_output(self) -> str:
        return self._compiled_code

    @property
    def target_path(self) -> str:
        return self._target
