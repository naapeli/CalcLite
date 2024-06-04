from llvmlite import ir

from AST import Node, NodeType, Statement, Expression, Program
from AST import ExpressionStatement, VarStatement, BlockStatement, FunctionStatement, ReturnStatement, AssignStatement
from AST import IfStatement, WhileStatement
from AST import InfixExpression, CallExpression
from AST import IntegerLiteral, FloatLiteral, IdentifierLiteral, BooleanLiteral
from AST import FunctionParameter
from Environment import Environment


class Compiler:
    def __init__(self) -> None:
        self.type_map = {
            "int": ir.IntType(32),
            "float": ir.FloatType(),
            "bool": ir.IntType(1),
        }
        self.module: ir.Module = ir.Module("Main")
        self.builder: ir.IRBuilder = ir.IRBuilder()
        self.environment = Environment(records={})
        self.errors: list[str] = []
        self._initialise_builtins()
    
    def _initialise_builtins(self):
        # initialise true and false constants
        boolean_type = self.type_map["bool"]

        true_var = ir.GlobalVariable(self.module, boolean_type, "true")
        true_var.initializer = ir.Constant(boolean_type, 1)
        true_var.global_constant = True
        self.environment.define("true", true_var, true_var.type)

        false_var = ir.GlobalVariable(self.module, boolean_type, "false")
        false_var.initializer = ir.Constant(boolean_type, 0)
        false_var.global_constant = True
        self.environment.define("false", false_var, false_var.type)

        # initialise exponentiation functions
        int_exponentiation = ir.Function(self.module, ir.FunctionType(self.type_map["int"], [self.type_map["int"], self.type_map["int"]]), name="llvm.pow.i32")
        self.environment.define("int_exponentiation", int_exponentiation, self.type_map["int"])
        float_exponentiation = ir.Function(self.module, ir.FunctionType(self.type_map["float"], [self.type_map["float"], self.type_map["float"]]), name="llvm.pow.f32")
        self.environment.define("float_exponentiation", float_exponentiation, self.type_map["float"])

        # initialise print
        printf_ty = ir.FunctionType(ir.VoidType(), [ir.IntType(8).as_pointer()], var_arg=True)
        printf = ir.Function(self.module, printf_ty, name="printf")
        self.environment.define("print", printf, ir.VoidType())

        str_format = "%.10f"
        format_str_var = ir.GlobalVariable(self.module, ir.ArrayType(ir.IntType(8), len(str_format)), name=f"float_string_format")
        format_str_var.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(str_format)), bytearray(str_format.encode("utf-8")))
        self.environment.define("float_string_format", format_str_var, ir.IntType(8).as_pointer())

        str_format = "%d\n"
        format_str_var = ir.GlobalVariable(self.module, ir.ArrayType(ir.IntType(8), len(str_format)), name=f"int_string_format")
        format_str_var.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(str_format)), bytearray(str_format.encode("utf-8")))
        self.environment.define("int_string_format", format_str_var, ir.IntType(8).as_pointer())

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
            case NodeType.IfStatement:
                self._visit_if_statement(node)
            case NodeType.WhileStatement:
                self._visit_while_statement(node)

            case NodeType.InfixExpression:
                self._visit_infix_expression(node)
            case NodeType.CallExpression:
                self._visit_call_expression(node)
    
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
            case NodeType.BooleanLiteral:
                value = ir.Constant(self.type_map["bool" if value_type is None else value_type], 1 if node.value else 0)
                return value, self.type_map["bool" if value_type is None else value_type]
            
            case NodeType.InfixExpression:
                return self._visit_infix_expression(node)
            case NodeType.CallExpression:
                return self._visit_call_expression(node)

    def _visit_program(self, node: Program):
        function_type = ir.FunctionType(self.type_map["int"], [])
        main_function = ir.Function(self.module, function_type, name="main")

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
            self.environment.define(name, pointer, type)
        # if variable exists in current scope
        else:
            self.errors.append(f"Identifier {name} tried to be declared more than once.")

    def _visit_function_statement(self, node: FunctionStatement):
        name = node.name.value
        body = node.body

        parameter_names = [parameter.name for parameter in node.parameters]
        parameter_types: list[ir.Type] = [self.type_map[parameter.value_type] for parameter in node.parameters]
        return_type: ir.Type = self.type_map[node.return_type]

        function_type = ir.FunctionType(return_type, parameter_types)
        function = ir.Function(self.module, function_type, name=name)
        block = function.append_basic_block(f"{name}_entry")

        previous_builder = self.builder
        self.builder = ir.IRBuilder(block)
        previous_environment = self.environment
        self.environment = Environment({}, previous_environment)
        # define function for recursion
        self.environment.define(name, function, return_type)

        for i, parameter_type in enumerate(parameter_types):
            pointer = self.builder.alloca(parameter_type)
            self.builder.store(function.args[i], pointer)
            self.environment.define(parameter_names[i], pointer, parameter_type)

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
    
    def _visit_if_statement(self, node: IfStatement):
        test, type = self._resolve_value(node.condition)

        if node.alternative:
            with self.builder.if_else(test) as (true, otherwise):
                with true:
                    self.compile(node.consequence)
                with otherwise:
                    self.compile(node.alternative)
        else:
            with self.builder.if_then(test):
                self.compile(node.consequence)
    
    def _visit_while_statement(self, node: WhileStatement):
        current_function = self.builder.block.function
        cond_block = current_function.append_basic_block(name="cond")
        body_block = current_function.append_basic_block(name="body")
        after_block = current_function.append_basic_block(name="after")

        # condition branch
        self.builder.branch(cond_block)
        self.builder.position_at_end(cond_block)
        test, _ = self._resolve_value(node.condition)
        self.builder.cbranch(test, body_block, after_block)

        # body branch
        self.builder.position_at_end(body_block)
        self.compile(node.body)
        self.builder.branch(cond_block)

        # after loop
        self.builder.position_at_end(after_block)

    
    def _visit_infix_expression(self, node: InfixExpression) -> tuple[ir.Value, ir.Type]:
        operator = node.operator
        left_value, left_type = self._resolve_value(node.left_node)
        right_value, right_type = self._resolve_value(node.right_node)

        node_type = None
        node_value = None
        if isinstance(left_type, ir.IntType) and isinstance(right_type, ir.IntType):
            match operator:
                case "+":
                    node_value = self.builder.add(left_value, right_value)
                    node_type = self.type_map["int"]
                case "-":
                    node_value = self.builder.sub(left_value, right_value)
                    node_type = self.type_map["int"]
                case "*":
                    node_value = self.builder.mul(left_value, right_value)
                    node_type = self.type_map["int"]
                case "/":
                    node_value = self.builder.sdiv(left_value, right_value)
                    node_type = self.type_map["int"]
                case "%":
                    node_value = self.builder.srem(left_value, right_value)
                    node_type = self.type_map["int"]
                case "^":
                    function, node_type = self.environment.lookup("int_exponentiation")
                    node_value = self.builder.call(function, [left_value, right_value])
                case "<":
                    node_value = self.builder.icmp_signed("<", left_value, right_value)
                    node_type = self.type_map["bool"]
                case "<=":
                    node_value = self.builder.icmp_signed("<=", left_value, right_value)
                    node_type = self.type_map["bool"]
                case ">":
                    node_value = self.builder.icmp_signed(">", left_value, right_value)
                    node_type = self.type_map["bool"]
                case ">=":
                    node_value = self.builder.icmp_signed(">=", left_value, right_value)
                    node_type = self.type_map["bool"]
                case "==":
                    node_value = self.builder.icmp_signed("==", left_value, right_value)
                    node_type = self.type_map["bool"]
                case "!=":
                    node_value = self.builder.icmp_signed("!=", left_value, right_value)
                    node_type = self.type_map["bool"]
        elif isinstance(left_type, ir.FloatType) and isinstance(right_type, ir.FloatType):
            match operator:
                case "+":
                    node_value = self.builder.fadd(left_value, right_value)
                    node_type = self.type_map["float"]
                case "-":
                    node_value = self.builder.fsub(left_value, right_value)
                    node_type = self.type_map["float"]
                case "*":
                    node_value = self.builder.fmul(left_value, right_value)
                    node_type = self.type_map["float"]
                case "/":
                    node_value = self.builder.fdiv(left_value, right_value)
                    node_type = self.type_map["float"]
                case "%":
                    node_value = self.builder.frem(left_value, right_value)
                    node_type = self.type_map["float"]
                case "^":
                    function, node_type = self.environment.lookup("float_exponentiation")
                    node_value = self.builder.call(function, [left_value, right_value])
                case "<":
                    node_value = self.builder.fcmp_ordered("<", left_value, right_value)
                    node_type = self.type_map["bool"]
                case "<=":
                    node_value = self.builder.fcmp_ordered("<=", left_value, right_value)
                    node_type = self.type_map["bool"]
                case ">":
                    node_value = self.builder.fcmp_ordered(">", left_value, right_value)
                    node_type = self.type_map["bool"]
                case ">=":
                    node_value = self.builder.fcmp_ordered(">=", left_value, right_value)
                    node_type = self.type_map["bool"]
                case "==":
                    node_value = self.builder.fcmp_ordered("==", left_value, right_value)
                    node_type = self.type_map["bool"]
                case "!=":
                    node_value = self.builder.fcmp_ordered("!=", left_value, right_value)
                    node_type = self.type_map["bool"]
        return node_value, node_type
    
    def _visit_call_expression(self, node: CallExpression) -> tuple[ir.Value, ir.Type]:
        arguments: list[ir.Value] = []
        types: list[ir.Type] = []
        for expression in node.parameters:
            value, type = self._resolve_value(expression)
            arguments.append(value)
            types.append(type)

        match node.name.value:
            case "print":
                function, return_type = self.environment.lookup("print")
                for value, type in zip(arguments, types):
                    if type == self.type_map["int"]:
                        str_format = "%d\n"
                        format_str_var, _ = self.environment.lookup("int_string_format")
                    elif type == self.type_map["float"]:
                        # convert to double to pass to printf
                        value = self.builder.fpext(value, ir.DoubleType())
                        format_str_var, _ = self.environment.lookup("float_string_format")
                    fmt_ptr = self.builder.bitcast(format_str_var, ir.IntType(8).as_pointer())
                    return_value = self.builder.call(function, [fmt_ptr, value])

            case _:
                function, return_type = self.environment.lookup(node.name.value)
                return_value = self.builder.call(function, arguments)
        return return_value, return_type
