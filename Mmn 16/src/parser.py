

import sys
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sly import Parser
from lexer import CPLScanner

INVALID = -1  # Used to mark expression type mismatch


# === Utility Structures ===

def is_numeric(val: str) -> bool:
    return val.replace(".", "", 1).isdigit()


@dataclass
class IDList:
    l: List[str]

@dataclass
class QuadResult:
    code: str       # Generated Quad code
    value: str      # Final value/result from the expression

@dataclass
class ErrorQueue:
    messages: List[str]

    def pop(self):
        return self.messages.pop(0)

    def push(self, msg):
        self.messages.append(msg)

    def empty(self):
        return not self.messages

    def display(self):
        while not self.empty():
            print(self.pop())


# === Main Parser ===

class CPLParser(Parser):
    tokens = CPLScanner.tokens
    start = "program"

    def __init__(self):
        self._symtab: Dict[str, str] = {}        # Symbol table: ID → Type
        self.label_counter = 0                   # For generating unique labels
        self.var_counter = 0                     # For generating temp variables
        self.error_queue = ErrorQueue([])

    def generate_tmp_id(self, typ="I"):
        # Generates fresh temp variable of the given type (I or R)
        while True:
            temp = f"t{self.var_counter}"
            self.var_counter += 1
            if temp not in self._symtab:
                self._symtab[temp] = typ
                return temp

    def generate_label(self):
        # Generates a unique label (used for jumps)
        lbl = f"L{self.label_counter}"
        self.label_counter += 1
        return lbl

    def cast(self, target_type, expression) -> QuadResult:
        # Type casting: int→float or float→int
        src_type = "R" if target_type == "I" else "I"
        tmp = self.generate_tmp_id(target_type)
        return QuadResult(f"{src_type}TO{target_type} {tmp} {expression}\n", tmp)

    def determine_prefix(self, expr: str) -> Optional[str]:
        # Gets type prefix: I or R
        if is_numeric(expr):
            return "I" if "." not in expr else "R"
        return self._symtab.get(expr)

    def determine_expr_prefix(self, line, left, right) -> str:
        # Ensures both sides of assignment have the same type
        p1 = self.determine_prefix(left)
        p2 = self.determine_prefix(right)
        if p1 != p2:
            self.error_queue.push(f"ERROR in line {line}: Operands must be of same type.")
            return INVALID
        return p1

    def prefix_with_cast(self, left, right) -> Tuple[str, int, QuadResult]:
        # Auto cast if needed (returns target type, which operand was casted, cast code)
        t1, t2 = self.determine_prefix(left), self.determine_prefix(right)
        if t1 == t2:
            return t1, 0, QuadResult("", "")
        if t1 == "I":
            return "R", 1, self.cast("R", left)
        return "R", 2, self.cast("R", right)

    def relop_to_instruction(self, a, b, op) -> QuadResult:
        # Generates Quad for relational operation
        code = ""
        prefix, index, casted = self.prefix_with_cast(a, b)
        if casted.value:
            a, b = (casted.value, b) if index == 1 else (a, casted.value)

        result = self.generate_tmp_id()
        instruction = {
            "==": f"{prefix}EQL {result} {a} {b}\n",
            "!=": f"{prefix}NQL {result} {a} {b}\n",
            "<":  f"{prefix}LSS {result} {a} {b}\n",
            ">":  f"{prefix}GRT {result} {a} {b}\n",
        }

        # Handle >= and <= using OR (eq || > or eq || <)
        if op in [">=", "<="]:
            alt = self.generate_tmp_id()
            code += instruction["=="]
            code += instruction[op[0]]  # "<" or ">"
            tmp = self.generate_or(result, alt)
            return QuadResult(casted.code + code + tmp.code, tmp.value)
        else:
            code += instruction[op]
            return QuadResult(casted.code + code, result)

    def generate_or(self, x, y) -> QuadResult:
        # Boolean OR logic: (x + y) > 0
        tmp = self.generate_tmp_id()
        return QuadResult(f"IADD {tmp} {x} {y}\nIGRT {tmp} {tmp} 0\n", tmp)

    def generate_addop(self, op, x, y):
        # Handles + / - operations with casting
        prefix, which, casted = self.prefix_with_cast(x, y)
        if casted.value:
            x, y = (casted.value, y) if which == 1 else (x, casted.value)
        tmp = self.generate_tmp_id(prefix)
        op_code = "ADD" if op == "+" else "SUB"
        return QuadResult(casted.code + f"{prefix}{op_code} {tmp} {x} {y}\n", tmp)

    def generate_mulop(self, op, x, y):
        # Handles * / operations with casting
        prefix, which, casted = self.prefix_with_cast(x, y)
        if casted.value:
            x, y = (casted.value, y) if which == 1 else (x, casted.value)
        tmp = self.generate_tmp_id(prefix)
        op_code = "MLT" if op == "*" else "DIV"
        return QuadResult(casted.code + f"{prefix}{op_code} {tmp} {x} {y}\n", tmp)

    def generate_if_stmt(self, cond_code, cond_val, true_code, false_code):
        # Generates IF ... ELSE ... block with jumps and labels
        lbl_else = self.generate_label()
        lbl_end = self.generate_label()
        code = cond_code + f"JMPZ {lbl_else} {cond_val}\n"
        code += true_code + f"JUMP {lbl_end}\n{lbl_else}:\n"
        code += false_code + f"{lbl_end}:\n"
        return QuadResult(code, "")

    def generate_while_stmt(self, cond_code, cond_val, loop_code):
        # Generates WHILE loop with jump logic
        start = self.generate_label()
        end = self.generate_label()
        code = f"JUMP {end}\n{start}:\n{loop_code}{end}:\n"
        code += cond_code
        code += f"ISUB {cond_val} 1 {cond_val}\nJMPZ {start} {cond_val}\n"
        return QuadResult(code, "")

    def error(self, p):
        # General parser error handler
        if not p:
            sys.stderr.write("ERROR: Input does not match valid CPL grammar.\n")
            return
        sys.stderr.write(f"Parsing error on line {p.lineno}\n")
        while next(self.tokens, None):
            pass
        self.restart()


    @property
    def symtab(self):
        return self._symtab

    @symtab.setter
    def symtab(self, tab):
        self._symtab = tab

    # Grammar rules according to the requirements

    @_('declarations stmt_block')
    def program(self, p):
        if not self.error_queue.empty():
            self.error_queue.display()
            return None
        return (p.stmt_block.code or "") + "HALT\n"

    @_('declarations declaration')
    def declarations(self, p):
        pass

    @_('')
    def declarations(self, p):
        pass

    @_('idlist COLON type SEMICOLON')
    def declaration(self, p):
        for identifier in p.idlist.l:
            self._symtab[identifier] = p.type

    @_('FLOAT')
    def type(self, p):
        return "R"

    @_('INT')
    def type(self, p):
        return "I"

    @_('idlist COMMA ID')
    def idlist(self, p):
        p.idlist.l.append(p.ID)
        return p.idlist

    @_('ID')
    def idlist(self, p):
        return IDList([p.ID])

    @_('assignment_stmt')
    def stmt(self, p):
        return QuadResult(p.assignment_stmt.code, "")

    @_('input_stmt')
    def stmt(self, p):
        return QuadResult(p.input_stmt.code, "")

    @_('output_stmt')
    def stmt(self, p):
        return QuadResult(p.output_stmt.code, "")

    @_('if_stmt')
    def stmt(self, p):
        return QuadResult(p.if_stmt.code, "")

    @_('while_stmt')
    def stmt(self, p):
        return QuadResult(p.while_stmt.code, "")

    @_('stmt_block')
    def stmt(self, p):
        return QuadResult(p.stmt_block.code or "", "")

    @_('ID ASSIGN expression SEMICOLON')
    def assignment_stmt(self, p):
        prefix = self.determine_expr_prefix(p.lineno, p.ID, p.expression.value)
        if prefix == INVALID:
            return QuadResult("", "")
        return QuadResult(p.expression.code + f"{prefix}ASN {p.ID} {p.expression.value}\n", "")

    @_('INPUT LBRACE ID RBRACE SEMICOLON')
    def input_stmt(self, p):
        typ = self.determine_prefix(p.ID)
        if not typ:
            self.error_queue.push(f"ERROR in line {p.lineno}: Unknown type for {p.ID}.")
            return QuadResult("", "")
        return QuadResult(f"{typ}INP {p.ID}\n", "")

    @_('OUTPUT LBRACE expression RBRACE SEMICOLON')
    def output_stmt(self, p):
        typ = self.determine_prefix(p.expression.value)
        if not typ:
            self.error_queue.push(f"ERROR in line {p.lineno}: Cannot determine type of {p.expression.value}.")
            return QuadResult("", "")
        return QuadResult(p.expression.code + f"{typ}PRT {p.expression.value}\n", "")

    @_('IF LBRACE boolexpr RBRACE stmt ELSE stmt')
    def if_stmt(self, p):
        return self.generate_if_stmt(p.boolexpr.code, p.boolexpr.value, p.stmt0.code, p.stmt1.code)

    @_('WHILE LBRACE boolexpr RBRACE stmt')
    def while_stmt(self, p):
        return self.generate_while_stmt(p.boolexpr.code, p.boolexpr.value, p.stmt.code)

    @_('LCBRACE stmtlist RCBRACE')
    def stmt_block(self, p):
        return QuadResult(p.stmtlist.code or "", "")

    @_('stmtlist stmt')
    def stmtlist(self, p):
        return QuadResult(p.stmtlist.code + p.stmt.code, "")

    @_('')
    def stmtlist(self, p):
        return QuadResult("", "")

    @_('boolexpr OR boolterm')
    def boolexpr(self, p):
        res = self.generate_or(p.boolexpr.value, p.boolterm.value)
        return QuadResult(p.boolexpr.code + p.boolterm.code + res.code, res.value)

    @_('boolterm')
    def boolexpr(self, p):
        return p.boolterm

    @_('boolterm AND boolfactor')
    def boolterm(self, p):
        tmp = self.generate_tmp_id()
        code = f"IMLT {tmp} {p.boolterm.value} {p.boolfactor.value}\n"
        return QuadResult(p.boolterm.code + p.boolfactor.code + code, tmp)

    @_('boolfactor')
    def boolterm(self, p):
        return QuadResult(p.boolfactor.code, p.boolfactor.value)

    @_('NOT LBRACE boolexpr RBRACE')
    def boolfactor(self, p):
        tmp = self.generate_tmp_id()
        return QuadResult(p.boolexpr.code + f"ISUB {tmp} 1 {p.boolexpr.value}\n", tmp)

    @_('expression RELOP expression')
    def boolfactor(self, p):
        res = self.relop_to_instruction(p.expression0.value, p.expression1.value, p.RELOP)
        return QuadResult(p.expression0.code + p.expression1.code + res.code, res.value)

    @_('expression ADDOP term')
    def expression(self, p):
        res = self.generate_addop(p.ADDOP, p.expression.value, p.term.value)
        return QuadResult(p.expression.code + p.term.code + res.code, res.value)

    @_('term')
    def expression(self, p):
        return p.term

    @_('term MULOP factor')
    def term(self, p):
        res = self.generate_mulop(p.MULOP, p.term.value, p.factor.value)
        return QuadResult(p.term.code + p.factor.code + res.code, res.value)

    @_('factor')
    def term(self, p):
        return p.factor

    @_('LBRACE expression RBRACE')
    def factor(self, p):
        return p.expression

    @_('CAST LBRACE expression RBRACE')
    def factor(self, p):
        return self.cast("I", p.expression.value) if "int" in p.CAST else self.cast("R", p.expression.value)

    @_('ID', 'NUM')
    def factor(self, p):
        return QuadResult("", p[0])
