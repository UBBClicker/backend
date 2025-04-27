import os
import sys
import subprocess
import time

# Define output file
output_file = "test_results.txt"

# Run tests using subprocess to capture all output
print(f"Running tests and saving output to {output_file}...")
with open(output_file, 'w') as f:
    f.write(f"Test run started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Run pytest with subprocess - include all test files
    process = subprocess.run(
        ["python3.11.exe", "-m", "pytest", "tests/", "-v"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Write output to file
    f.write("===== STDOUT =====\n")
    f.write(process.stdout)
    f.write("\n===== STDERR =====\n")
    f.write(process.stderr)
    f.write(f"\n\nExit code: {process.returncode}")
    f.write(f"\nTest run completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

print(f"Tests completed with exit code: {process.returncode}")
print(f"Full output saved to {output_file}")

# Print a summary of the results
print("\nTest Summary:")
if process.returncode == 0:
    print("✅ All tests PASSED!")
else:
    print("❌ Some tests FAILED!")