# type: ignore

from sly import Lexer


class CPLScanner(Lexer):
    # the tokens
    tokens = {
        ELSE, FLOAT, IF, INPUT, INT, OUTPUT, WHILE,
        LBRACE, RBRACE, LCBRACE, RCBRACE,
        COMMA, COLON, SEMICOLON,
        ASSIGN, NUM, ID,
        RELOP, ADDOP, MULOP,
        OR, AND, NOT,
        CAST,
    }

    # ignore characters
    ignore = " \t"
    ignore_comment = r"/\*[^*]*\*+([^\/*][^*]*\*+)*\/"

    # regexes for tokens
    ELSE = r"else"
    FLOAT = r"float"
    IF = r"if"
    INPUT = r"input"
    INT = r"int"
    OUTPUT = r"output"
    WHILE = r"while"

    LCBRACE = r"\{"
    RCBRACE = r"\}"
    LBRACE = r"\("
    RBRACE = r"\)"
    COMMA = r","
    COLON = r":"
    SEMICOLON = r";"
    ASSIGN = r"="

    NUM = r"[0-9]+\.[0-9]*|[0-9]+"
    CAST = r"(static_cast<int>)|(static_cast<float>)"
    ID = r"[a-zA-Z][a-zA-Z0-9]*"
    ADDOP = r"[+-]"
    MULOP = r"[*/]"
    OR = r"\|\|"
    AND = r"&&"
    NOT = r"!"
    RELOP = r"(>=|<=|==|!=|<|>)"

    # error handling
    @_(r"\n+")
    def count_newlines(self, token):
        self.lineno += token.value.count("\n")

    # error handling
    def error(self, token):
        print(f"✘ שגיאה בשורה {self.lineno}: תו לא חוקי '{token.value[0]}'")
        self.index += 1
