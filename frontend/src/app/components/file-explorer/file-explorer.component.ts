import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FileSystemService, FileNode } from '../../services/file-system.service';
import { Observable } from 'rxjs';
import { FileNodeComponent } from '../file-node/file-node.component';

@Component({
  selector: 'app-file-explorer',
  standalone: true,
  imports: [CommonModule, FileNodeComponent],
  templateUrl: './file-explorer.component.html',
  styleUrls: ['./file-explorer.component.css']
})
export class FileExplorerComponent implements OnInit {
  fileTree$: Observable<FileNode[]>;
  expandedFolders: Set<string> = new Set(['/src']);

  constructor(private fileSystem: FileSystemService) {
    this.fileTree$ = this.fileSystem.fileTree$;
  }

  ngOnInit() {}

  toggleFolder(path: string) {
    if (this.expandedFolders.has(path)) {
      this.expandedFolders.delete(path);
    } else {
      this.expandedFolders.add(path);
    }
  }

  isExpanded(path: string): boolean {
    return this.expandedFolders.has(path);
  }

  getIcon(node: FileNode): string {
    if (node.icon) return `codicon codicon-${node.icon}`;
    return node.type === 'folder' ? 'codicon codicon-folder' : 'codicon codicon-file';
  }

  getIconColor(node: FileNode): string {
    if (node.name.endsWith('.ts')) return 'text-blue-400';
    if (node.name.endsWith('.json')) return 'text-yellow-500';
    if (node.name.endsWith('.md')) return 'text-green-400';
    if (node.name.endsWith('.lng')) return 'text-orange-400';
    if (node.type === 'folder') return 'text-blue-400';
    return 'text-gray-500';
  }

  openFile(node: FileNode) {
    if (node.type === 'file') {
      this.fileSystem.openFile(node);
    } else {
      this.toggleFolder(node.path);
    }
  }

  createNewFile() {
    const name = prompt('Enter file name (with extension):');
    if (name) {
      this.fileSystem.createFile(name, '/src', 'file');
    }
  }

  createNewFolder() {
    const name = prompt('Enter folder name:');
    if (name) {
      this.fileSystem.createFile(name, '/src', 'folder');
    }
  }
}