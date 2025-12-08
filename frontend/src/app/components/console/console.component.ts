import { Component, Input, OnChanges, SimpleChanges, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-console',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './console.component.html',
  styleUrls: ['./console.component.css']
})
export class ConsoleComponent implements OnChanges {
  @Input() logs: { message: string, type: 'info' | 'error' | 'success' }[] = [];
  @ViewChild('scrollContainer') scrollContainer!: ElementRef;

  ngOnChanges(changes: SimpleChanges) {
    if (changes['logs']) {
      setTimeout(() => this.scrollToBottom(), 100);
    }
  }

  scrollToBottom(): void {
    if (this.scrollContainer) {
      this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
    }
  }

  clear() {
    this.logs = [];
  }
}
