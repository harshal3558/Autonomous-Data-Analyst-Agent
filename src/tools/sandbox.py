import sys
import io
import os
import traceback
import matplotlib
import ast
# Use a non-interactive backend (Agg) to prevent GUI popup freezes on Windows
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.config import OUTPUT_DIR

# Keep a session log of all generated charts
session_charts = []

def validate_code_safety(code_str: str) -> tuple[bool, str]:
    """
    Validates Python code syntax using AST to ensure it does not use harmful imports or functions.
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"

    FORBIDDEN_IMPORTS = {
        'os', 'subprocess', 'shutil', 'socket', 'urllib', 'requests', 'builtins', 
        'ctypes', 'threading', 'multiprocessing', 'sys', 'importlib'
    }
    FORBIDDEN_CALLS = {
        'eval', 'exec', 'open', 'compile', 'getattr', 'setattr', 'delattr', 'globals', 'locals'
    }

    for node in ast.walk(tree):
        # Block standard imports of forbidden modules
        if isinstance(node, ast.Import):
            for name in node.names:
                if name.name.split('.')[0] in FORBIDDEN_IMPORTS:
                    return False, f"Security Violation: Import of module '{name.name}' is blocked."

        # Block specific import modules
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in FORBIDDEN_IMPORTS:
                return False, f"Security Violation: Import from module '{node.module}' is blocked."

        # Block forbidden built-in calls (eval, exec, open)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_CALLS:
                    return False, f"Security Violation: Call to built-in function '{node.func.id}' is blocked."

        # Block direct references to blocked modules
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_IMPORTS:
                return False, f"Security Violation: Reference to blocked module/variable '{node.id}' is forbidden. Use pre-loaded utilities (e.g. path_join)."

    return True, ""

def execute_python_code(code_str: str) -> dict:
    """
    Executes Python data analysis code in a controlled namespace.
    Redirects stdout and stderr, intercepts matplotlib figure generation,
    and automatically saves charts to the output directory.
    
    Returns a dictionary:
    {
        "success": bool,
        "stdout": str,
        "stderr": str,
        "charts": list of filenames (e.g. ['chart_1.png'])
    }
    """
    global session_charts
    
    # Clean code formatting if it is inside markdown blocks
    cleaned_code = code_str.strip()
    if cleaned_code.startswith("```"):
        lines = cleaned_code.splitlines()
        if lines[0].startswith("```python") or lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned_code = "\n".join(lines)
        
    # Redirect system streams to capture print statements & error traceback
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    sys.stdout = captured_stdout
    sys.stderr = captured_stderr
    
    # Run AST security checks
    is_safe, error_msg = validate_code_safety(cleaned_code)
    if not is_safe:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        return {
            "success": False,
            "stdout": "",
            "stderr": error_msg,
            "charts": []
        }
    
    orig_show = plt.show
    orig_savefig = plt.savefig
    
    new_charts = []
    
    # Custom matplotlib wrapper to save plot instead of blocking GUI execution
    def custom_show(*args, **kwargs):
        fig = plt.gcf()
        if fig and fig.get_axes():
            chart_index = len(session_charts) + len(new_charts) + 1
            filename = f"chart_{chart_index}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            orig_savefig(filepath, bbox_inches="tight", dpi=150)
            new_charts.append(filename)
            plt.close(fig) # close to free memory
            print(f"[Visual Chart Saved: {filename}]")
        else:
            print("[Warning] No active visual chart to display.")

    def custom_savefig(fname, *args, **kwargs):
        if isinstance(fname, str):
            filename = os.path.basename(fname)
            filepath = os.path.join(OUTPUT_DIR, filename)
            # Route to our output directory
            orig_savefig(filepath, *args, **kwargs)
            new_charts.append(filename)
            print(f"[Visual Chart Saved: {filename}]")
        else:
            orig_savefig(fname, *args, **kwargs)
            
    # Mocking environment variables & pre-imported libraries
    import pandas as pd
    import numpy as np
    import seaborn as sns
    
    execution_globals = {
        "pd": pd,
        "np": np,
        "plt": plt,
        "sns": sns,
        "OUTPUT_DIR": OUTPUT_DIR,
        "path_join": os.path.join,
        "__builtins__": __builtins__
    }
    
    # Override standard matplotlib visualization functions
    plt.show = custom_show
    plt.savefig = custom_savefig
    
    success = True
    try:
        # Execute the python code block
        exec(cleaned_code, execution_globals)
    except Exception as e:
        success = False
        # Log the detailed traceback directly into standard error capture
        traceback.print_exc(file=captured_stderr)
    finally:
        # Restore normal matplotlib behavior
        plt.show = orig_show
        plt.savefig = orig_savefig
        
        # Restore standard streams
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
    stdout_text = captured_stdout.getvalue()
    stderr_text = captured_stderr.getvalue()
    
    # Add new charts to global list
    session_charts.extend(new_charts)
    
    return {
        "success": success,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "charts": new_charts
    }
