from typing import Any, Dict, List, Optional, Callable
from parser.nodes import *
import time

class Environment:
    """
    Gère la portée des variables (Scope).
    Associe des noms de variables à leurs valeurs.
    Gère aussi les portées imbriquées (via 'enclosing').
    """
    def __init__(self, enclosing: Optional['Environment'] = None):
        self.values: Dict[str, Any] = {}
        self.enclosing = enclosing

    def define(self, name: str, value: Any):
        """ Définit une nouvelle variable dans la portée actuelle """
        self.values[name] = value

    def get(self, name: str) -> Any:
        """ Récupère la valeur d'une variable (cherche aussi dans les portées parentes) """
        if name in self.values:
            return self.values[name]
        if self.enclosing:
            return self.enclosing.get(name)
        raise Exception(f"Variable non définie '{name}'.")

    def assign(self, name: str, value: Any):
        """ Modifie la valeur d'une variable existante """
        if name in self.values:
            self.values[name] = value
            return
        if self.enclosing:
            self.enclosing.assign(name, value)
            return
        raise Exception(f"Variable non définie '{name}'.")

class ReturnException(Exception):
    """ Exception utilisée pour remonter la valeur de retour d'une fonction """
    def __init__(self, value: Any):
        self.value = value

class BreakException(Exception):
    """ Exception pour gérer 'break' """
    pass

class ContinueException(Exception):
    """ Exception pour gérer 'continue' """
    pass

class Interpreter:
    """
    L'Interpréteur exécute directement l'AST.
    Il parcourt l'arbre et effectue les actions correspondantes.
    """
    def __init__(self):
        self.globals = Environment()
        self.environment = self.globals
        self.output: List[str] = []
        
        # Définition des fonctions natives
        self.globals.define("pf", self.native_print)
        self.globals.define("clock", self.native_clock)

    def native_print(self, args: List[Any]) -> None:
        self.output.append(" ".join(map(str, args)))

    def native_clock(self, args: List[Any]) -> float:
        return time.time()

    def interpret(self, program: Program) -> List[str]:
        """ Exécute tout le programme """
        self.output = []
        try:
            for statement in program.statements:
                self.execute(statement)
        except Exception as e:
            self.output.append(f"Erreur d'exécution: {e}")
        return self.output

    def execute(self, stmt: Statement):
        """ Exécute une instruction spécifique (Statement) """
        if isinstance(stmt, Block):
            self.execute_block(stmt.statements, Environment(self.environment))
        elif isinstance(stmt, VariableDecl):
            value = None
            if stmt.initializer:
                value = self.evaluate(stmt.initializer)
            self.environment.define(stmt.name, value)
        elif isinstance(stmt, FunctionDecl):
            self.environment.define(stmt.name, stmt)
        elif isinstance(stmt, IfStatement):
            if self.is_truthy(self.evaluate(stmt.condition)):
                self.execute(stmt.then_branch)
            elif stmt.else_branch:
                self.execute(stmt.else_branch)
        elif isinstance(stmt, WhileStatement):
            while self.is_truthy(self.evaluate(stmt.condition)):
                try:
                    self.execute(stmt.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
        elif isinstance(stmt, ForStatement):
            previous = self.environment
            self.environment = Environment(previous)
            try:
                if stmt.init:
                    self.execute(stmt.init)
                while True:
                    if stmt.condition:
                        if not self.is_truthy(self.evaluate(stmt.condition)):
                            break
                    try:
                        self.execute(stmt.body)
                    except BreakException:
                        break
                    except ContinueException:
                        pass
                    if stmt.update:
                        self.evaluate(stmt.update)
            finally:
                self.environment = previous
        elif isinstance(stmt, ReturnStatement):
            value = None
            if stmt.value:
                value = self.evaluate(stmt.value)
            raise ReturnException(value)
        elif isinstance(stmt, BreakStatement):
            raise BreakException()
        elif isinstance(stmt, ContinueStatement):
            raise ContinueException()
        elif isinstance(stmt, ExpressionStatement):
            self.evaluate(stmt.expression)
        else:
            raise Exception(f"Type d'instruction inconnu: {type(stmt)}")

    def execute_block(self, statements: List[Statement], environment: Environment):
        """ Exécute un bloc d'instructions dans un nouvel environnement """
        previous = self.environment
        self.environment = environment
        try:
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def evaluate(self, expr: Expression) -> Any:
        """ Évalue une expression pour obtenir sa valeur """
        if isinstance(expr, Literal):
            return expr.value
        elif isinstance(expr, Identifier):
            return self.environment.get(expr.name)
        elif isinstance(expr, Assignment):
            value = self.evaluate(expr.value)
            if isinstance(expr.target, Identifier):
                current = self.environment.get(expr.target.name)
                
                if expr.operator == '=':
                    self.environment.assign(expr.target.name, value)
                    return value
                
                # Gestion des opérateurs composés +=, -=, etc.
                if expr.operator == '+=': value = current + value
                elif expr.operator == '-=': value = current - value
                elif expr.operator == '*=': value = current * value
                elif expr.operator == '/=': value = current / value
                elif expr.operator == '%=': value = current % value
                
                self.environment.assign(expr.target.name, value)
                return value
            raise Exception("Cible d'assignation invalide.")
        elif isinstance(expr, BinaryOp):
            left = self.evaluate(expr.left)
            right = self.evaluate(expr.right)
            
            if expr.operator == 'PLUS': return left + right
            if expr.operator == 'MINUS': return left - right
            if expr.operator == 'MUL': return left * right
            if expr.operator == 'DIV': return left / right
            if expr.operator == 'MOD': return left % right
            if expr.operator == 'GREATER': return left > right
            if expr.operator == 'GREATER_EQ': return left >= right
            if expr.operator == 'LESS': return left < right
            if expr.operator == 'LESS_EQ': return left <= right
            if expr.operator == 'EQ_EQ': return left == right
            if expr.operator == 'NOT_EQ': return left != right
            if expr.operator == 'AND': return self.is_truthy(left) and self.is_truthy(right)
            if expr.operator == 'OR': return self.is_truthy(left) or self.is_truthy(right)
            
            raise Exception(f"Opérateur binaire inconnu: {expr.operator}")
        elif isinstance(expr, UnaryOp):
            right = self.evaluate(expr.operand)
            if expr.operator == 'MINUS': return -right
            if expr.operator == 'NOT': return not self.is_truthy(right)
            raise Exception(f"Opérateur unaire inconnu: {expr.operator}")
        elif isinstance(expr, FunctionCall):
            callee = self.evaluate(expr.callee)
            arguments = [self.evaluate(arg) for arg in expr.arguments]
            
            if callable(callee): # Fonction native
                return callee(arguments)
            
            if isinstance(callee, FunctionDecl):
                if len(arguments) != len(callee.params):
                    raise Exception(f"Attendait {len(callee.params)} arguments mais {len(arguments)} reçus.")
                
                environment = Environment(self.environment)
                for i, param in enumerate(callee.params):
                    environment.define(param['name'], arguments[i])
                
                try:
                    self.execute_block(callee.body.statements, environment)
                except ReturnException as r:
                    return r.value
                return None
                
            raise Exception("Ne peut appeler que des fonctions.")
        else:
            raise Exception(f"Type d'expression inconnu: {type(expr)}")

    def is_truthy(self, value: Any) -> bool:
        """ Détermine si une valeur est 'vraie' dans le contexte booléen """
        if value is None: return False
        if isinstance(value, bool): return value
        return True
