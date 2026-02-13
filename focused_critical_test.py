#!/usr/bin/env python3
"""
اختبار نهائي مركز على المشاكل الحرجة التي تم إصلاحها
Critical Fixes Final Test - Focus on the three specific issues mentioned in review request

Test Focus:
1. تطابق طرق الدفع مع حسابات الخزينة - Payment method matching with treasury accounts
2. API معاملات الجرد - Inventory transactions API
3. تكامل المواد الخام مع الجرد - Raw materials integration with inventory
"""

import requests
import json
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class CriticalFixesTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0
        self.results = []
        
    def log_result(self, test_name, success, message, details=None):
        self.total += 1
        if success:
            self.passed += 1
            status = "✅ نجح"
        else:
            self.failed += 1
            status = "❌ فشل"
            
        result = f"{status} - {test_name}: {message}"
        if details:
            result += f"\n   التفاصيل: {details}"
            
        self.results.append(result)
        print(result)
        
    def test_payment_method_treasury_matching(self):
        """اختبار 1: تطابق طرق الدفع مع حسابات الخزينة"""
        print("\n=== اختبار 1: تطابق طرق الدفع مع حسابات الخزينة ===")
        
        # Test data for different payment methods
        payment_methods_tests = [
            {
                "payment_method": "فودافون كاش محمد الصاوي",
                "expected_account": "vodafone_elsawy",
                "customer_name": "أحمد محمد الصاوي"
            },
            {
                "payment_method": "انستاباي", 
                "expected_account": "instapay",
                "customer_name": "فاطمة أحمد علي"
            },
            {
                "payment_method": "يد الصاوي",
                "expected_account": "yad_elsawy", 
                "customer_name": "محمد حسن إبراهيم"
            },
            {
                "payment_method": "نقدي",
                "expected_account": "cash",
                "customer_name": "سارة محمود عبدالله"
            }
        ]
        
        for i, test_case in enumerate(payment_methods_tests, 1):
            try:
                # Get initial treasury balances
                response = requests.get(f"{BACKEND_URL}/treasury/balances")
                if response.status_code != 200:
                    self.log_result(f"اختبار طريقة الدفع {i}", False, 
                                  f"فشل في الحصول على أرصدة الخزينة: {response.status_code}")
                    continue
                    
                initial_balances = response.json()
                initial_balance = initial_balances.get(test_case["expected_account"], 0)
                
                # Create invoice with specific payment method
                invoice_data = {
                    "customer_name": test_case["customer_name"],
                    "payment_method": test_case["payment_method"],
                    "items": [
                        {
                            "seal_type": "RSL",
                            "material_type": "NBR", 
                            "inner_diameter": 25.0,
                            "outer_diameter": 35.0,
                            "height": 8.0,
                            "quantity": 2,
                            "unit_price": 15.0,
                            "total_price": 30.0,
                            "product_type": "manufactured"
                        }
                    ]
                }
                
                response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data)
                if response.status_code != 200:
                    self.log_result(f"اختبار طريقة الدفع {i}", False,
                                  f"فشل في إنشاء الفاتورة: {response.status_code} - {response.text}")
                    continue
                    
                invoice = response.json()
                
                # Check treasury balances after invoice creation
                response = requests.get(f"{BACKEND_URL}/treasury/balances")
                if response.status_code != 200:
                    self.log_result(f"اختبار طريقة الدفع {i}", False,
                                  "فشل في الحصول على أرصدة الخزينة بعد إنشاء الفاتورة")
                    continue
                    
                final_balances = response.json()
                final_balance = final_balances.get(test_case["expected_account"], 0)
                
                # Verify the balance increased by the invoice amount
                expected_increase = 30.0  # Total invoice amount
                actual_increase = final_balance - initial_balance
                
                if abs(actual_increase - expected_increase) < 0.01:
                    self.log_result(f"اختبار طريقة الدفع {i}", True,
                                  f"تم تطابق طريقة الدفع '{test_case['payment_method']}' مع حساب '{test_case['expected_account']}' بنجاح",
                                  f"الرصيد زاد من {initial_balance} إلى {final_balance}")
                else:
                    self.log_result(f"اختبار طريقة الدفع {i}", False,
                                  f"فشل في تطابق طريقة الدفع '{test_case['payment_method']}'",
                                  f"متوقع زيادة {expected_increase} في حساب {test_case['expected_account']}, لكن الزيادة الفعلية {actual_increase}")
                    
                    # Debug: Check if amount went to cash instead
                    cash_increase = final_balances.get('cash', 0) - initial_balances.get('cash', 0)
                    if abs(cash_increase - expected_increase) < 0.01:
                        print(f"   🔍 تشخيص: المبلغ ذهب إلى حساب 'cash' بدلاً من '{test_case['expected_account']}'")
                        
            except Exception as e:
                self.log_result(f"اختبار طريقة الدفع {i}", False, f"خطأ: {str(e)}")
                
    def test_inventory_transactions_api(self):
        """اختبار 2: API معاملات الجرد"""
        print("\n=== اختبار 2: API معاملات الجرد ===")
        
        try:
            # First, create an inventory item for testing
            inventory_item_data = {
                "material_type": "NBR",
                "inner_diameter": 30.0,
                "outer_diameter": 40.0,
                "available_pieces": 20,
                "min_stock_level": 5,
                "notes": "عنصر اختبار لمعاملات الجرد"
            }
            
            response = requests.post(f"{BACKEND_URL}/inventory", json=inventory_item_data)
            if response.status_code != 200:
                self.log_result("إنشاء عنصر جرد للاختبار", False,
                              f"فشل في إنشاء عنصر الجرد: {response.status_code} - {response.text}")
                return
                
            inventory_item = response.json()
            item_id = inventory_item["id"]
            
            self.log_result("إنشاء عنصر جرد للاختبار", True, "تم إنشاء عنصر الجرد بنجاح")
            
            # Test 1: POST /api/inventory-transactions - Add pieces (IN)
            transaction_in_data = {
                "inventory_item_id": item_id,
                "material_type": "NBR",
                "inner_diameter": 30.0,
                "outer_diameter": 40.0,
                "transaction_type": "in",
                "pieces_change": 10,
                "reason": "إضافة مخزون جديد - اختبار",
                "notes": "اختبار إضافة 10 قطع"
            }
            
            response = requests.post(f"{BACKEND_URL}/inventory-transactions", json=transaction_in_data)
            if response.status_code == 200:
                self.log_result("POST معاملة جرد (إضافة)", True, "تم إنشاء معاملة الإضافة بنجاح")
            else:
                self.log_result("POST معاملة جرد (إضافة)", False,
                              f"فشل في إنشاء معاملة الإضافة: {response.status_code} - {response.text}")
                
            # Test 2: POST /api/inventory-transactions - Remove pieces (OUT)  
            transaction_out_data = {
                "inventory_item_id": item_id,
                "material_type": "NBR",
                "inner_diameter": 30.0,
                "outer_diameter": 40.0,
                "transaction_type": "out",
                "pieces_change": -5,
                "reason": "استهلاك في الإنتاج - اختبار",
                "notes": "اختبار خصم 5 قطع"
            }
            
            response = requests.post(f"{BACKEND_URL}/inventory-transactions", json=transaction_out_data)
            if response.status_code == 200:
                self.log_result("POST معاملة جرد (خصم)", True, "تم إنشاء معاملة الخصم بنجاح")
            else:
                self.log_result("POST معاملة جرد (خصم)", False,
                              f"فشل في إنشاء معاملة الخصم: {response.status_code} - {response.text}")
                
            # Test 3: GET /api/inventory-transactions - This was giving HTTP 500
            response = requests.get(f"{BACKEND_URL}/inventory-transactions")
            if response.status_code == 200:
                transactions = response.json()
                self.log_result("GET معاملات الجرد", True, 
                              f"تم استرجاع معاملات الجرد بنجاح - العدد: {len(transactions)}")
            else:
                self.log_result("GET معاملات الجرد", False,
                              f"فشل في استرجاع معاملات الجرد: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("API معاملات الجرد", False, f"خطأ عام: {str(e)}")
            
    def test_raw_materials_inventory_integration(self):
        """اختبار 3: تكامل المواد الخام مع الجرد"""
        print("\n=== اختبار 3: تكامل المواد الخام مع الجرد ===")
        
        try:
            # Step 1: Create inventory item with 20 pieces
            inventory_item_data = {
                "material_type": "BUR",
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "available_pieces": 20,
                "min_stock_level": 3,
                "notes": "عنصر اختبار تكامل المواد الخام"
            }
            
            response = requests.post(f"{BACKEND_URL}/inventory", json=inventory_item_data)
            if response.status_code != 200:
                self.log_result("إنشاء عنصر جرد للتكامل", False,
                              f"فشل في إنشاء عنصر الجرد: {response.status_code} - {response.text}")
                return
                
            inventory_item = response.json()
            initial_pieces = inventory_item["available_pieces"]
            
            self.log_result("إنشاء عنصر جرد للتكامل", True,
                          f"تم إنشاء عنصر الجرد بـ {initial_pieces} قطعة")
            
            # Step 2: Create raw material that needs 3 pieces
            raw_material_data = {
                "material_type": "BUR",
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "height": 10.0,
                "pieces_count": 3,
                "unit_code": "BUR-25x35-TEST",
                "cost_per_mm": 0.5
            }
            
            response = requests.post(f"{BACKEND_URL}/raw-materials", json=raw_material_data)
            if response.status_code == 200:
                raw_material = response.json()
                self.log_result("إنشاء مادة خام", True, 
                              f"تم إنشاء المادة الخام بنجاح - تحتاج {raw_material_data['pieces_count']} قطع")
            else:
                self.log_result("إنشاء مادة خام", False,
                              f"فشل في إنشاء المادة الخام: {response.status_code} - {response.text}")
                return
                
            # Step 3: Check inventory after raw material creation - should be reduced
            response = requests.get(f"{BACKEND_URL}/inventory/{inventory_item['id']}")
            if response.status_code == 200:
                updated_inventory = response.json()
                final_pieces = updated_inventory["available_pieces"]
                expected_pieces = initial_pieces - raw_material_data["pieces_count"]  # 20 - 3 = 17
                
                if final_pieces == expected_pieces:
                    self.log_result("تحديث الجرد بعد إنشاء المادة الخام", True,
                                  f"تم تحديث الجرد بشكل صحيح من {initial_pieces} إلى {final_pieces} قطعة")
                else:
                    self.log_result("تحديث الجرد بعد إنشاء المادة الخام", False,
                                  f"خطأ في تحديث الجرد - متوقع {expected_pieces} قطعة، لكن الفعلي {final_pieces} قطعة")
            else:
                self.log_result("فحص الجرد بعد إنشاء المادة الخام", False,
                              f"فشل في استرجاع بيانات الجرد: {response.status_code}")
                
        except Exception as e:
            self.log_result("تكامل المواد الخام مع الجرد", False, f"خطأ عام: {str(e)}")
            
    def run_all_tests(self):
        """تشغيل جميع الاختبارات"""
        print("🚀 بدء الاختبار النهائي للمشاكل الحرجة")
        print("=" * 60)
        
        # Run the three critical tests
        self.test_payment_method_treasury_matching()
        self.test_inventory_transactions_api()
        self.test_raw_materials_inventory_integration()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ملخص نتائج الاختبار")
        print("=" * 60)
        
        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        
        print(f"إجمالي الاختبارات: {self.total}")
        print(f"نجح: {self.passed} ✅")
        print(f"فشل: {self.failed} ❌")
        print(f"نسبة النجاح: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("\n🎉 ممتاز! جميع المشاكل الحرجة تم إصلاحها بنجاح")
        elif success_rate >= 70:
            print("\n⚠️ جيد، لكن هناك بعض المشاكل التي تحتاج إصلاح")
        else:
            print("\n🚨 تحذير: المشاكل الحرجة لا تزال موجودة وتحتاج إصلاح فوري")
            
        print("\n📋 تفاصيل النتائج:")
        for result in self.results:
            print(result)
            
        return success_rate >= 90

if __name__ == "__main__":
    test = CriticalFixesTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)