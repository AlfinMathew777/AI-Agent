import os
from pathlib import Path

total_lines = 0
file_counts = {}
extensions = {'.py': 'Python', '.js': 'JavaScript', '.jsx': 'React', '.css': 'CSS', '.html': 'HTML'}
exclude_dirs = {'node_modules', 'venv', '.venv', '__pycache__', '.git', 'dist', 'build'}

for root, dirs, files in os.walk('.'):
    # Remove excluded directories
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    
    for file in files:
        ext = Path(file).suffix
        if ext in extensions:
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    total_lines += lines
                    lang = extensions[ext]
                    if lang not in file_counts:
                        file_counts[lang] = {'files': 0, 'lines': 0}
                    file_counts[lang]['files'] += 1
                    file_counts[lang]['lines'] += lines
            except:
                pass

print("\n" + "="*50)
print("CODE STATISTICS FOR YOUR PROJECT")
print("="*50)
for lang, stats in sorted(file_counts.items()):
    print(f"{lang:15} {stats['files']:4} files  {stats['lines']:7,} lines")
print("="*50)
print(f"{'TOTAL':15} {sum(s['files'] for s in file_counts.values()):4} files  {total_lines:7,} lines")
print("="*50)
