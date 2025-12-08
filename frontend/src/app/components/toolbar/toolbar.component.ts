import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-toolbar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './toolbar.component.html',
  styleUrls: ['./toolbar.component.css']
})
export class ToolbarComponent {
  @Input() isAnalyzing: boolean = false;
  @Input() isRunning: boolean = false;
  @Input() loading = false;

  @Output() analyze = new EventEmitter<void>();
  @Output() run = new EventEmitter<void>();
}
