#!/usr/bin/env python3
"""
Focused Test for Invoice Discount Calculation Bug Fix
اختبار مركز لإصلاح مشكلة حساب الخصم في الفواتير
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class DiscountFixTester:
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
                "name": "عميل اختبار الخصم",
                "phone": "01234567890",
                "address": "عنوان اختبار الخصم"
            }
            
            response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if response.status_code == 200:
                customer = response.json()
                self.log_test("إنشاء عميل اختبار", True, f"تم إنشاء العميل: {customer['name']}")
                return customer
            else:
                self.log_test("إنشاء عميل اختبار", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("إنشاء عميل اختبار", False, f"خطأ: {str(e)}")
            return None
    
    def create_test_invoice(self, customer_id: str, customer_name: str, initial_discount_value: float = 0.0, discount_type: str = "amount"):
        """Create a test invoice with initial discount"""
        try:
            invoice_data = {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "invoice_title": "فاتورة اختبار الخصم",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "seal_type": "RSL",
                        "material_type": "NBR",
                        "inner_diameter": 25.0,
                        "outer_diameter": 40.0,
                        "height": 10.0,
                        "quantity": 2,
                        "unit_price": 50.0,
                        "total_price": 100.0,
                        "product_type": "manufactured"
                    },
                    {
                        "seal_type": "RS",
                        "material_type": "BUR",
                        "inner_diameter": 30.0,
                        "outer_diameter": 45.0,
                        "height": 8.0,
                        "quantity": 3,
                        "unit_price": 60.0,
                        "total_price": 180.0,
                        "product_type": "manufactured"
                    }
                ],
                "payment_method": "نقدي",
                "discount_type": discount_type,
                "discount_value": initial_discount_value,
                "notes": "فاتورة اختبار لإصلاح مشكلة الخصم"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                invoice = response.json()
                self.created_invoices.append(invoice['id'])
                
                # Verify initial calculations
                expected_subtotal = 280.0  # 100 + 180
                expected_discount = initial_discount_value if discount_type == "amount" else (expected_subtotal * initial_discount_value / 100)
                expected_total = expected_subtotal - expected_discount
                
                success = (
                    abs(invoice.get('subtotal', 0) - expected_subtotal) < 0.01 and
                    abs(invoice.get('discount', 0) - expected_discount) < 0.01 and
                    abs(invoice.get('total_after_discount', 0) - expected_total) < 0.01
                )
                
                details = f"المجموع الفرعي: {invoice.get('subtotal', 0)}, الخصم: {invoice.get('discount', 0)}, الإجمالي: {invoice.get('total_after_discount', 0)}"
                self.log_test("إنشاء فاتورة اختبار مع خصم ابتدائي", success, details)
                return invoice
            else:
                self.log_test("إنشاء فاتورة اختبار", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("إنشاء فاتورة اختبار", False, f"خطأ: {str(e)}")
            return None
    
    def test_discount_only_update(self, invoice_id: str, new_discount_type: str, new_discount_value: float):
        """Test updating ONLY discount fields without updating items"""
        try:
            # Get current invoice first
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if response.status_code != 200:
                self.log_test("الحصول على الفاتورة قبل التحديث", False, f"HTTP {response.status_code}")
                return False
            
            current_invoice = response.json()
            original_subtotal = current_invoice.get('subtotal', 0)
            
            # Update ONLY discount fields (no items)
            update_data = {
                "discount_type": new_discount_type,
                "discount_value": new_discount_value
            }
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            if response.status_code != 200:
                self.log_test("تحديث الخصم فقط", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            # Get updated invoice
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if response.status_code != 200:
                self.log_test("الحصول على الفاتورة بعد التحديث", False, f"HTTP {response.status_code}")
                return False
            
            updated_invoice = response.json()
            
            # Calculate expected values
            expected_discount = new_discount_value if new_discount_type == "amount" else (original_subtotal * new_discount_value / 100)
            expected_total = original_subtotal - expected_discount
            
            # Verify calculations
            actual_discount = updated_invoice.get('discount', 0)
            actual_total = updated_invoice.get('total_after_discount', 0)
            
            discount_correct = abs(actual_discount - expected_discount) < 0.01
            total_correct = abs(actual_total - expected_total) < 0.01
            
            success = discount_correct and total_correct
            details = f"متوقع - خصم: {expected_discount:.2f}, إجمالي: {expected_total:.2f} | فعلي - خصم: {actual_discount:.2f}, إجمالي: {actual_total:.2f}"
            
            test_name = f"تحديث الخصم فقط ({new_discount_type}: {new_discount_value})"
            self.log_test(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test("تحديث الخصم فقط", False, f"خطأ: {str(e)}")
            return False
    
    def test_regular_invoice_update(self, invoice_id: str):
        """Test updating items along with discount to ensure we didn't break existing functionality"""
        try:
            # Update both items and discount
            update_data = {
                "items": [
                    {
                        "seal_type": "RSL",
                        "material_type": "NBR",
                        "inner_diameter": 25.0,
                        "outer_diameter": 40.0,
                        "height": 10.0,
                        "quantity": 1,  # Changed from 2 to 1
                        "unit_price": 50.0,
                        "total_price": 50.0,  # Updated total
                        "product_type": "manufactured"
                    },
                    {
                        "seal_type": "RS",
                        "material_type": "BUR",
                        "inner_diameter": 30.0,
                        "outer_diameter": 45.0,
                        "height": 8.0,
                        "quantity": 4,  # Changed from 3 to 4
                        "unit_price": 60.0,
                        "total_price": 240.0,  # Updated total
                        "product_type": "manufactured"
                    }
                ],
                "discount_type": "percentage",
                "discount_value": 10.0  # 10% discount
            }
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            if response.status_code != 200:
                self.log_test("تحديث العناصر والخصم معاً", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            # Get updated invoice
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if response.status_code != 200:
                self.log_test("الحصول على الفاتورة بعد التحديث المختلط", False, f"HTTP {response.status_code}")
                return False
            
            updated_invoice = response.json()
            
            # Calculate expected values
            expected_subtotal = 290.0  # 50 + 240
            expected_discount = expected_subtotal * 0.10  # 10%
            expected_total = expected_subtotal - expected_discount
            
            # Verify calculations
            actual_subtotal = updated_invoice.get('subtotal', 0)
            actual_discount = updated_invoice.get('discount', 0)
            actual_total = updated_invoice.get('total_after_discount', 0)
            
            subtotal_correct = abs(actual_subtotal - expected_subtotal) < 0.01
            discount_correct = abs(actual_discount - expected_discount) < 0.01
            total_correct = abs(actual_total - expected_total) < 0.01
            
            success = subtotal_correct and discount_correct and total_correct
            details = f"متوقع - مجموع: {expected_subtotal:.2f}, خصم: {expected_discount:.2f}, إجمالي: {expected_total:.2f} | فعلي - مجموع: {actual_subtotal:.2f}, خصم: {actual_discount:.2f}, إجمالي: {actual_total:.2f}"
            
            self.log_test("تحديث العناصر والخصم معاً", success, details)
            return success
            
        except Exception as e:
            self.log_test("تحديث العناصر والخصم معاً", False, f"خطأ: {str(e)}")
            return False
    
    def test_invoice_list_persistence(self):
        """Test that invoices don't disappear from the list after updates"""
        try:
            # Get invoice count before
            response = self.session.get(f"{BACKEND_URL}/invoices")
            if response.status_code != 200:
                self.log_test("الحصول على قائمة الفواتير قبل التحديث", False, f"HTTP {response.status_code}")
                return False
            
            invoices_before = response.json()
            count_before = len(invoices_before)
            
            # Verify our test invoices are in the list
            test_invoice_ids = set(self.created_invoices)
            found_invoices = set(inv['id'] for inv in invoices_before if inv['id'] in test_invoice_ids)
            
            if len(found_invoices) != len(test_invoice_ids):
                self.log_test("التحقق من وجود فواتير الاختبار", False, f"متوقع: {len(test_invoice_ids)}, موجود: {len(found_invoices)}")
                return False
            
            # Get invoice count after all updates
            response = self.session.get(f"{BACKEND_URL}/invoices")
            if response.status_code != 200:
                self.log_test("الحصول على قائمة الفواتير بعد التحديث", False, f"HTTP {response.status_code}")
                return False
            
            invoices_after = response.json()
            count_after = len(invoices_after)
            
            # Verify our test invoices are still in the list
            found_invoices_after = set(inv['id'] for inv in invoices_after if inv['id'] in test_invoice_ids)
            
            success = (count_after >= count_before and len(found_invoices_after) == len(test_invoice_ids))
            details = f"عدد الفواتير قبل: {count_before}, بعد: {count_after}, فواتير الاختبار الموجودة: {len(found_invoices_after)}/{len(test_invoice_ids)}"
            
            self.log_test("استمرارية الفواتير في القائمة", success, details)
            return success
            
        except Exception as e:
            self.log_test("استمرارية الفواتير في القائمة", False, f"خطأ: {str(e)}")
            return False
    
    def run_discount_fix_tests(self):
        """Run all discount calculation fix tests"""
        print("🔧 بدء اختبار إصلاح مشكلة حساب الخصم في الفواتير")
        print("=" * 60)
        
        # Create test customer
        customer = self.create_test_customer()
        if not customer:
            print("❌ فشل في إنشاء عميل الاختبار - توقف الاختبار")
            return
        
        # Test 1: Create invoice with no discount
        print("\n📝 اختبار 1: إنشاء فاتورة بدون خصم")
        invoice1 = self.create_test_invoice(customer['id'], customer['name'], 0.0, "amount")
        if not invoice1:
            print("❌ فشل في إنشاء الفاتورة الأولى")
            return
        
        # Test 2: Update with fixed amount discount only
        print("\n💰 اختبار 2: تحديث خصم ثابت فقط (بدون تحديث العناصر)")
        self.test_discount_only_update(invoice1['id'], "amount", 25.0)
        
        # Test 3: Update with percentage discount only
        print("\n📊 اختبار 3: تحديث خصم نسبة مئوية فقط")
        self.test_discount_only_update(invoice1['id'], "percentage", 15.0)
        
        # Test 4: Create another invoice with initial percentage discount
        print("\n📝 اختبار 4: إنشاء فاتورة مع خصم نسبة مئوية ابتدائي")
        invoice2 = self.create_test_invoice(customer['id'], customer['name'], 20.0, "percentage")
        if not invoice2:
            print("❌ فشل في إنشاء الفاتورة الثانية")
            return
        
        # Test 5: Update discount only on the second invoice
        print("\n🔄 اختبار 5: تحديث خصم ثابت على الفاتورة الثانية")
        self.test_discount_only_update(invoice2['id'], "amount", 50.0)
        
        # Test 6: Test regular update (items + discount) to ensure we didn't break existing functionality
        print("\n🔧 اختبار 6: تحديث العناصر والخصم معاً (الوظيفة الموجودة)")
        self.test_regular_invoice_update(invoice1['id'])
        
        # Test 7: Verify invoice list persistence
        print("\n📋 اختبار 7: التحقق من استمرارية الفواتير في القائمة")
        self.test_invoice_list_persistence()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ملخص نتائج اختبار إصلاح الخصم")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"إجمالي الاختبارات: {total_tests}")
        print(f"نجح: {passed_tests} ✅")
        print(f"فشل: {failed_tests} ❌")
        print(f"نسبة النجاح: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ الاختبارات الفاشلة:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        # Critical assessment
        discount_only_tests = [r for r in self.test_results if 'تحديث الخصم فقط' in r['test']]
        discount_only_passed = sum(1 for r in discount_only_tests if r['success'])
        
        print(f"\n🎯 التقييم الحرج: اختبارات تحديث الخصم فقط")
        print(f"نجح: {discount_only_passed}/{len(discount_only_tests)} من اختبارات الخصم المنفرد")
        
        if discount_only_passed == len(discount_only_tests) and len(discount_only_tests) > 0:
            print("✅ إصلاح مشكلة حساب الخصم يعمل بشكل مثالي!")
        elif discount_only_passed > 0:
            print("⚠️ إصلاح مشكلة حساب الخصم يعمل جزئياً")
        else:
            print("❌ مشكلة حساب الخصم لا تزال موجودة!")

def main():
    """Main test execution"""
    tester = DiscountFixTester()
    
    try:
        tester.run_discount_fix_tests()
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف الاختبار بواسطة المستخدم")
    except Exception as e:
        print(f"\n💥 خطأ غير متوقع: {str(e)}")
    
    return len([r for r in tester.test_results if not r['success']]) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)