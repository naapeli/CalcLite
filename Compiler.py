from llvmlite import ir

from AST import Node, NodeType, Statement, Expression, Program
from AST import ExpressionStatement, VarStatement
from AST import InfixExpression
from AST import IntegerLiteral, FloatLiteral, IdentifierLiteral
from Environment import Environment


class Compiler:
    def __init__(self) -> None:
        self.type_map = {
            "int": ir.IntType(32),
            "float": ir.FloatType(),
        }
        self.module: ir.Module = ir.Module("Main")
        self.builder: ir.IRBuilder = ir.IRBuilder()
        self.environment = Environment(records={})
        self.standard_functions = {
            "float_exponentiation": ir.Function(self.module, ir.FunctionType(self.type_map["float"], [self.type_map["float"], self.type_map["float"]]), name="llvm.pow.f32"),
            "int_exponentiation": ir.Function(self.module, ir.FunctionType(self.type_map["int"], [self.type_map["int"], self.type_map["int"]]), name="llvm.pow.i32"),
        }

    def compile(self, node: Node):
        match node.type():
            case NodeType.Program:
                self._visit_program(node)
            
            case NodeType.ExpressionStatement:
                self._visit_expression_statement(node)
            case NodeType.VarStatement:
                self._visit_var_statement(node)

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
            case NodeType.IdentifierLiteral:
                pointer, node_type = self.environment.lookup(node.value)
                # TODO: error handling if trying to load a non existent variable, function etc.???
                return self.builder.load(pointer), node_type
            
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
    
    def _visit_var_statement(self, node: VarStatement):
        name = node.name.value
        value, type = self._resolve_value(node=node.value, value_type=node.value_type)

        # if variable does not exist in current scope
        if self.environment.lookup(name) is None:
            pointer = self.builder.alloca(type)
            self.builder.store(value, pointer)
            self.environment.define(name, value, type)
        # if variable exists in current scope
        else:
            # TODO: raise an error trying to re-declare a variable???
            pointer, _ = self.environment.lookup(name)
            self.builder.store(value, pointer)
    
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
                case "%":
                    node_value = self.builder.srem(left_value, right_value)
                case "^":
                    exponentiation = self.standard_functions["int_exponentiation"]
                    node_value = self.builder.call(exponentiation, [left_value, right_value])
        elif isinstance(left_type, ir.FloatType) and isinstance(right_type, ir.FloatType):
            node_type = self.type_map["float"]
            match operator:
                case "+":
                    node_value = self.builder.fadd(left_value, right_value)
                case "-":
                    node_value = self.builder.fsub(left_value, right_value)
                case "*":
                    node_value = self.builder.fmul(left_value, right_value)
                case "/":
                    node_value = self.builder.fdiv(left_value, right_value)
                case "%":
                    node_value = self.builder.frem(left_value, right_value)
                case "^":
                    exponentiation = self.standard_functions["float_exponentiation"]
                    node_value = self.builder.call(exponentiation, [left_value, right_value])
        return node_value, node_type
