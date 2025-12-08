import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface Token {
  type: string;
  value: any;
  line: number;
  column: number;
}

export interface ASTResponse {
  status: 'success' | 'error';
  ast?: any;
  errors?: { message: string, line: number }[];
}

export interface RunResponse {
  output: string[];
  error?: string;
  errors?: { message: string, line: number }[];
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) { }

  /**
   * Analyse Lexicale : Envoie le code brut et reçoit une liste de tokens.
   */
  lex(code: string): Observable<Token[]> {
    return this.http.post<Token[]>(`${this.apiUrl}/lex`, { code });
  }

  /**
   * Analyse Syntaxique : Envoie le code et reçoit l'AST (Arbre Syntaxique).
   */
  parse(code: string): Observable<ASTResponse> {
    return this.http.post<ASTResponse>(`${this.apiUrl}/parse`, { code });
  }

  /**
   * Récupère l'AST pour l'affichage (similaire à parse).
   */
  getAST(code: string): Observable<ASTResponse> {
    return this.parse(code);
  }

  /**
   * Exécute le code via l'interpréteur backend.
   */
  run(code: string): Observable<RunResponse> {
    return this.http.post<RunResponse>(`${this.apiUrl}/run`, { code });
  }
}
