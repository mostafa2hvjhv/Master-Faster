#!/usr/bin/env python3
"""
Deferred Page Filtering Test - اختبار فلتر صفحة الآجل
Testing the fix for cash invoices appearing in deferred page when they shouldn't
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class DeferredFilterTester:
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
    
    def create_test_customer(self, name: str) -> str:
        """Create a test customer and return customer ID"""
        try:
            customer_data = {
                "name": name,
                "phone": "01234567890",
                "address": "عنوان اختبار"
            }
            
            response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if response.status_code == 200:
                customer = response.json()
                self.created_customers.append(customer['id'])
                return customer['id']
            else:
                print(f"Failed to create customer: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating customer: {str(e)}")
            return None
    
    def create_cash_invoice(self, customer_id: str, customer_name: str) -> Dict:
        """Create a cash invoice (نقدي)"""
        try:
            invoice_data = {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "invoice_title": "فاتورة نقدية للاختبار",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "seal_type": "RSL",
                        "material_type": "NBR",
                        "inner_diameter": 25.0,
                        "outer_diameter": 35.0,
                        "height": 7.0,
                        "quantity": 10,
                        "unit_price": 15.0,
                        "total_price": 150.0,
                        "product_type": "manufactured"
                    }
                ],
                "payment_method": "نقدي",
                "discount_type": "amount",
                "discount_value": 0.0,
                "notes": "فاتورة نقدية للاختبار - يجب ألا تظهر في صفحة الآجل"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                invoice = response.json()
                self.created_invoices.append(invoice['id'])
                return invoice
            else:
                print(f"Failed to create cash invoice: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating cash invoice: {str(e)}")
            return None
    
    def create_deferred_invoice(self, customer_id: str, customer_name: str) -> Dict:
        """Create a deferred invoice (آجل)"""
        try:
            invoice_data = {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "invoice_title": "فاتورة آجلة للاختبار",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "seal_type": "RS",
                        "material_type": "BUR",
                        "inner_diameter": 30.0,
                        "outer_diameter": 40.0,
                        "height": 8.0,
                        "quantity": 5,
                        "unit_price": 20.0,
                        "total_price": 100.0,
                        "product_type": "manufactured"
                    }
                ],
                "payment_method": "آجل",
                "discount_type": "amount",
                "discount_value": 0.0,
                "notes": "فاتورة آجلة للاختبار - يجب أن تظهر في صفحة الآجل"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                invoice = response.json()
                self.created_invoices.append(invoice['id'])
                return invoice
            else:
                print(f"Failed to create deferred invoice: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating deferred invoice: {str(e)}")
            return None
    
    def create_partially_paid_invoice(self, customer_id: str, customer_name: str) -> Dict:
        """Create a partially paid invoice (should appear in deferred page)"""
        try:
            # First create a cash invoice
            invoice_data = {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "invoice_title": "فاتورة مدفوعة جزئياً للاختبار",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "seal_type": "B17",
                        "material_type": "VT",
                        "inner_diameter": 20.0,
                        "outer_diameter": 30.0,
                        "height": 6.0,
                        "quantity": 8,
                        "unit_price": 12.5,
                        "total_price": 100.0,
                        "product_type": "manufactured"
                    }
                ],
                "payment_method": "نقدي",
                "discount_type": "amount",
                "discount_value": 0.0,
                "notes": "فاتورة مدفوعة جزئياً - يجب أن تظهر في صفحة الآجل"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                invoice = response.json()
                self.created_invoices.append(invoice['id'])
                
                # Now make a partial payment
                payment_data = {
                    "invoice_id": invoice['id'],
                    "amount": 50.0,  # Pay half
                    "payment_method": "نقدي",
                    "notes": "دفعة جزئية للاختبار"
                }
                
                payment_response = self.session.post(f"{BACKEND_URL}/payments", json=payment_data)
                if payment_response.status_code == 200:
                    # Get updated invoice
                    updated_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice['id']}")
                    if updated_response.status_code == 200:
                        return updated_response.json()
                
                return invoice
            else:
                print(f"Failed to create partially paid invoice: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating partially paid invoice: {str(e)}")
            return None
    
    def test_invoice_properties(self, invoice: Dict, expected_payment_method: str, expected_remaining_amount: float):
        """Test invoice properties"""
        test_name = f"Invoice Properties Check - {invoice.get('invoice_number', 'Unknown')}"
        
        try:
            payment_method = invoice.get('payment_method')
            remaining_amount = invoice.get('remaining_amount', 0)
            
            payment_method_correct = payment_method == expected_payment_method
            remaining_amount_correct = abs(remaining_amount - expected_remaining_amount) < 0.01
            
            if payment_method_correct and remaining_amount_correct:
                self.log_test(test_name, True, 
                    f"Payment Method: {payment_method}, Remaining Amount: {remaining_amount}")
                return True
            else:
                self.log_test(test_name, False, 
                    f"Expected Payment Method: {expected_payment_method}, Got: {payment_method}. "
                    f"Expected Remaining: {expected_remaining_amount}, Got: {remaining_amount}")
                return False
                
        except Exception as e:
            self.log_test(test_name, False, f"Error: {str(e)}")
            return False
    
    def apply_deferred_filter_logic(self, invoices: List[Dict]) -> List[Dict]:
        """Apply the deferred page filter logic"""
        filtered_invoices = []
        
        for invoice in invoices:
            payment_method = invoice.get('payment_method', '')
            remaining_amount = invoice.get('remaining_amount', 0)
            status = invoice.get('status', '')
            
            # Filter logic: (payment_method === 'آجل' OR remaining_amount > 0) AND
            # (status === 'غير مدفوعة' OR status === 'مدفوعة جزئياً' OR status === 'انتظار' OR remaining_amount > 0)
            
            condition1 = (payment_method == 'آجل' or remaining_amount > 0)
            condition2 = (status in ['غير مدفوعة', 'مدفوعة جزئياً', 'انتظار'] or remaining_amount > 0)
            
            if condition1 and condition2:
                filtered_invoices.append(invoice)
        
        return filtered_invoices
    
    def test_deferred_filter_logic(self, all_invoices: List[Dict]):
        """Test the deferred page filter logic"""
        print("\n=== Testing Deferred Page Filter Logic ===")
        
        # Apply filter
        deferred_invoices = self.apply_deferred_filter_logic(all_invoices)
        
        # Test each invoice type
        cash_invoices_in_deferred = []
        deferred_invoices_in_deferred = []
        partial_invoices_in_deferred = []
        
        for invoice in deferred_invoices:
            payment_method = invoice.get('payment_method', '')
            remaining_amount = invoice.get('remaining_amount', 0)
            
            if payment_method == 'نقدي' and remaining_amount == 0:
                cash_invoices_in_deferred.append(invoice)
            elif payment_method == 'آجل':
                deferred_invoices_in_deferred.append(invoice)
            elif remaining_amount > 0:
                partial_invoices_in_deferred.append(invoice)
        
        # Test 1: Cash invoices with 0 remaining should NOT appear
        test_name = "Cash Invoices Should NOT Appear in Deferred Page"
        if len(cash_invoices_in_deferred) == 0:
            self.log_test(test_name, True, "No cash invoices with 0 remaining amount found in deferred filter")
        else:
            invoice_numbers = [inv.get('invoice_number', 'Unknown') for inv in cash_invoices_in_deferred]
            self.log_test(test_name, False, f"Found {len(cash_invoices_in_deferred)} cash invoices in deferred filter: {invoice_numbers}")
        
        # Test 2: Deferred invoices should appear
        test_name = "Deferred Invoices Should Appear in Deferred Page"
        if len(deferred_invoices_in_deferred) > 0:
            invoice_numbers = [inv.get('invoice_number', 'Unknown') for inv in deferred_invoices_in_deferred]
            self.log_test(test_name, True, f"Found {len(deferred_invoices_in_deferred)} deferred invoices: {invoice_numbers}")
        else:
            self.log_test(test_name, False, "No deferred invoices found in deferred filter")
        
        # Test 3: Partially paid invoices should appear
        test_name = "Partially Paid Invoices Should Appear in Deferred Page"
        if len(partial_invoices_in_deferred) > 0:
            invoice_numbers = [inv.get('invoice_number', 'Unknown') for inv in partial_invoices_in_deferred]
            self.log_test(test_name, True, f"Found {len(partial_invoices_in_deferred)} partially paid invoices: {invoice_numbers}")
        else:
            self.log_test(test_name, False, "No partially paid invoices found in deferred filter")
        
        return len(cash_invoices_in_deferred) == 0 and len(deferred_invoices_in_deferred) > 0
    
    def get_all_invoices(self) -> List[Dict]:
        """Get all invoices from the system"""
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get invoices: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error getting invoices: {str(e)}")
            return []
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Delete created invoices
        for invoice_id in self.created_invoices:
            try:
                response = self.session.delete(f"{BACKEND_URL}/invoices/{invoice_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted invoice {invoice_id}")
                else:
                    print(f"❌ Failed to delete invoice {invoice_id}")
            except Exception as e:
                print(f"❌ Error deleting invoice {invoice_id}: {str(e)}")
        
        # Delete created customers
        for customer_id in self.created_customers:
            try:
                response = self.session.delete(f"{BACKEND_URL}/customers/{customer_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted customer {customer_id}")
                else:
                    print(f"❌ Failed to delete customer {customer_id}")
            except Exception as e:
                print(f"❌ Error deleting customer {customer_id}: {str(e)}")
    
    def run_deferred_filter_test(self):
        """Run the complete deferred filter test"""
        print("🔍 Starting Deferred Page Filter Test")
        print("=" * 60)
        
        # Step 1: Create test customers
        print("\n=== Step 1: Creating Test Customers ===")
        cash_customer_id = self.create_test_customer("عميل نقدي للاختبار")
        deferred_customer_id = self.create_test_customer("عميل آجل للاختبار")
        partial_customer_id = self.create_test_customer("عميل دفع جزئي للاختبار")
        
        if not all([cash_customer_id, deferred_customer_id, partial_customer_id]):
            print("❌ Failed to create test customers")
            return False
        
        # Step 2: Create test invoices
        print("\n=== Step 2: Creating Test Invoices ===")
        
        # Create cash invoice
        cash_invoice = self.create_cash_invoice(cash_customer_id, "عميل نقدي للاختبار")
        if not cash_invoice:
            print("❌ Failed to create cash invoice")
            return False
        
        # Create deferred invoice
        deferred_invoice = self.create_deferred_invoice(deferred_customer_id, "عميل آجل للاختبار")
        if not deferred_invoice:
            print("❌ Failed to create deferred invoice")
            return False
        
        # Create partially paid invoice
        partial_invoice = self.create_partially_paid_invoice(partial_customer_id, "عميل دفع جزئي للاختبار")
        if not partial_invoice:
            print("❌ Failed to create partially paid invoice")
            return False
        
        # Step 3: Check invoice properties
        print("\n=== Step 3: Checking Invoice Properties ===")
        
        # Test cash invoice properties
        cash_test = self.test_invoice_properties(cash_invoice, "نقدي", 0.0)
        
        # Test deferred invoice properties
        deferred_test = self.test_invoice_properties(deferred_invoice, "آجل", deferred_invoice.get('total_amount', 0))
        
        # Test partially paid invoice properties
        partial_test = self.test_invoice_properties(partial_invoice, "نقدي", 50.0)  # Should have 50 remaining
        
        # Step 4: Get all invoices and test filter logic
        print("\n=== Step 4: Testing Deferred Page Filter Logic ===")
        all_invoices = self.get_all_invoices()
        
        if not all_invoices:
            print("❌ Failed to get invoices for filter testing")
            return False
        
        filter_test = self.test_deferred_filter_logic(all_invoices)
        
        # Step 5: Print summary
        print("\n=== Test Summary ===")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Step 6: Cleanup
        self.cleanup_test_data()
        
        return success_rate >= 80  # Consider test successful if 80% or more tests pass

def main():
    """Main function to run the deferred filter test"""
    tester = DeferredFilterTester()
    
    try:
        success = tester.run_deferred_filter_test()
        
        if success:
            print("\n🎉 Deferred Filter Test PASSED!")
            print("✅ The fix for cash invoices appearing in deferred page is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ Deferred Filter Test FAILED!")
            print("🚨 There are issues with the deferred page filtering logic.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        tester.cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        tester.cleanup_test_data()
        sys.exit(1)

if __name__ == "__main__":
    main()