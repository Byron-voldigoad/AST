from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class Token:
    """
    Représente un Token (unité lexicale).
    Exemple: le mot-clé 'var', le signe '+', le nombre '42'.
    Stocke le type, la valeur brute, et la position (ligne, colonne).
    """
    type: str
    value: Any
    line: int
    column: int

class Lexer:
    """
    Le Lexer (Analyseur Lexical) lit le code source caractère par caractère
    et le transforme en une liste de Tokens.
    """
    def __init__(self, source_code: str):
        self.source = source_code
        self.tokens: List[Token] = []
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_pos = 0
        self.start_column = 1

    def tokenize(self) -> List[Token]:
        """ Tâche principale : scnanne tout le code et retourne tous les tokens. """
        while not self.is_at_end():
            self.start_pos = self.current
            self.start_column = self.column
            self.scan_token()
        
        self.tokens.append(Token("EOF", "", self.line, self.column))
        return self.tokens

    def scan_token(self):
        """ Analyse le caractère actuel pour déterminer quel token produire. """
        char = self.advance()
        
        if char in [' ', '\r', '\t']:
            pass
        elif char == '\n':
            self.line += 1
            self.column = 1
        elif char == '(': self.add_token('LPAREN')
        elif char == ')': self.add_token('RPAREN')
        elif char == '{': self.add_token('LBRACE')
        elif char == '}': self.add_token('RBRACE')
        elif char == '[': self.add_token('LBRACKET')
        elif char == ']': self.add_token('RBRACKET')
        elif char == ',': self.add_token('COMMA')
        elif char == '.': self.add_token('DOT')
        elif char == ';': self.add_token('SEMICOLON')
        elif char == ':': self.add_token('COLON')
        elif char == '+':
            self.add_token('PLUS_EQ' if self.match('=') else 'PLUS')
        elif char == '-':
            self.add_token('MINUS_EQ' if self.match('=') else 'MINUS')
        elif char == '*':
            self.add_token('MUL_EQ' if self.match('=') else 'MUL')
        elif char == '/':
            if self.match('/'):
                # Commentaire ligne unique //
                while self.peek() != '\n' and not self.is_at_end():
                    self.advance()
            elif self.match('*'):
                # Commentaire multi-lignes /* ... */
                self.scan_multiline_comment()
            else:
                self.add_token('DIV_EQ' if self.match('=') else 'DIV')
        elif char == '%':
            self.add_token('MOD_EQ' if self.match('=') else 'MOD')
        elif char == '!':
            self.add_token('NOT_EQ' if self.match('=') else 'NOT')
        elif char == '=':
            self.add_token('EQ_EQ' if self.match('=') else 'EQ')
        elif char == '<':
            self.add_token('LESS_EQ' if self.match('=') else 'LESS')
        elif char == '>':
            self.add_token('GREATER_EQ' if self.match('=') else 'GREATER')
        elif char == '&':
            if self.match('&'): self.add_token('AND')
            elif self.match('='): self.add_token('BIT_AND_EQ')
            else: self.add_token('BIT_AND')
        elif char == '|':
            if self.match('|'): self.add_token('OR')
            elif self.match('='): self.add_token('BIT_OR_EQ')
            else: self.add_token('BIT_OR')
        elif char == '^':
            self.add_token('BIT_XOR_EQ' if self.match('=') else 'BIT_XOR')
        elif char == '"' or char == "'":
            self.scan_string(char)
        elif char.isdigit():
            self.scan_number()
        elif self.is_alpha(char):
            self.scan_identifier()
        else:
            # Pour l'instant on ignore les caractères inconnus ou on pourrait lever une erreur
            pass

    def scan_string(self, quote_char):
        """ Analyse une chaîne de caractères """
        value = ""
        while self.peek() != quote_char and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
                self.column = 1
            value += self.advance()
        
        if self.is_at_end():
            # Chaîne non terminée
            return

        self.advance() # Fermeture des guillemets
        self.add_token('STRING', value)

    def scan_number(self):
        """ Analyse les nombres entiers et flottants """
        while self.peek().isdigit():
            self.advance()
        
        if self.peek() == '.' and self.peek_next().isdigit():
            self.advance() # Consomme le point
            while self.peek().isdigit():
                self.advance()
            self.add_token('FLOAT', float(self.source[self.start_pos:self.current]))
        else:
            self.add_token('INT', int(self.source[self.start_pos:self.current]))

    def scan_identifier(self):
        """ Analyse les identifiants et mots-clés """
        while self.is_alpha_numeric(self.peek()):
            self.advance()
        
        text = self.source[self.start_pos:self.current]
        type = self.keywords.get(text, 'IDENT')
        self.add_token(type, text if type == 'IDENT' else None)

    def scan_multiline_comment(self):
        """ Ignore les blocs de commentaires """
        while not self.is_at_end():
            if self.peek() == '*' and self.peek_next() == '/':
                self.advance()
                self.advance()
                return
            if self.peek() == '\n':
                self.line += 1
                self.column = 1
            self.advance()

    def advance(self):
        self.current += 1
        self.column += 1
        return self.source[self.current - 1]

    def match(self, expected):
        if self.is_at_end(): return False
        if self.source[self.current] != expected: return False
        self.current += 1
        self.column += 1
        return True

    def peek(self):
        if self.is_at_end(): return '\0'
        return self.source[self.current]

    def peek_next(self):
        if self.current + 1 >= len(self.source): return '\0'
        return self.source[self.current + 1]

    def is_at_end(self):
        return self.current >= len(self.source)

    def is_alpha(self, char):
        return char.isalpha() or char == '_'

    def is_alpha_numeric(self, char):
        return self.is_alpha(char) or char.isdigit()

    def add_token(self, type, value=None):
        self.tokens.append(Token(type, value, self.line, self.start_column))

    keywords = {
        'import': 'IMPORT', 'as': 'AS',
        'var': 'VAR', 'const': 'CONST',
        'function': 'FUNCTION', 'return': 'RETURN',
        'if': 'IF', 'else': 'ELSE',
        'while': 'WHILE', 'for': 'FOR',
        'break': 'BREAK', 'continue': 'CONTINUE',
        'class': 'CLASS', 'extends': 'EXTENDS', 'constructor': 'CONSTRUCTOR',
        'true': 'TRUE', 'false': 'FALSE', 'null': 'NULL',
        'int': 'TYPE_INT', 'float': 'TYPE_FLOAT', 'string': 'TYPE_STRING',
        'bool': 'TYPE_BOOL', 'char': 'TYPE_CHAR'
    }
