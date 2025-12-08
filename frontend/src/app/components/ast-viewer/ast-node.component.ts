import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-ast-node',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './ast-node.component.html',
    styleUrls: ['./ast-node.component.css']
})
export class AstNodeComponent {
    @Input() node: any;
    expanded = true;

    toggle() {
        this.expanded = !this.expanded;
    }

    getKeys(node: any): string[] {
        return Object.keys(node).filter(k => k !== 'type');
    }

    isNode(value: any): boolean {
        return value && typeof value === 'object' && 'type' in value;
    }

    isNodeList(value: any): boolean {
        return Array.isArray(value) && value.length > 0 && this.isNode(value[0]);
    }

    hasValue(node: any): boolean {
        return 'value' in node || 'name' in node || 'operator' in node;
    }

    getValue(node: any): string {
        if ('value' in node) return String(node.value);
        if ('name' in node) return node.name;
        if ('operator' in node) return node.operator;
        return '';
    }
}
