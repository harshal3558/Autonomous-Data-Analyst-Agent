import os
from src.tools.sandbox import execute_python_code
from src.config import OUTPUT_DIR

def test_sandbox():
    print("[*] Testing Python code execution sandbox...")
    
    # 1. Clean output directory
    for file in os.listdir(OUTPUT_DIR):
        if file.startswith("chart_") or file.endswith(".png"):
            try:
                os.remove(os.path.join(OUTPUT_DIR, file))
            except Exception:
                pass

    # 2. Define test code
    test_code = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Generate dummy data
dates = pd.date_range(start="2026-06-01", periods=10, freq="D")
values = np.random.randn(10).cumsum()
df = pd.DataFrame({"Date": dates, "Value": values})

print(f"Dataframe size: {df.shape}")
print(df.head(2).to_string())

# Plot chart
plt.figure(figsize=(8, 4))
plt.plot(df["Date"], df["Value"], marker='o', color='purple')
plt.title("Sandbox Automated Verification Plot")
plt.xlabel("Date")
plt.ylabel("Value")
plt.grid(True)
plt.show() # Should be intercepted and saved
"""
    
    # 3. Execute code in sandbox
    result = execute_python_code(test_code)
    
    print("\nSandbox Result Keys:", list(result.keys()))
    print("Success status:", result["success"])
    print("StdoutCaptured:\n", result["stdout"])
    print("StderrCaptured:\n", result["stderr"])
    print("Charts generated:", result["charts"])
    
    # 4. Assertions
    assert result["success"] is True, "Execution failed!"
    assert len(result["charts"]) == 1, "Expected exactly 1 chart to be generated!"
    
    chart_filename = result["charts"][0]
    chart_path = os.path.join(OUTPUT_DIR, chart_filename)
    assert os.path.exists(chart_path), f"Chart file {chart_path} does not exist!"
    
    print("\n[SUCCESS] Sandbox verification test PASSED successfully!")
    print(f"Saved chart exists at: {chart_path}")
    
    # 5. Run Guardrails Tests
    test_sandbox_security_guardrails()

def test_sandbox_security_guardrails():
    print("\n[*] Testing Sandbox Security Guardrails...")
    
    # Attempt 1: Blocked Import
    malicious_code_1 = """
import subprocess
print("Running command...")
"""
    result_1 = execute_python_code(malicious_code_1)
    print("Test 1 (Forbidden Import):")
    print(f"  Success: {result_1['success']}")
    print(f"  Error: {result_1['stderr'].strip()}")
    assert result_1["success"] is False
    assert "Security Violation" in result_1["stderr"]
    
    # Attempt 2: Blocked Function Call
    malicious_code_2 = """
eval("2 + 2")
"""
    result_2 = execute_python_code(malicious_code_2)
    print("Test 2 (Forbidden Call):")
    print(f"  Success: {result_2['success']}")
    print(f"  Error: {result_2['stderr'].strip()}")
    assert result_2["success"] is False
    assert "Security Violation" in result_2["stderr"]

    # Attempt 3: Blocked OS module access
    malicious_code_3 = """
import os
os.system("echo Hello")
"""
    result_3 = execute_python_code(malicious_code_3)
    print("Test 3 (Blocked OS Reference):")
    print(f"  Success: {result_3['success']}")
    print(f"  Error: {result_3['stderr'].strip()}")
    assert result_3["success"] is False
    assert "Security Violation" in result_3["stderr"]
    
    print("\n[SUCCESS] Sandbox Security Guardrails PASSED successfully!")

if __name__ == "__main__":
    test_sandbox()
