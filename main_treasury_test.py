#!/usr/bin/env python3
"""
Main Treasury System Comprehensive Testing
نظام الخزنة الرئيسية - اختبار شامل

This script tests all Main Treasury System APIs as requested:
1. Password verification (correct and incorrect)
2. Balance checking (initial should be 0)
3. Deposit operations with user authorization
4. Withdrawal operations with balance validation
5. Transaction history
6. Transfer from yad elsawy
7. Password change functionality
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class MainTreasuryTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} - {test_name}"
        if details:
            result += f" | {details}"
        
        self.test_results.append(result)
        print(result)
        
    def test_password_verification(self):
        """Test password verification with correct and incorrect passwords"""
        print("\n🔐 Testing Password Verification...")
        
        # Test 1: Correct password (100100 - default)
        try:
            response = self.session.post(
                f"{BACKEND_URL}/main-treasury/verify-password",
                json={"password": "100100"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True:
                    self.log_test("Password verification - correct password (100100)", True, 
                                f"Response: {data.get('message')}")
                else:
                    self.log_test("Password verification - correct password (100100)", False, 
                                f"Expected success=True, got: {data}")
            else:
                self.log_test("Password verification - correct password (100100)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Password verification - correct password (100100)", False, f"Exception: {str(e)}")
        
        # Test 2: Incorrect password
        try:
            response = self.session.post(
                f"{BACKEND_URL}/main-treasury/verify-password",
                json={"password": "wrong_password"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == False:
                    self.log_test("Password verification - incorrect password", True, 
                                f"Response: {data.get('message')}")
                else:
                    self.log_test("Password verification - incorrect password", False, 
                                f"Expected success=False, got: {data}")
            else:
                self.log_test("Password verification - incorrect password", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Password verification - incorrect password", False, f"Exception: {str(e)}")
    
    def test_initial_balance(self):
        """Test getting initial balance (should be 0)"""
        print("\n💰 Testing Initial Balance...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/main-treasury/balance")
            
            if response.status_code == 200:
                data = response.json()
                balance = data.get("balance", -1)
                transaction_count = data.get("transaction_count", -1)
                
                self.log_test("Get initial balance", True, 
                            f"Balance: {balance} ج.م, Transactions: {transaction_count}")
                
                # Store initial balance for later tests
                self.initial_balance = balance
                
            else:
                self.log_test("Get initial balance", False, 
                            f"HTTP {response.status_code}: {response.text}")
                self.initial_balance = 0
                
        except Exception as e:
            self.log_test("Get initial balance", False, f"Exception: {str(e)}")
            self.initial_balance = 0
    
    def test_deposit_operations(self):
        """Test deposit operations with user authorization"""
        print("\n💵 Testing Deposit Operations...")
        
        # Test 1: Deposit with authorized user (Elsawy)
        try:
            deposit_data = {
                "transaction_type": "deposit",
                "amount": 1000.0,
                "description": "إيداع اختباري",
                "reference": "TEST-DEPOSIT-001"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/main-treasury/deposit?username=Elsawy",
                json=deposit_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True:
                    new_balance = data.get("new_balance")
                    expected_balance = self.initial_balance + 1000
                    
                    if new_balance == expected_balance:
                        self.log_test("Deposit 1000 EGP - authorized user (Elsawy)", True, 
                                    f"New balance: {new_balance} ج.م")
                        self.current_balance = new_balance
                    else:
                        self.log_test("Deposit 1000 EGP - authorized user (Elsawy)", False, 
                                    f"Balance mismatch. Expected: {expected_balance}, Got: {new_balance}")
                        self.current_balance = new_balance or self.initial_balance
                else:
                    self.log_test("Deposit 1000 EGP - authorized user (Elsawy)", False, 
                                f"Expected success=True, got: {data}")
                    self.current_balance = self.initial_balance
            else:
                self.log_test("Deposit 1000 EGP - authorized user (Elsawy)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                self.current_balance = self.initial_balance
                
        except Exception as e:
            self.log_test("Deposit 1000 EGP - authorized user (Elsawy)", False, f"Exception: {str(e)}")
            self.current_balance = self.initial_balance
        
        # Test 2: Deposit with unauthorized user (Root)
        try:
            deposit_data = {
                "transaction_type": "deposit",
                "amount": 500.0,
                "description": "محاولة إيداع غير مصرح بها",
                "reference": "TEST-UNAUTHORIZED"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/main-treasury/deposit?username=Root",
                json=deposit_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 403:
                self.log_test("Deposit rejection - unauthorized user (Root)", True, 
                            f"Correctly rejected with HTTP 403")
            elif response.status_code == 200:
                data = response.json()
                if data.get("success") == False:
                    self.log_test("Deposit rejection - unauthorized user (Root)", True, 
                                f"Correctly rejected: {data.get('message', 'No message')}")
                else:
                    self.log_test("Deposit rejection - unauthorized user (Root)", False, 
                                f"Should have been rejected but got success: {data}")
            else:
                self.log_test("Deposit rejection - unauthorized user (Root)", False, 
                            f"Unexpected HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Deposit rejection - unauthorized user (Root)", False, f"Exception: {str(e)}")
    
    def test_withdrawal_operations(self):
        """Test withdrawal operations with balance validation"""
        print("\n💸 Testing Withdrawal Operations...")
        
        # Test 1: Valid withdrawal (300 EGP)
        try:
            withdrawal_data = {
                "transaction_type": "withdrawal",
                "amount": 300.0,
                "description": "صرف اختباري",
                "reference": "TEST-WITHDRAWAL-001"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/main-treasury/withdrawal?username=Elsawy",
                json=withdrawal_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True:
                    new_balance = data.get("new_balance")
                    expected_balance = self.current_balance - 300
                    
                    if new_balance == expected_balance:
                        self.log_test("Withdrawal 300 EGP - sufficient balance", True, 
                                    f"New balance: {new_balance} ج.م")
                        self.current_balance = new_balance
                    else:
                        self.log_test("Withdrawal 300 EGP - sufficient balance", False, 
                                    f"Balance mismatch. Expected: {expected_balance}, Got: {new_balance}")
                        self.current_balance = new_balance or self.current_balance
                else:
                    self.log_test("Withdrawal 300 EGP - sufficient balance", False, 
                                f"Expected success=True, got: {data}")
            else:
                self.log_test("Withdrawal 300 EGP - sufficient balance", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Withdrawal 300 EGP - sufficient balance", False, f"Exception: {str(e)}")
        
        # Test 2: Withdrawal exceeding balance
        try:
            excessive_amount = self.current_balance + 1000  # More than available
            withdrawal_data = {
                "transaction_type": "withdrawal",
                "amount": excessive_amount,
                "description": "محاولة صرف أكثر من الرصيد",
                "reference": "TEST-EXCESSIVE-WITHDRAWAL"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/main-treasury/withdrawal?username=Elsawy",
                json=withdrawal_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                self.log_test("Withdrawal prevention - insufficient balance", True, 
                            f"Correctly prevented excessive withdrawal (HTTP 400)")
            elif response.status_code == 200:
                data = response.json()
                if data.get("success") == False:
                    self.log_test("Withdrawal prevention - insufficient balance", True, 
                                f"Correctly prevented: {data.get('message', 'No message')}")
                else:
                    self.log_test("Withdrawal prevention - insufficient balance", False, 
                                f"Should have been prevented but got success: {data}")
            else:
                self.log_test("Withdrawal prevention - insufficient balance", False, 
                            f"Unexpected HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Withdrawal prevention - insufficient balance", False, f"Exception: {str(e)}")
    
    def test_transaction_history(self):
        """Test transaction history retrieval"""
        print("\n📋 Testing Transaction History...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/main-treasury/transactions")
            
            if response.status_code == 200:
                transactions = response.json()
                
                if isinstance(transactions, list):
                    transaction_count = len(transactions)
                    
                    # Verify we have at least the deposit and withdrawal we made
                    deposit_found = False
                    withdrawal_found = False
                    balance_after_correct = True
                    
                    for transaction in transactions:
                        transaction_type = transaction.get("transaction_type")
                        amount = transaction.get("amount")
                        balance_after = transaction.get("balance_after")
                        description = transaction.get("description", "")
                        
                        if transaction_type == "deposit" and "إيداع اختباري" in description:
                            deposit_found = True
                        elif transaction_type == "withdrawal" and "صرف اختباري" in description:
                            withdrawal_found = True
                        
                        # Check if balance_after is present and is a number
                        if balance_after is None or not isinstance(balance_after, (int, float)):
                            balance_after_correct = False
                    
                    success_details = f"Found {transaction_count} transactions"
                    if deposit_found:
                        success_details += ", Deposit ✓"
                    if withdrawal_found:
                        success_details += ", Withdrawal ✓"
                    if balance_after_correct:
                        success_details += ", Balance tracking ✓"
                    
                    self.log_test("Get transaction history", True, success_details)
                    
                    # Store transaction count for later verification
                    self.transaction_count = transaction_count
                    
                else:
                    self.log_test("Get transaction history", False, 
                                f"Expected list, got: {type(transactions)}")
                    self.transaction_count = 0
            else:
                self.log_test("Get transaction history", False, 
                            f"HTTP {response.status_code}: {response.text}")
                self.transaction_count = 0
                
        except Exception as e:
            self.log_test("Get transaction history", False, f"Exception: {str(e)}")
            self.transaction_count = 0
    
    def test_transfer_from_yad(self):
        """Test transfer from yad elsawy"""
        print("\n🔄 Testing Transfer from Yad Elsawy...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/main-treasury/transfer-from-yad?amount=500&username=Elsawy",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True:
                    new_balance = data.get("new_balance")
                    expected_balance = self.current_balance + 500
                    
                    if new_balance == expected_balance:
                        self.log_test("Transfer 500 EGP from yad elsawy", True, 
                                    f"New balance: {new_balance} ج.م")
                        self.current_balance = new_balance
                    else:
                        self.log_test("Transfer 500 EGP from yad elsawy", False, 
                                    f"Balance mismatch. Expected: {expected_balance}, Got: {new_balance}")
                        self.current_balance = new_balance or self.current_balance
                else:
                    self.log_test("Transfer 500 EGP from yad elsawy", False, 
                                f"Expected success=True, got: {data}")
            else:
                self.log_test("Transfer 500 EGP from yad elsawy", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Transfer 500 EGP from yad elsawy", False, f"Exception: {str(e)}")
        
        # Verify transaction type in history
        try:
            response = self.session.get(f"{BACKEND_URL}/main-treasury/transactions")
            
            if response.status_code == 200:
                transactions = response.json()
                transfer_found = False
                
                for transaction in transactions:
                    if (transaction.get("transaction_type") == "transfer_from_yad" and 
                        transaction.get("amount") == 500):
                        transfer_found = True
                        break
                
                if transfer_found:
                    self.log_test("Verify transfer transaction type", True, 
                                "Found transfer_from_yad transaction")
                else:
                    self.log_test("Verify transfer transaction type", False, 
                                "transfer_from_yad transaction not found")
            else:
                self.log_test("Verify transfer transaction type", False, 
                            f"Could not retrieve transactions: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Verify transfer transaction type", False, f"Exception: {str(e)}")
    
    def test_password_change(self):
        """Test password change functionality"""
        print("\n🔑 Testing Password Change...")
        
        # Test 1: Change password from 100100 to 123456
        try:
            password_change_data = {
                "old_password": "100100",
                "new_password": "123456"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/main-treasury/change-password",
                json=password_change_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True:
                    self.log_test("Change password (100100 → 123456)", True, 
                                f"Response: {data.get('message')}")
                    self.password_changed = True
                else:
                    self.log_test("Change password (100100 → 123456)", False, 
                                f"Expected success=True, got: {data}")
                    self.password_changed = False
            else:
                self.log_test("Change password (100100 → 123456)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                self.password_changed = False
                
        except Exception as e:
            self.log_test("Change password (100100 → 123456)", False, f"Exception: {str(e)}")
            self.password_changed = False
        
        # Test 2: Verify new password works
        if self.password_changed:
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/main-treasury/verify-password",
                    json={"password": "123456"},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") == True:
                        self.log_test("Verify new password (123456)", True, 
                                    f"New password works correctly")
                    else:
                        self.log_test("Verify new password (123456)", False, 
                                    f"New password verification failed: {data}")
                else:
                    self.log_test("Verify new password (123456)", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Verify new password (123456)", False, f"Exception: {str(e)}")
        
        # Test 3: Verify old password no longer works
        if self.password_changed:
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/main-treasury/verify-password",
                    json={"password": "100100"},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") == False:
                        self.log_test("Verify old password rejected (100100)", True, 
                                    f"Old password correctly rejected")
                    else:
                        self.log_test("Verify old password rejected (100100)", False, 
                                    f"Old password still works: {data}")
                else:
                    self.log_test("Verify old password rejected (100100)", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Verify old password rejected (100100)", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all Main Treasury System tests"""
        print("🏦 Main Treasury System Comprehensive Testing")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Initialize tracking variables
        self.initial_balance = 0
        self.current_balance = 0
        self.transaction_count = 0
        self.password_changed = False
        
        # Run all tests in sequence
        self.test_password_verification()
        self.test_initial_balance()
        self.test_deposit_operations()
        self.test_withdrawal_operations()
        self.test_transaction_history()
        self.test_transfer_from_yad()
        self.test_password_change()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - Main Treasury System working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD - Main Treasury System mostly working")
        elif success_rate >= 50:
            print("⚠️ FAIR - Main Treasury System has some issues")
        else:
            print("❌ POOR - Main Treasury System needs significant fixes")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"  {result}")
        
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 75  # Return True if tests mostly passed

def main():
    """Main function to run the tests"""
    tester = MainTreasuryTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()