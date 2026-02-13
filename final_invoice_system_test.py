#!/usr/bin/env python3
"""
Final Comprehensive Invoice System Test
اختبار شامل نهائي لنظام الفواتير

This test verifies all aspects of the invoice system after investigating the duplication bug
"""

import requests
import json
import sys
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class FinalInvoiceSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_data = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_complete_invoice_workflow(self):
        """Test complete invoice workflow from creation to treasury integration"""
        print("\n=== Testing Complete Invoice Workflow ===")
        
        # Create test customer
        customer_data = {
            "name": "عميل اختبار النظام النهائي",
            "phone": "01555555555",
            "address": "عنوان اختبار نهائي"
        }
        
        response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
        if response.status_code != 200:
            self.log_test("Create test customer", False, f"Status: {response.status_code}")
            return False
        
        customer = response.json()
        self.created_data.append(('customer', customer['id']))
        
        # Get initial counts
        initial_counts = self.get_system_counts()
        
        # Test 1: Cash Invoice
        cash_invoice_data = {
            "customer_id": customer['id'],
            "customer_name": customer['name'],
            "invoice_title": "فاتورة نقدية اختبار نهائي",
            "supervisor_name": "مشرف الاختبار النهائي",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 20.0,
                    "outer_diameter": 30.0,
                    "height": 8.0,
                    "quantity": 2,
                    "unit_price": 75.0,
                    "total_price": 150.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "نقدي",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "notes": "فاتورة اختبار نهائي نقدية"
        }
        
        response = self.session.post(f"{BACKEND_URL}/invoices", json=cash_invoice_data)
        if response.status_code != 200:
            self.log_test("Create cash invoice", False, f"Status: {response.status_code}")
            return False
        
        cash_invoice = response.json()
        self.created_data.append(('invoice', cash_invoice['id']))
        
        # Verify cash invoice calculations
        expected_subtotal = 150.0
        expected_discount = 15.0  # 10% of 150
        expected_total = 135.0
        
        success = (
            cash_invoice['subtotal'] == expected_subtotal and
            cash_invoice['discount'] == expected_discount and
            cash_invoice['total_after_discount'] == expected_total and
            cash_invoice['total_amount'] == expected_total
        )
        
        self.log_test("Cash invoice calculations", success, 
                     f"Subtotal: {cash_invoice['subtotal']}, Discount: {cash_invoice['discount']}, Total: {cash_invoice['total_amount']}")
        
        # Test 2: Deferred Invoice
        deferred_invoice_data = {
            "customer_id": customer['id'],
            "customer_name": customer['name'],
            "invoice_title": "فاتورة آجلة اختبار نهائي",
            "supervisor_name": "مشرف الاختبار النهائي",
            "items": [
                {
                    "seal_type": "RS",
                    "material_type": "BUR",
                    "inner_diameter": 15.0,
                    "outer_diameter": 25.0,
                    "height": 6.0,
                    "quantity": 3,
                    "unit_price": 60.0,
                    "total_price": 180.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "آجل",
            "discount_type": "amount",
            "discount_value": 20.0,
            "notes": "فاتورة اختبار نهائي آجلة"
        }
        
        response = self.session.post(f"{BACKEND_URL}/invoices", json=deferred_invoice_data)
        if response.status_code != 200:
            self.log_test("Create deferred invoice", False, f"Status: {response.status_code}")
            return False
        
        deferred_invoice = response.json()
        self.created_data.append(('invoice', deferred_invoice['id']))
        
        # Verify deferred invoice
        expected_remaining = 160.0  # 180 - 20 discount
        success = (
            deferred_invoice['remaining_amount'] == expected_remaining and
            deferred_invoice['payment_method'] == "آجل"
        )
        
        self.log_test("Deferred invoice setup", success,
                     f"Remaining: {deferred_invoice['remaining_amount']}, Payment method: {deferred_invoice['payment_method']}")
        
        # Wait for processing
        time.sleep(1)
        
        # Get final counts
        final_counts = self.get_system_counts()
        
        # Verify system changes
        invoice_increase = final_counts['invoices'] - initial_counts['invoices']
        treasury_increase = final_counts['treasury_transactions'] - initial_counts['treasury_transactions']
        
        # Should have 2 new invoices and 1 new treasury transaction (only for cash invoice)
        success = invoice_increase == 2 and treasury_increase == 1
        self.log_test("System counts after invoice creation", success,
                     f"Invoices: +{invoice_increase} (expected 2), Treasury: +{treasury_increase} (expected 1)")
        
        return True
    
    def test_payment_processing(self):
        """Test payment processing for deferred invoices"""
        print("\n=== Testing Payment Processing ===")
        
        # Find a deferred invoice to make payment for
        response = self.session.get(f"{BACKEND_URL}/invoices")
        if response.status_code != 200:
            self.log_test("Get invoices for payment test", False, f"Status: {response.status_code}")
            return False
        
        invoices = response.json()
        deferred_invoices = [inv for inv in invoices if inv.get('payment_method') == 'آجل' and inv.get('remaining_amount', 0) > 0]
        
        if not deferred_invoices:
            self.log_test("Find deferred invoice for payment", False, "No deferred invoices found")
            return False
        
        deferred_invoice = deferred_invoices[0]
        payment_amount = min(50.0, deferred_invoice['remaining_amount'])
        
        # Get initial treasury count
        initial_treasury_count = len(self.session.get(f"{BACKEND_URL}/treasury/transactions").json())
        
        # Create payment
        payment_data = {
            "invoice_id": deferred_invoice['id'],
            "amount": payment_amount,
            "payment_method": "نقدي",
            "notes": "دفعة اختبار نهائي"
        }
        
        response = self.session.post(f"{BACKEND_URL}/payments", json=payment_data)
        if response.status_code != 200:
            self.log_test("Create payment", False, f"Status: {response.status_code}")
            return False
        
        payment = response.json()
        self.created_data.append(('payment', payment['id']))
        
        # Verify payment created treasury transactions
        final_treasury_count = len(self.session.get(f"{BACKEND_URL}/treasury/transactions").json())
        treasury_increase = final_treasury_count - initial_treasury_count
        
        # Should create 2 transactions: income to cash, expense from deferred
        success = treasury_increase == 2
        self.log_test("Payment treasury transactions", success,
                     f"Treasury transactions increased by {treasury_increase} (expected 2)")
        
        # Verify invoice updated
        response = self.session.get(f"{BACKEND_URL}/invoices/{deferred_invoice['id']}")
        if response.status_code == 200:
            updated_invoice = response.json()
            expected_paid = deferred_invoice['paid_amount'] + payment_amount
            expected_remaining = deferred_invoice['remaining_amount'] - payment_amount
            
            success = (
                updated_invoice['paid_amount'] == expected_paid and
                updated_invoice['remaining_amount'] == expected_remaining
            )
            
            self.log_test("Invoice updated after payment", success,
                         f"Paid: {updated_invoice['paid_amount']}, Remaining: {updated_invoice['remaining_amount']}")
        
        return True
    
    def test_treasury_balance_accuracy(self):
        """Test treasury balance calculations"""
        print("\n=== Testing Treasury Balance Accuracy ===")
        
        response = self.session.get(f"{BACKEND_URL}/treasury/balances")
        if response.status_code != 200:
            self.log_test("Get treasury balances", False, f"Status: {response.status_code}")
            return False
        
        balances = response.json()
        
        # Verify all expected accounts exist
        expected_accounts = ['cash', 'vodafone_elsawy', 'vodafone_wael', 'deferred', 'instapay', 'yad_elsawy']
        missing_accounts = [acc for acc in expected_accounts if acc not in balances]
        
        if missing_accounts:
            self.log_test("Treasury accounts completeness", False, f"Missing accounts: {missing_accounts}")
            return False
        
        self.log_test("Treasury accounts completeness", True, "All expected accounts present")
        
        # Verify balances are numeric
        for account, balance in balances.items():
            if not isinstance(balance, (int, float)):
                self.log_test(f"Treasury balance type for {account}", False, f"Balance is not numeric: {type(balance)}")
                return False
        
        self.log_test("Treasury balance types", True, "All balances are numeric")
        
        # Log current balances for reference
        balance_details = ", ".join([f"{acc}: {bal}" for acc, bal in balances.items()])
        self.log_test("Treasury balance values", True, balance_details)
        
        return True
    
    def test_work_order_integration(self):
        """Test work order integration with invoices"""
        print("\n=== Testing Work Order Integration ===")
        
        # Get today's work order
        today = datetime.now().strftime("%Y-%m-%d")
        response = self.session.get(f"{BACKEND_URL}/work-orders/daily/{today}")
        
        if response.status_code != 200:
            self.log_test("Get daily work order", False, f"Status: {response.status_code}")
            return False
        
        work_order = response.json()
        
        # Verify work order structure
        required_fields = ['id', 'title', 'is_daily', 'work_date', 'invoices', 'total_amount', 'total_items']
        missing_fields = [field for field in required_fields if field not in work_order]
        
        if missing_fields:
            self.log_test("Work order structure", False, f"Missing fields: {missing_fields}")
            return False
        
        self.log_test("Work order structure", True, "All required fields present")
        
        # Verify invoices in work order
        invoices_in_wo = work_order.get('invoices', [])
        if len(invoices_in_wo) > 0:
            # Check for duplicate invoice IDs
            invoice_ids = [inv.get('id') for inv in invoices_in_wo if inv.get('id')]
            unique_ids = set(invoice_ids)
            
            success = len(invoice_ids) == len(unique_ids)
            self.log_test("Work order invoice uniqueness", success,
                         f"Total: {len(invoice_ids)}, Unique: {len(unique_ids)}")
        else:
            self.log_test("Work order invoice count", True, "No invoices in work order (acceptable)")
        
        return True
    
    def get_system_counts(self):
        """Get current counts of system entities"""
        counts = {}
        
        try:
            # Count invoices
            response = self.session.get(f"{BACKEND_URL}/invoices")
            counts['invoices'] = len(response.json()) if response.status_code == 200 else 0
            
            # Count treasury transactions
            response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
            counts['treasury_transactions'] = len(response.json()) if response.status_code == 200 else 0
            
            # Count work orders
            response = self.session.get(f"{BACKEND_URL}/work-orders")
            counts['work_orders'] = len(response.json()) if response.status_code == 200 else 0
            
            # Count payments
            response = self.session.get(f"{BACKEND_URL}/payments")
            counts['payments'] = len(response.json()) if response.status_code == 200 else 0
            
        except Exception as e:
            print(f"Error getting system counts: {str(e)}")
            counts = {'invoices': 0, 'treasury_transactions': 0, 'work_orders': 0, 'payments': 0}
        
        return counts
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== Cleaning up test data ===")
        
        for data_type, data_id in reversed(self.created_data):
            try:
                if data_type == 'invoice':
                    response = self.session.delete(f"{BACKEND_URL}/invoices/{data_id}")
                elif data_type == 'customer':
                    response = self.session.delete(f"{BACKEND_URL}/customers/{data_id}")
                elif data_type == 'payment':
                    response = self.session.delete(f"{BACKEND_URL}/payments/{data_id}")
                
                if response.status_code == 200:
                    print(f"✅ Deleted {data_type}: {data_id}")
                else:
                    print(f"❌ Failed to delete {data_type}: {data_id}")
            except Exception as e:
                print(f"❌ Error deleting {data_type}: {str(e)}")
    
    def run_all_tests(self):
        """Run all final system tests"""
        print("🔍 Starting Final Invoice System Test")
        print("=" * 60)
        
        tests = [
            self.test_complete_invoice_workflow,
            self.test_payment_processing,
            self.test_treasury_balance_accuracy,
            self.test_work_order_integration
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test failed with exception: {str(e)}")
        
        # Print summary
        self.print_summary()
        
        # Cleanup
        self.cleanup_test_data()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 FINAL INVOICE SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"❌ {result['test']}: {result['details']}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = FinalInvoiceSystemTester()
    tester.run_all_tests()