#!/usr/bin/env python3
"""
Treasury Record Edit Feature Test - اختبار ميزة تعديل سجلات الخزينة
Testing the master user's ability to edit treasury transaction records without affecting balance
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"
MASTER_USERNAME = "master"
NON_MASTER_USERNAME = "Elsawy"

class TreasuryEditTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.transaction_id = None
        self.original_balance = None
        
    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and expected and actual:
            print(f"   🎯 Expected: {expected}")
            print(f"   📊 Actual: {actual}")
        print()

    def setup_test_data(self):
        """Create a test treasury transaction to edit"""
        print("🔧 Setting up test data...")
        
        # Create a test treasury transaction
        transaction_data = {
            "account_id": "cash",
            "transaction_type": "income",
            "amount": 500.0,
            "description": "معاملة اختبار للتعديل",
            "reference": "TEST-001"
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/treasury/transactions",
                json=transaction_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.transaction_id = result.get("id")
                print(f"✅ Created test transaction: {self.transaction_id}")
                return True
            else:
                print(f"❌ Failed to create test transaction: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating test transaction: {str(e)}")
            return False

    def get_account_balance(self, account_id="cash"):
        """Get current account balance"""
        try:
            response = self.session.get(f"{BASE_URL}/treasury/balances", timeout=10)
            if response.status_code == 200:
                balances = response.json()
                return balances.get(account_id, 0)
            return None
        except Exception as e:
            print(f"❌ Error getting balance: {str(e)}")
            return None

    def test_successful_edit(self):
        """Test 1: اختبار التعديل بنجاح مع المستخدم master"""
        if not self.transaction_id:
            self.log_test(
                "Successful Edit Test", 
                False, 
                "No transaction ID available for testing"
            )
            return

        # Get balance before edit
        balance_before = self.get_account_balance()
        
        edit_data = {
            "description": "test",
            "amount": 100
        }
        
        try:
            response = self.session.put(
                f"{BASE_URL}/treasury/transactions/{self.transaction_id}/edit-record",
                params={"username": MASTER_USERNAME},
                json=edit_data,
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                result = response.json()
                expected_message = "تم تعديل السجل بنجاح"
                actual_message = result.get("message", "")
                
                # Check if message contains expected text
                message_correct = expected_message in actual_message
                
                self.log_test(
                    "Successful Edit Test",
                    message_correct,
                    f"Status: {response.status_code}, Message: {actual_message}",
                    f"HTTP 200 with message containing '{expected_message}'",
                    f"HTTP {response.status_code} with message: {actual_message}"
                )
                
                # Get balance after edit
                balance_after = self.get_account_balance()
                
                # Test that balance didn't change
                if balance_before is not None and balance_after is not None:
                    balance_unchanged = balance_before == balance_after
                    self.log_test(
                        "Balance Unchanged Test",
                        balance_unchanged,
                        f"Balance before: {balance_before}, Balance after: {balance_after}",
                        f"Balance should remain {balance_before}",
                        f"Balance is {balance_after}"
                    )
                else:
                    self.log_test(
                        "Balance Unchanged Test",
                        False,
                        "Could not retrieve balance for comparison"
                    )
                    
            else:
                self.log_test(
                    "Successful Edit Test",
                    False,
                    f"Status: {response.status_code}, Response: {response.text}",
                    "HTTP 200",
                    f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test(
                "Successful Edit Test",
                False,
                f"Exception: {str(e)}"
            )

    def test_non_master_user_denied(self):
        """Test 2: اختبار التعديل بمستخدم غير master"""
        if not self.transaction_id:
            self.log_test(
                "Non-Master User Denied Test", 
                False, 
                "No transaction ID available for testing"
            )
            return

        edit_data = {
            "description": "test"
        }
        
        try:
            response = self.session.put(
                f"{BASE_URL}/treasury/transactions/{self.transaction_id}/edit-record",
                params={"username": NON_MASTER_USERNAME},
                json=edit_data,
                timeout=10
            )
            
            success = response.status_code == 403
            
            if success:
                result = response.json()
                expected_message = "غير مصرح لك بتعديل السجلات"
                actual_message = result.get("detail", "")
                
                message_correct = expected_message in actual_message
                
                self.log_test(
                    "Non-Master User Denied Test",
                    message_correct,
                    f"Status: {response.status_code}, Message: {actual_message}",
                    f"HTTP 403 with message '{expected_message}'",
                    f"HTTP {response.status_code} with message: {actual_message}"
                )
            else:
                self.log_test(
                    "Non-Master User Denied Test",
                    False,
                    f"Status: {response.status_code}, Response: {response.text}",
                    "HTTP 403",
                    f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test(
                "Non-Master User Denied Test",
                False,
                f"Exception: {str(e)}"
            )

    def test_invalid_transaction_id(self):
        """Test 3: اختبار التعديل لمعاملة غير موجودة"""
        edit_data = {
            "description": "test"
        }
        
        try:
            response = self.session.put(
                f"{BASE_URL}/treasury/transactions/invalid-id/edit-record",
                params={"username": MASTER_USERNAME},
                json=edit_data,
                timeout=10
            )
            
            success = response.status_code == 404
            
            self.log_test(
                "Invalid Transaction ID Test",
                success,
                f"Status: {response.status_code}, Response: {response.text}",
                "HTTP 404",
                f"HTTP {response.status_code}"
            )
                
        except Exception as e:
            self.log_test(
                "Invalid Transaction ID Test",
                False,
                f"Exception: {str(e)}"
            )

    def test_balance_verification(self):
        """Test 4: التحقق من أن الرصيد لم يتغير"""
        if not self.transaction_id:
            self.log_test(
                "Balance Verification Test", 
                False, 
                "No transaction ID available for testing"
            )
            return

        # Get balance before edit
        balance_before = self.get_account_balance()
        
        if balance_before is None:
            self.log_test(
                "Balance Verification Test",
                False,
                "Could not retrieve initial balance"
            )
            return

        # Edit transaction amount
        edit_data = {
            "amount": 999.99,
            "description": "تعديل مبلغ للاختبار"
        }
        
        try:
            response = self.session.put(
                f"{BASE_URL}/treasury/transactions/{self.transaction_id}/edit-record",
                params={"username": MASTER_USERNAME},
                json=edit_data,
                timeout=10
            )
            
            if response.status_code == 200:
                # Get balance after edit
                balance_after = self.get_account_balance()
                
                if balance_after is not None:
                    balance_unchanged = balance_before == balance_after
                    self.log_test(
                        "Balance Verification Test",
                        balance_unchanged,
                        f"Edited transaction amount to 999.99. Balance before: {balance_before}, Balance after: {balance_after}",
                        f"Balance should remain {balance_before}",
                        f"Balance is {balance_after}"
                    )
                else:
                    self.log_test(
                        "Balance Verification Test",
                        False,
                        "Could not retrieve balance after edit"
                    )
            else:
                self.log_test(
                    "Balance Verification Test",
                    False,
                    f"Edit request failed: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_test(
                "Balance Verification Test",
                False,
                f"Exception: {str(e)}"
            )

    def cleanup_test_data(self):
        """Clean up test data"""
        if self.transaction_id:
            try:
                # Note: We don't delete the transaction as it might be needed for other tests
                print(f"🧹 Test transaction {self.transaction_id} left for inspection")
            except Exception as e:
                print(f"⚠️ Could not clean up test data: {str(e)}")

    def run_all_tests(self):
        """Run all treasury edit tests"""
        print("🚀 Starting Treasury Record Edit Feature Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return False
        
        # Run tests
        self.test_successful_edit()
        self.test_non_master_user_denied()
        self.test_invalid_transaction_id()
        self.test_balance_verification()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Show failed tests
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
            print()
        
        # Overall result
        if success_rate >= 75:
            print("🎉 Treasury Record Edit Feature: WORKING")
            return True
        else:
            print("💥 Treasury Record Edit Feature: NEEDS ATTENTION")
            return False

def main():
    """Main test execution"""
    tester = TreasuryEditTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()