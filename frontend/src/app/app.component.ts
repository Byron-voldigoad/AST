import { Component, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EditorComponent } from './components/editor/editor.component';
import { ConsoleComponent } from './components/console/console.component';
import { ApiService } from './services/api.service';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, EditorComponent, ConsoleComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  code: string = '';
  consoleLogs: { message: string, type: 'info' | 'error' | 'success' }[] = [];

  isAnalyzing: boolean = false;
  isRunning: boolean = false;

  private codeChangeSubject = new Subject<string>();

  // CORRECTION : Ajouter cette ligne pour référencer l'éditeur
  @ViewChild(EditorComponent) editor!: EditorComponent;

  constructor(private apiService: ApiService) {
     console.log('Constructeur appelé');
    // Debounce analysis to avoid spamming the backend
    this.codeChangeSubject.pipe(
      debounceTime(500),
      distinctUntilChanged()
    ).subscribe(code => {
      console.log('ANALYSE AUTOMATIQUE DÉCLENCHÉE ! Code:', code.substring(0, 30) + '...');
      this.code = code;
      this.analyze(true); // Silent analysis
    });
  }

  onCodeChange(newCode: string) {
    console.log('onCodeChange appelé avec code longueur:', newCode.length);
    this.codeChangeSubject.next(newCode);
  }

  analyze(silent: boolean = false) {
    if (!this.code.trim()) return;

    this.isAnalyzing = true;
    if (!silent) this.consoleLogs = []; // Clear logs on manual trigger

    console.log(`ANALYSE ${silent ? '(silencieuse)' : '(manuelle)'} déclenchée`);

    this.apiService.parse(this.code).subscribe({
      next: (response) => {
        console.log('RÉPONSE API parse:', response);
        this.isAnalyzing = false;
        
        // CORRECTION : Vérifier que l'éditeur existe
        if (response.errors && response.errors.length > 0) {
        console.log(`Erreurs trouvées: ${response.errors.length}`);
        this.editor.setErrors(response.errors);
        if (!silent) {
          response.errors.forEach((err: any) =>
            this.log(`Erreur ligne ${err.line}: ${err.message}`, 'error')
          );
        }
        } else if (this.editor) {
          console.log('Aucune erreur ou statut success');
          this.editor.setErrors([]); // Clear errors
          if (!silent) this.log('Analyse syntaxique réussie !', 'success');
        }
      },
      error: (err) => {
        this.isAnalyzing = false;
        if (!silent) this.log('Erreur serveur lors de l\'analyse.', 'error');
        console.error(err);
      }
    });
  }

  run() {
    if (!this.code.trim()) return;

    this.isRunning = true;
    this.consoleLogs = []; // Clear for new run
    this.log('Exécution en cours...', 'info');

    this.apiService.run(this.code).subscribe({
      next: (response) => {
        this.isRunning = false;

        // Affichage des erreurs de compilation s'il y en a
         if (response.errors && response.errors.length > 0) {
        this.editor.setErrors(response.errors);
        response.errors.forEach((err: any) =>
          this.log(`Erreur ligne ${err.line}: ${err.message}`, 'error')
        );
        this.log('Échec de la compilation.', 'error');
        return;
      }

        // Affichage de la sortie standard
        if (response.output && response.output.length > 0) {
          response.output.forEach((line: string) => this.log(line, 'info'));
        }

        this.log('Fin de l\'exécution.', 'success');
      },
      error: (err) => {
        this.isRunning = false;
        this.log('Erreur serveur lors de l\'exécution.', 'error');
        console.error(err);
      }
    });
  }

  private log(message: string, type: 'info' | 'error' | 'success') {
    this.consoleLogs.push({ message, type });
  }
}