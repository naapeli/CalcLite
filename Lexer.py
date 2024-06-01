from Token import TokenType, Token, get_identifier


class Lexer:
    def __init__(self, code: str) -> None:
        self.code = code
        self.position = 0
        self.line_number = 1
        self.current_character = None
        self._next_character()

    def _next_character(self) -> None:
        if self.position >= len(self.code):
            self.current_character = None
        else:
            self.current_character = self.code[self.position]
            self.position += 1

    def _peek_character(self) -> str:
        if self.position >= len(self.code): return None
        return self.code[self.position]
    
    def _skip_white_space(self) -> None:
        while self.current_character in [" ", "\t", "\r"]:
            self._next_character()
    
    def _create_token(self, type: TokenType, literal: str) -> Token:
        return Token(type, literal, self.line_number, self.position)

    def _is_number(self) -> bool:
        return "0" <= self.current_character and self.current_character <= "9"
    
    def _read_number(self) -> Token:
        number = ""
        comma_counter = 0
        while self._is_number() or self.current_character == ".":
            if self.current_character == ".":
                comma_counter += 1
            number += self.current_character
            self._next_character()
            if self.current_character is None:
                break
        if comma_counter == 0:
            return self._create_token(TokenType.INT, int(number))
        elif comma_counter == 1:
            return self._create_token(TokenType.FLOAT, float(number))
        else:
            return self._create_token(TokenType.EXCEPTION, number)
    
    def _is_letter(self) -> bool:
        return ("a" <= self.current_character and self.current_character <= "z") or ("A" <= self.current_character and self.current_character <= "Z") or self.current_character in ["å", "ä", "ö", "Å", "Ä", "Ö", "_"]
    
    def _read_identifier(self) -> str:
        start = self.position - 1
        while self.current_character is not None and (self.current_character.isalnum() or self._is_letter()):
            self._next_character()
        return self.code[start:self.position - 1]
    
    def get_next_token(self) -> Token:
        self._skip_white_space()
        token: Token | None = None

        # print(self.current_character, self.code[self.position])
        match self.current_character:
            case "+":
                token = self._create_token(TokenType.PLUS, self.current_character)
            case "-":
                token = self._create_token(TokenType.MINUS, self.current_character)
            case "*":
                token = self._create_token(TokenType.MULTIPLY, self.current_character)
            case "/":
                token = self._create_token(TokenType.DIVIDE, self.current_character)
            case "^":
                token = self._create_token(TokenType.EXPONENT, self.current_character)
            case "%":
                token = self._create_token(TokenType.MODULO, self.current_character)
            case "=":
                if self._peek_character() == "=":
                    self._next_character()
                    token = self._create_token(TokenType.DOUBLE_EQUALS, "==")
                else:
                    token = self._create_token(TokenType.EQUALS, self.current_character)
            case "<":
                if self._peek_character() == "=":
                    self._next_character()
                    token = self._create_token(TokenType.LESSTHAN_EQUALS, "<=")
                else:
                    token = self._create_token(TokenType.LESSTHAN, self.current_character)
            case ">":
                if self._peek_character() == "=":
                    self._next_character()
                    token = self._create_token(TokenType.GREATERTHAN_EQUALS, ">=")
                else:
                    token = self._create_token(TokenType.GREATERTHAN, self.current_character)
            case "!":
                if self._peek_character() == "=":
                    self._next_character()
                    token = self._create_token(TokenType.NOT_EQUALS, "!=")
                else:
                    token = self._create_token(TokenType.BANG, self.current_character)
            case ":":
                token = self._create_token(TokenType.COLON, self.current_character)
            case "(":
                token = self._create_token(TokenType.LPAREN, self.current_character)
            case ")":
                token = self._create_token(TokenType.RPAREN, self.current_character)
            case "{":
                token = self._create_token(TokenType.LBRACE, self.current_character)
            case "}":
                token = self._create_token(TokenType.RBRACE, self.current_character)
            case "\n":
                token = self._create_token(TokenType.EOL, self.current_character)
                self.line_number += 1
            case None:
                token = self._create_token(TokenType.EOF, self.current_character)
            case _:
                if self._is_number():
                    token = self._read_number()
                    return token # do not increment
                elif self._is_letter():
                    literal = self._read_identifier()
                    token_type = get_identifier(literal)
                    token = self._create_token(token_type, literal)
                    return token # do not increment
                else:
                    token = self._create_token(TokenType.EXCEPTION, self.current_character)
        self._next_character()
        return token
