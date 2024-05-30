from Lexer import Lexer
from Parser import Parser
from Compiler import Compiler
from Token import TokenType

import json
from llvmlite import ir
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float


if __name__ == "__main__":
    DEBUG_LEXER = False
    DEBUG_PARSER = True
    DEBUG_COMPILER = True

    with open("Testing/Test.txt", "r") as f:
        code = f.read()

    lexer = Lexer(code=code)
    parser = Parser(lexer=lexer)
    program = parser.parse()
    if parser.errors:
        for error in parser.errors:
            print(error)
        exit()
    compiler = Compiler()
    compiler.compile(node=program)

    module = compiler.module
    module.triple = llvm.get_default_triple()

    if DEBUG_LEXER:
        token = lexer.get_next_token()
        while True:
            print(token)
            if token.type == TokenType.EOF:
                break
            token = lexer.get_next_token()

    if DEBUG_PARSER:
        with open("Testing/AST.json", "w") as f:
            json.dump(program.json(), f, indent=2)
    
    if DEBUG_COMPILER:
        with open("Testing/assembly.txt", "w") as f:
            f.write(str(module))
