import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-syntax-reference',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './syntax-reference.component.html',
  styleUrls: ['./syntax-reference.component.css']
})
export class SyntaxReferenceComponent {
  currentLanguage: string = 'TypeScript';
  tabs: string[] = ['Variables', 'Functions', 'Loops', 'Classes'];
  activeTab: string = 'Variables';

  setActiveTab(tab: string) {
    this.activeTab = tab;
  }
}