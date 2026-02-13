#!/usr/bin/env python3
"""
اختبار مركز لوظيفة إلغاء الفواتير
Focused Invoice Cancellation Testing

Based on the Arabic review request:
- Test invoice cancellation with correct password (1462) and username (Elsawy)
- Test with wrong password
- Test cancelling non-existent invoice
- Test invoice update functionality
- Test payment method change functionality
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class FocusedInvoiceCancellationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.test_invoice_id = None
        self.test_customer_id = None
        
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
    
    def get_existing_invoices(self):
        """Get existing invoices for testing"""
        print("\n=== Getting Existing Invoices for Testing ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            
            if response.status_code == 200:
                invoices = response.json()
                
                if invoices:
                    # Use the first invoice for testing
                    test_invoice = invoices[0]
                    self.test_invoice_id = test_invoice.get('id')
                    self.test_customer_id = test_invoice.get('customer_id')
                    
                    self.log_test("Get Existing Invoices", True, 
                                f"Found {len(invoices)} invoices, using: {test_invoice.get('invoice_number')}")
                    return True
                else:
                    self.log_test("Get Existing Invoices", False, "No existing invoices found")
                    return False
            else:
                self.log_test("Get Existing Invoices", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Existing Invoices", False, f"Exception: {str(e)}")
            return False
    
    def create_simple_test_invoice(self):
        """Create a simple test invoice for cancellation testing"""
        print("\n=== Creating Simple Test Invoice ===")
        
        # First, get or create a customer
        try:
            customers_response = self.session.get(f"{BACKEND_URL}/customers")
            
            if customers_response.status_code == 200:
                customers = customers_response.json()
                
                if customers:
                    customer = customers[0]
                    self.test_customer_id = customer.get('id')
                else:
                    # Create a simple customer
                    customer_data = {
                        "name": "عميل اختبار إلغاء الفواتير",
                        "phone": "01234567890",
                        "address": "القاهرة"
                    }
                    
                    customer_response = self.session.post(f"{BACKEND_URL}/customers", 
                                                        json=customer_data,
                                                        headers={'Content-Type': 'application/json'})
                    
                    if customer_response.status_code == 200:
                        customer = customer_response.json()
                        self.test_customer_id = customer.get('id')
                    else:
                        self.log_test("Create Test Customer", False, f"HTTP {customer_response.status_code}")
                        return False
            else:
                self.log_test("Get Customers", False, f"HTTP {customers_response.status_code}")
                return False
        
        except Exception as e:
            self.log_test("Customer Setup", False, f"Exception: {str(e)}")
            return False
        
        # Create a simple local product invoice (no inventory dependency)
        invoice_data = {
            "customer_id": self.test_customer_id,
            "customer_name": "عميل اختبار إلغاء الفواتير",
            "invoice_title": "فاتورة اختبار إلغاء",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "product_name": "منتج اختبار إلغاء الفاتورة",
                    "quantity": 2,
                    "unit_price": 50.0,
                    "total_price": 100.0,
                    "product_type": "local",
                    "local_product_details": {
                        "name": "منتج اختبار إلغاء الفاتورة",
                        "supplier": "مورد اختبار",
                        "purchase_price": 30.0,
                        "selling_price": 50.0
                    }
                }
            ],
            "payment_method": "نقدي",
            "notes": "فاتورة اختبار إلغاء الفواتير"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/invoices", 
                                       json=invoice_data,
                                       headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                invoice = response.json()
                self.test_invoice_id = invoice.get('id')
                
                self.log_test("Create Simple Test Invoice", True, 
                            f"Invoice: {invoice.get('invoice_number')}, Amount: {invoice.get('total_amount')}")
                return True
            else:
                self.log_test("Create Simple Test Invoice", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Simple Test Invoice", False, f"Exception: {str(e)}")
            return False
    
    def test_1_invoice_cancellation_correct_credentials(self):
        """Test 1: Invoice cancellation with correct password and username"""
        print("\n=== Test 1: Invoice Cancellation with Correct Credentials ===")
        
        if not self.test_invoice_id:
            self.log_test("Test 1 - Correct Credentials", False, "No test invoice available")
            return
        
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/invoices/{self.test_invoice_id}/cancel",
                params={
                    "password": "1462",
                    "username": "Elsawy"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                success_message = data.get('message', '')
                
                # Check for Arabic success message
                if any(keyword in success_message for keyword in ['تم إلغاء', 'نجح', 'success', 'cancelled']):
                    self.log_test("Test 1 - Correct Credentials", True, 
                                f"Successfully cancelled invoice: {success_message}")
                    
                    # Verify invoice is no longer accessible
                    verify_response = self.session.get(f"{BACKEND_URL}/invoices/{self.test_invoice_id}")
                    if verify_response.status_code == 404:
                        self.log_test("Test 1 - Verify Invoice Removed", True, 
                                    "Invoice correctly removed from main collection")
                    else:
                        self.log_test("Test 1 - Verify Invoice Removed", False, 
                                    f"Invoice still accessible: {verify_response.status_code}")
                else:
                    self.log_test("Test 1 - Correct Credentials", False, 
                                f"Unexpected response message: {success_message}")
            else:
                self.log_test("Test 1 - Correct Credentials", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Test 1 - Correct Credentials", False, f"Exception: {str(e)}")
    
    def test_2_wrong_password(self):
        """Test 2: Invoice cancellation with wrong password"""
        print("\n=== Test 2: Invoice Cancellation with Wrong Password ===")
        
        # Create another test invoice for this test
        if not self.create_simple_test_invoice():
            self.log_test("Test 2 Setup", False, "Failed to create test invoice")
            return
        
        wrong_passwords = ["wrong", "1234", "0000", "incorrect", ""]
        
        for wrong_password in wrong_passwords:
            try:
                response = self.session.delete(
                    f"{BACKEND_URL}/invoices/{self.test_invoice_id}/cancel",
                    params={
                        "password": wrong_password,
                        "username": "Elsawy"
                    }
                )
                
                if response.status_code == 401:
                    data = response.json()
                    error_message = data.get('detail', '')
                    
                    if "كلمة المرور غير صحيحة" in error_message or "incorrect" in error_message.lower():
                        self.log_test(f"Test 2 - Wrong Password '{wrong_password or 'empty'}'", True, 
                                    f"Correctly rejected: {error_message}")
                    else:
                        self.log_test(f"Test 2 - Wrong Password '{wrong_password or 'empty'}'", False, 
                                    f"Unexpected error message: {error_message}")
                else:
                    self.log_test(f"Test 2 - Wrong Password '{wrong_password or 'empty'}'", False, 
                                f"Expected HTTP 401, got {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Test 2 - Wrong Password '{wrong_password or 'empty'}'", False, f"Exception: {str(e)}")
    
    def test_3_nonexistent_invoice(self):
        """Test 3: Cancelling non-existent invoice"""
        print("\n=== Test 3: Cancelling Non-Existent Invoice ===")
        
        invalid_ids = ["invalid-id", "00000000-0000-0000-0000-000000000000", "nonexistent"]
        
        for invalid_id in invalid_ids:
            try:
                response = self.session.delete(
                    f"{BACKEND_URL}/invoices/{invalid_id}/cancel",
                    params={
                        "password": "1462",
                        "username": "Elsawy"
                    }
                )
                
                if response.status_code == 404:
                    data = response.json()
                    error_message = data.get('detail', '')
                    
                    if "الفاتورة غير موجودة" in error_message or "not found" in error_message.lower():
                        self.log_test(f"Test 3 - Non-Existent Invoice '{invalid_id}'", True, 
                                    f"Correctly returned 404: {error_message}")
                    else:
                        self.log_test(f"Test 3 - Non-Existent Invoice '{invalid_id}'", False, 
                                    f"Unexpected error message: {error_message}")
                else:
                    self.log_test(f"Test 3 - Non-Existent Invoice '{invalid_id}'", False, 
                                f"Expected HTTP 404, got {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Test 3 - Non-Existent Invoice '{invalid_id}'", False, f"Exception: {str(e)}")
    
    def test_4_invoice_update_functionality(self):
        """Test 4: Invoice update functionality (ensure it's not broken)"""
        print("\n=== Test 4: Invoice Update Functionality ===")
        
        # Create another test invoice for update testing
        if not self.create_simple_test_invoice():
            self.log_test("Test 4 Setup", False, "Failed to create test invoice")
            return
        
        # Test invoice update
        update_data = {
            "invoice_title": "فاتورة اختبار التحديث - محدثة",
            "notes": "تم تحديث الفاتورة بنجاح",
            "supervisor_name": "مشرف محدث"
        }
        
        try:
            response = self.session.put(
                f"{BACKEND_URL}/invoices/{self.test_invoice_id}",
                params={"password": "1462"},
                json=update_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify update was successful
                if (data.get('invoice_title') == update_data['invoice_title'] and
                    data.get('notes') == update_data['notes']):
                    self.log_test("Test 4 - Invoice Update", True, 
                                f"Invoice updated successfully: {data.get('invoice_title')}")
                else:
                    self.log_test("Test 4 - Invoice Update", False, 
                                f"Update not reflected correctly: {data}")
            else:
                self.log_test("Test 4 - Invoice Update", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Test 4 - Invoice Update", False, f"Exception: {str(e)}")
    
    def test_5_payment_method_change(self):
        """Test 5: Payment method change functionality"""
        print("\n=== Test 5: Payment Method Change Functionality ===")
        
        # Create another test invoice for payment method change testing
        if not self.create_simple_test_invoice():
            self.log_test("Test 5 Setup", False, "Failed to create test invoice")
            return
        
        # Test payment method changes
        payment_methods = ["نقدي", "فودافون 010", "كاش 0100", "انستاباي"]
        
        for new_method in payment_methods:
            try:
                response = self.session.put(
                    f"{BACKEND_URL}/invoices/{self.test_invoice_id}/change-payment-method",
                    params={
                        "new_payment_method": new_method,
                        "password": "1462"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify payment method was changed
                    if data.get('payment_method') == new_method:
                        self.log_test(f"Test 5 - Change to {new_method}", True, 
                                    f"Successfully changed to: {new_method}")
                    else:
                        self.log_test(f"Test 5 - Change to {new_method}", False, 
                                    f"Payment method not updated: {data.get('payment_method')}")
                else:
                    self.log_test(f"Test 5 - Change to {new_method}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Test 5 - Change to {new_method}", False, f"Exception: {str(e)}")
    
    def test_6_check_deleted_invoices_collection(self):
        """Test 6: Check if deleted invoices are properly stored"""
        print("\n=== Test 6: Check Deleted Invoices Collection ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/deleted-invoices")
            
            if response.status_code == 200:
                deleted_invoices = response.json()
                
                if isinstance(deleted_invoices, list):
                    self.log_test("Test 6 - Access Deleted Invoices", True, 
                                f"Successfully accessed deleted invoices collection: {len(deleted_invoices)} items")
                    
                    # Check if any deleted invoices have the required fields
                    if deleted_invoices:
                        sample_invoice = deleted_invoices[0]
                        required_fields = ['id', 'invoice_number', 'deleted_at', 'deleted_by']
                        
                        has_required_fields = all(field in sample_invoice for field in required_fields)
                        
                        if has_required_fields:
                            self.log_test("Test 6 - Deleted Invoice Structure", True, 
                                        "Deleted invoices have required metadata fields")
                        else:
                            missing_fields = [f for f in required_fields if f not in sample_invoice]
                            self.log_test("Test 6 - Deleted Invoice Structure", False, 
                                        f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("Test 6 - Deleted Invoice Structure", True, 
                                    "No deleted invoices to check structure (empty collection)")
                else:
                    self.log_test("Test 6 - Access Deleted Invoices", False, 
                                f"Expected list, got: {type(deleted_invoices)}")
            else:
                self.log_test("Test 6 - Access Deleted Invoices", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Test 6 - Access Deleted Invoices", False, f"Exception: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("اختبار وظيفة إلغاء الفواتير - ملخص النتائج النهائي")
        print("Invoice Cancellation Testing - Final Results Summary")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"إجمالي الاختبارات: {total_tests}")
        print(f"الاختبارات الناجحة: {passed_tests}")
        print(f"الاختبارات الفاشلة: {failed_tests}")
        print(f"معدل النجاح: {success_rate:.1f}%")
        
        # Group results by test category
        test_categories = {
            "Test 1": "إلغاء الفاتورة بالبيانات الصحيحة",
            "Test 2": "إلغاء الفاتورة بكلمة مرور خاطئة", 
            "Test 3": "إلغاء فاتورة غير موجودة",
            "Test 4": "تحديث الفاتورة",
            "Test 5": "تغيير طريقة الدفع",
            "Test 6": "فحص مجموعة الفواتير المحذوفة"
        }
        
        print(f"\n📊 تفاصيل النتائج حسب الفئة:")
        for category, description in test_categories.items():
            category_results = [r for r in self.test_results if category in r['test']]
            if category_results:
                category_passed = sum(1 for r in category_results if r['success'])
                category_total = len(category_results)
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
                status = "✅" if category_rate == 100 else "⚠️" if category_rate >= 50 else "❌"
                print(f"  {status} {description}: {category_passed}/{category_total} ({category_rate:.0f}%)")
        
        if failed_tests > 0:
            print(f"\n❌ الاختبارات الفاشلة:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        # Overall assessment
        if success_rate >= 90:
            print(f"\n🎉 ممتاز! وظيفة إلغاء الفواتير تعمل بشكل مثالي")
            print("   جميع المتطلبات المحددة في طلب المراجعة تم تلبيتها بنجاح")
        elif success_rate >= 70:
            print(f"\n✅ جيد! وظيفة إلغاء الفواتير تعمل بشكل عام مع بعض المشاكل البسيطة")
        else:
            print(f"\n❌ يحتاج إصلاح! وظيفة إلغاء الفواتير تحتاج مراجعة وإصلاح")
        
        return success_rate >= 80  # Consider 80%+ as overall success
    
    def run_all_tests(self):
        """Run all focused invoice cancellation tests"""
        print("🚀 بدء الاختبار المركز لوظيفة إلغاء الفواتير")
        print("Starting Focused Invoice Cancellation Testing")
        print("="*80)
        
        # Try to get existing invoices first, if not available create new ones
        if not self.get_existing_invoices():
            if not self.create_simple_test_invoice():
                print("❌ فشل في إعداد فواتير الاختبار")
                return False
        
        # Run all tests in sequence
        self.test_1_invoice_cancellation_correct_credentials()
        self.test_2_wrong_password()
        self.test_3_nonexistent_invoice()
        self.test_4_invoice_update_functionality()
        self.test_5_payment_method_change()
        self.test_6_check_deleted_invoices_collection()
        
        # Print summary and return result
        return self.print_summary()

def main():
    """Main function to run the focused invoice cancellation tests"""
    tester = FocusedInvoiceCancellationTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ تم إيقاف الاختبار بواسطة المستخدم")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ خطأ غير متوقع: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()