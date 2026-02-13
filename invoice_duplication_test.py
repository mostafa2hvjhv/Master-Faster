#!/usr/bin/env python3
"""
Invoice Duplication Bug Investigation Test
اختبار تحقيق مشكلة تكرار الفواتير

This test specifically investigates the invoice duplication bug reported by the user:
- Check for duplicate invoices in database
- Check for duplicate treasury transactions
- Check for duplicate work order entries
- Test race conditions in invoice creation
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class InvoiceDuplicationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_invoices = []
        self.created_customers = []
        
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
    
    def setup_test_data(self):
        """Create test customer for invoice testing"""
        print("\n=== Setting up test data ===")
        
        # Create test customer
        customer_data = {
            "name": "عميل اختبار تكرار الفواتير",
            "phone": "01234567890",
            "address": "عنوان اختبار"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if response.status_code == 200:
                customer = response.json()
                self.created_customers.append(customer)
                self.log_test("Create test customer", True, f"Customer ID: {customer['id']}")
                return customer
            else:
                self.log_test("Create test customer", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Create test customer", False, f"Error: {str(e)}")
            return None
    
    def create_test_invoice(self, customer_id: str, invoice_suffix: str = "", payment_method: str = "نقدي"):
        """Create a test invoice"""
        invoice_data = {
            "customer_id": customer_id,
            "customer_name": f"عميل اختبار تكرار الفواتير {invoice_suffix}",
            "invoice_title": f"فاتورة اختبار تكرار {invoice_suffix}",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 10.0,
                    "quantity": 2,
                    "unit_price": 50.0,
                    "total_price": 100.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": payment_method,
            "discount_type": "amount",
            "discount_value": 0.0,
            "notes": f"فاتورة اختبار تكرار {invoice_suffix}"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                invoice = response.json()
                self.created_invoices.append(invoice)
                return invoice
            else:
                print(f"Failed to create invoice: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating invoice: {str(e)}")
            return None
    
    def check_duplicate_invoices(self):
        """Check for duplicate invoices in database"""
        print("\n=== Checking for Duplicate Invoices ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            if response.status_code == 200:
                invoices = response.json()
                
                # Group invoices by customer_name and invoice_title
                invoice_groups = {}
                for invoice in invoices:
                    key = f"{invoice.get('customer_name', '')}-{invoice.get('invoice_title', '')}"
                    if key not in invoice_groups:
                        invoice_groups[key] = []
                    invoice_groups[key].append(invoice)
                
                # Check for duplicates
                duplicates_found = []
                for key, group in invoice_groups.items():
                    if len(group) > 1:
                        duplicates_found.append({
                            'key': key,
                            'count': len(group),
                            'invoice_numbers': [inv.get('invoice_number') for inv in group],
                            'invoice_ids': [inv.get('id') for inv in group]
                        })
                
                if duplicates_found:
                    details = f"Found {len(duplicates_found)} duplicate groups: {duplicates_found}"
                    self.log_test("Check duplicate invoices", False, details)
                    return duplicates_found
                else:
                    self.log_test("Check duplicate invoices", True, f"No duplicates found among {len(invoices)} invoices")
                    return []
                    
            else:
                self.log_test("Check duplicate invoices", False, f"Failed to get invoices: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Check duplicate invoices", False, f"Error: {str(e)}")
            return None
    
    def check_duplicate_treasury_transactions(self):
        """Check for duplicate treasury transactions"""
        print("\n=== Checking for Duplicate Treasury Transactions ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
            if response.status_code == 200:
                transactions = response.json()
                
                # Group transactions by reference (invoice reference)
                transaction_groups = {}
                for transaction in transactions:
                    reference = transaction.get('reference', '')
                    if reference.startswith('invoice_'):
                        if reference not in transaction_groups:
                            transaction_groups[reference] = []
                        transaction_groups[reference].append(transaction)
                
                # Check for duplicates
                duplicates_found = []
                for reference, group in transaction_groups.items():
                    if len(group) > 1:
                        # Check if they are truly duplicates (same amount, same account)
                        unique_transactions = {}
                        for trans in group:
                            key = f"{trans.get('account_id')}-{trans.get('amount')}-{trans.get('transaction_type')}"
                            if key not in unique_transactions:
                                unique_transactions[key] = []
                            unique_transactions[key].append(trans)
                        
                        for key, trans_list in unique_transactions.items():
                            if len(trans_list) > 1:
                                duplicates_found.append({
                                    'reference': reference,
                                    'key': key,
                                    'count': len(trans_list),
                                    'transaction_ids': [t.get('id') for t in trans_list]
                                })
                
                if duplicates_found:
                    details = f"Found {len(duplicates_found)} duplicate transaction groups: {duplicates_found}"
                    self.log_test("Check duplicate treasury transactions", False, details)
                    return duplicates_found
                else:
                    self.log_test("Check duplicate treasury transactions", True, f"No duplicate transactions found among {len(transactions)} transactions")
                    return []
                    
            else:
                self.log_test("Check duplicate treasury transactions", False, f"Failed to get transactions: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Check duplicate treasury transactions", False, f"Error: {str(e)}")
            return None
    
    def check_duplicate_work_order_entries(self):
        """Check for duplicate invoice entries in work orders"""
        print("\n=== Checking for Duplicate Work Order Entries ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/work-orders")
            if response.status_code == 200:
                work_orders = response.json()
                
                duplicates_found = []
                for work_order in work_orders:
                    invoices = work_order.get('invoices', [])
                    if len(invoices) > 0:
                        # Check for duplicate invoice IDs within the same work order
                        invoice_ids = [inv.get('id') for inv in invoices if inv.get('id')]
                        unique_ids = set(invoice_ids)
                        
                        if len(invoice_ids) != len(unique_ids):
                            # Found duplicates
                            duplicate_ids = []
                            seen = set()
                            for inv_id in invoice_ids:
                                if inv_id in seen:
                                    duplicate_ids.append(inv_id)
                                seen.add(inv_id)
                            
                            duplicates_found.append({
                                'work_order_id': work_order.get('id'),
                                'work_order_title': work_order.get('title'),
                                'total_invoices': len(invoices),
                                'unique_invoices': len(unique_ids),
                                'duplicate_invoice_ids': duplicate_ids
                            })
                
                if duplicates_found:
                    details = f"Found {len(duplicates_found)} work orders with duplicate entries: {duplicates_found}"
                    self.log_test("Check duplicate work order entries", False, details)
                    return duplicates_found
                else:
                    self.log_test("Check duplicate work order entries", True, f"No duplicate entries found in {len(work_orders)} work orders")
                    return []
                    
            else:
                self.log_test("Check duplicate work order entries", False, f"Failed to get work orders: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Check duplicate work order entries", False, f"Error: {str(e)}")
            return None
    
    def test_single_invoice_creation_flow(self):
        """Test creating a single invoice and check all related database entries"""
        print("\n=== Testing Single Invoice Creation Flow ===")
        
        if not self.created_customers:
            customer = self.setup_test_data()
            if not customer:
                return False
        else:
            customer = self.created_customers[0]
        
        # Get initial counts
        initial_counts = self.get_database_counts()
        
        # Create a cash invoice
        print("Creating cash invoice...")
        cash_invoice = self.create_test_invoice(customer['id'], "نقدي", "نقدي")
        
        if not cash_invoice:
            self.log_test("Create cash invoice", False, "Failed to create invoice")
            return False
        
        # Wait a moment for processing
        time.sleep(1)
        
        # Get final counts
        final_counts = self.get_database_counts()
        
        # Analyze the changes
        invoice_increase = final_counts['invoices'] - initial_counts['invoices']
        treasury_increase = final_counts['treasury_transactions'] - initial_counts['treasury_transactions']
        work_order_increase = final_counts['work_orders'] - initial_counts['work_orders']
        
        success = True
        details = []
        
        # Check invoice creation
        if invoice_increase == 1:
            details.append(f"✅ Invoice count increased by 1 (expected)")
        else:
            details.append(f"❌ Invoice count increased by {invoice_increase} (expected 1)")
            success = False
        
        # Check treasury transaction creation
        if treasury_increase == 1:
            details.append(f"✅ Treasury transactions increased by 1 (expected for cash payment)")
        else:
            details.append(f"❌ Treasury transactions increased by {treasury_increase} (expected 1)")
            success = False
        
        # Check work order creation/update
        if work_order_increase <= 1:  # Could be 0 if added to existing daily work order, or 1 if new daily work order created
            details.append(f"✅ Work orders increased by {work_order_increase} (acceptable)")
        else:
            details.append(f"❌ Work orders increased by {work_order_increase} (unexpected)")
            success = False
        
        self.log_test("Single cash invoice creation flow", success, "; ".join(details))
        
        # Now test deferred invoice
        print("Creating deferred invoice...")
        deferred_invoice = self.create_test_invoice(customer['id'], "آجل", "آجل")
        
        if not deferred_invoice:
            self.log_test("Create deferred invoice", False, "Failed to create invoice")
            return False
        
        # Wait a moment for processing
        time.sleep(1)
        
        # Get new final counts
        new_final_counts = self.get_database_counts()
        
        # Analyze the changes for deferred invoice
        invoice_increase_2 = new_final_counts['invoices'] - final_counts['invoices']
        treasury_increase_2 = new_final_counts['treasury_transactions'] - final_counts['treasury_transactions']
        
        success_2 = True
        details_2 = []
        
        # Check invoice creation
        if invoice_increase_2 == 1:
            details_2.append(f"✅ Invoice count increased by 1 (expected)")
        else:
            details_2.append(f"❌ Invoice count increased by {invoice_increase_2} (expected 1)")
            success_2 = False
        
        # Check treasury transaction creation (should be 0 for deferred)
        if treasury_increase_2 == 0:
            details_2.append(f"✅ Treasury transactions increased by 0 (expected for deferred payment)")
        else:
            details_2.append(f"❌ Treasury transactions increased by {treasury_increase_2} (expected 0 for deferred)")
            success_2 = False
        
        self.log_test("Single deferred invoice creation flow", success_2, "; ".join(details_2))
        
        return success and success_2
    
    def get_database_counts(self):
        """Get current counts of various database entities"""
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
            
        except Exception as e:
            print(f"Error getting database counts: {str(e)}")
            counts = {'invoices': 0, 'treasury_transactions': 0, 'work_orders': 0}
        
        return counts
    
    def test_invoice_number_uniqueness(self):
        """Check if invoice numbers are unique"""
        print("\n=== Testing Invoice Number Uniqueness ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            if response.status_code == 200:
                invoices = response.json()
                
                invoice_numbers = [inv.get('invoice_number') for inv in invoices if inv.get('invoice_number')]
                unique_numbers = set(invoice_numbers)
                
                if len(invoice_numbers) == len(unique_numbers):
                    self.log_test("Invoice number uniqueness", True, f"All {len(invoice_numbers)} invoice numbers are unique")
                    return True
                else:
                    duplicates = []
                    seen = set()
                    for num in invoice_numbers:
                        if num in seen:
                            duplicates.append(num)
                        seen.add(num)
                    
                    self.log_test("Invoice number uniqueness", False, f"Found duplicate invoice numbers: {duplicates}")
                    return False
                    
            else:
                self.log_test("Invoice number uniqueness", False, f"Failed to get invoices: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Invoice number uniqueness", False, f"Error: {str(e)}")
            return False
    
    def test_race_condition_simulation(self):
        """Simulate potential race conditions by creating multiple invoices quickly"""
        print("\n=== Testing Race Condition Simulation ===")
        
        if not self.created_customers:
            customer = self.setup_test_data()
            if not customer:
                return False
        else:
            customer = self.created_customers[0]
        
        # Get initial counts
        initial_counts = self.get_database_counts()
        
        # Create multiple invoices quickly
        created_invoices = []
        for i in range(3):
            invoice = self.create_test_invoice(customer['id'], f"سريع-{i+1}", "نقدي")
            if invoice:
                created_invoices.append(invoice)
            time.sleep(0.1)  # Small delay to simulate rapid creation
        
        # Wait for processing
        time.sleep(2)
        
        # Get final counts
        final_counts = self.get_database_counts()
        
        # Analyze results
        invoice_increase = final_counts['invoices'] - initial_counts['invoices']
        treasury_increase = final_counts['treasury_transactions'] - initial_counts['treasury_transactions']
        
        success = True
        details = []
        
        if invoice_increase == len(created_invoices):
            details.append(f"✅ Created {len(created_invoices)} invoices, database shows increase of {invoice_increase}")
        else:
            details.append(f"❌ Created {len(created_invoices)} invoices, but database shows increase of {invoice_increase}")
            success = False
        
        if treasury_increase == len(created_invoices):
            details.append(f"✅ Treasury transactions increased by {treasury_increase} (expected {len(created_invoices)})")
        else:
            details.append(f"❌ Treasury transactions increased by {treasury_increase} (expected {len(created_invoices)})")
            success = False
        
        self.log_test("Race condition simulation", success, "; ".join(details))
        return success
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== Cleaning up test data ===")
        
        # Delete created invoices
        for invoice in self.created_invoices:
            try:
                response = self.session.delete(f"{BACKEND_URL}/invoices/{invoice['id']}")
                if response.status_code == 200:
                    print(f"✅ Deleted invoice {invoice['invoice_number']}")
                else:
                    print(f"❌ Failed to delete invoice {invoice['invoice_number']}")
            except Exception as e:
                print(f"❌ Error deleting invoice: {str(e)}")
        
        # Delete created customers
        for customer in self.created_customers:
            try:
                response = self.session.delete(f"{BACKEND_URL}/customers/{customer['id']}")
                if response.status_code == 200:
                    print(f"✅ Deleted customer {customer['name']}")
                else:
                    print(f"❌ Failed to delete customer {customer['name']}")
            except Exception as e:
                print(f"❌ Error deleting customer: {str(e)}")
    
    def run_all_tests(self):
        """Run all duplication tests"""
        print("🔍 Starting Invoice Duplication Bug Investigation")
        print("=" * 60)
        
        # Setup test data
        self.setup_test_data()
        
        # Run all tests
        tests = [
            self.check_duplicate_invoices,
            self.check_duplicate_treasury_transactions,
            self.check_duplicate_work_order_entries,
            self.test_invoice_number_uniqueness,
            self.test_single_invoice_creation_flow,
            self.test_race_condition_simulation
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
        print("📊 INVOICE DUPLICATION TEST SUMMARY")
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
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = InvoiceDuplicationTester()
    tester.run_all_tests()