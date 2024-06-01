from llvmlite import ir

from AST import Node, NodeType, Statement, Expression, Program
from AST import ExpressionStatement, VarStatement, BlockStatement, FunctionStatement, ReturnStatement, AssignStatement
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
        self.errors: list[str] = []
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
            case NodeType.FunctionStatement:
                self._visit_function_statement(node)
            case NodeType.BlockStatement:
                self._visit_block_statement(node)
            case NodeType.ReturnStatement:
                self._visit_return_statement(node)
            case NodeType.AssignStatement:
                self._visit_assign_statement(node)

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
        # function_type = ir.FunctionType(self.type_map["int"], [])
        # main_function = ir.Function(self.module, function_type, name="main")

        # block = main_function.append_basic_block("Main function")
        # self.builder = ir.IRBuilder(block)

        for statement in node.statements:
            self.compile(statement)
        
        # return_value: ir.Constant = ir.Constant(self.type_map["int"], 0)
        # self.builder.ret(return_value)
    
    def _visit_expression_statement(self, node: ExpressionStatement):
        self.compile(node.expression)
    
    def _visit_var_statement(self, node: VarStatement):
        name = node.name.value
        value, type = self._resolve_value(node=node.value, value_type=node.value_type)

        # if variable does not exist in current scope
        if self.environment.lookup(name) is None:
            pointer = self.builder.alloca(type)
            self.builder.store(value, pointer)
            self.environment.define(name, pointer, type)
        # if variable exists in current scope
        else:
            self.errors.append(f"Identifier {name} tried to be declared more than once.")

    def _visit_function_statement(self, node: FunctionStatement):
        name = node.name.value
        body = node.body

        parameter_names = [parameter.value for parameter in node.parameters]
        parameter_types: list[ir.Type] = []
        return_type: ir.Type = self.type_map[node.return_type]

        function_type = ir.FunctionType(return_type, parameter_types)
        function = ir.Function(self.module, function_type, name=name)
        block = function.append_basic_block(f"{name}_entry")

        previous_builder = self.builder
        self.builder = ir.IRBuilder(block)
        previous_environment = self.environment
        self.environment = Environment({}, previous_environment)
        self.environment.define(name, function, return_type)

        self.compile(body)

        self.environment = previous_environment
        self.environment.define(name, function, return_type)
        self.builder = previous_builder

    def _visit_block_statement(self, node: BlockStatement):
        for statement in node.statements:
            self.compile(statement)

    def _visit_return_statement(self, node: ReturnStatement):
        value, type = self._resolve_value(node.return_value)

        self.builder.ret(value)
    
    def _visit_assign_statement(self, node: AssignStatement):
        variable_name = node.identifier.value
        value, type = self._resolve_value(node.expression)

        if self.environment.lookup(variable_name) is None:
            self.errors.append(f"Identifier {variable_name} was not declared before re-assignment.")
        else:
            pointer, type2 = self.environment.lookup(variable_name)
            if type != type2:
                self.errors.append(f"Identifier {variable_name} of type {type2} tried to be re-assigned to {type}.")
            else:
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
