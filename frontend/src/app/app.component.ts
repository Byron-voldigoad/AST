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
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule, 
    EditorComponent, 
    ConsoleComponent,
    SyntaxReferenceComponent,
    FileExplorerComponent,
    FileTabsComponent
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  @ViewChild(EditorComponent) editor!: EditorComponent;
  
  consoleLogs: { message: string, type: 'info' | 'error' | 'success' }[] = [];
  isAnalyzing: boolean = false;
  isRunning: boolean = false;
  
  activeFile: FileNode | null = null;
  isDirty = false;
  showExplorer: boolean = true;
  showDocumentation: boolean = true;
  
  private codeChangeSubject = new Subject<string>();

  constructor(
    private apiService: ApiService,
    public fileSystem: FileSystemService // CHANGÉ EN public
  ) {}

  ngOnInit() {
    // Analyse automatique
    this.codeChangeSubject.pipe(
      debounceTime(500),
      distinctUntilChanged(),
    ).subscribe(code => {
      this.analyze(true);
    });

    // Écouter les changements de fichier actif
    this.fileSystem.activeFile$.subscribe(file => {
      this.activeFile = file;
    });
  }

  onCodeChange(newCode: string) {
    this.codeChangeSubject.next(newCode);
    
    // Mettre à jour le contenu du fichier actif
    if (this.activeFile) {
      this.fileSystem.updateFileContent(this.activeFile.path, newCode);
      this.isDirty = true;
    }
  }

  analyze(silent: boolean = false) {
    // Synchroniser le code depuis l'éditeur Monaco
    if (this.editor && this.editor.editorInstance) {
      const currentCode = this.editor.editorInstance.getValue();
      if (this.activeFile) {
        this.activeFile.content = currentCode;
      }
    }
    if (!this.activeFile?.content?.trim()) return;

    this.isAnalyzing = true;
    if (!silent) this.consoleLogs = [];

    console.log('Code envoyé au backend:', this.activeFile.content);
    this.apiService.parse(this.activeFile.content).subscribe({
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
        if (!silent) this.log('Erreur serveur lors de l\'analyse.', 'error');
      }
    });
  }

  run() {
    // Synchroniser le code depuis l'éditeur Monaco
    if (this.editor && this.editor.editorInstance) {
      const currentCode = this.editor.editorInstance.getValue();
      if (this.activeFile) {
        this.activeFile.content = currentCode;
      }
    }
    if (!this.activeFile?.content?.trim()) return;

    this.isRunning = true;
    this.consoleLogs = [];
    this.log('Exécution en cours...', 'info');

    console.log('Code envoyé à l\'exécution:', this.activeFile.content);
    this.apiService.run(this.activeFile.content).subscribe({
      next: (response) => {
        this.isRunning = false;

        if (response.errors && response.errors.length > 0) {
          this.editor.setErrors(response.errors);
          response.errors.forEach((err: any) =>
            this.log(`Erreur ligne ${err.line}: ${err.message}`, 'error')
          );
          this.log('Échec de la compilation.', 'error');
          return;
        }

        if (response.output && response.output.length > 0) {
          response.output.forEach((line: string) => this.log(line, 'info'));
        }

        this.log('Fin de l\'exécution.', 'success');
      },
      error: (err) => {
        this.isRunning = false;
        this.log('Erreur serveur lors de l\'exécution.', 'error');
      }
    });
  }

  toggleExplorer() {
    this.showExplorer = !this.showExplorer;
  }

  toggleDocumentation() {
    this.showDocumentation = !this.showDocumentation;
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
        this.log(`Fichier ${this.activeFile.name} enregistré avec succès`, 'success');
      }
    }
  }

  private log(message: string, type: 'info' | 'error' | 'success') {
    this.consoleLogs.push({ message, type });
  }

  ngOnDestroy() {
    this.codeChangeSubject.complete();
  }
}