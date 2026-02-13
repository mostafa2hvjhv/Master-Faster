#!/usr/bin/env python3
"""
اختبار سريع للتأكد من الإصلاحات الجديدة المطلوبة من المستخدم
Quick test to verify the new fixes requested by the user

Based on Arabic review request:
**اختبار 1: مشكلة الخزينة والآجل**
- إنشاء فاتورة آجلة بمبلغ 1000 جنيه
- إنشاء دفعة جزئية 300 جنيه بطريقة "فودافون كاش وائل محمد"
- التحقق من:
  * زيادة رصيد فودافون كاش وائل بـ 300 جنيه ✅
  * تقليل رصيد الآجل بـ 300 جنيه ✅ (هذا ما تم إصلاحه)

**اختبار 2: APIs الإكسل الجديدة**
- GET /api/excel/export/inventory
- GET /api/excel/export/raw-materials

**اختبار 3: تكامل الجرد مع المواد الخام**
- إنشاء عنصر جرد + إنشاء مادة خام للتأكد من الخصم التلقائي

**اختبار 4: APIs الجرد الأساسية (للتأكد من عدم كسر الوظائف الموجودة)**
- GET /api/inventory
- DELETE /api/inventory/{id} (للحذف من الواجهة الجديدة)
- PUT /api/inventory/{id} (للتعديل من الواجهة الجديدة)
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class TestResults:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.results = []
        self.critical_issues = []
    
    def add_result(self, test_name, passed, details="", is_critical=False):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            if is_critical:
                self.critical_issues.append(f"{test_name}: {details}")
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        self.results.append(result)
        print(result)
    
    def print_summary(self):
        print(f"\n{'='*80}")
        print(f"اختبار سريع للإصلاحات الجديدة - نتائج الاختبار")
        print(f"Quick Test Results for New Fixes")
        print(f"{'='*80}")
        print(f"إجمالي الاختبارات: {self.total_tests}")
        print(f"نجح: {self.passed_tests}")
        print(f"فشل: {self.failed_tests}")
        print(f"نسبة النجاح: {(self.passed_tests/self.total_tests)*100:.1f}%")
        
        if self.critical_issues:
            print(f"\n🚨 مشاكل حرجة تحتاج إصلاح فوري:")
            for issue in self.critical_issues:
                print(f"   - {issue}")
        
        print(f"{'='*80}")

def make_request(method, endpoint, data=None, timeout=15):
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=HEADERS, json=data, timeout=timeout)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=HEADERS, json=data, timeout=timeout)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=HEADERS, timeout=timeout)
        
        return response
    except requests.exceptions.Timeout:
        print(f"⚠️  Timeout for {method} {endpoint}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Request error for {method} {endpoint}: {str(e)}")
        return None

def test_treasury_deferred_issue(results):
    """اختبار 1: مشكلة الخزينة والآجل"""
    print(f"\n{'='*60}")
    print("اختبار 1: مشكلة الخزينة والآجل")
    print("Test 1: Treasury and Deferred Issue")
    print(f"{'='*60}")
    
    # Get initial balances
    response = make_request("GET", "/treasury/balances")
    if not response or response.status_code != 200:
        results.add_result("الحصول على أرصدة الخزينة الأولية", False, "فشل في الحصول على الأرصدة", True)
        return
    
    initial_balances = response.json()
    initial_vodafone_wael = initial_balances.get('vodafone_wael', 0)
    initial_deferred = initial_balances.get('deferred', 0)
    
    results.add_result("الحصول على أرصدة الخزينة الأولية", True, 
                      f"فودافون وائل: {initial_vodafone_wael} ج.م، آجل: {initial_deferred} ج.م")
    
    # Step 1: Create deferred invoice for 1000 EGP
    print("\n--- إنشاء فاتورة آجلة بمبلغ 1000 جنيه ---")
    deferred_invoice_data = {
        "customer_name": "عميل اختبار آجل",
        "items": [{
            "seal_type": "RSL",
            "material_type": "NBR",
            "inner_diameter": 50.0,
            "outer_diameter": 70.0,
            "height": 15.0,
            "quantity": 10,
            "unit_price": 100.0,
            "total_price": 1000.0,
            "product_type": "manufactured"
        }],
        "payment_method": "آجل",
        "discount_type": "amount",
        "discount_value": 0.0
    }
    
    response = make_request("POST", "/invoices", deferred_invoice_data)
    if not response or response.status_code != 200:
        results.add_result("إنشاء فاتورة آجلة 1000 ج.م", False, 
                          f"HTTP {response.status_code if response else 'No Response'}", True)
        return
    
    deferred_invoice = response.json()
    invoice_id = deferred_invoice.get('id')
    results.add_result("إنشاء فاتورة آجلة 1000 ج.م", True, 
                      f"فاتورة {deferred_invoice.get('invoice_number')}")
    
    # Verify deferred balance increased
    time.sleep(2)
    response = make_request("GET", "/treasury/balances")
    if response and response.status_code == 200:
        after_invoice_balances = response.json()
        new_deferred = after_invoice_balances.get('deferred', 0)
        deferred_increase = new_deferred - initial_deferred
        
        if abs(deferred_increase - 1000.0) < 0.01:
            results.add_result("زيادة رصيد الآجل بـ 1000 ج.م", True, f"زيادة {deferred_increase} ج.م")
        else:
            results.add_result("زيادة رصيد الآجل بـ 1000 ج.م", False, 
                              f"متوقع 1000 ج.م، فعلي {deferred_increase} ج.م", True)
    
    # Step 2: Create partial payment of 300 EGP with "فودافون كاش وائل محمد"
    print("\n--- إنشاء دفعة جزئية 300 جنيه بطريقة فودافون كاش وائل ---")
    payment_data = {
        "invoice_id": invoice_id,
        "amount": 300.0,
        "payment_method": "فودافون كاش وائل محمد",
        "notes": "دفعة جزئية اختبار"
    }
    
    response = make_request("POST", "/payments", payment_data)
    if not response or response.status_code != 200:
        results.add_result("إنشاء دفعة جزئية 300 ج.م", False, 
                          f"HTTP {response.status_code if response else 'No Response'}", True)
        return
    
    payment = response.json()
    results.add_result("إنشاء دفعة جزئية 300 ج.م", True, f"دفعة ID: {payment.get('id')}")
    
    # Step 3: Verify the fixes
    time.sleep(2)
    response = make_request("GET", "/treasury/balances")
    if not response or response.status_code != 200:
        results.add_result("فحص الأرصدة بعد الدفعة", False, "فشل في الحصول على الأرصدة", True)
        return
    
    final_balances = response.json()
    final_vodafone_wael = final_balances.get('vodafone_wael', 0)
    final_deferred = final_balances.get('deferred', 0)
    
    # Check Vodafone Wael increase (✅ should work)
    vodafone_increase = final_vodafone_wael - initial_vodafone_wael
    if abs(vodafone_increase - 300.0) < 0.01:
        results.add_result("✅ زيادة رصيد فودافون كاش وائل بـ 300 ج.م", True, f"زيادة {vodafone_increase} ج.م")
    else:
        results.add_result("❌ زيادة رصيد فودافون كاش وائل بـ 300 ج.م", False, 
                          f"متوقع 300 ج.م، فعلي {vodafone_increase} ج.م", True)
    
    # Check Deferred decrease (✅ this was the fix)
    deferred_decrease = initial_deferred + 1000.0 - final_deferred  # Expected decrease from payment
    if abs(deferred_decrease - 300.0) < 0.01:
        results.add_result("✅ تقليل رصيد الآجل بـ 300 ج.م (الإصلاح الجديد)", True, f"تقليل {deferred_decrease} ج.م")
    else:
        results.add_result("❌ تقليل رصيد الآجل بـ 300 ج.م (الإصلاح الجديد)", False, 
                          f"متوقع 300 ج.م، فعلي {deferred_decrease} ج.م", True)

def test_excel_apis(results):
    """اختبار 2: APIs الإكسل الجديدة"""
    print(f"\n{'='*60}")
    print("اختبار 2: APIs الإكسل الجديدة")
    print("Test 2: New Excel APIs")
    print(f"{'='*60}")
    
    # Test inventory export
    print("\n--- اختبار GET /api/excel/export/inventory ---")
    response = make_request("GET", "/excel/export/inventory")
    if response and response.status_code == 200:
        content_type = response.headers.get('content-type', '')
        content_length = len(response.content)
        results.add_result("GET /api/excel/export/inventory", True, 
                          f"نوع المحتوى: {content_type}, حجم: {content_length} bytes")
    else:
        results.add_result("GET /api/excel/export/inventory", False, 
                          f"HTTP {response.status_code if response else 'No Response'}")
    
    # Test raw materials export
    print("\n--- اختبار GET /api/excel/export/raw-materials ---")
    response = make_request("GET", "/excel/export/raw-materials")
    if response and response.status_code == 200:
        content_type = response.headers.get('content-type', '')
        content_length = len(response.content)
        results.add_result("GET /api/excel/export/raw-materials", True, 
                          f"نوع المحتوى: {content_type}, حجم: {content_length} bytes")
    else:
        results.add_result("GET /api/excel/export/raw-materials", False, 
                          f"HTTP {response.status_code if response else 'No Response'}")

def test_inventory_raw_materials_integration(results):
    """اختبار 3: تكامل الجرد مع المواد الخام"""
    print(f"\n{'='*60}")
    print("اختبار 3: تكامل الجرد مع المواد الخام")
    print("Test 3: Inventory Integration with Raw Materials")
    print(f"{'='*60}")
    
    # Create inventory item
    print("\n--- إنشاء عنصر جرد جديد ---")
    inventory_data = {
        "material_type": "NBR",
        "inner_diameter": 25.0,
        "outer_diameter": 35.0,
        "available_pieces": 20,
        "min_stock_level": 5,
        "notes": "اختبار تكامل مع المواد الخام"
    }
    
    response = make_request("POST", "/inventory", inventory_data)
    if not response or response.status_code != 200:
        results.add_result("إنشاء عنصر جرد", False, 
                          f"HTTP {response.status_code if response else 'No Response'}", True)
        return
    
    inventory_item = response.json()
    inventory_id = inventory_item.get('id')
    results.add_result("إنشاء عنصر جرد", True, f"ID: {inventory_id}, قطع: 20")
    
    # Create raw material that should deduct from inventory
    print("\n--- إنشاء مادة خام للتأكد من الخصم التلقائي ---")
    raw_material_data = {
        "material_type": "NBR",
        "inner_diameter": 25.0,
        "outer_diameter": 35.0,
        "height": 12.0,
        "pieces_count": 5,
        "unit_code": "NBR-25-35-INTEGRATION-TEST",
        "cost_per_mm": 0.8
    }
    
    response = make_request("POST", "/raw-materials", raw_material_data)
    if not response or response.status_code != 200:
        results.add_result("إنشاء مادة خام مع خصم تلقائي", False, 
                          f"HTTP {response.status_code if response else 'No Response'}", True)
        return
    
    raw_material = response.json()
    results.add_result("إنشاء مادة خام مع خصم تلقائي", True, 
                      f"كود: {raw_material.get('unit_code')}")
    
    # Verify automatic deduction
    time.sleep(2)
    response = make_request("GET", f"/inventory/{inventory_id}")
    if response and response.status_code == 200:
        updated_inventory = response.json()
        remaining_pieces = updated_inventory.get('available_pieces', 0)
        expected_remaining = 20 - 5  # 20 initial - 5 deducted
        
        if remaining_pieces == expected_remaining:
            results.add_result("✅ الخصم التلقائي من الجرد", True, 
                              f"متبقي {remaining_pieces} قطعة (كان 20، خُصم 5)")
        else:
            results.add_result("❌ الخصم التلقائي من الجرد", False, 
                              f"متوقع {expected_remaining} قطعة، فعلي {remaining_pieces} قطعة", True)
    else:
        results.add_result("فحص الجرد بعد الخصم", False, 
                          f"HTTP {response.status_code if response else 'No Response'}", True)

def test_basic_inventory_apis(results):
    """اختبار 4: APIs الجرد الأساسية"""
    print(f"\n{'='*60}")
    print("اختبار 4: APIs الجرد الأساسية (للتأكد من عدم كسر الوظائف الموجودة)")
    print("Test 4: Basic Inventory APIs (to ensure existing functions aren't broken)")
    print(f"{'='*60}")
    
    # Test GET /api/inventory
    print("\n--- اختبار GET /api/inventory ---")
    response = make_request("GET", "/inventory")
    if response and response.status_code == 200:
        inventory_items = response.json()
        results.add_result("GET /api/inventory", True, f"تم الحصول على {len(inventory_items)} عنصر")
        
        if inventory_items:
            test_item = inventory_items[0]
            test_item_id = test_item.get('id')
            
            # Test PUT /api/inventory/{id} (للتعديل من الواجهة الجديدة)
            print(f"\n--- اختبار PUT /api/inventory/{test_item_id} ---")
            update_data = {
                "material_type": test_item.get('material_type'),
                "inner_diameter": test_item.get('inner_diameter'),
                "outer_diameter": test_item.get('outer_diameter'),
                "available_pieces": test_item.get('available_pieces', 0) + 2,  # Add 2 pieces
                "min_stock_level": test_item.get('min_stock_level', 2),
                "notes": "تم التحديث من اختبار APIs الأساسية"
            }
            
            response = make_request("PUT", f"/inventory/{test_item_id}", update_data)
            if response and response.status_code == 200:
                results.add_result("PUT /api/inventory/{id} (تعديل)", True, "تم تحديث عنصر الجرد")
                
                # Verify the update
                response = make_request("GET", f"/inventory/{test_item_id}")
                if response and response.status_code == 200:
                    updated_item = response.json()
                    if updated_item.get('available_pieces') == update_data['available_pieces']:
                        results.add_result("التحقق من التحديث", True, "التحديث تم بنجاح")
                    else:
                        results.add_result("التحقق من التحديث", False, "التحديث لم يُحفظ بشكل صحيح")
            else:
                results.add_result("PUT /api/inventory/{id} (تعديل)", False, 
                                  f"HTTP {response.status_code if response else 'No Response'}")
            
            # Test DELETE /api/inventory/{id} (للحذف من الواجهة الجديدة)
            print(f"\n--- اختبار DELETE /api/inventory/{test_item_id} ---")
            response = make_request("DELETE", f"/inventory/{test_item_id}")
            if response and response.status_code == 200:
                results.add_result("DELETE /api/inventory/{id} (حذف)", True, "تم حذف عنصر الجرد")
                
                # Verify deletion
                response = make_request("GET", f"/inventory/{test_item_id}")
                if response and response.status_code == 404:
                    results.add_result("التحقق من الحذف", True, "العنصر تم حذفه فعلياً")
                else:
                    results.add_result("التحقق من الحذف", False, "العنصر لم يُحذف من قاعدة البيانات")
            else:
                results.add_result("DELETE /api/inventory/{id} (حذف)", False, 
                                  f"HTTP {response.status_code if response else 'No Response'}")
        else:
            results.add_result("عناصر الجرد للاختبار", False, "لا توجد عناصر جرد للاختبار")
    else:
        results.add_result("GET /api/inventory", False, 
                          f"HTTP {response.status_code if response else 'No Response'}", True)

def main():
    print("🚀 بدء اختبار سريع للإصلاحات الجديدة المطلوبة من المستخدم")
    print("🚀 Starting Quick Test for New User-Requested Fixes")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = TestResults()
    
    try:
        # اختبار 1: مشكلة الخزينة والآجل
        test_treasury_deferred_issue(results)
        
        # اختبار 2: APIs الإكسل الجديدة
        test_excel_apis(results)
        
        # اختبار 3: تكامل الجرد مع المواد الخام
        test_inventory_raw_materials_integration(results)
        
        # اختبار 4: APIs الجرد الأساسية
        test_basic_inventory_apis(results)
        
    except KeyboardInterrupt:
        print("\n⚠️  اختبار متوقف بواسطة المستخدم")
        print("⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
    
    # Print final results
    results.print_summary()
    
    # Print detailed results
    print(f"\nتفاصيل النتائج:")
    print("Detailed Results:")
    print("-" * 80)
    for result in results.results:
        print(result)
    
    # Return exit code based on results
    if results.failed_tests > 0:
        print(f"\n⚠️  يوجد {results.failed_tests} اختبار فاشل - يحتاج إصلاح")
        print(f"⚠️  {results.failed_tests} tests failed - needs fixing")
        return False
    else:
        print(f"\n✅ جميع الاختبارات نجحت!")
        print(f"✅ All tests passed!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)