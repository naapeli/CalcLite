from Lexer import Lexer
from Parser import Parser
from Token import TokenType
import json


if __name__ == "__main__":
    DEBUG_LEXER = False
    DEBUG_PARSER = True

    with open("Testing/Test.txt", "r") as f:
        code = f.read()

    lexer = Lexer(code=code)
    parser = Parser(lexer=lexer)

    if DEBUG_LEXER:
        token = lexer.get_next_token()
        while True:
            print(token)
            if token.type == TokenType.EOF:
                break
            token = lexer.get_next_token()

    if DEBUG_PARSER:
        program = parser.parse()

        if parser.errors:
            for error in parser.errors:
                print(error)
        else:
            with open("Testing/AST.json", "w") as f:
                json.dump(program.json(), f, indent=2)
