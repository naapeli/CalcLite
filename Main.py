from Lexer import Lexer
from Parser import Parser
from Compiler import Compiler
from Token import TokenType

import json
from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float
from time import perf_counter


if __name__ == "__main__":
    DEBUG_LEXER = False
    DEBUG_PARSER = False
    DEBUG_COMPILER = False
    RUN_CODE = True

    with open("Testing/Test.txt", "r") as f:
        code = f.read()

    lexer = Lexer(code=code)

    if DEBUG_LEXER:
        token = lexer.get_next_token()
        while True:
            print(token)
            if token.type == TokenType.EOF:
                break
            token = lexer.get_next_token()
        exit()
    
    parser = Parser(lexer=lexer)
    program = parser.parse()
    if parser.errors:
        for error in parser.errors:
            print(error)
        exit()

    if DEBUG_PARSER:
        with open("Testing/AST.json", "w") as f:
            json.dump(program.json(), f, indent=2)
        print("AST printed succesfully")
        exit()
    
    compiler = Compiler()
    compiler.compile(node=program)
    if compiler.errors:
        for error in compiler.errors:
            print(error)
        exit()

    module = compiler.module
    module.triple = llvm.get_default_triple()
    
    if DEBUG_COMPILER:
        with open("Testing/assembly.txt", "w") as f:
            f.write(str(module))
        exit()
    
    if RUN_CODE:
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        try:
            parsed_assembly = llvm.parse_assembly(str(module))
            parsed_assembly.verify()
        except Exception as e:
            print(e)
            raise

        target_machine = llvm.Target.from_default_triple().create_target_machine()

        engine = llvm.create_mcjit_compiler(parsed_assembly, target_machine)
        engine.finalize_object()

        entry = engine.get_function_address("main")
        cfunc = CFUNCTYPE(c_int)(entry)

        start = perf_counter()

        result = cfunc()

        end = perf_counter()

        print(f"Program returned: {result}, Runtime: {end - start} ms.")
