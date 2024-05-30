from llvmlite import ir

from AST import Node, NodeType, Statement, Expression, Program
from AST import ExpressionStatement
from AST import InfixExpression
from AST import IntegerLiteral, FloatLiteral


class Compiler:
    def __init__(self) -> None:
        self.type_map = {
            "int": ir.IntType(32),
            "float": ir.FloatType,
        }
        self.module: ir.Module = ir.Module("Main")
        self.builder: ir.IRBuilder = ir.IRBuilder()

    def compile(self, node: Node):
        match node.type():
            case NodeType.Program:
                self._visit_program(node)
            
            case NodeType.ExpressionStatement:
                self._visit_expression_statement(node)

            case NodeType.InfixExpression:
                self._visit_infix_expression(node)
    
    def _resolve_value(self, node: Expression, value_type: str = None) -> tuple[ir.Value, ir.Type]:
        match node.type():
            case NodeType.IntegerLiteral:
                node_value, node_type = node.value, self.type_map["int" if value_type is None else value_type]
                return ir.Constant(node_type, node_value), node_type
            case NodeType.FloatLiteral:
                node_value, node_type = node.value, self.type_map["float" if value_type is None else value_type]
                return ir.Constant(node_type, node_value), node_type
            
            case NodeType.InfixExpression:
                return self._visit_infix_expression(node)

    def _visit_program(self, node: Program):
        function_type = ir.FunctionType(self.type_map["int"], [])
        main_function = ir.Function(self.module, function_type, name="Main")

        block = main_function.append_basic_block("Main function")
        self.builder = ir.IRBuilder(block)

        for statement in node.statements:
            self.compile(statement)
        
        return_value: ir.Constant = ir.Constant(self.type_map["int"], 0)
        self.builder.ret(return_value)
    
    def _visit_expression_statement(self, node: ExpressionStatement):
        self.compile(node.expression)
    
    def _visit_infix_expression(self, node: InfixExpression) -> tuple[ir.Value, ir.Type]:
        operator = node.operator
        left_value, left_type = self._resolve_value(node.left_node)
        right_value, right_type = self._resolve_value(node.right_node)

        node_type = None
        node_value = None
        if isinstance(left_type, ir.IntType) and isinstance(right_type, ir.IntType):
            node_type = self.type_map["int"]
            match operator:
                case "+":
                    node_value = self.builder.add(left_value, right_value)
                case "-":
                    node_value = self.builder.sub(left_value, right_value)
                case "*":
                    node_value = self.builder.mul(left_value, right_value)
                case "/":
                    node_value = self.builder.sdiv(left_value, right_value)
        return node_value, node_type


