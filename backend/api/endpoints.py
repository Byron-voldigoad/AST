from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Any, Dict, Optional
from lexer.lexer import Lexer
from parser.parser import Parser
from interpreter.interpreter import Interpreter
from parser.semantic_analyzer import SemanticAnalyzer
import traceback
import logging

logger = logging.getLogger("analyseur_api")
logging.basicConfig(level=logging.INFO)

router = APIRouter()

class CodeRequest(BaseModel):
    """ Modèle pour la requête contenant le code source """
    code: str

class TokenResponse(BaseModel):
    """ Modèle pour un token dans la réponse """
    type: str
    value: Any
    line: int
    column: int

class ErrorResponse(BaseModel):
    """ Modèle pour une erreur structurée """
    message: str
    line: int

class ASTResponse(BaseModel):
    """ Modèle pour la réponse de l'AST """
    ast: Optional[Dict[str, Any]] = None
    errors: Optional[List[ErrorResponse]] = None

class RunResponse(BaseModel):
    """ Modèle pour la réponse d'exécution """
    output: List[str]
    error: Optional[str] = None
    errors: Optional[List[ErrorResponse]] = None

@router.post("/lex", response_model=List[TokenResponse])
async def lex_code(request: CodeRequest):
    """ Endpoint pour l'analyse lexicale (transformer code -> tokens) """
    try:
        logger.info(f"/lex called (len={len(request.code)})")
        lexer = Lexer(request.code)
        tokens = lexer.tokenize()
        return [
            TokenResponse(
                type=t.type,
                value=str(t.value) if t.value is not None else None,
                line=t.line,
                column=t.column
            )
            for t in tokens
        ]
    except Exception as e:
        logger.exception("Erreur dans /lex")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/parse", response_model=ASTResponse)
async def parse_code(request: CodeRequest):
    """ Endpoint pour l'analyse syntaxique (tokens -> AST) """
    try:
        logger.info(f"/parse called (len={len(request.code)})")
        lexer = Lexer(request.code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        
        errors = [ErrorResponse(**e) for e in parser.errors] if parser.errors else []
        
        # Lance l'analyse sémantique si le parsing a réussi
        if program:
            analyzer = SemanticAnalyzer()
            semantic_errors = analyzer.analyze(program)
            for err in semantic_errors:
                errors.append(ErrorResponse(**err))
        
        return ASTResponse(ast=program.to_dict() if not errors else None, errors=errors if errors else None)
    except Exception as e:
        logger.exception("Erreur dans /parse")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ast", response_model=ASTResponse)
async def get_ast(request: CodeRequest):
    """ Endpoint pour récupérer l'AST (identique à /parse pour l'instant) """
    return await parse_code(request)

@router.post("/run", response_model=RunResponse)
async def run_code(request: CodeRequest):
    """ Endpoint pour exécuter le code """
    try:
        logger.info(f"/run called (len={len(request.code)})")
        lexer = Lexer(request.code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        
        errors = [ErrorResponse(**e) for e in parser.errors] if parser.errors else []
        
        # Lance l'analyse sémantique
        if program:
            analyzer = SemanticAnalyzer()
            semantic_errors = analyzer.analyze(program)
            for err in semantic_errors:
                errors.append(ErrorResponse(**err))

        if errors:
            logger.info(f"/run aborté: erreurs statiques ({len(errors)})")
            return RunResponse(output=[], error="Erreur d'analyse statique", errors=errors)
        
        interpreter = Interpreter()
        output = interpreter.interpret(program)
        
        # Vérifie si la dernière ligne de sortie indique une erreur d'exécution
        error = None
        if output and output[-1].startswith("Runtime Error:"):
            error = output[-1]
            
        return RunResponse(output=output, error=error)
    except Exception as e:
        logger.exception("Erreur système dans /run")
        return RunResponse(output=[], error=f"Erreur système: {str(e)}")
