from typing import List, Optional, Any, Dict
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
        # NOTE: Nous ignorons l'import_statement ici, comme demandé.
        while not self.is_at_end():
            stmt = self.declaration()
            if stmt:
                statements.append(stmt)
        return Program(statements)

    # --- Déclarations (Variables, Fonctions, Classes) ---

    def declaration(self) -> Optional[Statement]:
        """
        Détermine quel type de déclaration est en cours.
        """
        try:
            if self.match('VAR'):
                return self.variable_declaration(is_const=False)
            if self.match('CONST'):
                return self.variable_declaration(is_const=True)
            if self.match('FUNCTION'):
                return self.function_declaration()
            if self.match('CLASS'):
                return self.class_declaration()
            
            # Si ce n'est pas une déclaration, c'est une instruction classique (statement)
            return self.statement()
        except ParseError as e:
            self.synchronize()
            self.errors.append({"message": e.message, "line": e.line})
            return None

    def variable_declaration(self, is_const: bool) -> VariableDecl:
        """ Gère: var x: int = 10; OU const PI = 3.14; """
        keyword_token = self.previous()
        
        name = self.consume('IDENT', f"Nom de {'constante' if is_const else 'variable'} attendu.").value
        var_type = None
        
        if self.match('COLON'): # Typage optionnel
            var_type = self.parse_type()
        
        initializer = None
        if self.match('EQ'): # Valeur initiale
            initializer = self.expression()
        elif is_const:
            # Une constante DOIT avoir une valeur initiale (règle LNG-255)
            raise ParseError("Les constantes doivent être initialisées.", keyword_token.line)
        
        self.consume('SEMICOLON', f"Attendait ';' après la déclaration de {'constante' if is_const else 'variable'}.")
        
        node = VariableDecl(name, var_type, initializer, is_const=is_const)
        node.line = keyword_token.line
        return node
    
    # NOTE: L'ancienne fonction constant_declaration est fusionnée dans variable_declaration.
    
    def function_declaration(self) -> FunctionDecl:
        """ Gère: function add(a: int, b: int): int { ... } """
        # ... (Le code de function_declaration reste inchangé, il était déjà correct)
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
    
    # NOUVEAU: Déclaration de Classe (Point 7)
    def class_declaration(self) -> ClassDecl:
        """ Gère: class Point extends Shape { ... } """
        class_keyword = self.previous()
        name = self.consume('IDENT', "Nom de classe attendu.").value
        
        super_class = None
        if self.match('EXTENDS'):
            # La super classe doit être un simple identifiant
            super_class_name = self.consume('IDENT', "Nom de la super-classe attendu après 'extends'.").value
            super_class = Identifier(super_class_name)

        self.consume('LBRACE', "Attendait '{' avant le corps de la classe.")
        
        members = []
        while not self.check('RBRACE') and not self.is_at_end():
            if self.match('VAR'):
                # Variable de membre (pas de const dans les classes par défaut)
                members.append(self.variable_declaration(is_const=False))
            elif self.match('FUNCTION'):
                members.append(self.function_declaration())
            elif self.match('CONSTRUCTOR'):
                members.append(self.constructor_declaration())
            else:
                # Synchronisation simple en cas de membre de classe invalide
                raise ParseError(f"Membre de classe inattendu: {self.peek().type}", self.peek().line)
        
        self.consume('RBRACE', "Attendait '}' après le corps de la classe.")
        
        node = ClassDecl(name, super_class, members)
        node.line = class_keyword.line
        return node
    
    # NOUVEAU: Déclaration de Constructeur (Point 7)
    def constructor_declaration(self) -> ConstructorDecl:
        """ Gère: constructor(n) { this.name = n; } """
        self.consume('LPAREN', "Attendait '(' après 'constructor'.")
        
        parameters = []
        if not self.check('RPAREN'):
            while True:
                param_name = self.consume('IDENT', "Nom de paramètre attendu dans le constructeur.").value
                param_type = None
                if self.match('COLON'):
                    param_type = self.parse_type()
                parameters.append({"name": param_name, "type": param_type})
                if not self.match('COMMA'):
                    break
        self.consume('RPAREN', "Attendait ')' après les paramètres du constructeur.")
        
        self.consume('LBRACE', "Attendait '{' avant le corps du constructeur.")
        body = self.block()
        
        return ConstructorDecl(parameters, body)


    def parse_type(self) -> str:
        """ Analyse le type (int, float, string, bool, char, IDENT, type[], {fields}) """
        
        # Types Primitifs / Identifiants
        type_str = ""
        if self.match('TYPE_INT'): type_str = 'int'
        elif self.match('TYPE_FLOAT'): type_str = 'float'
        elif self.match('TYPE_STRING'): type_str = 'string'
        elif self.match('TYPE_BOOL'): type_str = 'bool'
        elif self.match('TYPE_CHAR'): type_str = 'char'
        elif self.match('IDENT'): type_str = self.previous().value
        elif self.check('LBRACE'):
            # Type Object/Struct { field: type, ... } (Point 5)
            return self.parse_object_type()
        else:
            raise ParseError("Type attendu", self.peek().line)
            
        # Type Tableau (type[]) (Point 5)
        if self.match('LBRACKET'):
            self.consume('RBRACKET', "Attendait ']' pour fermer la déclaration de type tableau.")
            type_str += '[]'
            
        return type_str
    
    # NOUVEAU: Parsing des types Object/Struct (Point 5)
    def parse_object_type(self) -> str:
        """ Gère le parsing d'un type objet/struct: { x: int, y: float } """
        self.consume('LBRACE', "Attendait '{' pour le type objet.")
        fields = []
        
        if not self.check('RBRACE'):
            while True:
                field_name = self.consume('IDENT', "Nom de champ attendu dans le type objet.").value
                self.consume('COLON', "Attendait ':' après le nom de champ dans le type objet.")
                field_type = self.parse_type()
                fields.append(f"{field_name}:{field_type}")
                
                if not self.match('COMMA'):
                    break
        
        self.consume('RBRACE', "Attendait '}' après la définition du type objet.")
        return '{' + ','.join(fields) + '}'

    # --- Instructions (Statements) ---

    def statement(self) -> Statement:
        """ Détermine le type d'instruction """
        # ... (Reste inchangé)
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

    # Le reste des méthodes block, if_statement, while_statement, for_statement, 
    # return_statement, break_statement, continue_statement, expression_statement
    # restent inchangées car elles étaient correctes.

    def block(self) -> Block:
        """ Gère un bloc de code entre { ... } """
        statements = []
        while not self.check('RBRACE') and not self.is_at_end():
            # Utilise self.declaration() pour permettre des déclarations locales (var, const, function, class)
            stmt = self.declaration() 
            if stmt:
                 statements.append(stmt)
        self.consume('RBRACE', "Attendait '}' après le bloc.")
        return Block(statements)

    def if_statement(self) -> IfStatement:
        keyword = self.previous()
        self.consume('LPAREN', "Attendait '(' après 'if'.")
        condition = self.expression()
        self.consume('RPAREN', "Attendait ')' après la condition du if.")
        then_branch = self.statement()
        else_branch = None
        if self.match('ELSE'):
            else_branch = self.statement()
        return IfStatement(condition, then_branch, else_branch)

    def while_statement(self) -> WhileStatement:
        self.consume('LPAREN', "Attendait '(' après 'while'.")
        condition = self.expression()
        self.consume('RPAREN', "Attendait ')' après la condition du while.")
        body = self.statement()
        return WhileStatement(condition, body)

    def for_statement(self) -> ForStatement:
        self.consume('LPAREN', "Attendait '(' après 'for'.")

        init = None
        if self.match('SEMICOLON'):
            init = None
        else:
            if self.match('VAR'):
                init = self.variable_declaration(is_const=False)
            else:
                expr = self.expression()
                self.consume('SEMICOLON', "Attendait ';' après l'initialiseur du for.")
                init = ExpressionStatement(expr)

        condition = None
        if not self.check('SEMICOLON'):
            condition = self.expression()
        self.consume('SEMICOLON', "Attendait ';' après la condition du for.")

        update = None
        if not self.check('RPAREN'):
            update = self.expression()
        self.consume('RPAREN', "Attendait ')' après les clauses du for.")

        body = self.statement()
        return ForStatement(init, condition, update, body)

    def break_statement(self) -> BreakStatement:
        self.consume('SEMICOLON', "Attendait ';' après 'break'.")
        return BreakStatement()

    def continue_statement(self) -> ContinueStatement:
        self.consume('SEMICOLON', "Attendait ';' après 'continue'.")
        return ContinueStatement()

    def expression_statement(self) -> ExpressionStatement:
        expr = self.expression()
        self.consume('SEMICOLON', "Attendait ';' après l'expression.")
        return ExpressionStatement(expr)

    def return_statement(self) -> ReturnStatement:
        value = None
        if not self.check('SEMICOLON'):
            value = self.expression()
        self.consume('SEMICOLON', "Attendait ';' après la valeur de retour.")
        return ReturnStatement(value)
    
    # ... autres statements (if, while, for, break, continue) ...

    # --- Expressions (Hiérarchie de précédence) ---

    def expression(self) -> Expression:
        return self.assignment()

    def assignment(self) -> Expression:
        """ Gère l'assignation: x = 10, obj.x = 5, arr[i] += 1 """
        # Nous n'appelons PLUS expression à ce niveau (comme logical_or), mais une expression
        # qui peut être une cible d'assignation (call, member access, index access)
        expr = self.logical_or() 
        
        if self.match('EQ', 'PLUS_EQ', 'MINUS_EQ', 'MUL_EQ', 'DIV_EQ', 'MOD_EQ'):
            operator = self.previous().type
            
            # Récursion pour l'associativité à droite: a = b = c
            value = self.assignment()
            
            # Le côté gauche DOIT être une cible d'assignation
            if isinstance(expr, Identifier) or isinstance(expr, MemberAccess) or isinstance(expr, IndexAccess):
                return Assignment(expr, operator, value)
            
            raise ParseError("Cible d'assignation invalide. Attendait identifiant, accès membre ou index.", self.peek().line)
            
        return expr

    # --- Niveau d'expression manquant (précédence) ---
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
        expr = self.comparison()
        while self.match('EQ_EQ', 'NOT_EQ'):
            operator = self.previous().type
            right = self.comparison()
            expr = BinaryOp(expr, operator, right)
        return expr

    def comparison(self) -> Expression:
        expr = self.term()
        while self.match('LESS', 'LESS_EQ', 'GREATER', 'GREATER_EQ'):
            operator = self.previous().type
            right = self.term()
            expr = BinaryOp(expr, operator, right)
        return expr

    def term(self) -> Expression:
        expr = self.factor()
        while self.match('PLUS', 'MINUS'):
            operator = self.previous().type
            right = self.factor()
            expr = BinaryOp(expr, operator, right)
        return expr

    def factor(self) -> Expression:
        expr = self.unary()
        while self.match('MUL', 'DIV', 'MOD'):
            operator = self.previous().type
            right = self.unary()
            expr = BinaryOp(expr, operator, right)
        return expr

    # Les méthodes logical_or, logical_and, equality, comparison, term, factor et unary restent inchangées.
    
    def unary(self) -> Expression:
        """ !, - (négation) """
        if self.match('NOT', 'MINUS'):
            operator = self.previous().type
            right = self.unary()
            return UnaryOp(operator, right)
        return self.call()

    # MODIFIÉ: call() gère maintenant les appels, les accès aux membres et l'indexation (post-fixés)
    def call(self) -> Expression:
        """ Gère: appel de fonction (func()), accès membre (obj.x), indexation (arr[i]) """
        expr = self.primary()
        while True:
            if self.match('LPAREN'):
                # C'est un appel de fonction/méthode
                expr = self.finish_call(expr)
            elif self.match('DOT'):
                # C'est un accès membre (obj.member)
                member_name = self.consume('IDENT', "Nom de membre attendu après '.'.").value
                expr = MemberAccess(expr, Identifier(member_name))
            elif self.match('LBRACKET'):
                # C'est un accès par index (arr[i])
                index_expr = self.expression()
                self.consume('RBRACKET', "Attendait ']' après l'index.")
                expr = IndexAccess(expr, index_expr)
            else:
                break
        return expr

    def finish_call(self, callee: Expression) -> FunctionCall:
        arguments = []
        if not self.check('RPAREN'):
            while True:
                # La grammaire LNG-255 n'a pas de limite d'arguments
                arguments.append(self.expression())
                if not self.match('COMMA'):
                    break
        self.consume('RPAREN', "Attendait ')' après les arguments.")
        return FunctionCall(callee, arguments)

    # MODIFIÉ: primary() inclut les littéraux de tableau et d'objet
    def primary(self) -> Expression:
        """ Littéraux (nombres, chaines, booléens), identifiants, groupes, tableaux, objets """
        if self.match('FALSE'): return Literal(False, 'bool')
        if self.match('TRUE'): return Literal(True, 'bool')
        if self.match('NULL'): return Literal(None, 'null')
        
        if self.match('INT'): return Literal(self.previous().value, 'int')
        if self.match('FLOAT'): return Literal(self.previous().value, 'float')
        if self.match('STRING'): return Literal(self.previous().value, 'string')
        
        if self.match('LPAREN'):
            expr = self.expression()
            self.consume('RPAREN', "Attendait ')' après l'expression.")
            return expr
        
        # NOUVEAU: Littéral de Tableau (Point 19)
        if self.match('LBRACKET'):
            return self.array_literal()
            
        # NOUVEAU: Littéral d'Objet/Struct (Point 19)
        if self.match('LBRACE'):
            return self.object_literal()
            
        if self.match('IDENT'):
            ident = Identifier(self.previous().value)
            ident.line = self.previous().line
            return ident
            
        raise ParseError(f"Expression primaire attendue, trouvé {self.peek().type}", self.peek().line)

    # NOUVEAU: Parsing des Littéraux de Tableau (Point 19)
    def array_literal(self) -> ArrayLiteral:
        """ Gère: [exp1, exp2, ...] """
        elements = []
        # On vient de consommer '['
        
        if not self.check('RBRACKET'):
            while True:
                elements.append(self.expression())
                if not self.match('COMMA'):
                    break
        
        self.consume('RBRACKET', "Attendait ']' après les éléments du tableau.")
        return ArrayLiteral(elements)

    # NOUVEAU: Parsing des Littéraux d'Objet/Struct (Point 19)
    def object_literal(self) -> ObjectLiteral:
        """ Gère: { key1: exp1, key2: exp2, ... } """
        properties = {}
        # On vient de consommer '{'
        
        if not self.check('RBRACE'):
            while True:
                # La grammaire utilise IDENT comme clé
                key = self.consume('IDENT', "Nom de clé attendu dans le littéral objet.").value
                self.consume('COLON', "Attendait ':' après la clé dans le littéral objet.")
                value = self.expression()
                properties[key] = value
                
                if not self.match('COMMA'):
                    break
        
        self.consume('RBRACE', "Attendait '}' après les propriétés de l'objet.")
        return ObjectLiteral(properties)

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
        """
        self.advance()
        current_line = self.previous().line
        
        while not self.is_at_end():
            if self.previous().type == 'SEMICOLON': return
            
            # Stop si on change de ligne (méthode heuristique)
            if self.peek().line > current_line:
                return

            if self.peek().type in ['CLASS', 'FUNCTION', 'VAR', 'CONST', 'FOR', 'IF', 'WHILE', 'RETURN']:
                return
            self.advance()