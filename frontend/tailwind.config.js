/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{html,ts}",
    ],
    theme: {
        extend: {
            colors: {
                'vscode-base': '#1e1e1e',
                'vscode-sidebar': '#252526',
                'vscode-activity': '#333333',
                'vscode-status': '#007acc',
                'vscode-border': '#333333',
                'vscode-text': '#cccccc',
                'vscode-tab-active': '#1e1e1e',
                'vscode-tab-inactive': '#2d2d2d',
                'vscode-hover': '#2a2d2e',
                'vscode-selection': '#37373d',
            },
            fontFamily: {
                'sans': ['Segoe UI', 'Tahoma', 'Geneva', 'Verdana', 'sans-serif'],
                'mono': ['Consolas', 'Courier New', 'monospace'],
            }
        },
    },
    plugins: [],
}
