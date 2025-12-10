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
        
        # Définition des mots-clés du langage LNG-255
        self.keywords = {
            # Imports
            'import': 'IMPORT', 'as': 'AS',
            # Déclarations
            'var': 'VAR', 'const': 'CONST',
            'function': 'FUNCTION', 
            'class': 'CLASS', 'extends': 'EXTENDS', 'constructor': 'CONSTRUCTOR',
            # Contrôle de flux
            'return': 'RETURN',
            'if': 'IF', 'else': 'ELSE',
            'while': 'WHILE', 'for': 'FOR',
            'break': 'BREAK', 'continue': 'CONTINUE',
            # Types Primitifs
            'int': 'TYPE_INT', 'float': 'TYPE_FLOAT', 'string': 'TYPE_STRING',
            'bool': 'TYPE_BOOL', 'char': 'TYPE_CHAR',
            # Littéraux
            'true': 'TRUE', 'false': 'FALSE', 'null': 'NULL',
        }


    def tokenize(self) -> List[Token]:
        """ Tâche principale : scnanne tout le code et retourne tous les tokens. """
        while not self.is_at_end():
            self.start_pos = self.current
            self.start_column = self.column
            self.scan_token()
        
        # Ajout du Token de fin de fichier (EOF)
        self.tokens.append(Token("EOF", "", self.line, self.column))
        return self.tokens

    def scan_token(self):
        """ Analyse le caractère actuel pour déterminer quel token produire. """
        char = self.advance()
        
        # 1. Ignorer les espaces blancs
        if char in [' ', '\r', '\t']:
            pass
        elif char == '\n':
            # Gérer le saut de ligne
            self.line += 1
            self.column = 1
        
        # 2. Symboles et Opérateurs Simples/Composés
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
        
        # Opérateurs arithmétiques et d'assignation composée
        elif char == '+':
            self.add_token('PLUS_EQ' if self.match('=') else 'PLUS')
        elif char == '-':
            self.add_token('MINUS_EQ' if self.match('=') else 'MINUS')
        elif char == '*':
            self.add_token('MUL_EQ' if self.match('=') else 'MUL')
        elif char == '%':
            self.add_token('MOD_EQ' if self.match('=') else 'MOD')

        # Opérateur de division ou commentaires
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
        
        # Opérateurs logiques, d'égalité et de comparaison
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
            # Nous ignorons l'opérateur BIT_AND_EQ et BIT_AND car ils ne sont pas dans la grammaire principale.
            # elif self.match('='): self.add_token('BIT_AND_EQ')
            # else: self.add_token('BIT_AND')
            else: self.error(f"Caractère inattendu: '{char}' (Bitwise '&' non supporté)")
        elif char == '|':
            if self.match('|'): self.add_token('OR')
            # Nous ignorons l'opérateur BIT_OR_EQ et BIT_OR car ils ne sont pas dans la grammaire principale.
            # elif self.match('='): self.add_token('BIT_OR_EQ')
            # else: self.add_token('BIT_OR')
            else: self.error(f"Caractère inattendu: '{char}' (Bitwise '|' non supporté)")
        elif char == '^':
            # Nous ignorons l'opérateur BIT_XOR_EQ et BIT_XOR car ils ne sont pas dans la grammaire principale.
            # self.add_token('BIT_XOR_EQ' if self.match('=') else 'BIT_XOR')
            self.error(f"Caractère inattendu: '{char}' (Bitwise '^' non supporté)")

        # 3. Littéraux
        elif char == '"' or char == "'":
            self.scan_string(char)
        elif char.isdigit():
            self.scan_number()
        elif self.is_alpha(char):
            self.scan_identifier()
            
        # 4. Gestion des erreurs
        else:
            self.error(f"Caractère inconnu: '{char}'")

    # --- Méthodes de Scanning des Littéraux et Identifiants ---
    
    def scan_string(self, quote_char):
        """ Analyse une chaîne de caractères """
        value = ""
        while self.peek() != quote_char and not self.is_at_end():
            if self.peek() == '\n':
                # Les sauts de ligne sont permis dans les chaînes, mais nous mettons à jour la position
                self.line += 1
                self.column = 1
            value += self.advance()
        
        if self.is_at_end():
            # Chaîne non terminée (erreur)
            self.error("Chaîne de caractères non terminée.")
            return

        self.advance() # Consomme le guillemet fermant
        self.add_token('STRING', value)

    def scan_number(self):
        """ Analyse les nombres entiers et flottants """
        while self.peek().isdigit():
            self.advance()
        
        # Vérifie pour la partie fractionnaire
        is_float = False
        if self.peek() == '.' and self.peek_next().isdigit():
            is_float = True
            self.advance() # Consomme le point
            while self.peek().isdigit():
                self.advance()
        
        text = self.source[self.start_pos:self.current]

        if is_float:
            self.add_token('FLOAT', float(text))
        else:
            self.add_token('INT', int(text))

    def scan_identifier(self):
        """ Analyse les identifiants et mots-clés """
        while self.is_alpha_numeric(self.peek()):
            self.advance()
        
        text = self.source[self.start_pos:self.current]
        type = self.keywords.get(text, 'IDENT')
        
        # Les littéraux (TRUE, FALSE, NULL) doivent stocker leur valeur booléenne/None
        if type == 'TRUE':
            self.add_token(type, True)
        elif type == 'FALSE':
            self.add_token(type, False)
        elif type == 'NULL':
            self.add_token(type, None)
        else:
            # Les mots-clés (VAR, IF, etc.) n'ont pas de valeur explicite (value=None)
            # Les IDENTIFIERS stockent leur nom (value=text)
            self.add_token(type, text if type == 'IDENT' else None)


    def scan_multiline_comment(self):
        """ Ignore les blocs de commentaires /* ... */ """
        while not self.is_at_end():
            if self.peek() == '*' and self.peek_next() == '/':
                self.advance() # Consomme '*'
                self.advance() # Consomme '/'
                return
            if self.peek() == '\n':
                self.line += 1
                self.column = 1 # Sera corrigé par l'appel à advance()
            self.advance()
        
        # Si nous atteignons la fin sans fermer
        self.error("Commentaire multi-lignes non terminé.")


    # --- Fonctions d'Utilité ---
    
    def advance(self):
        """ Consomme le caractère actuel et avance les pointeurs de position. """
        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def match(self, expected):
        """ Vérifie si le caractère suivant correspond à `expected`. Si oui, le consomme. """
        if self.is_at_end(): return False
        if self.source[self.current] != expected: return False
        self.current += 1
        self.column += 1
        return True

    def peek(self):
        """ Retourne le caractère actuel sans le consommer. """
        if self.is_at_end(): return '\0'
        return self.source[self.current]

    def peek_next(self):
        """ Retourne le caractère après le caractère actuel sans le consommer. """
        if self.current + 1 >= len(self.source): return '\0'
        return self.source[self.current + 1]

    def is_at_end(self):
        """ Vérifie si le pointeur actuel a atteint la fin du code source. """
        return self.current >= len(self.source)

    def is_alpha(self, char):
        """ Vérifie si le caractère est une lettre ou un underscore. """
        return char.isalpha() or char == '_'

    def is_alpha_numeric(self, char):
        """ Vérifie si le caractère est alphanumérique ou un underscore. """
        return self.is_alpha(char) or char.isdigit()

    def add_token(self, type, value=None):
        """ Crée et ajoute un nouveau Token à la liste des tokens. """
        self.tokens.append(Token(type, value, self.line, self.start_column))

    def error(self, message):
        """ (Placeholder) Gestion simple des erreurs lexicales. """
        # Vous devriez implémenter une meilleure gestion des erreurs qui interrompt l'analyse ou les collecte.
        print(f"Erreur Lexicale à la ligne {self.line}, colonne {self.start_column}: {message}")
        # Optionnel: Ajouter un token d'erreur pour que le parseur puisse potentiellement continuer
        # self.add_token("ERROR", message)