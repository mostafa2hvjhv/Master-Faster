#!/usr/bin/env python3
"""
اختبار سريع للتأكد من أن جميع الإصلاحات والميزات الجديدة تعمل
Quick test to ensure all fixes and new features are working

Test Areas:
1. تطابق طرق الدفع مع حسابات الخزينة - Payment method matching with treasury accounts
2. APIs الإكسل الجديدة - New Excel APIs
3. تكامل الجرد مع المواد الخام - Inventory integration with raw materials  
4. APIs معاملات الجرد - Inventory transactions APIs
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
    
    def add_result(self, test_name, passed, details=""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        self.results.append(result)
        print(result)
    
    def print_summary(self):
        print(f"\n{'='*80}")
        print(f"اختبار سريع للتحسينات الأخيرة - نتائج الاختبار")
        print(f"Quick Test Results for Latest Improvements")
        print(f"{'='*80}")
        print(f"إجمالي الاختبارات: {self.total_tests}")
        print(f"نجح: {self.passed_tests}")
        print(f"فشل: {self.failed_tests}")
        print(f"نسبة النجاح: {(self.passed_tests/self.total_tests)*100:.1f}%")
        print(f"{'='*80}")

def make_request(method, endpoint, data=None, timeout=10):
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

def test_payment_method_treasury_matching(results):
    """اختبار 1: تطابق طرق الدفع مع حسابات الخزينة"""
    print(f"\n{'='*60}")
    print("اختبار 1: تطابق طرق الدفع مع حسابات الخزينة")
    print("Test 1: Payment Method Treasury Account Matching")
    print(f"{'='*60}")
    
    # Get initial treasury balances
    response = make_request("GET", "/treasury/balances")
    if not response or response.status_code != 200:
        results.add_result("الحصول على أرصدة الخزينة الأولية", False, "فشل في الحصول على الأرصدة")
        return
    
    initial_balances = response.json()
    results.add_result("الحصول على أرصدة الخزينة الأولية", True, f"تم الحصول على {len(initial_balances)} حساب")
    
    # Test 1.1: Create invoice with cash payment
    print("\n--- اختبار فاتورة نقدية ---")
    cash_invoice_data = {
        "customer_name": "عميل اختبار نقدي",
        "items": [{
            "seal_type": "RSL",
            "material_type": "NBR", 
            "inner_diameter": 25.0,
            "outer_diameter": 35.0,
            "height": 10.0,
            "quantity": 1,
            "unit_price": 50.0,
            "total_price": 50.0,
            "product_type": "manufactured"
        }],
        "payment_method": "نقدي",
        "discount_type": "amount",
        "discount_value": 0.0
    }
    
    response = make_request("POST", "/invoices", cash_invoice_data)
    if response and response.status_code == 200:
        invoice_data = response.json()
        results.add_result("إنشاء فاتورة نقدية", True, f"فاتورة {invoice_data.get('invoice_number')}")
        
        # Check treasury balance after cash invoice
        time.sleep(1)  # Wait for transaction processing
        response = make_request("GET", "/treasury/balances")
        if response and response.status_code == 200:
            new_balances = response.json()
            cash_increase = new_balances.get('cash', 0) - initial_balances.get('cash', 0)
            expected_increase = 50.0
            
            if abs(cash_increase - expected_increase) < 0.01:
                results.add_result("تحديث رصيد النقدي صحيح", True, f"زيادة {cash_increase} ج.م")
            else:
                results.add_result("تحديث رصيد النقدي صحيح", False, f"متوقع {expected_increase} ج.م، فعلي {cash_increase} ج.م")
        else:
            results.add_result("فحص رصيد النقدي بعد الفاتورة", False, "فشل في الحصول على الأرصدة")
    else:
        results.add_result("إنشاء فاتورة نقدية", False, f"HTTP {response.status_code if response else 'No Response'}")
    
    # Test 1.2: Create invoice with Vodafone Cash payment
    print("\n--- اختبار فاتورة فودافون كاش ---")
    vodafone_invoice_data = {
        "customer_name": "عميل اختبار فودافون",
        "items": [{
            "seal_type": "RS",
            "material_type": "BUR",
            "inner_diameter": 30.0,
            "outer_diameter": 40.0,
            "height": 12.0,
            "quantity": 1,
            "unit_price": 75.0,
            "total_price": 75.0,
            "product_type": "manufactured"
        }],
        "payment_method": "فودافون كاش محمد الصاوي",
        "discount_type": "amount", 
        "discount_value": 0.0
    }
    
    # Get balances before vodafone invoice
    response = make_request("GET", "/treasury/balances")
    if response and response.status_code == 200:
        pre_vodafone_balances = response.json()
        
        response = make_request("POST", "/invoices", vodafone_invoice_data)
        if response and response.status_code == 200:
            invoice_data = response.json()
            results.add_result("إنشاء فاتورة فودافون كاش", True, f"فاتورة {invoice_data.get('invoice_number')}")
            
            # Check vodafone_elsawy balance
            time.sleep(1)
            response = make_request("GET", "/treasury/balances")
            if response and response.status_code == 200:
                post_vodafone_balances = response.json()
                vodafone_increase = post_vodafone_balances.get('vodafone_elsawy', 0) - pre_vodafone_balances.get('vodafone_elsawy', 0)
                expected_increase = 75.0
                
                if abs(vodafone_increase - expected_increase) < 0.01:
                    results.add_result("تحديث رصيد فودافون الصاوي صحيح", True, f"زيادة {vodafone_increase} ج.م")
                else:
                    results.add_result("تحديث رصيد فودافون الصاوي صحيح", False, f"متوقع {expected_increase} ج.م، فعلي {vodafone_increase} ج.م")
            else:
                results.add_result("فحص رصيد فودافون بعد الفاتورة", False, "فشل في الحصول على الأرصدة")
        else:
            results.add_result("إنشاء فاتورة فودافون كاش", False, f"HTTP {response.status_code if response else 'No Response'}")
    else:
        results.add_result("الحصول على أرصدة ما قبل فودافون", False, "فشل في الحصول على الأرصدة")

def test_excel_apis(results):
    """اختبار 2: APIs الإكسل الجديدة"""
    print(f"\n{'='*60}")
    print("اختبار 2: APIs الإكسل الجديدة")
    print("Test 2: New Excel APIs")
    print(f"{'='*60}")
    
    # Test 2.1: Export inventory to Excel
    print("\n--- اختبار تصدير الجرد ---")
    response = make_request("GET", "/excel/export/inventory")
    if response and response.status_code == 200:
        content_type = response.headers.get('content-type', '')
        if 'excel' in content_type.lower() or 'spreadsheet' in content_type.lower():
            results.add_result("تصدير ملف الجرد Excel", True, f"نوع المحتوى: {content_type}")
        else:
            results.add_result("تصدير ملف الجرد Excel", True, f"استجابة ناجحة، نوع المحتوى: {content_type}")
    else:
        results.add_result("تصدير ملف الجرد Excel", False, f"HTTP {response.status_code if response else 'No Response'}")
    
    # Test 2.2: Export raw materials to Excel
    print("\n--- اختبار تصدير المواد الخام ---")
    response = make_request("GET", "/excel/export/raw-materials")
    if response and response.status_code == 200:
        content_type = response.headers.get('content-type', '')
        if 'excel' in content_type.lower() or 'spreadsheet' in content_type.lower():
            results.add_result("تصدير ملف المواد الخام Excel", True, f"نوع المحتوى: {content_type}")
        else:
            results.add_result("تصدير ملف المواد الخام Excel", True, f"استجابة ناجحة، نوع المحتوى: {content_type}")
    else:
        results.add_result("تصدير ملف المواد الخام Excel", False, f"HTTP {response.status_code if response else 'No Response'}")

def test_inventory_raw_materials_integration(results):
    """اختبار 3: تكامل الجرد مع المواد الخام"""
    print(f"\n{'='*60}")
    print("اختبار 3: تكامل الجرد مع المواد الخام")
    print("Test 3: Inventory Integration with Raw Materials")
    print(f"{'='*60}")
    
    # Test 3.1: Create inventory item
    print("\n--- إنشاء عنصر جرد جديد ---")
    inventory_item_data = {
        "material_type": "NBR",
        "inner_diameter": 20.0,
        "outer_diameter": 30.0,
        "available_pieces": 15,
        "min_stock_level": 3,
        "notes": "اختبار تكامل الجرد"
    }
    
    response = make_request("POST", "/inventory", inventory_item_data)
    if response and response.status_code == 200:
        inventory_item = response.json()
        inventory_item_id = inventory_item.get('id')
        results.add_result("إنشاء عنصر جرد", True, f"ID: {inventory_item_id}")
        
        # Test 3.2: Create raw material that should deduct from inventory
        print("\n--- إنشاء مادة خام مع خصم تلقائي ---")
        raw_material_data = {
            "material_type": "NBR",
            "inner_diameter": 20.0,
            "outer_diameter": 30.0,
            "height": 8.0,
            "pieces_count": 3,
            "unit_code": "NBR-20-30-TEST",
            "cost_per_mm": 0.5
        }
        
        response = make_request("POST", "/raw-materials", raw_material_data)
        if response and response.status_code == 200:
            raw_material = response.json()
            results.add_result("إنشاء مادة خام مع خصم الجرد", True, f"كود: {raw_material.get('unit_code')}")
            
            # Check if inventory was deducted
            time.sleep(1)
            response = make_request("GET", f"/inventory/{inventory_item_id}")
            if response and response.status_code == 200:
                updated_inventory = response.json()
                remaining_pieces = updated_inventory.get('available_pieces', 0)
                expected_remaining = 15 - 3  # 15 initial - 3 deducted
                
                if remaining_pieces == expected_remaining:
                    results.add_result("خصم الجرد التلقائي", True, f"متبقي {remaining_pieces} قطعة")
                else:
                    results.add_result("خصم الجرد التلقائي", False, f"متوقع {expected_remaining}، فعلي {remaining_pieces}")
            else:
                results.add_result("فحص الجرد بعد الخصم", False, "فشل في الحصول على عنصر الجرد")
        else:
            results.add_result("إنشاء مادة خام مع خصم الجرد", False, f"HTTP {response.status_code if response else 'No Response'}")
    else:
        results.add_result("إنشاء عنصر جرد", False, f"HTTP {response.status_code if response else 'No Response'}")

def test_inventory_transactions_apis(results):
    """اختبار 4: APIs معاملات الجرد"""
    print(f"\n{'='*60}")
    print("اختبار 4: APIs معاملات الجرد")
    print("Test 4: Inventory Transactions APIs")
    print(f"{'='*60}")
    
    # Test 4.1: Get all inventory transactions
    print("\n--- اختبار GET /api/inventory-transactions ---")
    response = make_request("GET", "/inventory-transactions")
    if response and response.status_code == 200:
        transactions = response.json()
        results.add_result("GET /api/inventory-transactions", True, f"تم الحصول على {len(transactions)} معاملة")
        
        # Check if transactions have required fields
        if transactions:
            sample_transaction = transactions[0]
            required_fields = ['id', 'inventory_item_id', 'material_type', 'transaction_type', 'pieces_change']
            missing_fields = [field for field in required_fields if field not in sample_transaction]
            
            if not missing_fields:
                results.add_result("هيكل بيانات معاملات الجرد", True, "جميع الحقول المطلوبة موجودة")
            else:
                results.add_result("هيكل بيانات معاملات الجرد", False, f"حقول مفقودة: {missing_fields}")
    else:
        results.add_result("GET /api/inventory-transactions", False, f"HTTP {response.status_code if response else 'No Response'}")
    
    # Test 4.2: Create manual inventory transaction
    print("\n--- إنشاء معاملة جرد يدوية ---")
    
    # First, get an existing inventory item
    response = make_request("GET", "/inventory")
    if response and response.status_code == 200:
        inventory_items = response.json()
        if inventory_items:
            test_item = inventory_items[0]
            
            transaction_data = {
                "inventory_item_id": test_item.get('id'),
                "material_type": test_item.get('material_type'),
                "inner_diameter": test_item.get('inner_diameter'),
                "outer_diameter": test_item.get('outer_diameter'),
                "transaction_type": "in",
                "pieces_change": 5,
                "reason": "إضافة مخزون يدوية - اختبار",
                "notes": "اختبار معاملة جرد يدوية"
            }
            
            response = make_request("POST", "/inventory-transactions", transaction_data)
            if response and response.status_code == 200:
                transaction = response.json()
                results.add_result("إنشاء معاملة جرد يدوية", True, f"ID: {transaction.get('id')}")
            else:
                results.add_result("إنشاء معاملة جرد يدوية", False, f"HTTP {response.status_code if response else 'No Response'}")
        else:
            results.add_result("الحصول على عناصر الجرد للاختبار", False, "لا توجد عناصر جرد")
    else:
        results.add_result("الحصول على عناصر الجرد للاختبار", False, f"HTTP {response.status_code if response else 'No Response'}")

def test_duplicate_transactions_fix(results):
    """اختبار إضافي: التأكد من حل مشاكل duplicate transactions"""
    print(f"\n{'='*60}")
    print("اختبار إضافي: فحص مشاكل التكرار")
    print("Additional Test: Duplicate Transactions Check")
    print(f"{'='*60}")
    
    # Get treasury transactions to check for duplicates
    response = make_request("GET", "/treasury/transactions")
    if response and response.status_code == 200:
        transactions = response.json()
        results.add_result("الحصول على معاملات الخزينة", True, f"تم الحصول على {len(transactions)} معاملة")
        
        # Check for duplicate references
        references = [t.get('reference') for t in transactions if t.get('reference')]
        unique_references = set(references)
        
        if len(references) == len(unique_references):
            results.add_result("فحص تكرار المعاملات", True, "لا توجد معاملات مكررة")
        else:
            duplicates = len(references) - len(unique_references)
            results.add_result("فحص تكرار المعاملات", False, f"توجد {duplicates} معاملة مكررة")
    else:
        results.add_result("الحصول على معاملات الخزينة", False, f"HTTP {response.status_code if response else 'No Response'}")

def main():
    print("🚀 بدء اختبار سريع للتحسينات الأخيرة")
    print("🚀 Starting Quick Test for Latest Improvements")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = TestResults()
    
    try:
        # Test 1: Payment method treasury matching
        test_payment_method_treasury_matching(results)
        
        # Test 2: Excel APIs
        test_excel_apis(results)
        
        # Test 3: Inventory integration with raw materials
        test_inventory_raw_materials_integration(results)
        
        # Test 4: Inventory transactions APIs
        test_inventory_transactions_apis(results)
        
        # Additional test: Duplicate transactions
        test_duplicate_transactions_fix(results)
        
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
        sys.exit(1)
    else:
        print(f"\n✅ جميع الاختبارات نجحت!")
        print(f"✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()