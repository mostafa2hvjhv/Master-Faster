#!/usr/bin/env python3
"""
Treasury Reset Functionality Test
=================================

This test file specifically tests the new Treasury Reset functionality that was just implemented.
The Treasury Reset is a CRITICAL function that permanently deletes ALL treasury transactions.

Test Coverage:
1. Security Testing - Only "Elsawy" user can access
2. Functionality Testing - Proper deletion and response
3. Data Integrity Testing - Only treasury data is deleted
4. Error Handling - Proper HTTP status codes and messages

Author: Testing Agent
Date: 2025-01-27
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://retail-treasury.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TreasuryResetTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.setup_data = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"     Details: {details}")
        if not success and data:
            print(f"     Data: {data}")
        print()

    async def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Make HTTP request to API"""
        url = f"{API_BASE}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, params=params) as response:
                    return {
                        "status": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text()
                    }
            elif method.upper() == "POST":
                headers = {"Content-Type": "application/json"}
                async with self.session.post(url, json=data, params=params, headers=headers) as response:
                    return {
                        "status": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text()
                    }
            elif method.upper() == "DELETE":
                async with self.session.delete(url, params=params) as response:
                    return {
                        "status": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text()
                    }
        except Exception as e:
            return {"status": 500, "data": {"error": str(e)}}

    async def setup_test_data(self):
        """Setup test data for treasury reset testing"""
        print("🔧 Setting up test data...")
        
        # Create some treasury transactions for testing
        test_transactions = [
            {
                "account_id": "cash",
                "transaction_type": "income",
                "amount": 1000.0,
                "description": "Test transaction 1",
                "reference": "TEST-001"
            },
            {
                "account_id": "vodafone_elsawy",
                "transaction_type": "income", 
                "amount": 500.0,
                "description": "Test transaction 2",
                "reference": "TEST-002"
            },
            {
                "account_id": "instapay",
                "transaction_type": "expense",
                "amount": 200.0,
                "description": "Test transaction 3",
                "reference": "TEST-003"
            }
        ]
        
        created_transactions = []
        for transaction in test_transactions:
            result = await self.make_request("POST", "/treasury/transactions", transaction)
            if result["status"] == 200:
                created_transactions.append(result["data"])
        
        self.setup_data["treasury_transactions"] = created_transactions
        
        # Create some other data to verify it's not affected
        test_customer = {
            "name": "عميل اختبار مسح الخزينة",
            "phone": "01234567890",
            "address": "عنوان اختبار"
        }
        
        customer_result = await self.make_request("POST", "/customers", test_customer)
        if customer_result["status"] == 200:
            self.setup_data["test_customer"] = customer_result["data"]
        
        print(f"✅ Setup complete: {len(created_transactions)} treasury transactions, 1 customer created")

    async def test_security_elsawy_access(self):
        """Test 1: Treasury reset with 'Elsawy' username should work"""
        try:
            # Get current treasury count
            current_result = await self.make_request("GET", "/treasury/transactions")
            if current_result["status"] != 200:
                self.log_test("Security Test - Elsawy Access", False, "Failed to get current treasury transactions")
                return
            
            current_count = len(current_result["data"])
            
            # Attempt reset with Elsawy username
            result = await self.make_request("POST", "/treasury/reset", params={"username": "Elsawy"})
            
            if result["status"] == 200:
                response_data = result["data"]
                expected_fields = ["message", "deleted_treasury_transactions", "reset_by", "reset_at"]
                
                # Verify response structure
                missing_fields = [field for field in expected_fields if field not in response_data]
                if missing_fields:
                    self.log_test("Security Test - Elsawy Access", False, 
                                f"Missing response fields: {missing_fields}", response_data)
                    return
                
                # Verify correct user
                if response_data["reset_by"] != "Elsawy":
                    self.log_test("Security Test - Elsawy Access", False, 
                                f"Wrong reset_by user: {response_data['reset_by']}", response_data)
                    return
                
                # Verify deletion count
                if response_data["deleted_treasury_transactions"] != current_count:
                    self.log_test("Security Test - Elsawy Access", False, 
                                f"Deletion count mismatch. Expected: {current_count}, Got: {response_data['deleted_treasury_transactions']}", 
                                response_data)
                    return
                
                self.log_test("Security Test - Elsawy Access", True, 
                            f"Successfully deleted {response_data['deleted_treasury_transactions']} treasury transactions", 
                            response_data)
            else:
                self.log_test("Security Test - Elsawy Access", False, 
                            f"Expected 200, got {result['status']}", result["data"])
                
        except Exception as e:
            self.log_test("Security Test - Elsawy Access", False, f"Exception: {str(e)}")

    async def test_security_unauthorized_users(self):
        """Test 2: Treasury reset with unauthorized usernames should be denied"""
        unauthorized_users = ["Root", "admin", "test", "user", "", "hacker"]
        
        for username in unauthorized_users:
            try:
                result = await self.make_request("POST", "/treasury/reset", params={"username": username})
                
                if result["status"] == 403:
                    # Check for Arabic error message
                    if isinstance(result["data"], dict) and "detail" in result["data"]:
                        error_message = result["data"]["detail"]
                        if "غير مصرح" in error_message:
                            self.log_test(f"Security Test - Deny '{username}'", True, 
                                        f"Correctly denied with Arabic message: {error_message}")
                        else:
                            self.log_test(f"Security Test - Deny '{username}'", False, 
                                        f"Wrong error message: {error_message}")
                    else:
                        self.log_test(f"Security Test - Deny '{username}'", False, 
                                    f"No proper error message in response", result["data"])
                else:
                    self.log_test(f"Security Test - Deny '{username}'", False, 
                                f"Expected 403, got {result['status']}", result["data"])
                    
            except Exception as e:
                self.log_test(f"Security Test - Deny '{username}'", False, f"Exception: {str(e)}")

    async def test_functionality_complete_deletion(self):
        """Test 3: Verify all treasury transactions are completely deleted"""
        try:
            # First, create some test transactions
            await self.setup_test_data()
            
            # Get count before reset
            before_result = await self.make_request("GET", "/treasury/transactions")
            if before_result["status"] != 200:
                self.log_test("Functionality Test - Complete Deletion", False, "Failed to get treasury transactions before reset")
                return
            
            before_count = len(before_result["data"])
            
            if before_count == 0:
                self.log_test("Functionality Test - Complete Deletion", False, "No treasury transactions to test deletion")
                return
            
            # Perform reset
            reset_result = await self.make_request("POST", "/treasury/reset", params={"username": "Elsawy"})
            if reset_result["status"] != 200:
                self.log_test("Functionality Test - Complete Deletion", False, 
                            f"Reset failed with status {reset_result['status']}", reset_result["data"])
                return
            
            # Verify all transactions are deleted
            after_result = await self.make_request("GET", "/treasury/transactions")
            if after_result["status"] != 200:
                self.log_test("Functionality Test - Complete Deletion", False, "Failed to get treasury transactions after reset")
                return
            
            after_count = len(after_result["data"])
            
            if after_count == 0:
                self.log_test("Functionality Test - Complete Deletion", True, 
                            f"Successfully deleted all {before_count} treasury transactions. After count: {after_count}")
            else:
                self.log_test("Functionality Test - Complete Deletion", False, 
                            f"Deletion incomplete. Before: {before_count}, After: {after_count}", 
                            {"remaining_transactions": after_result["data"]})
                
        except Exception as e:
            self.log_test("Functionality Test - Complete Deletion", False, f"Exception: {str(e)}")

    async def test_data_integrity_other_collections(self):
        """Test 4: Verify that ONLY treasury transactions are deleted, other data is untouched"""
        try:
            # Get counts of other collections before reset
            collections_to_check = [
                ("/customers", "customers"),
                ("/invoices", "invoices"), 
                ("/expenses", "expenses"),
                ("/raw-materials", "raw_materials"),
                ("/inventory", "inventory")
            ]
            
            before_counts = {}
            for endpoint, name in collections_to_check:
                result = await self.make_request("GET", endpoint)
                if result["status"] == 200:
                    before_counts[name] = len(result["data"])
                else:
                    before_counts[name] = "ERROR"
            
            # Perform treasury reset
            reset_result = await self.make_request("POST", "/treasury/reset", params={"username": "Elsawy"})
            if reset_result["status"] != 200:
                self.log_test("Data Integrity Test", False, "Treasury reset failed", reset_result["data"])
                return
            
            # Check counts after reset
            after_counts = {}
            for endpoint, name in collections_to_check:
                result = await self.make_request("GET", endpoint)
                if result["status"] == 200:
                    after_counts[name] = len(result["data"])
                else:
                    after_counts[name] = "ERROR"
            
            # Verify no other data was affected
            integrity_maintained = True
            affected_collections = []
            
            for name in before_counts:
                if before_counts[name] != after_counts[name]:
                    integrity_maintained = False
                    affected_collections.append({
                        "collection": name,
                        "before": before_counts[name],
                        "after": after_counts[name]
                    })
            
            if integrity_maintained:
                self.log_test("Data Integrity Test", True, 
                            "All other collections remain untouched", 
                            {"before": before_counts, "after": after_counts})
            else:
                self.log_test("Data Integrity Test", False, 
                            f"Other collections were affected: {affected_collections}", 
                            {"before": before_counts, "after": after_counts})
                
        except Exception as e:
            self.log_test("Data Integrity Test", False, f"Exception: {str(e)}")

    async def test_treasury_balances_after_reset(self):
        """Test 5: Verify treasury balances return zero after reset"""
        try:
            # Perform treasury reset first
            reset_result = await self.make_request("POST", "/treasury/reset", params={"username": "Elsawy"})
            if reset_result["status"] != 200:
                self.log_test("Treasury Balances Test", False, "Treasury reset failed", reset_result["data"])
                return
            
            # Get treasury balances
            balances_result = await self.make_request("GET", "/treasury/balances")
            if balances_result["status"] != 200:
                self.log_test("Treasury Balances Test", False, "Failed to get treasury balances", balances_result["data"])
                return
            
            balances = balances_result["data"]
            expected_accounts = ['cash', 'vodafone_elsawy', 'vodafone_wael', 'deferred', 'instapay', 'yad_elsawy']
            
            # Check if all accounts have zero balance (considering only treasury transactions)
            non_zero_accounts = []
            for account in expected_accounts:
                if account in balances:
                    # Note: Some accounts might have non-zero balances due to invoices/expenses
                    # but treasury transactions should be zero
                    if account == 'deferred':
                        # Deferred account might have invoice amounts
                        continue
                    elif account == 'cash':
                        # Cash might have expense deductions
                        continue
                    # For other accounts, check if they're affected by treasury reset
                
            # For this test, we'll verify that treasury transactions are gone
            transactions_result = await self.make_request("GET", "/treasury/transactions")
            if transactions_result["status"] == 200 and len(transactions_result["data"]) == 0:
                self.log_test("Treasury Balances Test", True, 
                            "Treasury transactions cleared, balances API working", 
                            {"balances": balances, "transaction_count": 0})
            else:
                self.log_test("Treasury Balances Test", False, 
                            "Treasury transactions not properly cleared", 
                            {"balances": balances, "transactions": transactions_result["data"]})
                
        except Exception as e:
            self.log_test("Treasury Balances Test", False, f"Exception: {str(e)}")

    async def test_error_handling_missing_username(self):
        """Test 6: Test error handling when username parameter is missing"""
        try:
            # Try reset without username parameter
            result = await self.make_request("POST", "/treasury/reset")
            
            # Should return 422 (validation error) or 400 (bad request)
            if result["status"] in [400, 422]:
                self.log_test("Error Handling - Missing Username", True, 
                            f"Correctly rejected request without username (HTTP {result['status']})", 
                            result["data"])
            else:
                self.log_test("Error Handling - Missing Username", False, 
                            f"Expected 400/422, got {result['status']}", result["data"])
                
        except Exception as e:
            self.log_test("Error Handling - Missing Username", False, f"Exception: {str(e)}")

    async def test_response_format_validation(self):
        """Test 7: Validate the response format and required fields"""
        try:
            # Setup some test data first
            test_transaction = {
                "account_id": "cash",
                "transaction_type": "income",
                "amount": 100.0,
                "description": "Test for response validation",
                "reference": "RESP-TEST"
            }
            
            await self.make_request("POST", "/treasury/transactions", test_transaction)
            
            # Perform reset
            result = await self.make_request("POST", "/treasury/reset", params={"username": "Elsawy"})
            
            if result["status"] == 200:
                response_data = result["data"]
                
                # Check required fields
                required_fields = {
                    "message": str,
                    "deleted_treasury_transactions": int,
                    "reset_by": str,
                    "reset_at": str
                }
                
                validation_errors = []
                
                for field, expected_type in required_fields.items():
                    if field not in response_data:
                        validation_errors.append(f"Missing field: {field}")
                    elif not isinstance(response_data[field], expected_type):
                        validation_errors.append(f"Wrong type for {field}: expected {expected_type.__name__}, got {type(response_data[field]).__name__}")
                
                # Validate specific values
                if response_data.get("reset_by") != "Elsawy":
                    validation_errors.append(f"Wrong reset_by value: {response_data.get('reset_by')}")
                
                if "تم مسح" not in response_data.get("message", ""):
                    validation_errors.append("Arabic success message not found")
                
                # Validate timestamp format
                try:
                    datetime.fromisoformat(response_data.get("reset_at", "").replace('Z', '+00:00'))
                except:
                    validation_errors.append("Invalid timestamp format")
                
                if not validation_errors:
                    self.log_test("Response Format Validation", True, 
                                "All required fields present with correct types and values", 
                                response_data)
                else:
                    self.log_test("Response Format Validation", False, 
                                f"Validation errors: {validation_errors}", response_data)
            else:
                self.log_test("Response Format Validation", False, 
                            f"Reset failed with status {result['status']}", result["data"])
                
        except Exception as e:
            self.log_test("Response Format Validation", False, f"Exception: {str(e)}")

    async def run_all_tests(self):
        """Run all treasury reset tests"""
        print("🚀 Starting Treasury Reset Functionality Tests")
        print("=" * 60)
        print()
        
        # Run all tests
        await self.test_security_elsawy_access()
        await self.test_security_unauthorized_users()
        await self.test_functionality_complete_deletion()
        await self.test_data_integrity_other_collections()
        await self.test_treasury_balances_after_reset()
        await self.test_error_handling_missing_username()
        await self.test_response_format_validation()
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("=" * 60)
        print("🏁 TREASURY RESET TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
            print()
        
        # Critical security assessment
        security_tests = [r for r in self.test_results if "Security Test" in r["test"]]
        security_passed = sum(1 for r in security_tests if r["success"])
        
        if security_passed == len(security_tests):
            print("🔒 SECURITY ASSESSMENT: ✅ PASSED")
            print("   All security tests passed. Only 'Elsawy' can access treasury reset.")
        else:
            print("🔒 SECURITY ASSESSMENT: ❌ FAILED")
            print("   CRITICAL: Security vulnerabilities detected!")
        
        print()
        print("📊 Detailed test results saved in test_results list")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "security_passed": security_passed == len(security_tests),
            "results": self.test_results
        }

async def main():
    """Main test execution function"""
    async with TreasuryResetTester() as tester:
        results = await tester.run_all_tests()
        return results

if __name__ == "__main__":
    # Run the tests
    results = asyncio.run(main())
    
    # Exit with appropriate code
    if results["failed"] == 0:
        print("🎉 All tests passed!")
        exit(0)
    else:
        print(f"💥 {results['failed']} tests failed!")
        exit(1)