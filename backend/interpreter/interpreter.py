from typing import Any, Dict, List, Optional, Callable
from parser.nodes import *
import time

# ====================================================================
# 1. CLASSES FONDAMENTALES (Environment et Exceptions)
# ====================================================================

class Environment:
    """
    Gère la portée des variables (Scope).
    Gère les portées imbriquées (via 'enclosing').
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
            # TODO: Ajouter la vérification si la variable est une const (VariableDecl.is_const)
            # Cette information n'est pas portée par l'Environment simple, une refonte serait nécessaire 
            # pour un support complet des 'const'. Pour l'instant, l'assignation passe.
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

# ====================================================================
# 2. CLASSES D'EXÉCUTION (LNGClass et LNGInstance)
# ====================================================================

class LNGClass:
    """ Représente une classe définie dans le programme (runtimes class) """
    def __init__(self, name: str, super_class: Optional['LNGClass'], methods: Dict[str, FunctionDecl], constructor: Optional[ConstructorDecl], interpreter: 'Interpreter'):
        self.name = name
        self.super_class = super_class
        self.methods = methods 
        self.constructor = constructor
        self.interpreter = interpreter

    def find_method(self, name: str) -> Optional[FunctionDecl]:
        """ Cherche une méthode dans la classe ou dans la super-classe """
        if name in self.methods:
            return self.methods[name]
        if self.super_class:
            return self.super_class.find_method(name)
        return None
    
    def __call__(self, arguments: List[Any]) -> 'LNGInstance':
        """ Permet d'appeler la classe (Class()) pour créer une instance """
        instance = LNGInstance(self)
        
        # 1. Exécuter le constructeur (s'il existe)
        if self.constructor:
            # Créer un environnement pour l'instance, avec accès à 'this'
            environment = Environment(self.interpreter.environment) 
            environment.define("this", instance)
            
            if len(arguments) != len(self.constructor.params):
                raise Exception(f"Constructeur de {self.name} attendait {len(self.constructor.params)} arguments mais {len(arguments)} reçus.")

            for i, param in enumerate(self.constructor.params):
                environment.define(param['name'], arguments[i])
            
            # Exécution
            try:
                self.interpreter.execute_block(self.constructor.body.statements, environment)
            except ReturnException as r:
                # Dans un constructeur, 'return' sans valeur est implicitement autorisé 
                # (ou on lève une exception s'il y a une valeur explicite retournée, comme dans Lox)
                if r.value is not None:
                     raise Exception(f"Ne peut pas retourner de valeur depuis un constructeur.")

        return instance

    def __str__(self):
        return f"<class {self.name}>"

class LNGInstance:
    """ Représente une instance d'une classe (runtimes instance) """
    def __init__(self, klass: LNGClass):
        self.klass = klass
        self.fields: Dict[str, Any] = {} # Pour stocker les champs (variables d'instance)

    def get_field(self, name: str) -> Any:
        """ Récupère la valeur d'un champ ou l'objet représentant une méthode """
        if name in self.fields:
            return self.fields[name]
        
        # Chercher la méthode
        method = self.klass.find_method(name)
        if method:
            # Retourner une fonction liée (closure)
            return self.bind_method(method) 

        raise Exception(f"Propriété non définie '{name}' sur l'objet de type {self.klass.name}.")

    def set_field(self, name: str, value: Any):
        """ Définit/modifie la valeur d'un champ """
        self.fields[name] = value
        
    def bind_method(self, method: FunctionDecl) -> Callable:
        """ Crée une closure pour lier 'this' à la méthode """
        
        def bound_method(args: List[Any]) -> Any:
            
            env = Environment(self.klass.interpreter.environment) 
            env.define("this", self) 
            
            if len(args) != len(method.params):
                raise Exception(f"Méthode {method.name} attendait {len(method.params)} arguments mais {len(args)} reçus.")

            for i, param in enumerate(method.params):
                env.define(param['name'], args[i])

            try:
                self.klass.interpreter.execute_block(method.body.statements, env)
            except ReturnException as r:
                return r.value
            return None 
            
        return bound_method

    def __str__(self):
        return f"<instance of {self.klass.name}>"

# ====================================================================
# 3. INTERPRETER
# ====================================================================

