from typing import List, Dict, Any, Optional
from parser.nodes import *

class SemanticError(Exception):
    def __init__(self, message: str, line: int = 0):
        self.message = message
        self.line = line
        super().__init__(f"{message} at line {line}")

class SemanticAnalyzer:
    """
    Analyseur Sémantique.
    Vérifie la cohérence du code qui ne peut pas être capturée par la grammaire seule.
    """
    def __init__(self):
        # Initialisation de la portée globale avec les fonctions natives (pf, clock)
        self.scopes: List[Dict[str, Any]] = [] 
        self.errors: List[Dict[str, Any]] = []
        
        # Types valides (primitifs + classes déclarées)
        self.declared_types = set()
        
        # Contexte de boucle pour valider 'break' et 'continue'
        self.in_loop = False 

    def analyze(self, program: Program) -> List[Dict[str, Any]]:
        """ Lance l'analyse sémantique sur tout le programme """
        self.errors = []
        self.in_loop = False
        
        # Réinitialisation des types et portée
        self.declared_types = {"int", "float", "string", "bool", "char", "void"}
        self.scopes = [{
            "pf": True,
            "clock": True
        }]
        
        for stmt in program.statements:
            self.visit_statement(stmt)
        return self.errors

    # --- Gestion de Portée et Types ---

    def enter_scope(self):
        """ Entre dans une nouvelle portée (ex: bloc if, while, fonction) """
        self.scopes.append({})

    def exit_scope(self):
        """ Sort de la portée actuelle """
        self.scopes.pop()

    def declare(self, name: str, line: int = 0):
        """ Enregistre une variable dans la portée actuelle """
        current_scope = self.scopes[-1]
        if name in current_scope:
            self.errors.append({"message": f"Variable '{name}' déjà déclarée dans cette portée.", "line": line})
        else:
            current_scope[name] = True
            
    def validate_type(self, type_name: str, line: int = 0):
        """ Vérifie si un type existe (primitif, classe déclarée, ou type composé) """
        if type_name is None:
            return
            
        # Simplification : vérifie le type de base (avant '[]' ou '{}')
        if type_name.endswith('[]'):
            base_type = type_name[:-2]
        elif type_name.startswith('{') and type_name.endswith('}'):
            # TODO: Vérification plus sophistiquée des types struct/objet
            base_type = "struct_type" # Marqueur temporaire
        else:
            base_type = type_name

        if base_type not in self.declared_types:
             # On ne lève pas d'erreur pour les types struct/objets pour l'instant
             if base_type != "struct_type":
                 self.errors.append({"message": f"Type inconnu '{type_name}'.", "line": line})

    def resolve(self, name: str) -> bool:
        """ Vérifie si une variable existe dans la portée actuelle ou parente """
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return False

    # --- Visiteurs de Statements ---

    def visit_statement(self, stmt: Statement):
        # Utilisation de getattr pour une gestion de ligne plus robuste si le noeud ne l'a pas
        line = getattr(stmt, 'line', 0) 
        
        if isinstance(stmt, Block):
            self.enter_scope()
            for s in stmt.statements:
                self.visit_statement(s)
            self.exit_scope()
            
        elif isinstance(stmt, VariableDecl):
            if stmt.initializer:
                self.visit_expression(stmt.initializer)
            
            # Règle 1: Vérification de l'initialisation des constantes
            if stmt.is_const and stmt.initializer is None:
                self.errors.append({"message": f"La constante '{stmt.name}' doit être initialisée.", "line": line})
                
            self.declare(stmt.name, line)
            if stmt.var_type:
                self.validate_type(stmt.var_type, line)
                
        elif isinstance(stmt, FunctionDecl):
            self.declare(stmt.name, line)
            
            if stmt.return_type:
                self.validate_type(stmt.return_type, line)
            
            self.enter_scope()
            # Valider et déclarer les paramètres
            for param in stmt.params:
                self.declare(param['name'], line) # Utilisation de la ligne de fonction pour l'erreur
                if param['type']:
                    self.validate_type(param['type'], line)
                    
            self.visit_statement(stmt.body) 
            self.exit_scope()
            
        # NOUVEAU: Visiteur de Classe
        elif isinstance(stmt, ClassDecl):
            self.declare(stmt.name, line) # Déclare le nom de la classe
            self.declared_types.add(stmt.name) # Ajoute le nom de la classe aux types valides
            
            if stmt.super_class:
                # Vérifie si la super-classe existe
                if stmt.super_class.name not in self.declared_types:
                    self.errors.append({"message": f"La super-classe '{stmt.super_class.name}' n'est pas définie.", "line": line})
            
            self.enter_scope() # Portée de la classe
            # Parcours des membres
            for member in stmt.members:
                if isinstance(member, ConstructorDecl):
                    self.visit_constructor(member, line)
                elif isinstance(member, FunctionDecl):
                    # Les méthodes sont déclarées dans la portée de la classe (implicitement)
                    self.visit_statement(member) 
                elif isinstance(member, VariableDecl):
                    # Les champs sont déclarés dans la portée de la classe
                    self.visit_statement(member) 
                else:
                    self.errors.append({"message": "Membre de classe invalide.", "line": line})
            
            self.exit_scope()
            
        elif isinstance(stmt, IfStatement):
            self.visit_expression(stmt.condition)
            self.visit_statement(stmt.then_branch)
            if stmt.else_branch:
                self.visit_statement(stmt.else_branch)
                
        # MODIFIÉ: Ajout de la gestion du contexte de boucle
        elif isinstance(stmt, (WhileStatement, ForStatement)):
            was_in_loop = self.in_loop
            self.in_loop = True
            
            if isinstance(stmt, WhileStatement):
                self.visit_expression(stmt.condition)
            elif isinstance(stmt, ForStatement):
                self.enter_scope()
                if stmt.init: self.visit_statement(stmt.init)
                if stmt.condition: self.visit_expression(stmt.condition)
                if stmt.update: self.visit_expression(stmt.update)
            
            self.visit_statement(stmt.body)
            
            if isinstance(stmt, ForStatement):
                self.exit_scope()
                
            self.in_loop = was_in_loop
            
        # NOUVEAU: Visiteur de Break/Continue
        elif isinstance(stmt, (BreakStatement, ContinueStatement)):
            # Règle 3: Vérification du contexte de boucle
            if not self.in_loop:
                keyword = 'break' if isinstance(stmt, BreakStatement) else 'continue'
                self.errors.append({"message": f"'{keyword}' doit être utilisé dans une boucle.", "line": line})

        elif isinstance(stmt, ReturnStatement):
            if stmt.value:
                self.visit_expression(stmt.value)
                
        elif isinstance(stmt, ExpressionStatement):
            self.visit_expression(stmt.expression)
            
    # NOUVEAU: Visiteur de Constructeur
    def visit_constructor(self, ctor: ConstructorDecl, class_line: int):
        # Un constructeur agit comme une fonction (nouvelle portée pour les paramètres)
        self.enter_scope() 
        # Valider et déclarer les paramètres
        for param in ctor.params:
            self.declare(param['name'], class_line) 
            if param['type']:
                self.validate_type(param['type'], class_line)
                
        self.visit_statement(ctor.body)
        self.exit_scope()

    # --- Visiteurs d'Expressions ---

    def visit_expression(self, expr: Expression):
        line = getattr(expr, 'line', 0)
        
        if isinstance(expr, BinaryOp):
            self.visit_expression(expr.left)
            self.visit_expression(expr.right)
            # TODO: Vérification des types d'opérandes (ex: int + string)
        elif isinstance(expr, UnaryOp):
            self.visit_expression(expr.operand)
        elif isinstance(expr, Literal):
            pass
            
        elif isinstance(expr, Identifier):
            if not self.resolve(expr.name):
                self.errors.append({"message": f"Variable non définie '{expr.name}'.", "line": line})
                
        elif isinstance(expr, Assignment):
            self.visit_expression(expr.value)
            
            # Règle 4: Vérification de la cible d'assignation
            target = expr.target
            if isinstance(target, Identifier):
                if not self.resolve(target.name):
                    self.errors.append({"message": f"Variable non définie '{target.name}'.", "line": line})
                # TODO: Vérification si l'identifiant n'est pas une constante (const)
            elif isinstance(target, (MemberAccess, IndexAccess)):
                self.visit_expression(target) # Visiter l'accès (qui validera les sous-expressions/résolution)
            else:
                self.errors.append({"message": "Cible d'assignation invalide (doit être un identifiant ou un accès).", "line": line})

        elif isinstance(expr, FunctionCall):
            self.visit_expression(expr.callee)
            for arg in expr.arguments:
                self.visit_expression(arg)
        
        # NOUVEAU: Visiteur d'Accès aux Membres (obj.member)
        elif isinstance(expr, MemberAccess):
            # Règle 5: Valider l'expression cible (obj)
            self.visit_expression(expr.target)
            # NOTE: La vérification de l'existence du membre (expr.member) nécessite une table de symboles de type plus avancée (classes/structs), non implémentée ici.
            
        # NOUVEAU: Visiteur d'Accès par Index (arr[index])
        elif isinstance(expr, IndexAccess):
            # Règle 5: Valider l'expression cible (arr) et l'index
            self.visit_expression(expr.target)
            self.visit_expression(expr.index)
            # TODO: Vérification de type (si target est un tableau/objet indexable et si index est un entier)
            
        # NOUVEAU: Visiteur de Littéraux Composés
        elif isinstance(expr, ArrayLiteral):
            for element in expr.elements:
                self.visit_expression(element)
                
        elif isinstance(expr, ObjectLiteral):
            for key, value_expr in expr.properties.items():
                self.visit_expression(value_expr)