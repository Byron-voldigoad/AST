import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FileNode } from '../../services/file-system.service';

@Component({
  selector: 'app-file-node',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './file-node.component.html',
  styleUrls: ['./file-node.component.css']
})
export class FileNodeComponent {
  @Input() node!: FileNode;
  @Input() expanded: boolean = false;
  @Output() toggle = new EventEmitter<string>();
  @Output() open = new EventEmitter<FileNode>();

  getIcon(): string {
    if (this.node.icon) return `codicon codicon-${this.node.icon}`;
    return this.node.type === 'folder' ? 'codicon codicon-folder' : 'codicon codicon-file';
  }

  getIconColor(): string {
    if (this.node.name.endsWith('.ts')) return 'text-blue-400';
    if (this.node.name.endsWith('.json')) return 'text-yellow-500';
    if (this.node.name.endsWith('.md')) return 'text-green-400';
    if (this.node.name.endsWith('.lng')) return 'text-orange-400';
    if (this.node.type === 'folder') return 'text-blue-400';
    return 'text-gray-500';
  }

  onToggle() {
    if (this.node.type === 'folder') {
      this.toggle.emit(this.node.path);
    }
  }

  onClick() {
    if (this.node.type === 'file') {
      this.open.emit(this.node);
    } else {
      this.onToggle();
    }
  }
}