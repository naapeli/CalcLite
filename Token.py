from enum import Enum
from typing import Any


class TokenType(Enum):
    EOF = "EOF"
    EXCEPTION = "EXCEPTION"

    INT = "INT"
    FLOAT = "FLOAT"
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"

    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    EXPONENT = "EXPONENT"
    MODULO = "MODULO"

    EOL = "EOL"  # end of line
    COLON = "COLON"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"

    EQUALS = "EQUALS"

    VAR = "VAR"
    FUNC = "FUNC"
    RETURN = "RETURN"

    TYPE = "TYPE"


class Token:
    def __init__(self, type: TokenType, literal: Any, line_number: int, position: int) -> None:
        self.type = type
        self.literal = literal
        self.line_number = line_number
        self.position = position
    
    def __str__(self) -> str:
        return f"literal: {repr(self.literal)}, type: {self.type}, line: {self.line_number}, position: {self.position}"
    
    def __repr__(self) -> str:
        return str(self)

KEYWORDS = {
    "var": TokenType.VAR,
    "func": TokenType.FUNC,
    "return": TokenType.RETURN,
}

TYPES = ["int", "float", "string"]

def get_identifier(identifier: str) -> TokenType:
    keyword = KEYWORDS.get(identifier)
    if keyword: return keyword
    if identifier in TYPES: return TokenType.TYPE
    return TokenType.IDENTIFIER
