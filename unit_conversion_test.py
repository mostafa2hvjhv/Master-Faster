#!/usr/bin/env python3
"""
اختبار المميزات الجديدة المنفذة:
1. تحويل الوحدات في فحص التوافق (البوصة إلى ملليمتر)
2. تحرير وحذف المنتجات المحلية
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://retail-treasury.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

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
            status = "✅ نجح"
        else:
            self.failed_tests += 1
            status = "❌ فشل"
        
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
        
        self.results.append(result)
        print(result)
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"ملخص نتائج الاختبار:")
        print(f"إجمالي الاختبارات: {self.total_tests}")
        print(f"نجح: {self.passed_tests}")
        print(f"فشل: {self.failed_tests}")
        print(f"نسبة النجاح: {(self.passed_tests/self.total_tests)*100:.1f}%")
        print(f"{'='*60}")

def test_unit_conversion_compatibility():
    """اختبار تحويل الوحدات في فحص التوافق"""
    results = TestResults()
    
    print("🔄 بدء اختبار تحويل الوحدات في فحص التوافق...")
    
    try:
        # Test 1: إنشاء منتج بوحدة البوصة
        print("\n1️⃣ اختبار إنشاء منتج بوحدة البوصة...")
        
        # Create test data with inch measurements
        test_product_inches = {
            "seal_type": "RSL",
            "inner_diameter": 4.0,  # 4 بوصة
            "outer_diameter": 4.5,  # 4.5 بوصة
            "height": 0.5,  # 0.5 بوصة
            "unit": "inch"  # وحدة البوصة
        }
        
        # Expected millimeter conversions
        expected_inner_mm = 4.0 * 25.4  # 101.6 مم
        expected_outer_mm = 4.5 * 25.4  # 114.3 مم
        expected_height_mm = 0.5 * 25.4  # 12.7 مم
        
        results.add_result(
            "إعداد بيانات الاختبار بالبوصة", 
            True, 
            f"القطر الداخلي: {test_product_inches['inner_diameter']} بوصة = {expected_inner_mm} مم"
        )
        
        # Test 2: فحص التوافق مع التحويل
        print("\n2️⃣ اختبار فحص التوافق مع تحويل الوحدات...")
        
        compatibility_data = {
            "seal_type": "RSL",
            "inner_diameter": expected_inner_mm,  # القيم المحولة للملليمتر
            "outer_diameter": expected_outer_mm,
            "height": expected_height_mm
        }
        
        response = requests.post(f"{API_BASE}/compatibility-check", json=compatibility_data)
        
        if response.status_code == 200:
            compatibility_result = response.json()
            results.add_result(
                "فحص التوافق مع القيم المحولة", 
                True, 
                f"تم العثور على {len(compatibility_result.get('compatible_materials', []))} مادة متوافقة"
            )
        else:
            results.add_result(
                "فحص التوافق مع القيم المحولة", 
                False, 
                f"خطأ HTTP {response.status_code}: {response.text}"
            )
        
        # Test 3: التحقق من دقة التحويل الرياضي
        print("\n3️⃣ اختبار دقة التحويل الرياضي...")
        
        # Test mathematical accuracy
        test_cases = [
            (4.0, 101.6),    # 4 بوصة = 101.6 مم
            (4.5, 114.3),    # 4.5 بوصة = 114.3 مم
            (0.5, 12.7),     # 0.5 بوصة = 12.7 مم
            (1.0, 25.4),     # 1 بوصة = 25.4 مم
            (2.5, 63.5)      # 2.5 بوصة = 63.5 مم
        ]
        
        conversion_accurate = True
        for inches, expected_mm in test_cases:
            calculated_mm = inches * 25.4
            if abs(calculated_mm - expected_mm) > 0.01:  # Allow small floating point errors
                conversion_accurate = False
                break
        
        results.add_result(
            "دقة التحويل الرياضي (×25.4)", 
            conversion_accurate, 
            "جميع حالات التحويل صحيحة رياضياً"
        )
        
        # Test 4: اختبار سير العمل الكامل
        print("\n4️⃣ اختبار سير العمل الكامل...")
        
        # Create a customer first
        customer_data = {
            "name": "عميل اختبار تحويل الوحدات",
            "phone": "01234567890",
            "address": "عنوان اختبار"
        }
        
        customer_response = requests.post(f"{API_BASE}/customers", json=customer_data)
        if customer_response.status_code == 200:
            customer = customer_response.json()
            
            # Create invoice with converted measurements
            invoice_data = {
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "invoice_title": "فاتورة اختبار تحويل الوحدات",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "seal_type": "RSL",
                        "material_type": "NBR",
                        "inner_diameter": expected_inner_mm,  # القيم المحولة
                        "outer_diameter": expected_outer_mm,
                        "height": expected_height_mm,
                        "quantity": 1,
                        "unit_price": 50.0,
                        "total_price": 50.0,
                        "product_type": "manufactured",
                        "original_unit": "inch",  # الوحدة الأصلية للعرض
                        "original_inner": 4.0,    # القيم الأصلية للعرض
                        "original_outer": 4.5,
                        "original_height": 0.5
                    }
                ],
                "payment_method": "نقدي",
                "discount_type": "amount",
                "discount_value": 0.0
            }
            
            invoice_response = requests.post(f"{API_BASE}/invoices", json=invoice_data)
            if invoice_response.status_code == 200:
                invoice = invoice_response.json()
                results.add_result(
                    "إنشاء فاتورة مع القيم المحولة", 
                    True, 
                    f"فاتورة {invoice['invoice_number']} تم إنشاؤها بنجاح"
                )
                
                # Verify the values are stored in millimeters
                stored_item = invoice["items"][0]
                mm_values_correct = (
                    abs(stored_item["inner_diameter"] - expected_inner_mm) < 0.1 and
                    abs(stored_item["outer_diameter"] - expected_outer_mm) < 0.1 and
                    abs(stored_item["height"] - expected_height_mm) < 0.1
                )
                
                results.add_result(
                    "حفظ القيم بالملليمتر في قاعدة البيانات", 
                    mm_values_correct, 
                    f"القطر الداخلي: {stored_item['inner_diameter']} مم (متوقع: {expected_inner_mm} مم)"
                )
                
            else:
                results.add_result(
                    "إنشاء فاتورة مع القيم المحولة", 
                    False, 
                    f"خطأ HTTP {invoice_response.status_code}: {invoice_response.text}"
                )
        else:
            results.add_result(
                "إنشاء عميل للاختبار", 
                False, 
                f"خطأ HTTP {customer_response.status_code}: {customer_response.text}"
            )
        
    except Exception as e:
        results.add_result("اختبار تحويل الوحدات", False, f"خطأ: {str(e)}")
    
    return results

def test_local_products_edit_delete():
    """اختبار تحرير وحذف المنتجات المحلية"""
    results = TestResults()
    
    print("\n🔄 بدء اختبار تحرير وحذف المنتجات المحلية...")
    
    try:
        # Test 1: إنشاء مورد للاختبار
        print("\n1️⃣ إنشاء مورد للاختبار...")
        
        supplier_data = {
            "name": "مورد اختبار التحرير والحذف",
            "phone": "01111111111",
            "address": "عنوان مورد الاختبار"
        }
        
        supplier_response = requests.post(f"{API_BASE}/suppliers", json=supplier_data)
        if supplier_response.status_code == 200:
            supplier = supplier_response.json()
            results.add_result("إنشاء مورد للاختبار", True, f"مورد {supplier['name']} تم إنشاؤه")
            
            # Test 2: إنشاء منتج محلي للاختبار
            print("\n2️⃣ إنشاء منتج محلي للاختبار...")
            
            product_data = {
                "name": "منتج محلي للاختبار",
                "supplier_id": supplier["id"],
                "purchase_price": 25.0,
                "selling_price": 40.0,
                "current_stock": 10
            }
            
            product_response = requests.post(f"{API_BASE}/local-products", json=product_data)
            if product_response.status_code == 200:
                product = product_response.json()
                results.add_result("إنشاء منتج محلي للاختبار", True, f"منتج {product['name']} تم إنشاؤه")
                
                # Test 3: تحرير المنتج المحلي (PUT)
                print("\n3️⃣ اختبار تحرير المنتج المحلي...")
                
                updated_product_data = {
                    "name": "منتج محلي محدث للاختبار",
                    "supplier_id": supplier["id"],
                    "purchase_price": 30.0,  # تغيير السعر
                    "selling_price": 50.0,   # تغيير السعر
                    "current_stock": 15      # تغيير المخزون
                }
                
                edit_response = requests.put(f"{API_BASE}/local-products/{product['id']}", json=updated_product_data)
                if edit_response.status_code == 200:
                    results.add_result(
                        "PUT /api/local-products/{product_id}", 
                        True, 
                        "تم تحديث المنتج المحلي بنجاح"
                    )
                    
                    # Verify the update
                    get_response = requests.get(f"{API_BASE}/local-products")
                    if get_response.status_code == 200:
                        products = get_response.json()
                        updated_product = next((p for p in products if p["id"] == product["id"]), None)
                        
                        if updated_product:
                            update_verified = (
                                updated_product["name"] == "منتج محلي محدث للاختبار" and
                                updated_product["purchase_price"] == 30.0 and
                                updated_product["selling_price"] == 50.0 and
                                updated_product["current_stock"] == 15
                            )
                            
                            results.add_result(
                                "التحقق من حفظ التحديثات", 
                                update_verified, 
                                f"الاسم: {updated_product['name']}, سعر الشراء: {updated_product['purchase_price']}"
                            )
                        else:
                            results.add_result("التحقق من حفظ التحديثات", False, "لم يتم العثور على المنتج المحدث")
                else:
                    results.add_result(
                        "PUT /api/local-products/{product_id}", 
                        False, 
                        f"خطأ HTTP {edit_response.status_code}: {edit_response.text}"
                    )
                
                # Test 4: حذف المنتج المحلي (DELETE)
                print("\n4️⃣ اختبار حذف المنتج المحلي...")
                
                delete_response = requests.delete(f"{API_BASE}/local-products/{product['id']}")
                if delete_response.status_code == 200:
                    results.add_result(
                        "DELETE /api/local-products/{product_id}", 
                        True, 
                        "تم حذف المنتج المحلي بنجاح"
                    )
                    
                    # Verify deletion
                    get_after_delete = requests.get(f"{API_BASE}/local-products")
                    if get_after_delete.status_code == 200:
                        products_after_delete = get_after_delete.json()
                        deleted_product = next((p for p in products_after_delete if p["id"] == product["id"]), None)
                        
                        results.add_result(
                            "التحقق من الحذف الفعلي", 
                            deleted_product is None, 
                            "المنتج لم يعد موجوداً في قاعدة البيانات" if deleted_product is None else "المنتج لا يزال موجوداً"
                        )
                else:
                    results.add_result(
                        "DELETE /api/local-products/{product_id}", 
                        False, 
                        f"خطأ HTTP {delete_response.status_code}: {delete_response.text}"
                    )
                
            else:
                results.add_result(
                    "إنشاء منتج محلي للاختبار", 
                    False, 
                    f"خطأ HTTP {product_response.status_code}: {product_response.text}"
                )
        else:
            results.add_result(
                "إنشاء مورد للاختبار", 
                False, 
                f"خطأ HTTP {supplier_response.status_code}: {supplier_response.text}"
            )
    
    except Exception as e:
        results.add_result("اختبار تحرير وحذف المنتجات المحلية", False, f"خطأ: {str(e)}")
    
    return results

def test_complete_workflow():
    """اختبار سير العمل الكامل"""
    results = TestResults()
    
    print("\n🔄 بدء اختبار سير العمل الكامل...")
    
    try:
        # Test 1: إنشاء منتج بالبوصة → فحص التوافق → إضافة للفاتورة
        print("\n1️⃣ اختبار سير العمل: إنشاء منتج بالبوصة → فحص التوافق → إضافة للفاتورة...")
        
        # Create customer
        customer_data = {
            "name": "عميل سير العمل الكامل",
            "phone": "01555555555",
            "address": "عنوان سير العمل"
        }
        
        customer_response = requests.post(f"{API_BASE}/customers", json=customer_data)
        if customer_response.status_code == 200:
            customer = customer_response.json()
            
            # Step 1: Product with inch measurements
            inch_measurements = {
                "inner_diameter": 3.0,  # 3 بوصة
                "outer_diameter": 3.5,  # 3.5 بوصة
                "height": 0.75          # 0.75 بوصة
            }
            
            # Convert to millimeters
            mm_measurements = {
                "inner_diameter": inch_measurements["inner_diameter"] * 25.4,  # 76.2 مم
                "outer_diameter": inch_measurements["outer_diameter"] * 25.4,  # 88.9 مم
                "height": inch_measurements["height"] * 25.4                   # 19.05 مم
            }
            
            # Step 2: Compatibility check
            compatibility_data = {
                "seal_type": "RS",
                **mm_measurements
            }
            
            compatibility_response = requests.post(f"{API_BASE}/compatibility-check", json=compatibility_data)
            if compatibility_response.status_code == 200:
                compatibility_result = compatibility_response.json()
                results.add_result(
                    "فحص التوافق في سير العمل", 
                    True, 
                    f"تم العثور على {len(compatibility_result.get('compatible_materials', []))} مادة متوافقة"
                )
                
                # Step 3: Create invoice
                invoice_data = {
                    "customer_id": customer["id"],
                    "customer_name": customer["name"],
                    "invoice_title": "فاتورة سير العمل الكامل",
                    "supervisor_name": "مشرف سير العمل",
                    "items": [
                        {
                            "seal_type": "RS",
                            "material_type": "NBR",
                            **mm_measurements,  # القيم المحولة للحفظ
                            "quantity": 2,
                            "unit_price": 35.0,
                            "total_price": 70.0,
                            "product_type": "manufactured",
                            # معلومات العرض بالوحدة الأصلية
                            "display_unit": "inch",
                            "display_inner": inch_measurements["inner_diameter"],
                            "display_outer": inch_measurements["outer_diameter"],
                            "display_height": inch_measurements["height"]
                        }
                    ],
                    "payment_method": "نقدي",
                    "discount_type": "amount",
                    "discount_value": 0.0
                }
                
                invoice_response = requests.post(f"{API_BASE}/invoices", json=invoice_data)
                if invoice_response.status_code == 200:
                    invoice = invoice_response.json()
                    results.add_result(
                        "إنشاء فاتورة في سير العمل", 
                        True, 
                        f"فاتورة {invoice['invoice_number']} تم إنشاؤها بقيمة {invoice['total_amount']} ج.م"
                    )
                    
                    # Verify measurements are stored in mm but can display in original unit
                    item = invoice["items"][0]
                    storage_correct = (
                        abs(item["inner_diameter"] - mm_measurements["inner_diameter"]) < 0.1 and
                        abs(item["outer_diameter"] - mm_measurements["outer_diameter"]) < 0.1 and
                        abs(item["height"] - mm_measurements["height"]) < 0.1
                    )
                    
                    results.add_result(
                        "حفظ القياسات بالملليمتر", 
                        storage_correct, 
                        f"القطر الداخلي: {item['inner_diameter']:.1f} مم (من {inch_measurements['inner_diameter']} بوصة)"
                    )
                    
                else:
                    results.add_result(
                        "إنشاء فاتورة في سير العمل", 
                        False, 
                        f"خطأ HTTP {invoice_response.status_code}: {invoice_response.text}"
                    )
            else:
                results.add_result(
                    "فحص التوافق في سير العمل", 
                    False, 
                    f"خطأ HTTP {compatibility_response.status_code}: {compatibility_response.text}"
                )
        else:
            results.add_result(
                "إنشاء عميل لسير العمل", 
                False, 
                f"خطأ HTTP {customer_response.status_code}: {customer_response.text}"
            )
        
        # Test 2: اختبار إنشاء وتحرير وحذف منتج محلي
        print("\n2️⃣ اختبار سير العمل: إنشاء وتحرير وحذف منتج محلي...")
        
        # Create supplier
        supplier_data = {
            "name": "مورد سير العمل الكامل",
            "phone": "01666666666",
            "address": "عنوان مورد سير العمل"
        }
        
        supplier_response = requests.post(f"{API_BASE}/suppliers", json=supplier_data)
        if supplier_response.status_code == 200:
            supplier = supplier_response.json()
            
            # Create local product
            product_data = {
                "name": "منتج محلي سير العمل",
                "supplier_id": supplier["id"],
                "purchase_price": 20.0,
                "selling_price": 35.0,
                "current_stock": 5
            }
            
            product_response = requests.post(f"{API_BASE}/local-products", json=product_data)
            if product_response.status_code == 200:
                product = product_response.json()
                
                # Edit the product
                updated_data = {
                    "name": "منتج محلي سير العمل محدث",
                    "supplier_id": supplier["id"],
                    "purchase_price": 22.0,
                    "selling_price": 38.0,
                    "current_stock": 8
                }
                
                edit_response = requests.put(f"{API_BASE}/local-products/{product['id']}", json=updated_data)
                edit_success = edit_response.status_code == 200
                
                # Delete the product
                delete_response = requests.delete(f"{API_BASE}/local-products/{product['id']}")
                delete_success = delete_response.status_code == 200
                
                workflow_success = edit_success and delete_success
                results.add_result(
                    "سير العمل الكامل للمنتج المحلي", 
                    workflow_success, 
                    f"تحرير: {'نجح' if edit_success else 'فشل'}, حذف: {'نجح' if delete_success else 'فشل'}"
                )
            else:
                results.add_result(
                    "إنشاء منتج محلي لسير العمل", 
                    False, 
                    f"خطأ HTTP {product_response.status_code}: {product_response.text}"
                )
        else:
            results.add_result(
                "إنشاء مورد لسير العمل", 
                False, 
                f"خطأ HTTP {supplier_response.status_code}: {supplier_response.text}"
            )
    
    except Exception as e:
        results.add_result("اختبار سير العمل الكامل", False, f"خطأ: {str(e)}")
    
    return results

def main():
    """تشغيل جميع الاختبارات"""
    print("🚀 بدء اختبار المميزات الجديدة المنفذة")
    print("="*60)
    
    all_results = TestResults()
    
    # Test 1: Unit conversion in compatibility check
    print("\n📏 الميزة الأولى: تحويل الوحدات في فحص التوافق")
    unit_conversion_results = test_unit_conversion_compatibility()
    
    # Test 2: Local products edit/delete
    print("\n🏪 الميزة الثانية: تحرير وحذف المنتجات المحلية")
    local_products_results = test_local_products_edit_delete()
    
    # Test 3: Complete workflow
    print("\n🔄 اختبارات إضافية: سير العمل الكامل")
    workflow_results = test_complete_workflow()
    
    # Combine all results
    for results in [unit_conversion_results, local_products_results, workflow_results]:
        all_results.total_tests += results.total_tests
        all_results.passed_tests += results.passed_tests
        all_results.failed_tests += results.failed_tests
        all_results.results.extend(results.results)
    
    # Print final summary
    print("\n" + "="*60)
    print("📊 النتائج النهائية لجميع الاختبارات:")
    all_results.print_summary()
    
    # Print detailed results
    print("\n📋 تفاصيل النتائج:")
    for result in all_results.results:
        print(f"  {result}")
    
    return all_results.passed_tests == all_results.total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)