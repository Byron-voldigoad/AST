try:
    from parser.nodes import Literal
    print("Nodes imported successfully.")
    l = Literal(10, 'int')
    print(f"Literal created: {l}")
except Exception as e:
    print(f"Error: {e}")
