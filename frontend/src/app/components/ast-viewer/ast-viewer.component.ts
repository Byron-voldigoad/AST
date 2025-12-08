import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AstNodeComponent } from './ast-node.component';

@Component({
  selector: 'app-ast-viewer',
  standalone: true,
  imports: [CommonModule, AstNodeComponent],
  templateUrl: './ast-viewer.component.html',
  styleUrls: ['./ast-viewer.component.css']
})
export class AstViewerComponent {
  @Input() ast: any;
}
