import sys
import os

# Assume we are running from project root or backend
current_dir = os.getcwd()
print(f"Current Directory: {current_dir}")

# Add valid paths
if os.path.basename(current_dir) == "ai-hotel-assistant":
    sys.path.append(os.path.join(current_dir, "backend"))
elif os.path.basename(current_dir) == "backend":
    sys.path.append(current_dir)

print(f"Python Path: {sys.path}")
import threading
import time
import os

print("--- Debugging Imports ---")

def test_import(module_name):
    print(f"Importing {module_name}...")
    try:
        __import__(module_name)
        print(f"OK {module_name} imported.")
    except Exception as e:
        print(f"XX {module_name} failed: {e}")

# threading timeout wrapper
def run_with_timeout(func, args=(), timeout=5):
    t = threading.Thread(target=func, args=args)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        print(f"X TIMEOUT importing {args[0]}!")
        os._exit(1)

run_with_timeout(test_import, ("mcp",))
run_with_timeout(test_import, ("google.generativeai",))
run_with_timeout(test_import, ("chromadb",))
run_with_timeout(test_import, ("app.llm",))
run_with_timeout(test_import, ("app.ai_service",))
run_with_timeout(test_import, ("app.main",))

