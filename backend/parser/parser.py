from typing import List, Optional, Any
from lexer.lexer import Token, Lexer
from parser.nodes import *

class ParseError(Exception):
    """
    Exception personnalisée pour les erreurs de syntaxe.
    Stocke le message d'erreur et le numéro de ligne où elle s'est produite.
    """
    def __init__(self, message: str, line: int):
        self.message = message
        self.line = line
        super().__init__(f"{message} at line {line}")

class Parser:
    """
    Le Parser (Analyseur Syntaxique) transforme une liste de Tokens (mots) en un AST (Arbre Syntaxique Abstrait).
    Il utilise une méthode de 'Descente Récursive'.
    """
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens  # La liste des tokens générés par le Lexer
        self.current = 0      # L'index du token actuel qu'on regarde
        self.errors = []      # Liste pour stocker toutes les erreurs rencontrées

    def parse(self) -> Program:
        """
        Point d'entrée principal.
        Parcourt tous les tokens et crée une liste de 'Déclarations'.
        Retourne l'objet racine 'Program'.
        """
        statements = []
        while not self.is_at_end():
            stmt = self.declaration()
            if stmt:
                statements.append(stmt)
        return Program(statements)

    # --- Déclarations (Variables, Fonctions, etc.) ---

    def declaration(self) -> Optional[Statement]:
        """
        Détermine quel type de déclaration est en cours.
        Si une erreur survient, on tente de 'synchroniser' pour continuer l'analyse.
        """
        try:
            if self.match('VAR'):
                return self.variable_declaration()
            if self.match('CONST'):
                return self.constant_declaration()
            if self.match('FUNCTION'):
                return self.function_declaration()
            # Si ce n'est pas une déclaration, c'est une instruction classique (statement)
            return self.statement()
        except ParseError as e:
            self.synchronize()
            self.errors.append({"message": e.message, "line": e.line})
            return None

    def variable_declaration(self) -> VariableDecl:
        """ Gère: var x: int = 10; """
        var_keyword = self.previous() # Le token 'VAR' qui vient d'être consommé avant d'appeler cette fct
        # Mais attention, variable_declaration est appelé APRES match('VAR'). 
        # Donc self.previous() est 'VAR'.
        
        name = self.consume('IDENT', "Nom de variable attendu.").value
        var_type = None
        if self.match('COLON'): # S'il y a un ':'
            var_type = self.parse_type()
        
        initializer = None
        if self.match('EQ'): # S'il y a un '='
            initializer = self.expression()
        
        self.consume('SEMICOLON', "Attendait ';' après la déclaration de variable.")
        
        node = VariableDecl(name, var_type, initializer, is_const=False)
        node.line = var_keyword.line
        return node

    def constant_declaration(self) -> VariableDecl:
        """ Gère: const PI: float = 3.14; """
        name = self.consume('IDENT', "Nom de constante attendu.").value
        var_type = None
        if self.match('COLON'):
            var_type = self.parse_type()
        
        self.consume('EQ', "Attendait '=' après la déclaration de constante.")
        initializer = self.expression()
        
        self.consume('SEMICOLON', "Attendait ';' après la déclaration de constante.")
        return VariableDecl(name, var_type, initializer, is_const=True)

    def function_declaration(self) -> FunctionDecl:
        """ Gère: function add(a: int, b: int): int { ... } """
        name = self.consume('IDENT', "Nom de fonction attendu.").value
        self.consume('LPAREN', "Attendait '(' après le nom de la fonction.")
        parameters = []
        if not self.check('RPAREN'):
            while True:
                param_name = self.consume('IDENT', "Nom de paramètre attendu.").value
                param_type = None
                if self.match('COLON'):
                    param_type = self.parse_type()
                parameters.append({"name": param_name, "type": param_type})
                if not self.match('COMMA'):
                    break
        self.consume('RPAREN', "Attendait ')' après les paramètres.")
        
        return_type = None
        if self.match('COLON'):
            return_type = self.parse_type()
            
        self.consume('LBRACE', "Attendait '{' avant le corps de la fonction.")
        body = self.block()
        return FunctionDecl(name, parameters, return_type, body)

    def parse_type(self) -> str:
        """ Analyse le type (int, float, etc.) """
        if self.match('TYPE_INT'): return 'int'
        if self.match('TYPE_FLOAT'): return 'float'
        if self.match('TYPE_STRING'): return 'string'
        if self.match('TYPE_BOOL'): return 'bool'
        if self.match('TYPE_CHAR'): return 'char'
        if self.match('IDENT'): return self.previous().value
        raise ParseError("Type attendu", self.peek().line)

    # --- Instructions (Statements) ---

    def statement(self) -> Statement:
        """ Détermine le type d'instruction """
        if self.match('LBRACE'):
            return self.block()
        if self.match('IF'):
            return self.if_statement()
        if self.match('WHILE'):
            return self.while_statement()
        if self.match('FOR'):
            return self.for_statement()
        if self.match('RETURN'):
            return self.return_statement()
        if self.match('BREAK'):
            return self.break_statement()
        if self.match('CONTINUE'):
            return self.continue_statement()
        return self.expression_statement()

    def block(self) -> Block:
        """ Gère un bloc de code entre { ... } """
        statements = []
        while not self.check('RBRACE') and not self.is_at_end():
            statements.append(self.declaration())
        self.consume('RBRACE', "Attendait '}' après le bloc.")
        return Block(statements)

    def if_statement(self) -> IfStatement:
        """ Gère: if (condition) { ... } else { ... } """
        self.consume('LPAREN', "Attendait '(' après 'if'.")
        condition = self.expression()
        self.consume('RPAREN', "Attendait ')' après la condition if.")
        then_branch = self.statement()
        else_branch = None
        if self.match('ELSE'):
            else_branch = self.statement()
        return IfStatement(condition, then_branch, else_branch)

    def while_statement(self) -> WhileStatement:
        """ Gère: while (condition) { ... } """
        self.consume('LPAREN', "Attendait '(' après 'while'.")
        condition = self.expression()
        self.consume('RPAREN', "Attendait ')' après la condition while.")
        body = self.statement()
        return WhileStatement(condition, body)

    def for_statement(self) -> ForStatement:
        """ Gère: for (init; condition; update) { ... } """
        self.consume('LPAREN', "Attendait '(' après 'for'.")
        
        init = None
        if self.match('SEMICOLON'):
            init = None
        elif self.match('VAR'):
            init = self.variable_declaration()
        else:
            init = self.expression_statement()
            
        condition = None
        if not self.check('SEMICOLON'):
            condition = self.expression()
        self.consume('SEMICOLON', "Attendait ';' après la condition de boucle.")
        
        update = None
        if not self.check('RPAREN'):
            update = self.expression()
        self.consume('RPAREN', "Attendait ')' après les clauses for.")
        
        body = self.statement()
        return ForStatement(init, condition, update, body)

    def return_statement(self) -> ReturnStatement:
        value = None
        if not self.check('SEMICOLON'):
            value = self.expression()
        self.consume('SEMICOLON', "Attendait ';' après la valeur de retour.")
        return ReturnStatement(value)

    def break_statement(self) -> BreakStatement:
        self.consume('SEMICOLON', "Attendait ';' après 'break'.")
        return BreakStatement()

    def continue_statement(self) -> ContinueStatement:
        self.consume('SEMICOLON', "Attendait ';' après 'continue'.")
        return ContinueStatement()

    def expression_statement(self) -> ExpressionStatement:
        """ Une instruction qui est juste une expression (ex: appel de fonction) """
        expr = self.expression()
        self.consume('SEMICOLON', "Attendait ';' après l'expression.")
        return ExpressionStatement(expr)

    # --- Expressions ---

    def expression(self) -> Expression:
        return self.assignment()

    def assignment(self) -> Expression:
        """ Gère l'assignation: x = 10 """
        expr = self.logical_or()
        
        if self.match('EQ', 'PLUS_EQ', 'MINUS_EQ', 'MUL_EQ', 'DIV_EQ'):
            operator = self.previous().type
            value = self.assignment()
            if isinstance(expr, Identifier):
                return Assignment(expr, operator, value)
            raise ParseError("Cible d'assignation invalide.", self.peek().line)
            
        return expr

    def logical_or(self) -> Expression:
        expr = self.logical_and()
        while self.match('OR'):
            operator = self.previous().type
            right = self.logical_and()
            expr = BinaryOp(expr, operator, right)
        return expr

    def logical_and(self) -> Expression:
        expr = self.equality()
        while self.match('AND'):
            operator = self.previous().type
            right = self.equality()
            expr = BinaryOp(expr, operator, right)
        return expr

    def equality(self) -> Expression:
        """ ==, != """
        expr = self.comparison()
        while self.match('EQ_EQ', 'NOT_EQ'):
            operator = self.previous().type
            right = self.comparison()
            expr = BinaryOp(expr, operator, right)
        return expr

    def comparison(self) -> Expression:
        """ <, <=, >, >= """
        expr = self.term()
        while self.match('GREATER', 'GREATER_EQ', 'LESS', 'LESS_EQ'):
            operator = self.previous().type
            right = self.term()
            expr = BinaryOp(expr, operator, right)
        return expr

    def term(self) -> Expression:
        """ +, - """
        expr = self.factor()
        while self.match('MINUS', 'PLUS'):
            operator = self.previous().type
            right = self.factor()
            expr = BinaryOp(expr, operator, right)
        return expr

    def factor(self) -> Expression:
        """ *, /, % """
        expr = self.unary()
        while self.match('DIV', 'MUL', 'MOD'):
            operator = self.previous().type
            right = self.unary()
            expr = BinaryOp(expr, operator, right)
        return expr

    def unary(self) -> Expression:
        """ !, - (négation) """
        if self.match('NOT', 'MINUS'):
            operator = self.previous().type
            right = self.unary()
            return UnaryOp(operator, right)
        return self.call()

    def call(self) -> Expression:
        """ Appels de fonction: foo() """
        expr = self.primary()
        while True:
            if self.match('LPAREN'):
                expr = self.finish_call(expr)
            else:
                break
        return expr

    def finish_call(self, callee: Expression) -> FunctionCall:
        arguments = []
        if not self.check('RPAREN'):
            while True:
                arguments.append(self.expression())
                if not self.match('COMMA'):
                    break
        self.consume('RPAREN', "Attendait ')' après les arguments.")
        return FunctionCall(callee, arguments)

    def primary(self) -> Expression:
        """ Littéraux (nombres, chaines) et identifiants """
        if self.match('FALSE'): return Literal(False, 'bool')
        if self.match('TRUE'): return Literal(True, 'bool')
        if self.match('NULL'): return Literal(None, 'null')
        
        if self.match('INT'): return Literal(self.previous().value, 'int')
        if self.match('FLOAT'): return Literal(self.previous().value, 'float')
        if self.match('STRING'): return Literal(self.previous().value, 'string')
        
        if self.match('IDENT'):
            ident = Identifier(self.previous().value)
            ident.line = self.previous().line
            return ident
        
        if self.match('LPAREN'):
            expr = self.expression()
            self.consume('RPAREN', "Attendait ')' après l'expression.")
            return expr
            
        raise ParseError(f"Expression attendue, trouvé {self.peek().type}", self.peek().line)

    # --- Fonctions Utilitaires ---

    def match(self, *types) -> bool:
        """ Vérifie si le token actuel correspond à l'un des types et avance """
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def check(self, type) -> bool:
        """ Vérifie le type du token actuel sans avancer """
        if self.is_at_end(): return False
        return self.peek().type == type

    def advance(self) -> Token:
        """ Avance au prochain token """
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        """ Vérifie si on a atteint la fin du fichier """
        return self.peek().type == 'EOF'

    def peek(self) -> Token:
        """ Retourne le token actuel """
        return self.tokens[self.current]

    def previous(self) -> Token:
        """ Retourne le token précédent (celui qu'on vient de consommer) """
        return self.tokens[self.current - 1]

    def consume(self, type, message) -> Token:
        """ Avance si le type correspond, sinon lève une erreur """
        if self.check(type):
            return self.advance()
        raise ParseError(message, self.peek().line)

    def synchronize(self):
        """ 
        Méthode de récupération d'erreur.
        Avance jusqu'à trouver un point-virgule ou un début d'instruction
        pour pouvoir continuer l'analyse après une erreur.
        """
        self.advance()
        current_line = self.previous().line
        
        while not self.is_at_end():
            # Stop si on change de ligne (méthode heuristique)
            if self.peek().line > current_line:
                return

            if self.previous().type == 'SEMICOLON': return
            if self.peek().type in ['CLASS', 'FUNCTION', 'VAR', 'FOR', 'IF', 'WHILE', 'RETURN']:
                return
            self.advance()
