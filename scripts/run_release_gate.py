# scripts/run_release_gate.py
"""
MASTER GO / NO-GO RUNNER
This runs strict suites, skips performance unless asked, generates JSON report.
"""

import os
import json
import subprocess
from datetime import datetime

REPORT_FILE = "release_gate_report.json"

def run(cmd: str, name: str):
    print("\n" + "="*60)
    print(f"RUN: {name}")
    print("="*60)
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return {
        "name": name,
        "cmd": cmd,
        "passed": p.returncode == 0,
        "returncode": p.returncode,
        "stdout_tail": p.stdout[-800:],
        "stderr_tail": p.stderr[-800:]
    }

def main():
    include_perf = os.getenv("ACP_RUN_PERFORMANCE", "false").lower() == "true"

    results = {
        "timestamp": datetime.now().isoformat(),
        "env": {
            "ACP_BASE_URL": os.getenv("ACP_BASE_URL"),
            "ACP_TEST_MODE": os.getenv("ACP_TEST_MODE"),
        },
        "suites": []
    }

    # strict suites
    results["suites"].append(run("pytest -v tests/test_01_contract_endpoints.py", "Contract endpoints"))
    results["suites"].append(run("pytest -v tests/test_02_safety_features.py", "Safety features"))
    results["suites"].append(run("pytest -v tests/test_03_idempotency.py", "Idempotency"))
    results["suites"].append(run("pytest -v tests/test_04_database_schema.py", "Database schema"))

    # probes (non-failing info)
    results["suites"].append(run("pytest -v tests/test_00_probes_paths.py", "Probes (paths discovery)"))

    # standalone validators
    results["suites"].append(run("python backend/test_idempotency_standalone.py", "Standalone idempotency"))
    results["suites"].append(run("python backend/validate_commissions_advanced.py", "Commission validator"))

    if include_perf:
        results["suites"].append(run("pytest -m performance -v tests/test_99_performance.py", "Performance"))

    # Decision logic
    critical_names = {"Contract endpoints", "Safety features", "Idempotency", "Database schema"}
    failed_critical = [s["name"] for s in results["suites"] if s["name"] in critical_names and not s["passed"]]

    if failed_critical:
        results["decision"] = "NO-GO"
        results["reason"] = f"Critical suites failed: {failed_critical}"
    else:
        results["decision"] = "GO (fix docs if probes show mismatch)"
        results["reason"] = "All critical suites passed"

    with open(REPORT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*60)
    print("RELEASE GATE RESULT")
    print("="*60)
    print(results["decision"])
    print(results["reason"])
    print(f"Report saved: {REPORT_FILE}")

if __name__ == "__main__":
    main()
