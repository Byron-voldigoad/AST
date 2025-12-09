// src/app/components/syntax-reference/syntax-reference.component.ts

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-syntax-reference',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './syntax-reference.component.html',
  styleUrls: ['./syntax-reference.component.css'],
})
export class SyntaxReferenceComponent {
  currentLanguage: string = 'CustomLang';

  // Sections à afficher : plus de 'official' redondant
  sections = [
    { key: 'variables_types', title: 'Variables & Types', open: true },
    { key: 'functions', title: 'Fonctions', open: false },
    { key: 'classes_objects', title: 'Classes & Objets', open: false },
    { key: 'control_flow', title: 'Contrôle de Flux (if/loops)', open: false },
    { key: 'expressions', title: 'Expressions & Opérateurs', open: false },
    { key: 'program_structure', title: 'Structure Programme', open: false },
  ];

  // Store structured entries (cards) per section
  sectionEntries: Record<
    string,
    Array<{ title: string; snippet: string; desc: string; example: string }> // Nouveau champ 'example'
  > = {
    // ------------------------------------------------------------------------------------------------
    // VARIABLES & TYPES (Points 4 et 5 de votre grammaire)
    // ------------------------------------------------------------------------------------------------
    variables_types: [
      {
        title: 'Variable (var)',
        snippet: "var IDENT (':' type)? ('=' expression)? ';'",
        desc: 'Déclaration de variable mutable. Typage et initialisation sont optionnels.',
        example: 'var age: int = 20;\nvar nom = "Luna";\nvar compteur;',
      },
      {
        title: 'Constante (const)',
        snippet: "const IDENT (':' type)? '=' expression ';'",
        desc: 'Déclaration de valeur immuable. Le type est optionnel, mais la valeur initiale est obligatoire.',
        example: 'const PI: float = 3.14;\nconst VERSION = "1.0.0";',
      },
      {
        title: 'Types Primitifs',
        snippet: "type := 'int' | 'float' | 'string' | 'bool' | 'char'",
        desc: 'Types de données natifs (primitifs) du langage.',
        example: 'var x: int = 10;\nvar flag: bool = true;',
      },
      {
        title: 'Types Composés',
        snippet: "type := IDENT | type '[]' | '{' field: type, ... '}'",
        desc: 'Types personnalisés (classes), tableaux dynamiques et types objet/struct.',
        example: 'var notes: float[];\nvar p: {x:int, y:int};',
      },
    ],

    // ------------------------------------------------------------------------------------------------
    // FONCTIONS (Points 6 et 20)
    // ------------------------------------------------------------------------------------------------
    functions: [
      {
        title: 'Déclaration de Fonction',
        snippet: "function IDENT '(' param_list? ')' (':' type)? block",
        desc: 'Déclare une fonction. Le type de retour est optionnel.',
        example: 'function add(a:int, b:int): int {\n    return a+b;\n}',
      },
      {
        title: "Appel de Fonction",
        snippet: "IDENT '(' argument_list? ')'",
        desc: "Exécute une fonction définie.",
        example: 'var result = add(3, 5);\npf("Résultat: " + result);',
      },
      {
        title: "Retour (return)",
        snippet: "return_statement := 'return' expression? ';'",
        desc: "Termine l'exécution d'une fonction et retourne une valeur (optionnel).",
        example: 'return age;',
      },
    ],

    // ------------------------------------------------------------------------------------------------
    // CLASSES & OBJETS (Point 7 et 19)
    // ------------------------------------------------------------------------------------------------
    classes_objects: [
      {
        title: 'Déclaration de Classe',
        snippet: "class IDENT ('extends' IDENT)? '{' class_member* '}'",
        desc: 'Déclare une nouvelle classe avec héritage (`extends`) optionnel.',
        example: 'class Point {\n    var x:int;\n    function move(dx:int){ x += dx; }\n}',
      },
      {
        title: 'Constructeur',
        snippet: "constructor '(' parameter_list? ')' block",
        desc: 'Méthode spéciale pour initialiser les objets de la classe.',
        example: 'class Person {\n    var name;\n    constructor(n) { name = n; }\n}',
      },
      {
        title: 'Literal de Tableau',
        snippet: "array_literal := '[' (expression (',' expression)*)? ']'",
        desc: 'Création rapide d\'un tableau dynamique.',
        example: 'var liste = [1,2,3];',
      },
      {
        title: 'Literal d\'Objet/Struct',
        snippet: "object_literal := '{' (IDENT ':' expression (',' IDENT ':' expression)*)? '}'",
        desc: 'Création rapide d\'une valeur de type objet/struct.',
        example: 'var obj = {name:"Zed", age:30};',
      },
    ],

    // ------------------------------------------------------------------------------------------------
    // CONTRÔLE DE FLUX (Points 9, 10, 11)
    // ------------------------------------------------------------------------------------------------
    control_flow: [
      {
        title: 'Condition (if/else)',
        snippet: "if '(' expression ')' statement ('else' statement)?",
        desc: 'Exécution conditionnelle classique.',
        example: 'if (x > 10) pf(x);\nelse pf(0);',
      },
      {
        title: 'Boucle While',
        snippet: "while '(' expression ')' statement",
        desc: 'Répète un bloc tant que la condition est vraie.',
        example: 'var i = 0;\nwhile (i < 5) i++;',
      },
      {
        title: 'Boucle For',
        snippet: "for '(' init; condition?; increment? ')' statement",
        desc: 'Boucle For classique (init, condition, incrémentation).',
        example: 'for (var i=0; i<10; i=i+1)\n    pf(i);',
      },
      {
        title: 'Contrôle de Boucle',
        snippet: "break_statement := 'break' ';'\ncontinue_statement := 'continue' ';'",
        desc: "Interrompt (`break`) ou passe à l'itération suivante (`continue`) d'une boucle.",
        example: 'if (x == 5) break;\nif (x % 2 == 0) continue;',
      },
    ],

    // ------------------------------------------------------------------------------------------------
    // EXPRESSIONS & OPÉRATEURS (Point 12-18)
    // ------------------------------------------------------------------------------------------------
    expressions: [
      {
        title: 'Opérateurs',
        snippet: 'assignment -> logical_or -> ... -> unary -> primary',
        desc: 'Hiérarchie stricte des expressions (ordre de priorité).',
        example: 'a = 3 + 4 * 2\nx += 10\n!flag\n(a + b) * c',
      },
      {
        title: 'Arbre Binaire d\'Expression',
        snippet: 'Pour l’expression : a = 3 + 4 * 2',
        desc: "Représentation interne de l'arbre syntaxique pour les expressions complexes.",
        example: '             (=)\n            /   \\\n          (a)   (+)\n                /   \\\n              (3)   (*)\n                    / \\\n                  (4) (2)',
      },
    ],
    
    // ------------------------------------------------------------------------------------------------
    // STRUCTURE PROGRAMME (Points 1, 2, 3, 8, 21)
    // ------------------------------------------------------------------------------------------------
    // program_structure: [
    //     {
    //         title: 'Programme (Program)',
    //         snippet: "(import | declaration | statement)* EOF",
    //         desc: "Un programme est une séquence d'imports, de déclarations et d'instructions, suivie de la fin du fichier.",
    //         example: 'import math;\nvar x = 10;\npf(x);',
    //     },
    //     {
    //         title: 'Import de Module',
    //         snippet: "import IDENT ('.' IDENT)* ('as' IDENT)? ';'",
    //         desc: "Importation d'un module, sous-module, avec alias optionnel.",
    //         example: 'import util.string as str;',
    //     },
    //     {
    //         title: 'Déclarations Globales',
    //         snippet: 'declaration := var | const | function | class',
    //         desc: 'Tout ce qui peut être déclaré au niveau global du programme.',
    //         example: 'function main() { ... }',
    //     },
    //     {
    //         title: 'Commentaires',
    //         snippet: "// ... endline | /* ... */",
    //         desc: 'Commentaires sur une ligne ou multi-lignes.',
    //         example: '// Commentaire simple\n/* Bloc\nde commentaire */',
    //     },
    // ]
  };

  toggleSection(section: any) {
    section.open = !section.open;
  }

  getContent(key: string) {
    return this.sectionEntries[key] || [];
  }
}