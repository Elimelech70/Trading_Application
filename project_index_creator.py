import os
import fnmatch

# GitHub repository information - UPDATE THESE!
GITHUB_USERNAME = "Elimelech70"  # Your GitHub username
REPO_NAME = "Trading_Application"  # Your repository name
BRANCH = "main"  # Branch name (usually 'main' or 'master')

# Define patterns to include and exclude
include_patterns = ['*.py', '*.md', '*.txt', '*.json', '*.yml', '*.yaml', 'requirements.txt', '.env.example']
exclude_dirs = ['.git', '__pycache__', 'backups', 'logs', '.vscode', 'venv', 'env', '.idea', 'node_modules']
exclude_files = ['project_snapshot.txt', 'project_index.txt']  # Exclude output files

def should_include_file(filepath):
    """Check if file should be included based on patterns"""
    filename = os.path.basename(filepath)
    # Exclude specific files
    if filename in exclude_files:
        return False
    return any(fnmatch.fnmatch(filename, pattern) for pattern in include_patterns)

def path_to_github_url(filepath):
    """Convert local file path to GitHub raw URL"""
    # Normalize path and remove leading './'
    normalized_path = filepath.replace('\\', '/').lstrip('./')
    
    # Create GitHub raw URL
    github_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/refs/heads/{BRANCH}/{normalized_path}"
    return github_url

def create_project_index(output_file='project_index.txt'):
    """Create an index of project files with GitHub URLs"""
    files_data = []
    
    # Walk through directory tree
    for root, dirs, files in os.walk('.'):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Process files
        for file in sorted(files):
            filepath = os.path.join(root, file)
            if should_include_file(filepath):
                files_data.append({
                    'path': filepath,
                    'url': path_to_github_url(filepath),
                    'category': get_file_category(filepath)
                })
    
    # Write the index file
    with open(output_file, 'w') as f:
        f.write("PROJECT FILE INDEX\n")
        f.write("=" * 80 + "\n")
        f.write(f"Repository: {GITHUB_USERNAME}/{REPO_NAME}\n")
        f.write(f"Branch: {BRANCH}\n")
        f.write(f"Total files indexed: {len(files_data)}\n")
        f.write("=" * 80 + "\n\n")
        
        # Group files by category
        categories = {}
        for file_info in files_data:
            category = file_info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(file_info)
        
        # Write files by category
        for category in sorted(categories.keys()):
            f.write(f"\n{category.upper()}\n")
            f.write("-" * len(category) + "\n")
            
            for file_info in sorted(categories[category], key=lambda x: x['path']):
                f.write(f"\nFile: {file_info['path']}\n")
                f.write(f"URL: {file_info['url']}\n")
    
    print(f"Project index created: {output_file}")
    print(f"Total files indexed: {len(files_data)}")

def get_file_category(filepath):
    """Categorize files based on their path and extension"""
    ext = os.path.splitext(filepath)[1].lower()
    path_lower = filepath.lower()
    
    # Categorization logic
    if 'test' in path_lower:
        return 'Tests'
    elif 'doc' in path_lower or ext in ['.md', '.txt']:
        return 'Documentation'
    elif 'config' in path_lower or ext in ['.json', '.yml', '.yaml']:
        return 'Configuration'
    elif ext == '.py':
        if 'model' in path_lower:
            return 'Models'
        elif 'service' in path_lower:
            return 'Services'
        elif 'util' in path_lower:
            return 'Utilities'
        else:
            return 'Python Files'
    else:
        return 'Other'

def create_markdown_index(output_file='project_index.md'):
    """Create a markdown version of the project index"""
    files_data = []
    
    # Walk through directory tree
    for root, dirs, files in os.walk('.'):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Process files
        for file in sorted(files):
            filepath = os.path.join(root, file)
            if should_include_file(filepath):
                files_data.append({
                    'path': filepath,
                    'url': path_to_github_url(filepath),
                    'category': get_file_category(filepath)
                })
    
    # Write the markdown index file
    with open(output_file, 'w') as f:
        f.write("# Project File Index\n\n")
        f.write(f"**Repository:** [{GITHUB_USERNAME}/{REPO_NAME}](https://github.com/{GITHUB_USERNAME}/{REPO_NAME})\n")
        f.write(f"**Branch:** {BRANCH}\n")
        f.write(f"**Total files:** {len(files_data)}\n\n")
        
        # Group files by category
        categories = {}
        for file_info in files_data:
            category = file_info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(file_info)
        
        # Create table of contents
        f.write("## Table of Contents\n\n")
        for category in sorted(categories.keys()):
            f.write(f"- [{category}](#{category.lower().replace(' ', '-')})\n")
        f.write("\n")
        
        # Write files by category
        for category in sorted(categories.keys()):
            f.write(f"## {category}\n\n")
            
            for file_info in sorted(categories[category], key=lambda x: x['path']):
                f.write(f"- **{file_info['path']}**\n")
                f.write(f"  - [View Raw]({file_info['url']})\n")
    
    print(f"Markdown index created: {output_file}")

if __name__ == "__main__":
    # Create both text and markdown versions
    create_project_index()
    create_markdown_index()
