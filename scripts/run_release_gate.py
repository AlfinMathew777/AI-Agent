"""
ACP Release Gate Automation
GO/NO-GO decision engine for production deployment
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

class ReleaseGate:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "suites": {},
            "critical_failures": [],
            "warnings": [],
            "decision": "PENDING",
            "reason": ""
        }
        self.critical_suites = [
            "test_01_contract_endpoints.py",
            "test_02_safety_features.py", 
            "test_03_idempotency.py",
            "test_04_database_schema.py"
        ]
    
    def run_suite(self, suite_file):
        """Run a test suite and capture results"""
        suite_name = suite_file.replace("test_", "").replace(".py", "")
        print(f"\n{'='*60}")
        print(f"Running: {suite_name}")
        print(f"{'='*60}")
        
        cmd = [
            sys.executable, "-m", "pytest",
            f"tests/{suite_file}",
            "-v",
            "--tb=short",
            "--no-header"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per suite
            )
            
            # Parse results - use returncode as primary signal
            passed = result.returncode == 0
            output = result.stdout + result.stderr
            
            # Count tests (best effort - output format varies)
            # This is informational only, returncode is the source of truth
            passed_count = output.count(" PASSED")
            failed_count = output.count(" FAILED")
            skipped_count = output.count(" SKIPPED")
            
            self.results["suites"][suite_name] = {
                "file": suite_file,
                "passed": passed,
                "returncode": result.returncode,
                "tests_passed": passed_count,
                "tests_failed": failed_count,
                "tests_skipped": skipped_count,
                "output_snippet": output[-800:] if len(output) > 800 else output
            }
            
            status = "✅ PASS" if passed else "❌ FAIL"
            count_info = f"({passed_count}P" + (f"/{failed_count}F" if failed_count else "") + (f"/{skipped_count}S" if skipped_count else "") + ")"
            print(f"{status} {count_info}")
            
            if not passed:
                print(f"Output preview:\n{output[-400:]}")
            
            return passed
            
        except subprocess.TimeoutExpired:
            self.results["suites"][suite_name] = {
                "file": suite_file,
                "passed": False,
                "error": "Timeout after 5 minutes"
            }
            print("❌ TIMEOUT")
            return False
        except Exception as e:
            self.results["suites"][suite_name] = {
                "file": suite_file,
                "passed": False,
                "error": str(e)
            }
            print(f"❌ ERROR: {e}")
            return False
    
    def run_probe_tests(self):
        """Run path discovery tests (informational)"""
        print(f"\n{'='*60}")
        print("Path Discovery (Informational)")
        print(f"{'='*60}")
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_00_probes_paths.py", "-v", "--no-header"],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        # Probes always "pass" but we log findings
        self.results["path_discovery"] = {
            "executed": True,
            "output": result.stdout[-600:]
        }
    
    def run_performance_tests(self):
        """Optional performance tests"""
        if os.getenv("ACP_RUN_PERFORMANCE", "false").lower() != "true":
            print("\n⏭️  Performance tests skipped (set ACP_RUN_PERFORMANCE=true to enable)")
            return True
        
        print(f"\n{'='*60}")
        print("Performance Tests (Optional)")
        print(f"{'='*60}")
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_99_performance.py", "-v", "-m", "performance"],
            capture_output=True,
            text=True
        )
        
        print(result.stdout[-500:])
        
        self.results["performance"] = {
            "executed": True,
            "output": result.stdout[-400:]
        }
        
        return True
    
    def make_decision(self):
        """Determine GO/NO-GO based on results"""
        critical_results = [
            self.results["suites"].get(s.replace("test_", "").replace(".py", ""), {}).get("passed", False)
            for s in self.critical_suites
        ]
        
        all_critical_passed = all(critical_results)
        
        if all_critical_passed:
            self.results["decision"] = "GO"
            self.results["reason"] = "All critical test suites passed"
            
            # Check for warnings
            if self.results["warnings"]:
                self.results["reason"] += f" ({len(self.results['warnings'])} warnings)"
        else:
            self.results["decision"] = "NO-GO"
            failed_suites = [
                name for name, data in self.results["suites"].items()
                if not data.get("passed") and f"test_{name}.py" in self.critical_suites
            ]
            self.results["reason"] = f"Critical suites failed: {', '.join(failed_suites)}"
    
    def print_summary(self):
        """Print final decision report"""
        print(f"\n{'='*60}")
        print("RELEASE GATE DECISION")
        print(f"{'='*60}")
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Decision:  {self.results['decision']}")
        print(f"Reason:    {self.results['reason']}")
        print(f"\nSuite Results:")
        
        for name, data in self.results["suites"].items():
            status = "✅" if data.get("passed") else "❌"
            details = f"({data.get('tests_passed', 0)}/{data.get('tests_passed', 0) + data.get('tests_failed', 0)})"
            print(f"   {status} {name:<25} {details}")
        
        if self.results["warnings"]:
            print(f"\nWarnings:")
            for w in self.results["warnings"][:5]:
                print(f"   ⚠️  {w}")
        
        print(f"\n{'='*60}")
    
    def save_report(self):
        """Save JSON report"""
        report_file = "release_gate_report.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Report saved: {report_file}")
    
    def run(self):
        """Execute full release gate"""
        print("🚀 ACP RELEASE GATE")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Working directory: {os.getcwd()}")
        
        # Verify test directory exists
        if not Path("tests").exists():
            print("❌ ERROR: tests/ directory not found")
            sys.exit(1)
        
        # Run probe tests first (informational)
        self.run_probe_tests()
        
        # Run critical suites
        all_passed = True
        for suite in self.critical_suites:
            if not self.run_suite(suite):
                all_passed = False
        
        # Optional performance tests
        self.run_performance_tests()
        
        # Make decision
        self.make_decision()
        
        # Output results
        self.print_summary()
        self.save_report()
        
        # Exit with appropriate code
        if self.results["decision"] == "GO":
            print("\n✅ RELEASE APPROVED")
            return 0
        else:
            print("\n❌ RELEASE BLOCKED")
            return 1

if __name__ == "__main__":
    gate = ReleaseGate()
    sys.exit(gate.run())
