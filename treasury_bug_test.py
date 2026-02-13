#!/usr/bin/env python3
"""
Treasury Double Transaction Bug Investigation
============================================

This test specifically investigates the reported treasury double transaction bug:
- When creating an invoice, the amount is being added to treasury twice
- Focus on different payment methods and scenarios
- Monitor treasury balances before and after operations
- Check for duplicate treasury transactions
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import sys
import os

# Add the backend directory to Python path
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"
TEST_CUSTOMER_NAME = "عميل اختبار الخزينة"

class TreasuryBugTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.initial_balances = {}
        self.created_invoices = []
        self.created_customers = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def make_request(self, method, endpoint, data=None):
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        text = await response.text()
                        print(f"❌ GET {endpoint} failed: {response.status} - {text}")
                        return None
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        text = await response.text()
                        print(f"❌ POST {endpoint} failed: {response.status} - {text}")
                        return None
            elif method.upper() == "DELETE":
                async with self.session.delete(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        text = await response.text()
                        print(f"❌ DELETE {endpoint} failed: {response.status} - {text}")
                        return None
        except Exception as e:
            print(f"❌ Request error for {method} {endpoint}: {str(e)}")
            return None
            
    async def get_treasury_balances(self):
        """Get current treasury balances"""
        return await self.make_request("GET", "/treasury/balances")
        
    async def get_treasury_transactions(self):
        """Get all treasury transactions"""
        return await self.make_request("GET", "/treasury/transactions")
        
    async def create_test_customer(self):
        """Create a test customer for invoices"""
        customer_data = {
            "name": TEST_CUSTOMER_NAME,
            "phone": "01234567890",
            "address": "عنوان اختبار الخزينة"
        }
        
        customer = await self.make_request("POST", "/customers", customer_data)
        if customer:
            self.created_customers.append(customer["id"])
            print(f"✅ Created test customer: {customer['name']} (ID: {customer['id']})")
            return customer
        return None
        
    async def create_test_invoice(self, payment_method, amount=1000.0, customer_name=None):
        """Create a test invoice with specified payment method"""
        if not customer_name:
            customer_name = TEST_CUSTOMER_NAME
            
        invoice_data = {
            "customer_name": customer_name,
            "invoice_title": f"فاتورة اختبار الخزينة - {payment_method}",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR", 
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 7.0,
                    "quantity": 1,
                    "unit_price": amount,
                    "total_price": amount,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": payment_method,
            "discount_type": "amount",
            "discount_value": 0.0,
            "notes": f"اختبار الخزينة - {payment_method}"
        }
        
        invoice = await self.make_request("POST", "/invoices", invoice_data)
        if invoice:
            self.created_invoices.append(invoice["id"])
            print(f"✅ Created invoice: {invoice['invoice_number']} - {payment_method} - {amount} ج.م")
            return invoice
        return None
        
    async def create_payment_for_deferred_invoice(self, invoice_id, amount, payment_method):
        """Create a payment for a deferred invoice"""
        payment_data = {
            "invoice_id": invoice_id,
            "amount": amount,
            "payment_method": payment_method,
            "notes": f"دفعة اختبار الخزينة - {payment_method}"
        }
        
        payment = await self.make_request("POST", "/payments", payment_data)
        if payment:
            print(f"✅ Created payment: {amount} ج.م for invoice {invoice_id} via {payment_method}")
            return payment
        return None
        
    async def count_treasury_transactions_for_reference(self, reference_pattern):
        """Count treasury transactions matching a reference pattern"""
        transactions = await self.get_treasury_transactions()
        if not transactions:
            return 0
            
        count = 0
        matching_transactions = []
        for transaction in transactions:
            if reference_pattern in transaction.get("reference", ""):
                count += 1
                matching_transactions.append(transaction)
                
        return count, matching_transactions
        
    async def test_cash_payment_invoice(self):
        """Test 1: Create invoice with cash payment - check for double transactions"""
        print("\n🔍 Test 1: Cash Payment Invoice - Treasury Double Transaction Check")
        print("=" * 70)
        
        # Get initial balances
        initial_balances = await self.get_treasury_balances()
        initial_cash = initial_balances.get("cash", 0) if initial_balances else 0
        print(f"📊 Initial cash balance: {initial_cash} ج.م")
        
        # Get initial transaction count
        initial_transactions = await self.get_treasury_transactions()
        initial_count = len(initial_transactions) if initial_transactions else 0
        print(f"📊 Initial treasury transactions count: {initial_count}")
        
        # Create cash invoice
        invoice_amount = 500.0
        invoice = await self.create_test_invoice("نقدي", invoice_amount)
        
        if not invoice:
            print("❌ Failed to create cash invoice")
            return False
            
        # Wait a moment for processing
        await asyncio.sleep(1)
        
        # Check final balances
        final_balances = await self.get_treasury_balances()
        final_cash = final_balances.get("cash", 0) if final_balances else 0
        cash_increase = final_cash - initial_cash
        
        print(f"📊 Final cash balance: {final_cash} ج.م")
        print(f"📊 Cash increase: {cash_increase} ج.م (Expected: {invoice_amount} ج.م)")
        
        # Check treasury transactions
        final_transactions = await self.get_treasury_transactions()
        final_count = len(final_transactions) if final_transactions else 0
        new_transactions = final_count - initial_count
        
        print(f"📊 Final treasury transactions count: {final_count}")
        print(f"📊 New transactions created: {new_transactions}")
        
        # Check for duplicate transactions for this invoice
        duplicate_count, matching_transactions = await self.count_treasury_transactions_for_reference(f"invoice_{invoice['id']}")
        
        print(f"📊 Treasury transactions for this invoice: {duplicate_count}")
        
        if duplicate_count > 0:
            print("🔍 Matching treasury transactions:")
            for i, transaction in enumerate(matching_transactions, 1):
                print(f"   {i}. Account: {transaction.get('account_id')}, Amount: {transaction.get('amount')}, Type: {transaction.get('transaction_type')}")
                print(f"      Reference: {transaction.get('reference')}")
                print(f"      Description: {transaction.get('description')}")
        
        # Analysis
        expected_increase = invoice_amount
        is_double_transaction = cash_increase > expected_increase * 1.1  # 10% tolerance
        
        if is_double_transaction:
            print(f"🚨 POTENTIAL DOUBLE TRANSACTION DETECTED!")
            print(f"   Expected increase: {expected_increase} ج.م")
            print(f"   Actual increase: {cash_increase} ج.م")
            print(f"   Difference: {cash_increase - expected_increase} ج.م")
            
        if duplicate_count > 1:
            print(f"🚨 DUPLICATE TREASURY TRANSACTIONS DETECTED!")
            print(f"   Found {duplicate_count} transactions for the same invoice")
            
        # Test result
        test_passed = not is_double_transaction and duplicate_count <= 1
        result = "✅ PASSED" if test_passed else "❌ FAILED"
        print(f"\n{result} - Cash Payment Invoice Test")
        
        return test_passed
        
    async def test_deferred_payment_invoice(self):
        """Test 2: Create deferred invoice - check deferred account balance"""
        print("\n🔍 Test 2: Deferred Payment Invoice - Deferred Account Check")
        print("=" * 70)
        
        # Get initial balances
        initial_balances = await self.get_treasury_balances()
        initial_deferred = initial_balances.get("deferred", 0) if initial_balances else 0
        print(f"📊 Initial deferred balance: {initial_deferred} ج.م")
        
        # Create deferred invoice
        invoice_amount = 750.0
        invoice = await self.create_test_invoice("آجل", invoice_amount)
        
        if not invoice:
            print("❌ Failed to create deferred invoice")
            return False
            
        # Wait a moment for processing
        await asyncio.sleep(1)
        
        # Check final balances
        final_balances = await self.get_treasury_balances()
        final_deferred = final_balances.get("deferred", 0) if final_balances else 0
        deferred_increase = final_deferred - initial_deferred
        
        print(f"📊 Final deferred balance: {final_deferred} ج.م")
        print(f"📊 Deferred increase: {deferred_increase} ج.م (Expected: {invoice_amount} ج.م)")
        
        # Check for treasury transactions (should be none for deferred invoices at creation)
        duplicate_count, matching_transactions = await self.count_treasury_transactions_for_reference(f"invoice_{invoice['id']}")
        
        print(f"📊 Treasury transactions for this deferred invoice: {duplicate_count}")
        
        if duplicate_count > 0:
            print("⚠️  Unexpected treasury transactions for deferred invoice:")
            for i, transaction in enumerate(matching_transactions, 1):
                print(f"   {i}. Account: {transaction.get('account_id')}, Amount: {transaction.get('amount')}, Type: {transaction.get('transaction_type')}")
        
        # Analysis
        expected_increase = invoice_amount
        is_correct_deferred = abs(deferred_increase - expected_increase) < 0.01
        no_immediate_treasury = duplicate_count == 0
        
        # Test result
        test_passed = is_correct_deferred and no_immediate_treasury
        result = "✅ PASSED" if test_passed else "❌ FAILED"
        print(f"\n{result} - Deferred Payment Invoice Test")
        
        if not is_correct_deferred:
            print(f"❌ Deferred balance incorrect. Expected: {expected_increase}, Got: {deferred_increase}")
        if not no_immediate_treasury:
            print(f"❌ Unexpected treasury transactions for deferred invoice")
            
        return test_passed, invoice
        
    async def test_deferred_payment_settlement(self, deferred_invoice):
        """Test 3: Pay deferred invoice - check treasury and deferred account changes"""
        print("\n🔍 Test 3: Deferred Invoice Payment - Treasury Integration Check")
        print("=" * 70)
        
        if not deferred_invoice:
            print("❌ No deferred invoice provided for payment test")
            return False
            
        # Get initial balances
        initial_balances = await self.get_treasury_balances()
        initial_cash = initial_balances.get("cash", 0) if initial_balances else 0
        initial_deferred = initial_balances.get("deferred", 0) if initial_balances else 0
        
        print(f"📊 Initial cash balance: {initial_cash} ج.م")
        print(f"📊 Initial deferred balance: {initial_deferred} ج.م")
        
        # Make partial payment
        payment_amount = 300.0
        payment = await self.create_payment_for_deferred_invoice(
            deferred_invoice["id"], 
            payment_amount, 
            "نقدي"
        )
        
        if not payment:
            print("❌ Failed to create payment for deferred invoice")
            return False
            
        # Wait a moment for processing
        await asyncio.sleep(1)
        
        # Check final balances
        final_balances = await self.get_treasury_balances()
        final_cash = final_balances.get("cash", 0) if final_balances else 0
        final_deferred = final_balances.get("deferred", 0) if final_balances else 0
        
        cash_increase = final_cash - initial_cash
        deferred_decrease = initial_deferred - final_deferred
        
        print(f"📊 Final cash balance: {final_cash} ج.م")
        print(f"📊 Final deferred balance: {final_deferred} ج.م")
        print(f"📊 Cash increase: {cash_increase} ج.م (Expected: {payment_amount} ج.م)")
        print(f"📊 Deferred decrease: {deferred_decrease} ج.م (Expected: {payment_amount} ج.م)")
        
        # Check treasury transactions for this payment
        payment_count, payment_transactions = await self.count_treasury_transactions_for_reference(f"payment_{payment['id']}")
        
        print(f"📊 Treasury transactions for this payment: {payment_count}")
        
        if payment_count > 0:
            print("🔍 Payment treasury transactions:")
            for i, transaction in enumerate(payment_transactions, 1):
                print(f"   {i}. Account: {transaction.get('account_id')}, Amount: {transaction.get('amount')}, Type: {transaction.get('transaction_type')}")
                print(f"      Reference: {transaction.get('reference')}")
        
        # Analysis
        is_cash_correct = abs(cash_increase - payment_amount) < 0.01
        is_deferred_correct = abs(deferred_decrease - payment_amount) < 0.01
        has_proper_transactions = payment_count >= 2  # Should have income to cash and expense from deferred
        
        # Test result
        test_passed = is_cash_correct and is_deferred_correct and has_proper_transactions
        result = "✅ PASSED" if test_passed else "❌ FAILED"
        print(f"\n{result} - Deferred Invoice Payment Test")
        
        if not is_cash_correct:
            print(f"❌ Cash increase incorrect. Expected: {payment_amount}, Got: {cash_increase}")
        if not is_deferred_correct:
            print(f"❌ Deferred decrease incorrect. Expected: {payment_amount}, Got: {deferred_decrease}")
        if not has_proper_transactions:
            print(f"❌ Missing proper treasury transactions. Expected: 2+, Got: {payment_count}")
            
        return test_passed
        
    async def test_multiple_payment_methods(self):
        """Test 4: Test different payment methods for duplicate transactions"""
        print("\n🔍 Test 4: Multiple Payment Methods - Duplicate Transaction Check")
        print("=" * 70)
        
        payment_methods = [
            ("فودافون كاش محمد الصاوي", "vodafone_elsawy", 400.0),
            ("فودافون كاش وائل محمد", "vodafone_wael", 350.0),
            ("انستاباي", "instapay", 600.0),
            ("يد الصاوي", "yad_elsawy", 450.0)
        ]
        
        test_results = []
        
        for payment_method, account_key, amount in payment_methods:
            print(f"\n🔸 Testing payment method: {payment_method}")
            
            # Get initial balance
            initial_balances = await self.get_treasury_balances()
            initial_balance = initial_balances.get(account_key, 0) if initial_balances else 0
            
            # Create invoice
            invoice = await self.create_test_invoice(payment_method, amount)
            
            if not invoice:
                print(f"❌ Failed to create invoice for {payment_method}")
                test_results.append(False)
                continue
                
            # Wait for processing
            await asyncio.sleep(1)
            
            # Check final balance
            final_balances = await self.get_treasury_balances()
            final_balance = final_balances.get(account_key, 0) if final_balances else 0
            balance_increase = final_balance - initial_balance
            
            # Check for duplicate transactions
            duplicate_count, _ = await self.count_treasury_transactions_for_reference(f"invoice_{invoice['id']}")
            
            print(f"   📊 Balance increase: {balance_increase} ج.م (Expected: {amount} ج.م)")
            print(f"   📊 Treasury transactions: {duplicate_count}")
            
            # Analysis
            is_balance_correct = abs(balance_increase - amount) < 0.01
            no_duplicates = duplicate_count <= 1
            
            test_passed = is_balance_correct and no_duplicates
            result = "✅" if test_passed else "❌"
            print(f"   {result} {payment_method}")
            
            if not is_balance_correct:
                print(f"   ❌ Balance incorrect. Expected: {amount}, Got: {balance_increase}")
            if not no_duplicates:
                print(f"   ❌ Duplicate transactions detected: {duplicate_count}")
                
            test_results.append(test_passed)
            
        # Overall result
        all_passed = all(test_results)
        result = "✅ PASSED" if all_passed else "❌ FAILED"
        print(f"\n{result} - Multiple Payment Methods Test")
        
        return all_passed
        
    async def test_treasury_balance_consistency(self):
        """Test 5: Check overall treasury balance consistency"""
        print("\n🔍 Test 5: Treasury Balance Consistency Check")
        print("=" * 70)
        
        # Get all treasury data
        balances = await self.get_treasury_balances()
        transactions = await self.get_treasury_transactions()
        
        if not balances or not transactions:
            print("❌ Failed to get treasury data")
            return False
            
        print("📊 Current Treasury Balances:")
        total_balance = 0
        for account, balance in balances.items():
            print(f"   {account}: {balance} ج.م")
            total_balance += balance
            
        print(f"📊 Total Balance: {total_balance} ج.م")
        print(f"📊 Total Transactions: {len(transactions)}")
        
        # Check for suspicious patterns
        suspicious_patterns = []
        
        # Group transactions by reference
        reference_groups = {}
        for transaction in transactions:
            ref = transaction.get("reference", "")
            if ref not in reference_groups:
                reference_groups[ref] = []
            reference_groups[ref].append(transaction)
            
        # Check for duplicate invoice references
        for ref, trans_list in reference_groups.items():
            if ref.startswith("invoice_") and len(trans_list) > 1:
                suspicious_patterns.append(f"Multiple transactions for {ref}: {len(trans_list)} transactions")
                
        # Check for same amount/description duplicates
        amount_desc_groups = {}
        for transaction in transactions:
            key = f"{transaction.get('amount')}_{transaction.get('description')}"
            if key not in amount_desc_groups:
                amount_desc_groups[key] = []
            amount_desc_groups[key].append(transaction)
            
        for key, trans_list in amount_desc_groups.items():
            if len(trans_list) > 1:
                # Check if they're not legitimate (like transfers)
                if not any("تحويل" in t.get("description", "") for t in trans_list):
                    suspicious_patterns.append(f"Duplicate amount/description: {key} - {len(trans_list)} transactions")
        
        # Report findings
        if suspicious_patterns:
            print("\n🚨 SUSPICIOUS PATTERNS DETECTED:")
            for pattern in suspicious_patterns:
                print(f"   ⚠️  {pattern}")
        else:
            print("\n✅ No suspicious patterns detected")
            
        # Test result
        test_passed = len(suspicious_patterns) == 0
        result = "✅ PASSED" if test_passed else "❌ FAILED"
        print(f"\n{result} - Treasury Balance Consistency Test")
        
        return test_passed
        
    async def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created invoices
        for invoice_id in self.created_invoices:
            await self.make_request("DELETE", f"/invoices/{invoice_id}")
            
        # Delete created customers
        for customer_id in self.created_customers:
            await self.make_request("DELETE", f"/customers/{customer_id}")
            
        print(f"✅ Cleaned up {len(self.created_invoices)} invoices and {len(self.created_customers)} customers")
        
    async def run_all_tests(self):
        """Run all treasury bug tests"""
        print("🔍 TREASURY DOUBLE TRANSACTION BUG INVESTIGATION")
        print("=" * 80)
        print("Testing for the reported issue: Invoice amounts being added to treasury twice")
        print("=" * 80)
        
        await self.setup_session()
        
        try:
            # Create test customer
            customer = await self.create_test_customer()
            if not customer:
                print("❌ Failed to create test customer. Aborting tests.")
                return
                
            # Run tests
            test_results = []
            
            # Test 1: Cash payment invoice
            result1 = await self.test_cash_payment_invoice()
            test_results.append(("Cash Payment Invoice", result1))
            
            # Test 2: Deferred payment invoice
            result2, deferred_invoice = await self.test_deferred_payment_invoice()
            test_results.append(("Deferred Payment Invoice", result2))
            
            # Test 3: Deferred payment settlement
            result3 = await self.test_deferred_payment_settlement(deferred_invoice)
            test_results.append(("Deferred Payment Settlement", result3))
            
            # Test 4: Multiple payment methods
            result4 = await self.test_multiple_payment_methods()
            test_results.append(("Multiple Payment Methods", result4))
            
            # Test 5: Treasury balance consistency
            result5 = await self.test_treasury_balance_consistency()
            test_results.append(("Treasury Balance Consistency", result5))
            
            # Summary
            print("\n" + "=" * 80)
            print("🔍 TREASURY BUG INVESTIGATION SUMMARY")
            print("=" * 80)
            
            passed_count = 0
            for test_name, passed in test_results:
                status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"{status} - {test_name}")
                if passed:
                    passed_count += 1
                    
            print(f"\nOverall Result: {passed_count}/{len(test_results)} tests passed")
            
            if passed_count == len(test_results):
                print("✅ NO TREASURY DOUBLE TRANSACTION BUG DETECTED")
                print("   All treasury operations appear to be working correctly.")
            else:
                print("🚨 TREASURY ISSUES DETECTED")
                print("   The reported double transaction bug may be present.")
                print("   Review the failed tests above for specific issues.")
                
            # Cleanup
            await self.cleanup_test_data()
            
        finally:
            await self.cleanup_session()

async def main():
    """Main test execution"""
    tester = TreasuryBugTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())