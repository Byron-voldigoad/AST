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

  // Sections à afficher (Mise à jour: ajout de 'operators')
  sections = [
    { key: 'variables_types', title: 'Variables & Types', open: true },
    { key: 'functions', title: 'Fonctions', open: false },
    { key: 'classes_objects', title: 'Classes & Objets', open: false },
    { key: 'control_flow', title: 'Contrôle de Flux (if/loops)', open: false },
    { key: 'operators', title: 'Opérateurs', open: true }, // NOUVELLE SECTION AJOUTÉE
  ];

  // Store structured entries (cards) per section
  sectionEntries: Record<
    string,
    Array<{ title: string; snippet: string; desc: string; example: string }>
  > = {
    // ------------------------------------------------------------------------------------------------
    // VARIABLES & TYPES 
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
    // FONCTIONS
    // ------------------------------------------------------------------------------------------------
    functions: [
        {
            title: 'Déclaration de Fonction',
            snippet: "function IDENT '(' param_list? ')' (':' type)? block",
            desc: 'Déclare une fonction. Le type de retour est optionnel.',
            example: 'function add(a:int, b:int): int {\n    return a+b;\n}',
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
    // CLASSES & OBJETS
    // ------------------------------------------------------------------------------------------------
    classes_objects: [
        {
            title: 'Déclaration de Classe',
            snippet: "class IDENT ('extends' IDENT)? '{' class_member* '}'",
            desc: 'Déclare une nouvelle classe avec héritage (`extends`) optionnel.',
            example: 'class Point {\n    var x:int;\n    function move(dx:int){ x += dx; }\n}',
        },
        {
            title: 'Constructeur',
            snippet: "constructor '(' parameter_list? ')' block",
            desc: 'Méthode spéciale pour initialiser les objets de la classe.',
            example: 'class Person {\n    var name;\n    constructor(n) { name = n; }\n}',
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
    // CONTRÔLE DE FLUX
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
            example: 'for (var i=0; i<10; i=i+1)\n    pf(i);',
        },
        {
            title: 'Contrôle de Boucle',
            snippet: "break_statement := 'break' ';'\ncontinue_statement := 'continue' ';'",
            desc: "Interrompt (`break`) ou passe à l'itération suivante (`continue`) d'une boucle.",
            example: 'if (x == 5) break;\nif (x % 2 == 0) continue;',
        },
    ],

    // ------------------------------------------------------------------------------------------------
    // OPÉRATEURS (NOUVELLE SECTION)
    // ------------------------------------------------------------------------------------------------
    operators: [
        {
            title: 'Opérateurs Arithmétiques',
            snippet: "op := '+' | '-' | '*' | '/' | '%'",
            desc: 'Opérations mathématiques de base. Respecte la priorité standard (multiplication/division avant addition/soustraction).',
            example: 'var a = 10 + 5 * 2; // Résultat: 20\nvar b = 15 % 4; // Résultat: 3 (Modulo/reste)\nvar c = (10 + 5) / 3; // Résultat: 5.0 (Parenthèses forcent la priorité)',
        },
        {
            title: 'Opérateurs d\'Assignation',
            snippet: "op := '=' | '+=' | '-=' | '*=' | '/=' | '%='",
            desc: 'Assignation simple (`=`) ou composée. L\'assignation composée effectue l\'opération avant d\'assigner la nouvelle valeur.',
            example: 'var x = 10;\nx += 5; // Équivalent à x = x + 5 (Résultat: 15)\nx *= 2; // Équivalent à x = x * 2 (Résultat: 30)',
        },
        {
            title: 'Opérateurs de Comparaison',
            snippet: "op := '==' | '!=' | '>' | '<' | '>=' | '<='",
            desc: 'Compare deux valeurs et retourne un booléen (`true` ou `false`).',
            example: 'if (age >= 18) pf("Majeur");\nvar isEqual = (a == b);\nvar notEqual = (a != b);',
        },
        {
            title: 'Opérateurs Logiques',
            snippet: "op := '&&' | '||' | '!'",
            desc: 'Utilisés pour combiner des expressions booléennes. **`!`** est l\'opérateur unaire de négation.',
            example: 'var isReady = true;\nif (isReady && (score > 5)) pf("Validé");\nif (!isReady || isError) pf("Non prêt");',
        },
    ],

   
    // ... suppression des sections non utilisées ou commentées ...
  };

  toggleSection(section: any) {
    section.open = !section.open;
  }

  getContent(key: string) {
    return this.sectionEntries[key] || [];
  }
}