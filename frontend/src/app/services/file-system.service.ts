import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface FileNode {
  name: string;
  type: 'file' | 'folder';
  path: string;
  children?: FileNode[];
  content?: string;
  language?: string;
  icon?: string;
}

@Injectable({
  providedIn: 'root'
})
export class FileSystemService {
  private fileTreeSubject = new BehaviorSubject<FileNode[]>(this.initialFiles());
  private openFilesSubject = new BehaviorSubject<FileNode[]>([]);
  private activeFileSubject = new BehaviorSubject<FileNode | null>(null);

  fileTree$ = this.fileTreeSubject.asObservable();
  openFiles$ = this.openFilesSubject.asObservable();
  activeFile$ = this.activeFileSubject.asObservable();

  private initialFiles(): FileNode[] {
    return [
      {
        name: 'src',
        type: 'folder',
        path: '/src',
        icon: 'folder',
        children: [
          {
            name: 'index.ts',
            type: 'file',
            path: '/src/index.ts',
            icon: 'file',
            language: 'typescript',
            content: `// Main entry point
export function main() {
  console.log("Hello World");
}`
          },
          {
            name: 'utils.ts',
            type: 'file',
            path: '/src/utils.ts',
            icon: 'file',
            language: 'typescript',
            content: `// Utility functions
export function add(a: number, b: number): number {
  return a + b;
}`
          },
          {
            name: 'components',
            type: 'folder',
            path: '/src/components',
            icon: 'folder',
            children: []
          }
        ]
      },
      {
        name: 'main.lng',
        type: 'file',
        path: '/main.lng',
        icon: 'file-code',
        language: 'custom-lang',
        content: `// Exemple de programme
var x: int = 10;
var y: int = 20;

function add(a: int, b: int): int {
    return a + b;
}

if (x < y) {
    pf("x est plus petit que y");
    pf(add(x, y));
}`
      },
      {
        name: 'package.json',
        type: 'file',
        path: '/package.json',
        icon: 'file-text',
        language: 'json',
        content: `{
  "name": "my-project",
  "version": "1.0.0",
  "dependencies": {}
}`
      },
      {
        name: 'README.md',
        type: 'file',
        path: '/README.md',
        icon: 'book',
        language: 'markdown',
        content: `# My Project\n\nWelcome to my project.`
      }
    ];
  }

  openFile(file: FileNode) {
    const currentOpenFiles = this.openFilesSubject.value;
    
    // Ne pas ouvrir le même fichier deux fois
    if (!currentOpenFiles.some(f => f.path === file.path)) {
      this.openFilesSubject.next([...currentOpenFiles, file]);
    }
    
    this.setActiveFile(file);
  }

  setActiveFile(file: FileNode) {
    this.activeFileSubject.next(file);
  }

  closeFile(filePath: string) {
    const currentOpenFiles = this.openFilesSubject.value;
    const newOpenFiles = currentOpenFiles.filter(f => f.path !== filePath);
    this.openFilesSubject.next(newOpenFiles);
    
    // Si on ferme le fichier actif, activer un autre fichier
    if (this.activeFileSubject.value?.path === filePath && newOpenFiles.length > 0) {
      this.setActiveFile(newOpenFiles[newOpenFiles.length - 1]);
    }
  }

  updateFileContent(path: string, content: string) {
    // Mettre à jour le contenu dans l'arborescence
    const updateTree = (nodes: FileNode[]): FileNode[] => {
      return nodes.map(node => {
        if (node.path === path && node.type === 'file') {
          return { ...node, content };
        }
        if (node.children) {
          return { ...node, children: updateTree(node.children) };
        }
        return node;
      });
    };

    const newTree = updateTree(this.fileTreeSubject.value);
    this.fileTreeSubject.next(newTree);

    // Mettre à jour aussi dans les fichiers ouverts
    const updatedOpenFiles = this.openFilesSubject.value.map(file => 
      file.path === path ? { ...file, content } : file
    );
    this.openFilesSubject.next(updatedOpenFiles);
  }

  createFile(name: string, parentPath: string, type: 'file' | 'folder') {
    const path = `${parentPath}/${name}`;
    const newNode: FileNode = {
      name,
      type,
      path,
      icon: type === 'folder' ? 'folder' : 'file',
      children: type === 'folder' ? [] : undefined,
      content: type === 'file' ? '' : undefined,
      language: this.getLanguageFromExtension(name)
    };

    const addNode = (nodes: FileNode[]): FileNode[] => {
      return nodes.map(node => {
        if (node.path === parentPath && node.type === 'folder') {
          return {
            ...node,
            children: [...(node.children || []), newNode]
          };
        }
        if (node.children) {
          return { ...node, children: addNode(node.children) };
        }
        return node;
      });
    };

    const newTree = addNode(this.fileTreeSubject.value);
    this.fileTreeSubject.next(newTree);
  }

  private getLanguageFromExtension(filename: string): string {
    if (filename.endsWith('.ts')) return 'typescript';
    if (filename.endsWith('.js')) return 'javascript';
    if (filename.endsWith('.json')) return 'json';
    if (filename.endsWith('.md')) return 'markdown';
    if (filename.endsWith('.lng')) return 'custom-lang';
    return 'text';
  }
}