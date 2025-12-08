from parser.parser import Parser
from parser.semantic_analyzer import SemanticAnalyzer
from parser.nodes import Program
from lexer.lexer import Lexer

def analyze_code(code):
    print(f"Analyzing: {code.strip()}")
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(ast)
    if errors:
        print(f"Errors: {errors}")
    else:
        print("Success: No errors.")
    print("-" * 20)

# Test 1: Should succeed (pf is defined)
analyze_code("pf(12);")

# Test 2: Should fail (print is no longer defined)
analyze_code("print(12);")
