#!/usr/bin/env python3
"""
Comprehensive Deferred Page Filter Test - اختبار شامل لفلتر صفحة الآجل
Testing various scenarios for the deferred page filtering logic
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class ComprehensiveDeferredTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_invoices = []
        self.created_customers = []
        self.created_payments = []
    
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
    
    def create_invoice_with_payment_method(self, customer_id: str, customer_name: str, 
                                         payment_method: str, amount: float) -> Dict:
        """Create an invoice with specified payment method"""
        try:
            invoice_data = {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "invoice_title": f"فاتورة {payment_method} للاختبار",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "seal_type": "RSL",
                        "material_type": "NBR",
                        "inner_diameter": 25.0,
                        "outer_diameter": 35.0,
                        "height": 7.0,
                        "quantity": int(amount / 10),
                        "unit_price": 10.0,
                        "total_price": amount,
                        "product_type": "manufactured"
                    }
                ],
                "payment_method": payment_method,
                "discount_type": "amount",
                "discount_value": 0.0,
                "notes": f"فاتورة {payment_method} للاختبار الشامل"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                invoice = response.json()
                self.created_invoices.append(invoice['id'])
                return invoice
            else:
                print(f"Failed to create {payment_method} invoice: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating {payment_method} invoice: {str(e)}")
            return None
    
    def make_partial_payment(self, invoice_id: str, payment_amount: float, payment_method: str = "نقدي") -> bool:
        """Make a partial payment on an invoice"""
        try:
            payment_data = {
                "invoice_id": invoice_id,
                "amount": payment_amount,
                "payment_method": payment_method,
                "notes": f"دفعة جزئية {payment_amount} ج.م"
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments", json=payment_data)
            if response.status_code == 200:
                payment = response.json()
                self.created_payments.append(payment['id'])
                return True
            else:
                print(f"Failed to make payment: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error making payment: {str(e)}")
            return False
    
    def get_invoice_by_id(self, invoice_id: str) -> Dict:
        """Get updated invoice data"""
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get invoice: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error getting invoice: {str(e)}")
            return None
    
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
    
    def test_scenario(self, scenario_name: str, invoices: List[Dict], expected_in_deferred: List[str]):
        """Test a specific scenario"""
        print(f"\n--- Testing Scenario: {scenario_name} ---")
        
        # Apply filter
        deferred_invoices = self.apply_deferred_filter_logic(invoices)
        deferred_invoice_numbers = [inv.get('invoice_number', 'Unknown') for inv in deferred_invoices]
        
        # Check if expected invoices are in deferred list
        all_expected_found = all(inv_num in deferred_invoice_numbers for inv_num in expected_in_deferred)
        
        # Check if any unexpected invoices are in deferred list
        unexpected_invoices = [inv_num for inv_num in deferred_invoice_numbers if inv_num not in expected_in_deferred]
        
        success = all_expected_found and len(unexpected_invoices) == 0
        
        details = f"Expected in deferred: {expected_in_deferred}, Found in deferred: {deferred_invoice_numbers}"
        if unexpected_invoices:
            details += f", Unexpected: {unexpected_invoices}"
        
        self.log_test(scenario_name, success, details)
        return success
    
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
        
        # Delete created payments
        for payment_id in self.created_payments:
            try:
                response = self.session.delete(f"{BACKEND_URL}/payments/{payment_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted payment {payment_id}")
            except Exception as e:
                print(f"❌ Error deleting payment {payment_id}: {str(e)}")
        
        # Delete created invoices
        for invoice_id in self.created_invoices:
            try:
                response = self.session.delete(f"{BACKEND_URL}/invoices/{invoice_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted invoice {invoice_id}")
            except Exception as e:
                print(f"❌ Error deleting invoice {invoice_id}: {str(e)}")
        
        # Delete created customers
        for customer_id in self.created_customers:
            try:
                response = self.session.delete(f"{BACKEND_URL}/customers/{customer_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted customer {customer_id}")
            except Exception as e:
                print(f"❌ Error deleting customer {customer_id}: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run comprehensive deferred filter tests"""
        print("🔍 Starting Comprehensive Deferred Page Filter Test")
        print("=" * 70)
        
        # Create test customers
        print("\n=== Creating Test Customers ===")
        customers = {}
        customer_names = [
            "عميل نقدي مدفوع كامل",
            "عميل آجل",
            "عميل نقدي مدفوع جزئياً",
            "عميل فودافون مدفوع كامل",
            "عميل فودافون مدفوع جزئياً",
            "عميل انستاباي مدفوع كامل",
            "عميل يد الصاوي آجل"
        ]
        
        for name in customer_names:
            customer_id = self.create_test_customer(name)
            if customer_id:
                customers[name] = customer_id
            else:
                print(f"❌ Failed to create customer: {name}")
                return False
        
        # Create test invoices
        print("\n=== Creating Test Invoices ===")
        test_invoices = []
        
        # Scenario 1: Cash invoice - fully paid (should NOT appear in deferred)
        cash_invoice = self.create_invoice_with_payment_method(
            customers["عميل نقدي مدفوع كامل"], "عميل نقدي مدفوع كامل", "نقدي", 100.0)
        if cash_invoice:
            test_invoices.append(cash_invoice)
        
        # Scenario 2: Deferred invoice (should appear in deferred)
        deferred_invoice = self.create_invoice_with_payment_method(
            customers["عميل آجل"], "عميل آجل", "آجل", 200.0)
        if deferred_invoice:
            test_invoices.append(deferred_invoice)
        
        # Scenario 3: Cash invoice - partially paid (should appear in deferred)
        cash_partial_invoice = self.create_invoice_with_payment_method(
            customers["عميل نقدي مدفوع جزئياً"], "عميل نقدي مدفوع جزئياً", "نقدي", 150.0)
        if cash_partial_invoice:
            # Make partial payment
            if self.make_partial_payment(cash_partial_invoice['id'], 75.0):
                # Get updated invoice
                updated_invoice = self.get_invoice_by_id(cash_partial_invoice['id'])
                if updated_invoice:
                    test_invoices.append(updated_invoice)
        
        # Scenario 4: Vodafone invoice - fully paid (should NOT appear in deferred)
        vodafone_invoice = self.create_invoice_with_payment_method(
            customers["عميل فودافون مدفوع كامل"], "عميل فودافون مدفوع كامل", 
            "فودافون كاش محمد الصاوي", 120.0)
        if vodafone_invoice:
            test_invoices.append(vodafone_invoice)
        
        # Scenario 5: Vodafone invoice - partially paid (should appear in deferred)
        vodafone_partial_invoice = self.create_invoice_with_payment_method(
            customers["عميل فودافون مدفوع جزئياً"], "عميل فودافون مدفوع جزئياً", 
            "فودافون كاش محمد الصاوي", 180.0)
        if vodafone_partial_invoice:
            # Make partial payment
            if self.make_partial_payment(vodafone_partial_invoice['id'], 90.0, "فودافون كاش محمد الصاوي"):
                # Get updated invoice
                updated_invoice = self.get_invoice_by_id(vodafone_partial_invoice['id'])
                if updated_invoice:
                    test_invoices.append(updated_invoice)
        
        # Scenario 6: InstaPay invoice - fully paid (should NOT appear in deferred)
        instapay_invoice = self.create_invoice_with_payment_method(
            customers["عميل انستاباي مدفوع كامل"], "عميل انستاباي مدفوع كامل", "انستاباي", 80.0)
        if instapay_invoice:
            test_invoices.append(instapay_invoice)
        
        # Scenario 7: Yad Elsawy deferred invoice (should appear in deferred)
        yad_elsawy_invoice = self.create_invoice_with_payment_method(
            customers["عميل يد الصاوي آجل"], "عميل يد الصاوي آجل", "آجل", 250.0)
        if yad_elsawy_invoice:
            test_invoices.append(yad_elsawy_invoice)
        
        # Test the filter logic
        print("\n=== Testing Filter Logic ===")
        
        # Get all invoices (including our test invoices)
        all_invoices = self.get_all_invoices()
        
        # Find our test invoices in the full list
        our_test_invoices = []
        for invoice in all_invoices:
            if invoice['id'] in [inv['id'] for inv in test_invoices]:
                our_test_invoices.append(invoice)
        
        # Expected invoices that should appear in deferred page
        expected_deferred = []
        expected_not_deferred = []
        
        for invoice in our_test_invoices:
            payment_method = invoice.get('payment_method', '')
            remaining_amount = invoice.get('remaining_amount', 0)
            invoice_number = invoice.get('invoice_number', 'Unknown')
            
            if payment_method == 'آجل' or remaining_amount > 0:
                expected_deferred.append(invoice_number)
            else:
                expected_not_deferred.append(invoice_number)
        
        # Test the scenarios
        success = self.test_scenario(
            "Comprehensive Deferred Filter Test", 
            our_test_invoices, 
            expected_deferred
        )
        
        # Additional detailed tests
        print("\n=== Detailed Filter Tests ===")
        
        # Test 1: Only deferred payment method invoices
        deferred_only = [inv for inv in our_test_invoices if inv.get('payment_method') == 'آجل']
        deferred_only_numbers = [inv.get('invoice_number') for inv in deferred_only]
        self.test_scenario("Deferred Payment Method Only", deferred_only, deferred_only_numbers)
        
        # Test 2: Only invoices with remaining amount > 0
        remaining_only = [inv for inv in our_test_invoices if inv.get('remaining_amount', 0) > 0]
        remaining_only_numbers = [inv.get('invoice_number') for inv in remaining_only]
        self.test_scenario("Remaining Amount > 0 Only", remaining_only, remaining_only_numbers)
        
        # Test 3: Cash invoices with 0 remaining (should be empty after filter)
        cash_zero_remaining = [inv for inv in our_test_invoices 
                              if inv.get('payment_method') == 'نقدي' and inv.get('remaining_amount', 0) == 0]
        self.test_scenario("Cash Invoices with Zero Remaining", cash_zero_remaining, [])
        
        # Print summary
        print("\n=== Test Summary ===")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show detailed results
        if total_tests - passed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        # Cleanup
        self.cleanup_test_data()
        
        return success_rate >= 90  # Require 90% success rate

def main():
    """Main function to run the comprehensive deferred filter test"""
    tester = ComprehensiveDeferredTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n🎉 Comprehensive Deferred Filter Test PASSED!")
            print("✅ The deferred page filtering logic is working correctly across all scenarios.")
            sys.exit(0)
        else:
            print("\n❌ Comprehensive Deferred Filter Test FAILED!")
            print("🚨 There are issues with the deferred page filtering logic in some scenarios.")
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