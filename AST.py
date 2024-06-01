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

    InfixExpression = "InfixExpression"

    IntegerLiteral = "IntegerLiteral"
    FloatLiteral = "FloatLiteral"
    IdentifierLiteral = "IdentifierLiteral"


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
    def __init__(self, parameters: list[IdentifierLiteral], body: BlockStatement, name: IdentifierLiteral, return_type: str) -> None:
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
