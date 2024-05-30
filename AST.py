from abc import ABC, abstractmethod
from enum import Enum


class NodeType(Enum):
    Program = "Program"

    ExpressionStatement = "ExpressionStatement"

    InfixExpression = "InfixExpression"

    IntegerLiteral = "IntegerLiteral"
    FloatLiteral = "FloatLiteral"


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

class Program(Node):
    def __init__(self) -> None:
        self.statements = []
    
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