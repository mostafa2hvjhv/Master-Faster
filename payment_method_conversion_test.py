#!/usr/bin/env python3
"""
اختبار محدد لإصلاح مشكلة تغيير طريقة الدفع مع "آجل"
Specific test for payment method conversion with deferred payment fix
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class PaymentMethodConversionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_invoices = []
        
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
    
    def create_test_customer(self):
        """Create a test customer for invoices"""
        try:
            customer_data = {
                "name": "عميل اختبار تحويل طرق الدفع",
                "phone": "01234567890",
                "address": "عنوان تجريبي"
            }
            
            response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to create test customer: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating test customer: {str(e)}")
            return None
    
    def create_test_invoice(self, payment_method: str, amount: float = 500.0):
        """Create a test invoice with specified payment method"""
        try:
            customer = self.create_test_customer()
            if not customer:
                return None
                
            invoice_data = {
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "invoice_title": f"فاتورة اختبار - {payment_method}",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "product_type": "local",
                        "product_name": "منتج اختبار",
                        "quantity": 1,
                        "unit_price": amount,
                        "total_price": amount,
                        "local_product_details": {
                            "name": "منتج اختبار",
                            "supplier": "مورد اختبار",
                            "purchase_price": amount * 0.7,
                            "selling_price": amount
                        }
                    }
                ],
                "payment_method": payment_method,
                "discount_type": "amount",
                "discount_value": 0.0,
                "notes": f"فاتورة اختبار تحويل طرق الدفع - {payment_method}"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                invoice = response.json()
                self.created_invoices.append(invoice["id"])
                return invoice
            else:
                print(f"Failed to create invoice: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating test invoice: {str(e)}")
            return None
    
    def get_treasury_balance(self, account_id: str):
        """Get treasury balance for specific account"""
        try:
            response = self.session.get(f"{BACKEND_URL}/treasury/balances")
            if response.status_code == 200:
                balances = response.json()
                return balances.get(account_id, 0.0)
            return 0.0
        except Exception as e:
            print(f"Error getting treasury balance: {str(e)}")
            return 0.0
    
    def change_payment_method(self, invoice_id: str, new_payment_method: str):
        """Change invoice payment method"""
        try:
            response = self.session.put(
                f"{BACKEND_URL}/invoices/{invoice_id}/change-payment-method",
                params={"new_payment_method": new_payment_method, "username": "Elsawy"}
            )
            return response
        except Exception as e:
            print(f"Error changing payment method: {str(e)}")
            return None
    
    def get_invoice(self, invoice_id: str):
        """Get invoice details"""
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting invoice: {str(e)}")
            return None
    
    def test_cash_to_deferred_conversion(self):
        """Test converting from cash to deferred payment"""
        print("\n=== اختبار التحويل من نقدي إلى آجل ===")
        
        # Create cash invoice
        invoice = self.create_test_invoice("نقدي", 500.0)
        if not invoice:
            self.log_test("إنشاء فاتورة نقدية", False, "فشل في إنشاء الفاتورة")
            return
        
        self.log_test("إنشاء فاتورة نقدية", True, f"تم إنشاء الفاتورة {invoice['invoice_number']}")
        
        # Get initial treasury balance
        initial_cash_balance = self.get_treasury_balance("cash")
        
        # Convert to deferred
        response = self.change_payment_method(invoice["id"], "آجل")
        if not response or response.status_code != 200:
            self.log_test("تحويل من نقدي إلى آجل", False, f"فشل في التحويل: {response.text if response else 'No response'}")
            return
        
        self.log_test("تحويل من نقدي إلى آجل", True, "تم التحويل بنجاح")
        
        # Verify invoice updates
        updated_invoice = self.get_invoice(invoice["id"])
        if updated_invoice:
            if updated_invoice["payment_method"] == "آجل":
                self.log_test("تحديث طريقة الدفع في الفاتورة", True, "تم تحديث طريقة الدفع إلى آجل")
            else:
                self.log_test("تحديث طريقة الدفع في الفاتورة", False, f"طريقة الدفع: {updated_invoice['payment_method']}")
            
            if updated_invoice["remaining_amount"] == 500.0:
                self.log_test("تحديث المبلغ المتبقي", True, f"المبلغ المتبقي: {updated_invoice['remaining_amount']}")
            else:
                self.log_test("تحديث المبلغ المتبقي", False, f"المبلغ المتبقي: {updated_invoice['remaining_amount']}")
        
        # Verify treasury balance change
        final_cash_balance = self.get_treasury_balance("cash")
        expected_balance = initial_cash_balance - 500.0
        
        if abs(final_cash_balance - expected_balance) < 0.01:
            self.log_test("تحديث رصيد الخزينة النقدية", True, f"الرصيد النهائي: {final_cash_balance}")
        else:
            self.log_test("تحديث رصيد الخزينة النقدية", False, f"متوقع: {expected_balance}, فعلي: {final_cash_balance}")
    
    def test_deferred_to_cash_conversion(self):
        """Test converting from deferred to cash payment"""
        print("\n=== اختبار التحويل من آجل إلى نقدي ===")
        
        # Create deferred invoice
        invoice = self.create_test_invoice("آجل", 400.0)
        if not invoice:
            self.log_test("إنشاء فاتورة آجلة", False, "فشل في إنشاء الفاتورة")
            return
        
        self.log_test("إنشاء فاتورة آجلة", True, f"تم إنشاء الفاتورة {invoice['invoice_number']}")
        
        # Get initial treasury balance
        initial_cash_balance = self.get_treasury_balance("cash")
        
        # Convert to cash
        response = self.change_payment_method(invoice["id"], "نقدي")
        if not response or response.status_code != 200:
            self.log_test("تحويل من آجل إلى نقدي", False, f"فشل في التحويل: {response.text if response else 'No response'}")
            return
        
        self.log_test("تحويل من آجل إلى نقدي", True, "تم التحويل بنجاح")
        
        # Verify invoice updates
        updated_invoice = self.get_invoice(invoice["id"])
        if updated_invoice:
            if updated_invoice["payment_method"] == "نقدي":
                self.log_test("تحديث طريقة الدفع في الفاتورة", True, "تم تحديث طريقة الدفع إلى نقدي")
            else:
                self.log_test("تحديث طريقة الدفع في الفاتورة", False, f"طريقة الدفع: {updated_invoice['payment_method']}")
            
            if updated_invoice["remaining_amount"] == 0.0:
                self.log_test("تحديث المبلغ المتبقي", True, f"المبلغ المتبقي: {updated_invoice['remaining_amount']}")
            else:
                self.log_test("تحديث المبلغ المتبقي", False, f"المبلغ المتبقي: {updated_invoice['remaining_amount']}")
        
        # Verify treasury balance change
        final_cash_balance = self.get_treasury_balance("cash")
        expected_balance = initial_cash_balance + 400.0
        
        if abs(final_cash_balance - expected_balance) < 0.01:
            self.log_test("تحديث رصيد الخزينة النقدية", True, f"الرصيد النهائي: {final_cash_balance}")
        else:
            self.log_test("تحديث رصيد الخزينة النقدية", False, f"متوقع: {expected_balance}, فعلي: {final_cash_balance}")
    
    def test_deferred_to_other_methods(self):
        """Test converting from deferred to other payment methods"""
        print("\n=== اختبار التحويل من آجل إلى طرق دفع أخرى ===")
        
        payment_methods = [
            ("فودافون 010", "vodafone_elsawy"),
            ("كاش 0100", "vodafone_wael"),
            ("انستاباي", "instapay")
        ]
        
        for method_name, account_id in payment_methods:
            print(f"\n--- اختبار التحويل من آجل إلى {method_name} ---")
            
            # Create deferred invoice
            invoice = self.create_test_invoice("آجل", 300.0)
            if not invoice:
                self.log_test(f"إنشاء فاتورة آجلة للتحويل إلى {method_name}", False, "فشل في إنشاء الفاتورة")
                continue
            
            # Get initial balance
            initial_balance = self.get_treasury_balance(account_id)
            
            # Convert to payment method
            response = self.change_payment_method(invoice["id"], method_name)
            if not response or response.status_code != 200:
                self.log_test(f"تحويل من آجل إلى {method_name}", False, f"فشل في التحويل: {response.text if response else 'No response'}")
                continue
            
            self.log_test(f"تحويل من آجل إلى {method_name}", True, "تم التحويل بنجاح")
            
            # Verify invoice updates
            updated_invoice = self.get_invoice(invoice["id"])
            if updated_invoice:
                if updated_invoice["payment_method"] == method_name:
                    self.log_test(f"تحديث طريقة الدفع إلى {method_name}", True)
                else:
                    self.log_test(f"تحديث طريقة الدفع إلى {method_name}", False, f"طريقة الدفع: {updated_invoice['payment_method']}")
                
                if updated_invoice["remaining_amount"] == 0.0:
                    self.log_test(f"تحديث المبلغ المتبقي - {method_name}", True)
                else:
                    self.log_test(f"تحديث المبلغ المتبقي - {method_name}", False, f"المبلغ المتبقي: {updated_invoice['remaining_amount']}")
            
            # Verify treasury balance
            final_balance = self.get_treasury_balance(account_id)
            expected_balance = initial_balance + 300.0
            
            if abs(final_balance - expected_balance) < 0.01:
                self.log_test(f"تحديث رصيد {method_name}", True, f"الرصيد النهائي: {final_balance}")
            else:
                self.log_test(f"تحديث رصيد {method_name}", False, f"متوقع: {expected_balance}, فعلي: {final_balance}")
    
    def test_other_methods_to_deferred(self):
        """Test converting from other payment methods to deferred"""
        print("\n=== اختبار التحويل إلى آجل من طرق دفع مختلفة ===")
        
        payment_methods = [
            ("فودافون 010", "vodafone_elsawy"),
            ("كاش 0100", "vodafone_wael")
        ]
        
        for method_name, account_id in payment_methods:
            print(f"\n--- اختبار التحويل من {method_name} إلى آجل ---")
            
            # Create invoice with payment method
            invoice = self.create_test_invoice(method_name, 350.0)
            if not invoice:
                self.log_test(f"إنشاء فاتورة {method_name} للتحويل إلى آجل", False, "فشل في إنشاء الفاتورة")
                continue
            
            # Get initial balance
            initial_balance = self.get_treasury_balance(account_id)
            
            # Convert to deferred
            response = self.change_payment_method(invoice["id"], "آجل")
            if not response or response.status_code != 200:
                self.log_test(f"تحويل من {method_name} إلى آجل", False, f"فشل في التحويل: {response.text if response else 'No response'}")
                continue
            
            self.log_test(f"تحويل من {method_name} إلى آجل", True, "تم التحويل بنجاح")
            
            # Verify invoice updates
            updated_invoice = self.get_invoice(invoice["id"])
            if updated_invoice:
                if updated_invoice["payment_method"] == "آجل":
                    self.log_test(f"تحديث طريقة الدفع من {method_name} إلى آجل", True)
                else:
                    self.log_test(f"تحديث طريقة الدفع من {method_name} إلى آجل", False, f"طريقة الدفع: {updated_invoice['payment_method']}")
                
                if updated_invoice["remaining_amount"] == 350.0:
                    self.log_test(f"تحديث المبلغ المتبقي - {method_name} إلى آجل", True)
                else:
                    self.log_test(f"تحديث المبلغ المتبقي - {method_name} إلى آجل", False, f"المبلغ المتبقي: {updated_invoice['remaining_amount']}")
            
            # Verify treasury balance
            final_balance = self.get_treasury_balance(account_id)
            expected_balance = initial_balance - 350.0
            
            if abs(final_balance - expected_balance) < 0.01:
                self.log_test(f"تحديث رصيد {method_name} بعد التحويل إلى آجل", True, f"الرصيد النهائي: {final_balance}")
            else:
                self.log_test(f"تحديث رصيد {method_name} بعد التحويل إلى آجل", False, f"متوقع: {expected_balance}, فعلي: {final_balance}")
    
    def test_unsupported_payment_method_error(self):
        """Test that unsupported payment methods are handled correctly"""
        print("\n=== اختبار رسالة 'طريقة الدفع غير مدعومة' ===")
        
        # Create a test invoice
        invoice = self.create_test_invoice("نقدي", 200.0)
        if not invoice:
            self.log_test("إنشاء فاتورة لاختبار طريقة دفع غير مدعومة", False, "فشل في إنشاء الفاتورة")
            return
        
        # Try to convert to unsupported payment method
        try:
            response = self.session.put(
                f"{BACKEND_URL}/invoices/{invoice['id']}/change-payment-method",
                params={"new_payment_method": "طريقة غير مدعومة", "username": "Elsawy"}
            )
            
            if response.status_code == 400:
                response_data = response.json()
                if "طريقة الدفع غير مدعومة" in response_data.get("detail", ""):
                    self.log_test("رسالة طريقة الدفع غير مدعومة", True, "تم عرض الرسالة الصحيحة")
                else:
                    self.log_test("رسالة طريقة الدفع غير مدعومة", False, f"رسالة خطأ غير متوقعة: {response_data.get('detail')}")
            else:
                self.log_test("رسالة طريقة الدفع غير مدعومة", False, f"كود الاستجابة غير متوقع: {response.status_code}")
        except Exception as e:
            self.log_test("رسالة طريقة الدفع غير مدعومة", False, f"خطأ في الاختبار: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up test invoices"""
        print("\n=== تنظيف بيانات الاختبار ===")
        
        deleted_count = 0
        for invoice_id in self.created_invoices:
            try:
                response = self.session.delete(f"{BACKEND_URL}/invoices/{invoice_id}")
                if response.status_code == 200:
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting invoice {invoice_id}: {str(e)}")
        
        print(f"تم حذف {deleted_count} فاتورة اختبار")
    
    def run_all_tests(self):
        """Run all payment method conversion tests"""
        print("🚀 بدء اختبار تحويل طرق الدفع مع الآجل")
        print("=" * 60)
        
        # Test scenarios
        self.test_cash_to_deferred_conversion()
        self.test_deferred_to_cash_conversion()
        self.test_deferred_to_other_methods()
        self.test_other_methods_to_deferred()
        self.test_unsupported_payment_method_error()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 ملخص نتائج الاختبار")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"إجمالي الاختبارات: {total_tests}")
        print(f"نجح: {passed_tests} ✅")
        print(f"فشل: {failed_tests} ❌")
        print(f"معدل النجاح: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ الاختبارات الفاشلة:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        # Cleanup
        self.cleanup_test_data()
        
        return success_rate >= 80  # Consider 80%+ success rate as passing

def main():
    """Main test execution"""
    tester = PaymentMethodConversionTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ تم إيقاف الاختبار بواسطة المستخدم")
        tester.cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 خطأ غير متوقع: {str(e)}")
        tester.cleanup_test_data()
        sys.exit(1)

if __name__ == "__main__":
    main()