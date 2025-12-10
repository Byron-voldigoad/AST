from typing import List, Optional, Any, Dict
from dataclasses import dataclass, field

@dataclass
class ASTNode:
    """
    Classe de base pour tous les noeuds de l'Arbre Syntaxique Abstrait (AST).
    Permet de convertir l'arbre en dictionnaire pour l'envoyer au frontend (JSON).
    """
    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.__class__.__name__}
        for k, v in self.__dict__.items():
            if isinstance(v, ASTNode):
                result[k] = v.to_dict()
            elif isinstance(v, list):
                result[k] = [item.to_dict() if isinstance(item, ASTNode) else item for item in v]
            elif isinstance(v, dict):
                # Gère les dictionnaires dans l'AST (ex: ObjectLiteral)
                processed_dict = {}
                for key, val in v.items():
                    processed_dict[key] = val.to_dict() if isinstance(val, ASTNode) else val
                result[k] = processed_dict
            else:
                result[k] = v
        return result

# --- Expressions (Produisent une valeur) ---

@dataclass
class Expression(ASTNode):
    """ Classe parent pour toutes les expressions """
    pass

@dataclass
class Literal(Expression):
    """ Valeurs directes: 10, 3.14, "texte", true """
    value: Any
    raw_type: str  # 'int', 'float', 'string', 'bool', 'null'

@dataclass
class Identifier(Expression):
    """ Utilisation d'une variable: x, y, maFonction """
    name: str

@dataclass
class BinaryOp(Expression):
    """ Opération binaire: a + b, x > y """
    left: Expression
    operator: str
    right: Expression

@dataclass
class UnaryOp(Expression):
    """ Opération unaire: -x, !vrai """
    operator: str
    operand: Expression

@dataclass
class FunctionCall(Expression):
    """ Appel de fonction: add(10, 20) """
    callee: Expression
    arguments: List[Expression]

@dataclass
class ArrayLiteral(Expression):
    """ Tableau: [1, 2, 3] """
    elements: List[Expression]

@dataclass
class ObjectLiteral(Expression):
    """ Objet/Struct: { x: 1, y: 2 } """
    # Les clés d'un objet/struct sont des identifiants (strings)
    properties: Dict[str, Expression] 

@dataclass
class Assignment(Expression):
    """ Assignation: x = 10 ou x += 5 """
    target: Expression  # Peut être Identifier, MemberAccess ou IndexAccess
    operator: str       # =, +=, -=, etc.
    value: Expression

# --- NOUVEAUX NŒUDS d'Accès de Membres (Point 19 & 20) ---

@dataclass
class MemberAccess(Expression):
    """ Accès aux membres: obj.member """
    target: Expression # L'objet ou la classe sur lequel on accède (ex: obj)
    member: Identifier # Le nom du membre accédé (ex: x)

@dataclass
class IndexAccess(Expression):
    """ Accès par indice: arr[index] """
    target: Expression # Le tableau ou la collection
    index: Expression  # L'expression qui donne l'indice

# --- Statements (Instructions qui effectuent une action) ---

@dataclass
class Statement(ASTNode):
    """ Classe parent pour toutes les instructions """
    pass

@dataclass
class Block(Statement):
    """ Un bloc de code: { ... } """
    statements: List[Statement]

# VariableDecl gère VAR et CONST (Point 4)
@dataclass
class VariableDecl(Statement):
    """ Déclaration de variable: var x: int = 10; OU const PI = 3.14; """
    name: str
    var_type: Optional[str]
    initializer: Optional[Expression]
    is_const: bool = False

@dataclass
class FunctionDecl(Statement):
    """ Déclaration de fonction: function test() { ... } """
    name: str
    params: List[Dict[str, str]]  # Liste de {name: str, type: str}
    return_type: Optional[str]
    body: Block

# --- NOUVEAUX NŒUDS de Classes (Point 7) ---

@dataclass
class ConstructorDecl(ASTNode):
    """ Déclaration de constructeur: constructor(params) { ... } """
    params: List[Dict[str, str]]
    body: Block

@dataclass
class ClassDecl(Statement):
    """ Déclaration de classe: class Point extends Shape { ... } """
    name: str
    # Le nom de la classe parente (Identifier)
    super_class: Optional[Identifier] 
    # Le corps peut contenir VariableDecl, FunctionDecl, ConstructorDecl
    members: List[ASTNode] 

# --- Contrôle de Flux de Base (Déjà existant) ---

@dataclass
class IfStatement(Statement):
    """ Condition: if (x) { ... } else { ... } """
    condition: Expression
    then_branch: Statement
    else_branch: Optional[Statement] = None

@dataclass
class WhileStatement(Statement):
    """ Boucle Tant Que: while (x) { ... } """
    condition: Expression
    body: Statement

@dataclass
class ForStatement(Statement):
    """ Boucle Pour: for (var i=0; i<10; i = i+1) { ... } """
    init: Optional[Statement]
    condition: Optional[Expression]
    update: Optional[Expression]
    body: Statement

# Contrôle de flux d'itération (Point 11)
@dataclass
class ReturnStatement(Statement):
    """ Retour de fonction: return result; """
    value: Optional[Expression]

@dataclass
class BreakStatement(Statement):
    """ Interrompre une boucle: break; """
    pass

@dataclass
class ContinueStatement(Statement):
    """ Passer à l'itération suivante: continue; """
    pass

@dataclass
class ExpressionStatement(Statement):
    """ Une expression utilisée comme instruction (ex: print("test")) """
    expression: Expression

@dataclass
class Program(ASTNode):
    """ Le noeud racine représentant tout le programme """
    statements: List[Statement]