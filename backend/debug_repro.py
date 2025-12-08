from lexer.lexer import Lexer
from parser.parser import Parser
from parser.semantic_analyzer import SemanticAnalyzer

code = "var f: double = 12;"
print(f"Analyzing code: {code}")

try:
    print("1. Lexing...")
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    print(f"Tokens: {[t.type for t in tokens]}")

    print("2. Parsing...")
    parser = Parser(tokens)
    ast = parser.parse()
    print("Parsing complete.")
    
    print("3. Semantic Analysis...")
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(ast)
    print(f"Semantic Errors: {errors}")
    
except Exception as e:
    print(f"Error: {e}")
