import { Component, ViewChild, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EditorComponent } from './components/editor/editor.component';
import { ConsoleComponent } from './components/console/console.component';
import { SyntaxReferenceComponent } from './components/syntax-reference/syntax-reference.component';
import { FileExplorerComponent } from './components/file-explorer/file-explorer.component';
import { FileTabsComponent } from './components/file-tabs/file-tabs.component';
import { ApiService } from './services/api.service';
import { FileSystemService, FileNode } from './services/file-system.service';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, take } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    EditorComponent,
    ConsoleComponent,
    SyntaxReferenceComponent,
    FileExplorerComponent,
    FileTabsComponent,
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent implements OnInit {
  title = 'frontend';
  @ViewChild(EditorComponent) editor!: EditorComponent;

  consoleLogs: {
    message: string;
    type: 'info' | 'error' | 'success';
    time?: string;
  }[] = [];
  isAnalyzing: boolean = false;
  isRunning: boolean = false;
  isConsoleOpen: boolean = false;

  activeFile: FileNode | null = null;
  isDirty = false;
  showExplorer: boolean = false; // no file explorer for this simplified UI
  showDocumentation: boolean = true; // grammar panel visible on the right

  private codeChangeSubject = new Subject<string>();
  editorFallback: string = '';

  constructor(
    private apiService: ApiService,
    public fileSystem: FileSystemService // CHANGÉ EN public
  ) {}

  ngOnInit() {
    // Analyse automatique
    this.codeChangeSubject
      .pipe(debounceTime(500), distinctUntilChanged())
      .subscribe((code) => {
        this.analyze(true);
      });

    // Écouter les changements de fichier actif
    this.fileSystem.activeFile$.subscribe((file) => {
      this.activeFile = file;
    });

    // Si aucun fichier actif, ouvrir automatiquement un fichier par défaut (par ex. /main.lng)
    this.fileSystem.fileTree$.pipe(take(1)).subscribe((tree) => {
      if (!this.activeFile) {
        const findFirstFile = (nodes: FileNode[]): FileNode | null => {
          for (const n of nodes) {
            if (n.type === 'file') return n;
            if (n.children) {
              const found = findFirstFile(n.children);
              if (found) return found;
            }
          }
          return null;
        };

        const first = findFirstFile(tree);
        if (first) this.fileSystem.openFile(first);
      }
    });
  }

  onCodeChange(newCode: string) {
    this.codeChangeSubject.next(newCode);

    // Mettre à jour le contenu du fichier actif
    if (this.activeFile) {
      this.fileSystem.updateFileContent(this.activeFile.path, newCode);
      this.isDirty = true;
    } else {
      // keep fallback content when no file is active so user can type arbitrary code
      this.editorFallback = newCode;
    }
  }

  analyze(silent: boolean = false) {
    // Récupérer le code depuis l'éditeur (ou fallback) et l'envoyer au backend
    let code: string | undefined = undefined;
    if (this.editor && this.editor.editorInstance) {
      code = this.editor.editorInstance.getValue();
      if (this.activeFile) {
        this.activeFile.content = code;
      }
    }
    if (!code) code = this.activeFile?.content || this.editorFallback;
    if (!code?.trim()) return;

    this.isAnalyzing = true;
    if (!silent) this.consoleLogs = [];
    if (!silent) this.isConsoleOpen = true;

    console.log('Code envoyé au backend:', code);
    this.apiService.parse(code).subscribe({
      next: (response) => {
        console.log('Réponse parse:', response);
        this.isAnalyzing = false;

        const errors = Array.isArray(response.errors) ? response.errors : [];
        if (errors.length > 0) {
          this.editor.setErrors(errors);
          if (!silent) {
            errors.forEach((err: any) =>
              this.log(`Erreur ligne ${err.line}: ${err.message}`, 'error')
            );
          }
        } else {
          this.editor.setErrors([]);
          if (!silent) this.log('Analyse syntaxique réussie !', 'success');
        }
      },
      error: (err) => {
        this.isAnalyzing = false;
        if (!silent) this.log("Erreur serveur lors de l'analyse.", 'error');
      },
    });
  }

  run() {
    // Récupérer le code depuis l'éditeur (ou fallback)
    let code: string | undefined = undefined;
    if (this.editor && this.editor.editorInstance) {
      code = this.editor.editorInstance.getValue();
      if (this.activeFile) this.activeFile.content = code;
    }
    if (!code) code = this.activeFile?.content || this.editorFallback;
    if (!code?.trim()) return;

    this.isRunning = true;
    this.consoleLogs = [];
    this.isConsoleOpen = true;
    this.log('Exécution en cours...', 'info');

    console.log("Code envoyé à l'exécution:", code);
    this.apiService.run(code).subscribe({
      next: (response) => {
        this.isRunning = false;

        if (response.errors && response.errors.length > 0) {
          this.editor.setErrors(response.errors);
          response.errors.forEach((err: any) =>
            this.log(`Erreur ligne ${err.line}: ${err.message}`, 'error')
          );
          this.log('Échec de la compilation.', 'error');
          this.isRunning = false;
          return;
        }

        if (response.output && response.output.length > 0) {
          response.output.forEach((line: string) => this.log(line, 'info'));
        }

        this.log("Fin de l'exécution.", 'success');
        this.isRunning = false;
      },
      error: (err) => {
        this.isRunning = false;
        this.log("Erreur serveur lors de l'exécution.", 'error');
      },
    });
  }

  toggleExplorer() {
    this.showExplorer = !this.showExplorer;
  }

  toggleDocumentation() {
    this.showDocumentation = !this.showDocumentation;
  }

  toggleConsole() {
    this.isConsoleOpen = !this.isConsoleOpen;
  }

  clearLogs() {
    this.consoleLogs = [];
  }

  getLogCount(): number {
    return this.consoleLogs.length;
  }

  hasErrors(): boolean {
    return this.consoleLogs.some((l) => l.type === 'error');
  }

  // Méthodes pour créer fichiers/dossiers
  createNewFile() {
    this.fileSystem.createFile('new.lng', '/', 'file');
  }

  createNewVDGFile() {
    this.fileSystem.createFile('nouveau.vdg', '/', 'file');
  }

  createNewFolder() {
    this.fileSystem.createFile('new-folder', '/', 'folder');
  }

  saveCurrentFile() {
    if (this.activeFile && this.editor) {
      const currentCode = this.editor.editorInstance?.getValue();
      if (currentCode !== undefined) {
        this.activeFile.content = currentCode;
        this.fileSystem.updateFileContent(this.activeFile.path, currentCode);
        this.isDirty = false;
        this.log(
          `Fichier ${this.activeFile.name} enregistré avec succès`,
          'success'
        );
      }
    }
  }

  private log(message: string, type: 'info' | 'error' | 'success') {
    const t = new Date().toLocaleTimeString();
    this.consoleLogs.push({ message, type, time: t });
    // auto-open console when something is logged
    this.isConsoleOpen = true;
  }

  ngOnDestroy() {
    this.codeChangeSubject.complete();
  }
}
