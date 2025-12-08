# Analyseur Syntaxique & Interpréteur

Ce projet est un analyseur syntaxique complet avec un backend Python (FastAPI) et un frontend Angular (Monaco Editor).

## Fonctionnalités

- **Éditeur de code** : Basé sur Monaco Editor (VSCode), avec coloration syntaxique personnalisée.
- **Analyse Lexicale & Syntaxique** : Lexer et Parser écrits manuellement en Python.
- **Visualisation AST** : Arbre syntaxique interactif.
- **Interpréteur** : Exécution du code directement dans le navigateur.
- **Console** : Affichage des sorties et des erreurs.

## Structure du Projet

```
analyseur_syntaxique/
├── backend/            # API Python (FastAPI)
│   ├── api/            # Endpoints REST
│   ├── interpreter/    # Interpréteur
│   ├── lexer/          # Analyseur lexical
│   ├── parser/         # Analyseur syntaxique
│   └── tests/          # Tests unitaires
└── frontend/           # Application Angular
    └── src/app/        # Composants (Editor, AST Viewer, Console)
```

## Installation

### Prérequis
- Python 3.10+
- Node.js 18+
- Angular CLI 19+

### 1. Backend (Python)

```bash
cd backend
# Créer un environnement virtuel
python -m venv venv
# Activer l'environnement
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
uvicorn main:app --reload
```
Le serveur sera accessible sur `http://localhost:8000`.

### 2. Frontend (Angular)

```bash
cd frontend
# Installer les dépendances
npm install

# Lancer l'application
ng serve
```
L'application sera accessible sur `http://localhost:4200`.

## Exemple de Code

```typescript
var x: int = 10;
var y: int = 20;

function add(a: int, b: int): int {
    return a + b;
}

if (x < y) {
    print("x est plus petit que y");
    print(add(x, y));
}
```

## Grammaire Supportée

- **Variables** : `var`, `const`
- **Types** : `int`, `float`, `string`, `bool`
- **Fonctions** : `function name(params): type { ... }`
- **Contrôle de flux** : `if`, `else`, `while`, `for`, `break`, `continue`
- **Opérateurs** : `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `>`, `&&`, `||`
