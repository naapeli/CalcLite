from abc import ABC, abstractmethod
from enum import Enum


class NodeType(Enum):
    Program = "Program"

    ExpressionStatement = "ExpressionStatement"
    VarStatement = "VarStatement"
    FunctionStatement = "FunctionStatement"
    BlockStatement = "BlockStatement"
    ReturnStatement = "ReturnStatement"
    AssignStatement = "AssignStatement"
    IfStatement = "IfStatement"

    InfixExpression = "InfixExpression"
    CallExpression = "CallExpression"

    IntegerLiteral = "IntegerLiteral"
    FloatLiteral = "FloatLiteral"
    IdentifierLiteral = "IdentifierLiteral"
    BooleanLiteral = "BooleanLiteral"

    FunctionParameter = "FunctionParameter"


class Node:
    @abstractmethod
    def type(self) -> NodeType:
        pass

    @abstractmethod
    def json(self) -> dict:
        pass

class Statement(Node):
    pass

class Expression(Node):
    pass


class IntegerLiteral(Expression):
    def __init__(self, value: int) -> None:
        self.value = value

    def type(self) -> NodeType:
        return NodeType.IntegerLiteral
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }
    
class FloatLiteral(Expression):
    def __init__(self, value: float) -> None:
        self.value = value

    def type(self) -> NodeType:
        return NodeType.FloatLiteral
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        }

class IdentifierLiteral(Expression):
    def __init__(self, value: str) -> None:
        self.value = value

    def type(self) -> NodeType:
        return NodeType.IdentifierLiteral
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        } 

class BooleanLiteral(Expression):
    def __init__(self, value: bool) -> None:
        self.value = value

    def type(self) -> NodeType:
        return NodeType.BooleanLiteral
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "value": self.value
        } 


class Program(Node):
    def __init__(self, statements: list[Statement]) -> None:
        self.statements = statements
    
    def type(self) -> NodeType:
        return NodeType.Program

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "statements": [{statement.type().value: statement.json()} for statement in self.statements]
        }
    

class FunctionParameter(Expression):
    def __init__(self, name: str, value_type: str) -> None:
        self.name = name
        self.value_type = value_type
    
    def type(self) -> NodeType:
        return NodeType.FunctionParameter

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name,
            "value_type": self.value_type
        }
    

class ExpressionStatement(Statement):
    def __init__(self, expression: Expression) -> None:
        self.expression = expression

    def type(self) -> NodeType:
        return NodeType.ExpressionStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "expression": self.expression.json()
        }

class VarStatement(Statement):
    def __init__(self, name: IdentifierLiteral, value: Expression, value_type: str) -> None:
        self.name = name
        self.value = value
        self.value_type = value_type
    
    def type(self) -> NodeType:
        return NodeType.VarStatement
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "value": self.value.json(),
            "value_type": self.value_type
        }

class BlockStatement(Statement):
    def __init__(self, statements: list[Statement]) -> None:
        self.statements = statements
    
    def type(self) -> NodeType:
        return NodeType.BlockStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "statements": [{statement.type().value: statement.json()} for statement in self.statements]
        }
    
class ReturnStatement(Statement):
    def __init__(self, return_value: Expression) -> None:
        self.return_value = return_value
    
    def type(self) -> NodeType:
        return NodeType.ReturnStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "return_value": self.return_value.json()
        }

class FunctionStatement(Statement):
    def __init__(self, parameters: list[FunctionParameter], body: BlockStatement, name: IdentifierLiteral, return_type: str) -> None:
        self.parameters = parameters
        self.body = body
        self.name = name
        self.return_type = return_type
    
    def type(self) -> NodeType:
        return NodeType.FunctionStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "return_type": self.return_type,
            "parameters": [parameter.json() for parameter in self.parameters],
            "body": self.body.json()
        }
    
class AssignStatement(Statement):
    def __init__(self, identifier: IdentifierLiteral, expression: Expression) -> None:
        self.identifier = identifier
        self.expression = expression
    
    def type(self) -> NodeType:
        return NodeType.AssignStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "identifier": self.identifier.json(),
            "expression": self.expression.json()
        }

class IfStatement(Statement):
    def __init__(self, condition: Expression, consequence: BlockStatement, alternative: BlockStatement | None = None) -> None:
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative
    
    def type(self) -> NodeType:
        return NodeType.IfStatement

    def json(self) -> dict:
        return {
            "type": self.type().value,
            "condition": self.condition.json(),
            "consequence": self.consequence.json(),
            "alternative": self.alternative.json() if self.alternative else None
        }


class InfixExpression(Expression):
    def __init__(self, left_node: Expression, operator: str, right_node: Expression) -> None:
        self.left_node = left_node
        self.operator = operator
        self.right_node = right_node

    def type(self) -> NodeType:
        return NodeType.InfixExpression
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "left_node": self.left_node.json(),
            "operator": self.operator,
            "right_node": self.right_node.json()
        }
    
class CallExpression(Expression):
    def __init__(self, name: IdentifierLiteral, parameters: list[Expression]) -> None:
        self.name = name
        self.parameters = parameters

    def type(self) -> NodeType:
        return NodeType.CallExpression
    
    def json(self) -> dict:
        return {
            "type": self.type().value,
            "name": self.name.json(),
            "parameters": [parameter.json() for parameter in self.parameters],
        }
