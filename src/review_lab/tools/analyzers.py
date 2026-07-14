import ast
import tempfile
import subprocess
from langchain_core.tools import tool

@tool
def analyze_style(code: str) -> str:
    """
    Analyzes Python code for style and PEP 8 violations using Pylint.
    Use this tool when evaluating code readability and formatting.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        # Run pylint on the temporary file
        result = subprocess.run(
            ['pylint', temp_file_path],
            capture_output=True,
            text=True
        )
        # Pylint usually returns non-zero exit codes if any issues are found
        output = result.stdout if result.stdout else result.stderr
        return output[:1500]  # Truncate to avoid context window overflow
    except Exception as e:
        return f"Style analysis failed: {str(e)}"

@tool
def analyze_security(code: str) -> str:
    """
    Analyzes Python code for common security vulnerabilities using Bandit.
    Use this tool when checking for hardcoded secrets, injection flaws, etc.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    try:
        # Run bandit on the temporary file
        result = subprocess.run(
            ['bandit', '-r', temp_file_path, '-f', 'txt'],
            capture_output=True,
            text=True
        )
        output = result.stdout if result.stdout else result.stderr
        return output[:1500]
    except Exception as e:
        return f"Security analysis failed: {str(e)}"

@tool
def analyze_performance(code: str) -> str:
    """
    Analyzes Python code for cyclomatic complexity and performance bottlenecks using AST.
    Use this tool when evaluating code efficiency.
    """
    try:
        tree = ast.parse(code)
        loops = sum(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))
        functions = sum(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
        nested_loops = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if child != node and isinstance(child, (ast.For, ast.While)):
                        nested_loops += 1

        report = (
            f"AST Analysis Report:\n"
            f"- Total Functions: {functions}\n"
            f"- Total Loops: {loops}\n"
            f"- Nested Loops (High Complexity Risk): {nested_loops}\n"
        )
        
        if nested_loops > 0:
            report += "Warning: O(N^2) or higher time complexity detected due to nested loops."
            
        return report
    except SyntaxError as e:
        return f"Code syntax is invalid, AST parsing failed: {e}"