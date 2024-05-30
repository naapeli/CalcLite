from Token import TokenType, Token


class Lexer:
    def __init__(self, code: str) -> None:
        self.code = code
        self.position = 0
        self.line_number = 0
        self.current_character = None
        self._next_character()

    def _next_character(self) -> None:
        if self.position >= len(self.code):
            self.current_character = None
        else:
            self.current_character = self.code[self.position]
            self.position += 1
    
    def _go_previous_character(self) -> None:
        self.position -= 1
        self.current_character = self.code[self.position]
    
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
        # get back to the last digit
        if self.current_character is not None: self._go_previous_character()
        if comma_counter == 0:
            return self._create_token(TokenType.INT, int(number))
        elif comma_counter == 1:
            return self._create_token(TokenType.FLOAT, float(number))
        else:
            return self._create_token(TokenType.EXCEPTION, number)
    
    # def _is_letter(self) -> bool:
    #     return ("a" <= self.current_character and self.current_character <= "z") or ("A" <= self.current_character and self.current_character <= "Z") or self.current_character in ["å", "ä", "ö", "_"]
    
    # should not return tokenType.string
    # def _read_letter(self) -> bool:
    #     text = ""
    #     while self._is_letter():
    #         number += self.current_character
    #         self._next_character()
    #         if self.current_character is None:
    #             break
    #     if self.current_character is not None: self._go_previous_character()
    #     return self._create_token(TokenType.STRING, text)
    
    def get_next_token(self) -> Token:
        self._skip_white_space()
        token: Token | None = None

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
            case "(":
                token = self._create_token(TokenType.LPAREN, self.current_character)
            case ")":
                token = self._create_token(TokenType.RPAREN, self.current_character)
            case "\n":
                token = self._create_token(TokenType.EOL, self.current_character)
                self.line_number += 1
            case None:
                token = self._create_token(TokenType.EOF, self.current_character)
            case _:
                if self._is_number():
                    token = self._read_number()
                # elif self._is_letter(): 
                #     token = self._read_letter()
                else:
                    token = self._create_token(TokenType.EXCEPTION, self.current_character)
        self._next_character()
        return token