class Interpreter:
    """
    L'Interpréteur exécute directement l'AST.
    """
    def __init__(self, max_depth: int = 1000):
        self.globals = Environment()
        self.environment = self.globals
        self.output: List[str] = []
        self.max_depth = max_depth
        self.call_depth = 0
        
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
        self.environment = self.globals 
        try:
            for statement in program.statements:
                self.execute(statement)
        except Exception as e:
            self.output.append(f"Erreur d'exécution: {e}")
        return self.output

    # --- Visiteurs de Statements ---

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
            
        elif isinstance(stmt, ClassDecl):
            methods: Dict[str, FunctionDecl] = {}
            constructor: Optional[ConstructorDecl] = None
            
            for member in stmt.members:
                if isinstance(member, FunctionDecl):
                    methods[member.name] = member
                elif isinstance(member, ConstructorDecl):
                    constructor = member
                    
            super_class_val = None
            if stmt.super_class:
                super_class_val = self.environment.get(stmt.super_class.name)
                if not isinstance(super_class_val, LNGClass):
                    raise Exception(f"La super-classe '{stmt.super_class.name}' n'est pas une classe.")
                    
            klass = LNGClass(stmt.name, super_class_val, methods, constructor, self)
            self.environment.define(stmt.name, klass)
            
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

    # --- Visiteurs d'Expressions ---

    def evaluate(self, expr: Expression) -> Any:
        """ Évalue une expression pour obtenir sa valeur """
        
        if isinstance(expr, Literal):
            return expr.value
        
        elif isinstance(expr, Identifier):
            return self.environment.get(expr.name)
        
        elif isinstance(expr, Assignment):
            value = self.evaluate(expr.value)
            target = expr.target
            
            # --- CORRECTION MAJEURE: Utilisation des noms de tokens pour l'opérateur ---
            
            # 1. Cas simple: Identifier (x = 10, x += 5)
            if isinstance(target, Identifier):
                # Assignation simple '=' devient 'EQ'
                if expr.operator == 'EQ': # 🟢 CORRECTION
                    self.environment.assign(target.name, value)
                    return value
                
                # Gestion des opérateurs composés
                current = self.environment.get(target.name)
                
                if expr.operator == 'PLUS_EQ': value = current + value # 🟢 CORRECTION
                elif expr.operator == 'MINUS_EQ': value = current - value # 🟢 CORRECTION
                elif expr.operator == 'MUL_EQ': value = current * value # 🟢 CORRECTION
                elif expr.operator == 'DIV_EQ': value = current / value # 🟢 CORRECTION
                elif expr.operator == 'MOD_EQ': value = current % value # 🟢 CORRECTION
                else:
                    raise Exception(f"Opérateur d'assignation inconnu: {expr.operator}")
                
                self.environment.assign(target.name, value)
                return value
            
            # 2. Cas complexe: Membre (obj.x = 10, obj.x += 5)
            elif isinstance(target, MemberAccess):
                obj = self.evaluate(target.target)
                member_name = target.member.name
                
                if not isinstance(obj, LNGInstance):
                    raise Exception("Accès membre sur une valeur non-instance.")
                
                # Assignation simple '=' devient 'EQ'
                if expr.operator == 'EQ': # 🟢 CORRECTION
                    obj.set_field(member_name, value)
                    return value

                # Gestion des opérateurs composés
                current = obj.get_field(member_name) 
                
                if expr.operator == 'PLUS_EQ': value = current + value # 🟢 CORRECTION
                elif expr.operator == 'MINUS_EQ': value = current - value # 🟢 CORRECTION
                elif expr.operator == 'MUL_EQ': value = current * value # 🟢 CORRECTION
                elif expr.operator == 'DIV_EQ': value = current / value # 🟢 CORRECTION
                elif expr.operator == 'MOD_EQ': value = current % value # 🟢 CORRECTION
                else:
                    raise Exception(f"Opérateur d'assignation composé inconnu: {expr.operator}")
                
                obj.set_field(member_name, value)
                return value

            # 3. Cas complexe: Index (arr[i] = 10, arr[i] += 5)
            elif isinstance(target, IndexAccess):
                collection = self.evaluate(target.target)
                index = self.evaluate(target.index)
                
                if not isinstance(collection, (list, dict)):
                    raise Exception("L'indexation n'est supportée que sur les listes ou dictionnaires.")
                
                # Vérification de l'index pour les listes (même si Python gère les dicts)
                if isinstance(collection, list) and not isinstance(index, int):
                    raise Exception("L'index de liste doit être un entier.")
                    
                # Assignation simple '=' devient 'EQ'
                if expr.operator == 'EQ': # 🟢 CORRECTION
                    collection[index] = value
                    return value
                
                # Gestion des opérateurs composés
                current = collection[index]

                if expr.operator == 'PLUS_EQ': value = current + value # 🟢 CORRECTION
                elif expr.operator == 'MINUS_EQ': value = current - value # 🟢 CORRECTION
                elif expr.operator == 'MUL_EQ': value = current * value # 🟢 CORRECTION
                elif expr.operator == 'DIV_EQ': value = current / value # 🟢 CORRECTION
                elif expr.operator == 'MOD_EQ': value = current % value # 🟢 CORRECTION
                else:
                    raise Exception(f"Opérateur d'assignation composé inconnu: {expr.operator}")
                
                collection[index] = value
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
            
            if callable(callee): 
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
                
            if isinstance(callee, LNGClass):
                return callee(arguments)
                
            raise Exception(f"Ne peut appeler que des fonctions, méthodes ou classes. Type trouvé: {type(callee)}")
        
        elif isinstance(expr, MemberAccess):
            obj = self.evaluate(expr.target)
            member_name = expr.member.name
            if isinstance(obj, LNGInstance):
                return obj.get_field(member_name)

            # L'accès membre sur un dictionnaire agit comme un accès par clé
            if isinstance(obj, dict):
                if member_name in obj:
                    return obj[member_name]
                raise Exception(f"Propriété non définie '{member_name}' sur l'objet littéral.")

            raise Exception(f"Accès membre invalide sur l'objet de type {type(obj)}.")

        elif isinstance(expr, IndexAccess):
            collection = self.evaluate(expr.target)
            index = self.evaluate(expr.index)
            
            if isinstance(collection, (list, dict)):
                try:
                    return collection[index]
                except (IndexError, KeyError):
                    raise Exception(f"Index ou clé invalide: {index}.")
            
            raise Exception(f"L'indexation n'est pas supportée sur le type {type(collection)}.")
            
        elif isinstance(expr, ArrayLiteral):
            return [self.evaluate(element) for element in expr.elements]
            
        elif isinstance(expr, ObjectLiteral):
            properties = {}
            for key, value_expr in expr.properties.items():
                properties[key] = self.evaluate(value_expr)
            return properties

        else:
            raise Exception(f"Type d'expression inconnu: {type(expr)}")

    def is_truthy(self, value: Any) -> bool:
        """ Détermine si une valeur est 'vraie' dans le contexte booléen """
        if value is None: return False
        if isinstance(value, bool): return value
        if isinstance(value, (int, float)): return value != 0
        if isinstance(value, (str, list, dict, LNGInstance)): return True
        return True