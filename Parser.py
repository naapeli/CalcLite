from Lexer import Lexer
from Token import Token, TokenType
from enum import Enum, auto

from AST import Statement, Expression, Program
from AST import ExpressionStatement, VarStatement, FunctionStatement, ReturnStatement, BlockStatement
from AST import InfixExpression
from AST import IntegerLiteral, FloatLiteral, IdentifierLiteral


class PrecedenceTypes(Enum):
    P_LOWEST = 0
    P_EQUALS = auto()
    P_LESSGREATER = auto()
    P_SUM = auto()
    P_PRODUCT = auto()
    P_EXPONENT = auto()
    P_PREFIX = auto()
    P_CALL = auto()
    P_INDEX = auto()


PRECEDENCES = {
    TokenType.PLUS: PrecedenceTypes.P_SUM,
    TokenType.MINUS: PrecedenceTypes.P_SUM,
    TokenType.MULTIPLY: PrecedenceTypes.P_PRODUCT,
    TokenType.DIVIDE: PrecedenceTypes.P_PRODUCT,
    TokenType.MODULO: PrecedenceTypes.P_PRODUCT,
    TokenType.EXPONENT: PrecedenceTypes.P_EXPONENT
}


class Parser:
    def __init__(self, lexer) -> None:
        self.lexer: Lexer = lexer
        self.errors = []
        self.current_token = None
        self.peek_token = None
        self.prefix_parse_functions = {
            TokenType.INT: self._parse_int_literal,
            TokenType.FLOAT: self._parse_float_literal,
            TokenType.LPAREN: self._parse_grouped_expression,
            TokenType.IDENTIFIER: self._parse_identifier,
        }
        self.infix_parse_functions = {
            TokenType.PLUS: self._parse_infix_expression,
            TokenType.MINUS: self._parse_infix_expression,
            TokenType.MULTIPLY: self._parse_infix_expression,
            TokenType.DIVIDE: self._parse_infix_expression,
            TokenType.EXPONENT: self._parse_infix_expression,
            TokenType.MODULO: self._parse_infix_expression,
        }
        self._get_next_token()
        self._get_next_token()

    def _get_next_token(self) -> None:
        self.current_token = self.peek_token
        self.peek_token = self.lexer.get_next_token()
    
    def _current_token_is(self, token_type: TokenType) -> bool:
        return self.current_token.type == token_type

    def _peek_token_is(self, token_type: TokenType) -> bool:
        return self.peek_token.type == token_type
    
    def _expect_peek(self, token_type: TokenType) -> bool:
        if self._peek_token_is(token_type):
            self._get_next_token()
            return True
        else:
            self._peek_error(token_type)
            return False
    
    def _peek_error(self, token_type: TokenType) -> None:
        self.errors.append(f"Expected {token_type}, but recieved {self.peek_token.type} instead.")

    def _no_prefix_parse_function_error(self, token_type: TokenType) -> None:
        self.errors.append(f"Prefix parse function missing for {token_type}")
    
    def _get_precidence(self, token: Token) -> PrecedenceTypes:
        precidence = PRECEDENCES.get(token.type)
        if precidence is None:
            return PrecedenceTypes.P_LOWEST
        return precidence
    
    def parse(self) -> None:
        statements = []
        while self.current_token.type != TokenType.EOF:
            if self._current_token_is(TokenType.EOL):
                # if we find an end of line token
                self._get_next_token()
                continue
                
            statement: Statement = self._parse_statement()
            if statement is not None:
                statements.append(statement)
            self._get_next_token()
        
        return Program(statements)
    
    def _parse_statement(self) -> Statement:
        match self.current_token.type:
            case TokenType.VAR:
                return self._parse_var_statement()
            case TokenType.FUNC:
                return self._parse_function_statement()
            case TokenType.RETURN:
                return self._parse_return_statement()
            case TokenType.LBRACE:
                return self._parse_block_statement()
            case _:
                return self._parse_expression_statement()

    def _parse_expression_statement(self) -> ExpressionStatement:
        expression = self._parse_expression(PrecedenceTypes.P_LOWEST)
        if self._peek_token_is(TokenType.EOL):
            self._get_next_token()
        
        statement: ExpressionStatement = ExpressionStatement(expression)
        return statement

    def _parse_var_statement(self) -> VarStatement:
        # variable
        if not self._expect_peek(TokenType.IDENTIFIER): return None
        name = IdentifierLiteral(value=self.current_token.literal)

        if not self._expect_peek(TokenType.COLON): return None

        # type
        if not self._expect_peek(TokenType.TYPE): return None
        type = self.current_token.literal

        if not self._expect_peek(TokenType.EQUALS): return None
        self._get_next_token()

        # value
        value = self._parse_expression(PrecedenceTypes.P_LOWEST)

        while not self._current_token_is(TokenType.EOL) and not self._current_token_is(TokenType.EOF):
            self._get_next_token()

        return VarStatement(name=name, value=value, value_type=type)
    
    def _parse_function_statement(self) -> FunctionStatement:
        if not self._expect_peek(TokenType.IDENTIFIER): return None
        function_name = IdentifierLiteral(self.current_token.literal)
        if not self._expect_peek(TokenType.LPAREN): return None
        parameters = [] # TODO: parse parameter list and remove checking RPAREN
        if not self._expect_peek(TokenType.RPAREN): return None
        if not self._expect_peek(TokenType.COLON): return None
        if not self._expect_peek(TokenType.TYPE): return None
        return_type = self.current_token.literal
        if not self._expect_peek(TokenType.LBRACE): return None
        body = self._parse_block_statement()

        return FunctionStatement(parameters, body, function_name, return_type)

    def _parse_return_statement(self) -> ReturnStatement:
        # skip over TokenType.RETURN
        self._get_next_token()

        return_value = self._parse_expression(PrecedenceTypes.P_LOWEST)
        if not self._expect_peek(TokenType.EOL):
            return None
        return ReturnStatement(return_value)

    def _parse_block_statement(self) -> BlockStatement:
        statements = []
        
        # skip over TokenType.LBRACE and possible end of line
        self._get_next_token()

        while not self._current_token_is(TokenType.RBRACE) and not self._current_token_is(TokenType.EOF):
            # skip possible end of line and try again
            if self._current_token_is(TokenType.EOL):
                self._get_next_token()
                continue
            statement = self._parse_statement()
            if statement is not None:
                statements.append(statement)
            self._get_next_token()

        return BlockStatement(statements)

    
    def _parse_expression(self, precedence: PrecedenceTypes) -> Expression | None:
        prefix_function = self.prefix_parse_functions.get(self.current_token.type)
        if prefix_function is None:
            self._no_prefix_parse_function_error(self.current_token.type)
            return None
        
        left_expression: Expression = prefix_function()
        while not self._peek_token_is(TokenType.EOL) and precedence.value < self._get_precidence(self.peek_token).value:
            infix_function = self.infix_parse_functions.get(self.peek_token.type)
            if infix_function is None:
                return left_expression
            self._get_next_token()

            left_expression = infix_function(left_expression)

        return left_expression

    def _parse_infix_expression(self, left_node: Expression) -> Expression:
        operator = self.current_token.literal
        precedence = self._get_precidence(self.current_token)
        self._get_next_token()
        right_node: Expression = self._parse_expression(precedence)
        infix_expression = InfixExpression(left_node=left_node, operator=operator, right_node=right_node)
        return infix_expression

    def _parse_grouped_expression(self) -> Expression:
        self._get_next_token()

        grouped_expression: Expression = self._parse_expression(PrecedenceTypes.P_LOWEST)

        if not self._expect_peek(TokenType.RPAREN):
            return None
        return grouped_expression

    def _parse_int_literal(self) -> IntegerLiteral:
        try:
            value = int(self.current_token.literal)
        except:
            self.errors.append(f"Could not parse {self.current_token.literal} as an integer.")
            return None
        return IntegerLiteral(value=value)
 
    def _parse_float_literal(self) -> FloatLiteral:
        try:
            value = float(self.current_token.literal)
        except:
            self.errors.append(f"Could not parse {self.current_token.literal} as a float.")
            return None
        return FloatLiteral(value=value)
    
    def _parse_identifier(self) -> IdentifierLiteral:
        return IdentifierLiteral(value=self.current_token.literal)
