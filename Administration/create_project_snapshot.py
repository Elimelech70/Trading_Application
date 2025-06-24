import os
import fnmatch

# Define patterns to include and exclude
include_patterns = ['*.py', '*.md', '*.txt', '*.json', '*.yml', '*.yaml', 'requirements.txt', '.env.example']
exclude_dirs = ['.git', '__pycache__', 'backups', 'logs', '.vscode', 'venv', 'env']

def should_include_file(filepath):
    """Check if file should be included based on patterns"""
    filename = os.path.basename(filepath)
    return any(fnmatch.fnmatch(filename, pattern) for pattern in include_patterns)

def create_project_snapshot(output_file='project_snapshot.txt'):
    """Create a comprehensive snapshot of the project"""
    with open(output_file, 'w') as f:
        # Write header
        f.write("PROJECT SNAPSHOT\n")
        f.write("=" * 50 + "\n\n")
        
        # Walk through directory tree
        for root, dirs, files in os.walk('.'):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # Process files
            for file in sorted(files):
                filepath = os.path.join(root, file)
                if should_include_file(filepath):
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"FILE: {filepath}\n")
                    f.write(f"{'=' * 80}\n\n")
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as src:
                            f.write(src.read())
                    except Exception as e:
                        f.write(f"Error reading file: {e}\n")
                    
                    f.write("\n")
        
        print(f"Project snapshot created: {output_file}")

if __name__ == "__main__":
    create_project_snapshot()
