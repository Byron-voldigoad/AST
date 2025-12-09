import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FileSystemService, FileNode } from '../../services/file-system.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-file-tabs',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './file-tabs.component.html',
  styleUrls: ['./file-tabs.component.css']
})
export class FileTabsComponent {
  openFiles$: Observable<FileNode[]>;
  activeFile$: Observable<FileNode | null>;

  constructor(private fileSystem: FileSystemService) {
    this.openFiles$ = this.fileSystem.openFiles$;
    this.activeFile$ = this.fileSystem.activeFile$;
  }

  setActiveFile(file: FileNode) {
    this.fileSystem.setActiveFile(file);
  }

  closeFile(file: FileNode, event: MouseEvent) {
    event.stopPropagation();
    this.fileSystem.closeFile(file.path);
  }

  getFileIcon(file: FileNode): string {
    if (file.name.endsWith('.lng')) return 'codicon codicon-file-code text-orange-400';
    if (file.name.endsWith('.ts')) return 'codicon codicon-file-code text-blue-400';
    if (file.name.endsWith('.json')) return 'codicon codicon-file-text text-yellow-500';
    if (file.name.endsWith('.md')) return 'codicon codicon-book text-green-400';
    return 'codicon codicon-file text-gray-500';
  }
}