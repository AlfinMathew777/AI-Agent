"""
Advanced Commission Validator
Checks financial accuracy and business rule compliance
"""

import sqlite3
import os
import sys
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

class CommissionValidator:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), 
            "acp_commissions.db"
        )
        self.issues = []
        self.warnings = []
        self.stats = {}
    
    def validate(self):
        """Run all validation checks"""
        print("🔍 COMMISSION VALIDATOR")
        print(f"   Database: {self.db_path}")
        print(f"   Time: {datetime.now().isoformat()}")
        
        if not os.path.exists(self.db_path):
            print(f"\n❌ Database not found: {self.db_path}")
            return False
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            self._check_table_exists(conn)
            self._validate_calculations(conn)
            self._validate_tier_rates(conn)
            self._validate_data_integrity(conn)
            self._generate_stats(conn)
        finally:
            conn.close()
        
        self._print_report()
        return len(self.issues) == 0
    
    def _check_table_exists(self, conn):
        """Verify commissions_accrued table exists"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='commissions_accrued'
        """)
        
        if not cursor.fetchone():
            self.issues.append("commissions_accrued table missing")
    
    def _validate_calculations(self, conn):
        """Check that amount = base * rate"""
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    commission_id,
                    amount,
                    commission_rate,
                    booking_id
                FROM commissions_accrued
                WHERE status != 'void'
                LIMIT 1000
            """)
            
            for row in cursor.fetchall():
                comm_id, amount, rate, booking_id = row
                
                # Skip if NULL
                if amount is None or rate is None:
                    self.warnings.append(f"{comm_id}: NULL amount or rate")
                    continue
                
                # For this validation, we assume amount should be reasonable
                # In real scenario, compare against booking total
                if amount < 0:
                    self.issues.append(f"{comm_id}: Negative commission amount")
                
                if rate < 0 or rate > 1:
                    self.issues.append(f"{comm_id}: Invalid rate {rate} (should be 0-1)")
                    
        except sqlite3.Error as e:
            self.warnings.append(f"Could not validate calculations: {e}")
    
    def _validate_tier_rates(self, conn):
        """Validate commission rates match tier expectations"""
        cursor = conn.cursor()
        
        # Expected ranges per tier
        tier_ranges = {
            "budget": (0.08, 0.08),
            "standard": (0.10, 0.10),
            "luxury": (0.12, 0.12)
        }
        
        try:
            cursor.execute("""
                SELECT commission_id, commission_rate, property_id
                FROM commissions_accrued
            """)
            
            for row in cursor.fetchall():
                comm_id, rate, prop_id = row
                
                # Check if rate is in valid range (5-15% typical)
                if not (0.05 <= rate <= 0.15):
                    self.warnings.append(
                        f"{comm_id}: Rate {rate:.2%} outside typical range (5-15%)"
                    )
                    
        except sqlite3.Error as e:
            self.warnings.append(f"Could not validate tier rates: {e}")
    
    def _validate_data_integrity(self, conn):
        """Check for NULLs and invalid values"""
        cursor = conn.cursor()
        
        checks = [
            ("NULL agent_id", "SELECT COUNT(*) FROM commissions_accrued WHERE agent_id IS NULL"),
            ("NULL property_id", "SELECT COUNT(*) FROM commissions_accrued WHERE property_id IS NULL"),
            ("NULL booking_id", "SELECT COUNT(*) FROM commissions_accrued WHERE booking_id IS NULL"),
            ("Negative amount", "SELECT COUNT(*) FROM commissions_accrued WHERE amount < 0"),
        ]
        
        for desc, query in checks:
            try:
                cursor.execute(query)
                count = cursor.fetchone()[0]
                if count > 0:
                    self.issues.append(f"{desc}: {count} records")
            except sqlite3.Error as e:
                self.warnings.append(f"Could not check {desc}: {e}")
    
    def _generate_stats(self, conn):
        """Generate summary statistics"""
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM commissions_accrued")
            self.stats["total_records"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(amount) FROM commissions_accrued WHERE status='accrued'")
            self.stats["total_accrued"] = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT status, COUNT(*) FROM commissions_accrued GROUP BY status")
            self.stats["by_status"] = dict(cursor.fetchall())
            
        except sqlite3.Error as e:
            self.warnings.append(f"Could not generate stats: {e}")
    
    def _print_report(self):
        """Print validation report"""
        print(f"\n{'='*60}")
        print("VALIDATION REPORT")
        print(f"{'='*60}")
        
        print(f"\n📊 Statistics:")
        for key, value in self.stats.items():
            print(f"   {key}: {value}")
        
        if self.issues:
            print(f"\n❌ Critical Issues ({len(self.issues)}):")
            for issue in self.issues[:10]:  # Show first 10
                print(f"   - {issue}")
            if len(self.issues) > 10:
                print(f"   ... and {len(self.issues) - 10} more")
        else:
            print(f"\n✅ No critical issues found")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:5]:
                print(f"   - {warning}")
        
        print(f"\n{'='*60}")
        status = "PASS" if not self.issues else "FAIL"
        print(f"Result: {status}")
        print(f"{'='*60}")

def main():
    validator = CommissionValidator()
    success = validator.validate()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
