from Lexer import Lexer
from Token import TokenType


if __name__ == "__main__":
    DEBUG_LEXEL = True

    with open("Test.txt", "r") as f:
        code = f.read()

    lexer = Lexer(code)

    if DEBUG_LEXEL:
        token = lexer.get_next_token()
        while True:
            print(token)
            if token.type == TokenType.EOF:
                break
            token = lexer.get_next_token()
