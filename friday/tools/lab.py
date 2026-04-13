"""
Lab Intelligence tools — workspace awareness, project scanning, and dev env info.
"""

import os
import subprocess
import glob

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {e}"

def register(mcp):

    @mcp.tool()
    def scan_projects(root: str = "d:\\", max_depth: int = 2) -> str:
        """Scans the given root directory for active projects (looks for .git or README)."""
        projects = []
        try:
            root_path = os.path.abspath(root)
            for dirpath, dirnames, filenames in os.walk(root_path):
                depth = dirpath[len(root_path):].count(os.sep)
                if depth >= max_depth:
                    dirnames.clear()
                    continue
                
                # Exclude obvious non-projects
                if any(x in dirpath for x in ['.venv', 'node_modules', '.git', '__pycache__']):
                    continue
                
                if '.git' in dirnames or 'README.md' in filenames or 'pyproject.toml' in filenames or 'package.json' in filenames:
                    # Found a project
                    size = 0
                    file_count = 0
                    for root2, _, files2 in os.walk(dirpath):
                        if any(x in root2 for x in ['.venv', 'node_modules', '.git']): continue
                        file_count += len(files2)
                        size += sum(os.path.getsize(os.path.join(root2, name)) for name in files2)
                    projects.append(f"- {os.path.basename(dirpath)} ({dirpath}) | Files: {file_count} | Size: {size / (1024*1024):.1f}MB")
                    # Don't recurse deeper if it's already a project
                    dirnames.clear()
        except Exception as e:
            return f"Failed to scan: {e}"

        if not projects:
            return f"No projects found in {root} up to depth {max_depth}."
        
        return f"## LAB PROJECTS FOUND IN {root} ##\n" + "\n".join(projects)

    @mcp.tool()
    def get_git_status(path: str) -> str:
        """Gets the git status, branch, stash, and recent commits for a project."""
        if not os.path.exists(os.path.join(path, '.git')):
            return f"Not a git repository: {path}"
        
        report = [f"## GIT STATUS: {os.path.basename(path)} ##"]
        report.append("\nBRANCH:')\n" + run_cmd("git branch --show-current", cwd=path))
        report.append("\nSTATUS:')\n" + run_cmd("git status -s", cwd=path))
        report.append("\nRECENT COMMITS:')\n" + run_cmd("git log -n 8 --oneline", cwd=path))
        
        stash = run_cmd("git stash list", cwd=path)
        if stash and not stash.startswith('Error'):
            report.append("\nSTASH:')\n" + stash)
            
        return "\n".join(report)

    @mcp.tool()
    def analyze_project(path: str) -> str:
        """Analyzes a project directory, calculating file count, total size, and languages."""
        if not os.path.exists(path):
            return "Path not found."
            
        ext_sizes = {}
        total_size = 0
        total_files = 0
        for root, dirs, files in os.walk(path):
            if any(x in root for x in ['.venv', 'node_modules', '.git']): continue
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    total_size += size
                    total_files += 1
                    ext = os.path.splitext(file)[1].lower() or 'no_ext'
                    ext_sizes[ext] = ext_sizes.get(ext, 0) + size
                except OSError: pass
                
        # Sort extensions by size
        sorted_exts = sorted(ext_sizes.items(), key=lambda x: x[1], reverse=True)[:5]
        
        report = [f"## PROJECT ANALYSIS: {os.path.basename(path)} ##"]
        report.append(f"Total Files: {total_files}")
        report.append(f"Total Size: {total_size / (1024*1024):.1f} MB")
        for ext, size in sorted_exts:
            pct = (size / total_size) * 100 if total_size else 0
            filled = int(pct / 5)
            bar = f"[{'#' * filled}{'-' * (20 - filled)}]"
            report.append(f"  {ext:6} : {bar} {pct:05.1f}%")
            
        return "\n".join(report)

    @mcp.tool()
    def find_todos(path: str, keywords: str = "TODO,FIXME,HACK,NOTE") -> str:
        """Searches for TODO/FIXME/etc comments across source files."""
        if not os.path.exists(path):
            return "Path not found."
            
        kws = [k.strip() for k in keywords.split(',')]
        results = []
        for root, _, files in os.walk(path):
            if any(x in root for x in ['.venv', 'node_modules', '.git']): continue
            for file in files:
                if not file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.md', '.txt', '.go', '.rs', '.java', '.c', '.cpp', '.h')):
                    continue
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f):
                            if any(k in line for k in kws):
                                results.append(f"{file}:{i+1} : {line.strip()}")
                except Exception: pass
                
        if not results:
            return f"No occurrences of {keywords} found."
        
        # limit results
        header = f"Found {len(results)} items. "
        if len(results) > 50:
            header += "Showing first 50."
            results = results[:50]
        return header + "\n" + "\n".join(results)

    @mcp.tool()
    def get_environment_info() -> str:
        """Gets active venv info, and system versions for Node/Go/Rust/Docker etc."""
        report = ["## ENVIRONMENT VERSIONS ##"]
        
        venv = os.environ.get("VIRTUAL_ENV", "None")
        report.append(f"Active VirtualEnv: {venv}")
        
        cmds = {
            "Node.js": "node --version",
            "NPM": "npm --version",
            "Go": "go version",
            "Rust": "rustc --version",
            "Docker": "docker --version",
            "Python": "python --version",
            "Pip": "pip --version"
        }
        
        for name, cmd in cmds.items():
            res = run_cmd(cmd)
            report.append(f"{name:8}: {res if not res.startswith('Error') else 'Not installed or error'}")
            
        return "\n".join(report)
