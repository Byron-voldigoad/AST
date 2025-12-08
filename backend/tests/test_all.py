import pytest
from backend.lexer.lexer import Lexer
from backend.parser.parser import Parser
from backend.interpreter.interpreter import Interpreter

def test_lexer():
    code = "var x: int = 10;"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    assert len(tokens) > 0
    assert tokens[0].type == 'VAR'
    assert tokens[1].type == 'IDENT'
    assert tokens[1].value == 'x'

def test_parser():
    code = "var x: int = 10;"
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    assert len(program.statements) == 1
    assert program.statements[0].name == 'x'

def test_interpreter():
    code = """
    var x: int = 10;
    var y: int = 20;
    print(x + y);
    """
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    interpreter = Interpreter()
    output = interpreter.interpret(program)
    assert output == ["30"]

def test_control_flow():
    code = """
    var i: int = 0;
    while (i < 3) {
        print(i);
        i = i + 1;
    }
    """
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    interpreter = Interpreter()
    output = interpreter.interpret(program)
    assert output == ["0", "1", "2"]

def test_function():
    code = """
    function add(a: int, b: int): int {
        return a + b;
    }
    print(add(5, 7));
    """
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    interpreter = Interpreter()
    output = interpreter.interpret(program)
    assert output == ["12"]
