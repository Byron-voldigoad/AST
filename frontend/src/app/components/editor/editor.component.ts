import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';

@Component({
  selector: 'app-editor',
  standalone: true,
  imports: [FormsModule, MonacoEditorModule],
  templateUrl: './editor.component.html',
  styleUrls: ['./editor.component.css']
})
export class EditorComponent {
  @Input() code: string | undefined = `// Exemple de programme
var x: int = 10;
var y: int = 20;

function add(a: int, b: int): int {
    return a + b;
}

if (x < y) {
    pf("x est plus petit que y");
    pf(add(x, y));
}`;
  @Output() codeChange = new EventEmitter<string>();


  editorOptions = {
    theme: 'vs-dark',
    language: 'custom-lang',
    minimap: { enabled: true },
    scrollBeyondLastLine: false,
    fontSize: 14,
    automaticLayout: true
  };

  editorInstance: any;

  onEditorInit(editor: any) {
    this.editorInstance = editor;
    const monaco = (window as any).monaco;

    // Enregistrement de notre langage personnalisé
    monaco.languages.register({ id: 'custom-lang' });

    // Définition d'un thème personnalisé pour avoir du Orange spécifique
    monaco.editor.defineTheme('lng-theme', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'native-func', foreground: 'FFA500' }, // Orange vif
        { token: 'type', foreground: '4EC9B0' },
        { token: 'keyword', foreground: '569CD6' }
      ],
      colors: {}
    });

    // Appliquer le thème immédiatement
    monaco.editor.setTheme('lng-theme');

    // Définition des tokens pour la coloration syntaxique
    monaco.languages.setMonarchTokensProvider('custom-lang', {
      tokenizer: {
        root: [
          [/\/\/.*/, 'comment'], // Commentaires ligne
          [/\/\*/, 'comment', '@comment'], // Commentaires bloc

          // Mots-clés du langage
          [/\b(var|const|function|return|if|else|while|for|break|continue|class|extends|constructor|import|as)\b/, 'keyword'],
          [/\b(true|false|null)\b/, 'keyword'],
          [/\b(int|float|string|bool|char)\b/, 'type'],

          // Fonctions natives (Orange via le token custom 'native-func')
          [/\b(pf|clock)\b/, 'native-func'],

          // Identifiants (noms de variables, fonctions)
          [/[a-zA-Z_]\w*/, 'identifier'],
          [/\d+/, 'number'],
          [/"[^"]*"/, 'string'],

          // Délimiteurs et opérateurs
          [/[{}()\[\]]/, 'delimiter'],
          [/[=+\-*/%&|^!<>]+/, 'operator'],
          [/[:;,.]/, 'delimiter']
        ],
        comment: [
          [/[^/*]+/, 'comment'],
          [/\*\//, 'comment', '@pop'],
          [/[/*]/, 'comment']
        ]
      }
    });
  }

  onCodeChange(code: string) {
    this.code = code;
    this.codeChange.emit(code);
  }

  /**
   * Applique les marqueurs d'erreurs (soulignement rouge) dans l'éditeur.
   */
  setErrors(errors: { message: string, line: number }[]) {
    console.log('setErrors appelé avec:', errors);
    
    if (!this.editorInstance) {
      console.error('Éditeur non initialisé !');
      return;
    }

    const monaco = (window as any).monaco;
    const model = this.editorInstance.getModel();
    
    // Nettoyer d'abord les anciens marqueurs
    monaco.editor.setModelMarkers(model, 'custom-lang', []);
    
    // Attendre un tick pour s'assurer que le nettoyage est appliqué
    setTimeout(() => {
      if (errors && errors.length > 0) {
        const markers = errors.map(err => {
          const lineContent = model.getLineContent(err.line);
          return {
            severity: monaco.MarkerSeverity.Error,
            message: err.message,
            startLineNumber: err.line,
            startColumn: 1,
            endLineNumber: err.line,
            endColumn: lineContent.length + 1
          };
        });
        
        console.log('Application des marqueurs:', markers);
        monaco.editor.setModelMarkers(model, 'custom-lang', markers);
      }
      
      // FORCER UNE MISE À JOUR DU RENDU
      this.editorInstance.render();
      
      // Alternative: changer le thème puis le remettre (trick pour forcer un refresh)
      setTimeout(() => {
        const currentTheme = this.editorInstance.getOption(monaco.editor.EditorOption.theme);
        if (currentTheme === 'lng-theme') {
          monaco.editor.setTheme('vs-dark');
          setTimeout(() => {
            monaco.editor.setTheme('lng-theme');
          }, 10);
        }
      }, 50);
    }, 10);
  }
}
