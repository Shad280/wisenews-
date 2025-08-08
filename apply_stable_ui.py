#!/usr/bin/env python3
"""
Script to automatically apply stable UI classes to remaining WiseNews templates
"""

import os
import re

def apply_stable_classes(file_path):
    """Apply stable UI classes to a template file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply common replacements
        replacements = [
            # Basic elements
            (r'<div class="card"([^>]*)>', r'<div class="card stable-card"\1>'),
            (r'<div class="card-body"([^>]*)>', r'<div class="card-body stable-card-body"\1>'),
            (r'<div class="card-header"([^>]*)>', r'<div class="card-header stable-header"\1>'),
            
            # Form elements
            (r'<form([^>]*)>', r'<form\1 class="stable-form">'),
            (r'<div class="form-group"([^>]*)>', r'<div class="form-group stable-form-group"\1>'),
            (r'<label([^>]*class="[^"]*)"([^>]*)>', r'<label\1 stable-label"\2>'),
            (r'<label([^>]*(?<!class=")[^>]*)>', r'<label\1 class="stable-label">'),
            (r'<input([^>]*class="form-control[^"]*)"([^>]*)>', r'<input\1 stable-input"\2>'),
            (r'<select([^>]*class="form-select[^"]*)"([^>]*)>', r'<select\1 stable-select"\2>'),
            (r'<textarea([^>]*class="form-control[^"]*)"([^>]*)>', r'<textarea\1 stable-textarea"\2>'),
            
            # Buttons
            (r'<button([^>]*class="btn[^"]*)"([^>]*)>', r'<button\1 stable-btn"\2>'),
            (r'<a([^>]*class="btn[^"]*)"([^>]*)>', r'<a\1 stable-btn"\2>'),
            
            # Containers with fade-in
            (r'<div class="container"([^>]*)>', r'<div class="container fade-in"\1>'),
            (r'<div class="container-fluid"([^>]*)>', r'<div class="container-fluid fade-in"\1>'),
            
            # Titles
            (r'<h1([^>]*)>([^<]*)</h1>', r'<h1\1 class="stable-page-title">\2</h1>'),
            (r'<h4([^>]*class="[^"]*)"([^>]*)>([^<]*)</h4>', r'<h4\1 stable-title"\2>\3</h4>'),
            (r'<h5([^>]*class="[^"]*)"([^>]*)>([^<]*)</h5>', r'<h5\1 stable-title"\2>\3</h5>'),
        ]
        
        # Apply replacements
        modified = False
        for pattern, replacement in replacements:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                modified = True
                content = new_content
        
        # Write back if modified
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Applied stable classes to: {file_path}")
            return True
        else:
            print(f"No changes needed for: {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all template files"""
    templates_dir = "templates"
    
    # Files to skip (already processed manually)
    skip_files = {
        'base.html', 'articles.html', 'dashboard.html', 'index.html', 
        'login.html', 'register.html', 'search.html', 'settings.html', 'profile.html'
    }
    
    processed_count = 0
    
    if not os.path.exists(templates_dir):
        print(f"Templates directory not found: {templates_dir}")
        return
    
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html') and filename not in skip_files:
            file_path = os.path.join(templates_dir, filename)
            if os.path.isfile(file_path):
                if apply_stable_classes(file_path):
                    processed_count += 1
    
    print(f"\nProcessed {processed_count} template files with stable UI improvements")

if __name__ == "__main__":
    main()
