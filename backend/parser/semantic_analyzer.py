from typing import List, Dict, Any, Optional
from parser.nodes import *

class SemanticError(Exception):
    def __init__(self, message: str, line: int = 0):
        self.message = message
        self.line = line

class SemanticAnalyzer:
    """
    Analyseur Sémantique.
    Vérifie la cohérence du code qui ne peut pas être capturée par la grammaire seule.
    Principalement : s'assurer que les variables utilisées ont bien été déclarées.
    """
    def __init__(self):
        # Initialisation de la portée globale avec les fonctions natives
        global_scope = {
            "pf": True,
            "clock": True
        }
        self.scopes: List[Dict[str, Any]] = [global_scope] 
        self.errors: List[Dict[str, Any]] = []
        
        # Types valides (primitifs + classes déclarées)
        self.declared_types = {"int", "float", "string", "bool", "char", "void"}

    def analyze(self, program: Program) -> List[Dict[str, Any]]:
        """ Lance l'analyse sémantique sur tout le programme """
        self.errors = []
        self.scopes = [{
            "pf": True,
            "clock": True
        }]
        # On réinitialise les types avec seulement les primitifs
        self.declared_types = {"int", "float", "string", "bool", "char", "void"}
        
        for stmt in program.statements:
            self.visit_statement(stmt)
        return self.errors

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
        """ Vérifie si un type existe (primitif ou classe déclarée) """
        if type_name is not None and type_name not in self.declared_types:
             self.errors.append({"message": f"Type inconnu '{type_name}'.", "line": line})

    def resolve(self, name: str) -> bool:
        """ Vérifie si une variable existe dans la portée actuelle ou parente """
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return False

    def visit_statement(self, stmt: Statement):
        if isinstance(stmt, Block):
            self.enter_scope()
            for s in stmt.statements:
                self.visit_statement(s)
            self.exit_scope()
        elif isinstance(stmt, VariableDecl):
            self.visit_expression(stmt.initializer) if stmt.initializer else None
            self.declare(stmt.name) 
            # Validation du type de la variable
            if stmt.var_type:
                line = getattr(stmt, 'line', 0)
                self.validate_type(stmt.var_type, line)
        elif isinstance(stmt, FunctionDecl):
            self.declare(stmt.name)
            
            # Validation du type de retour
            if stmt.return_type:
                line = getattr(stmt, 'line', 0)
                self.validate_type(stmt.return_type, line)
                
            self.enter_scope()
            for param in stmt.params:
                self.declare(param['name'])
                # Validation du type des paramètres
                if param['type']:
                    # Pour les params, l'endroit exact est dur à avoir sans changer 'params' en liste de Nodes
                    # On utilise la ligne de la fonction par défaut
                    line = getattr(stmt, 'line', 0) 
                    self.validate_type(param['type'], line)
                    
            self.visit_statement(stmt.body) 
            self.exit_scope()
        elif isinstance(stmt, IfStatement):
            self.visit_expression(stmt.condition)
            self.visit_statement(stmt.then_branch)
            if stmt.else_branch:
                self.visit_statement(stmt.else_branch)
        elif isinstance(stmt, WhileStatement):
            self.visit_expression(stmt.condition)
            self.visit_statement(stmt.body)
        elif isinstance(stmt, ForStatement):
            self.enter_scope()
            if stmt.init: self.visit_statement(stmt.init)
            if stmt.condition: self.visit_expression(stmt.condition)
            if stmt.update: self.visit_expression(stmt.update)
            self.visit_statement(stmt.body)
            self.exit_scope()
        elif isinstance(stmt, ReturnStatement):
            if stmt.value:
                self.visit_expression(stmt.value)
        elif isinstance(stmt, ExpressionStatement):
            self.visit_expression(stmt.expression)

    def visit_expression(self, expr: Expression):
        if isinstance(expr, BinaryOp):
            self.visit_expression(expr.left)
            self.visit_expression(expr.right)
        elif isinstance(expr, UnaryOp):
            self.visit_expression(expr.operand)
        elif isinstance(expr, Literal):
            pass
        elif isinstance(expr, Identifier):
            if not self.resolve(expr.name):
                line = getattr(expr, 'line', 0)
                self.errors.append({"message": f"Variable non définie '{expr.name}'.", "line": line})
        elif isinstance(expr, Assignment):
            self.visit_expression(expr.value)
            # Check target
            if isinstance(expr.target, Identifier):
                 if not self.resolve(expr.target.name):
                     line = getattr(expr.target, 'line', 0)
                     self.errors.append({"message": f"Variable non définie '{expr.target.name}'.", "line": line})
            else:
                self.visit_expression(expr.target)
        elif isinstance(expr, FunctionCall):
            self.visit_expression(expr.callee)
            for arg in expr.arguments:
                self.visit_expression(arg)
