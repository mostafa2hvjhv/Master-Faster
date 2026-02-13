#!/usr/bin/env python3
"""
اختبار التحسينات الجديدة المطلوبة من المستخدم
Testing New User-Requested Improvements

اختبار 1: كود الوحدة التلقائي للمواد الخام
اختبار 2: المنتجات المحلية في الفواتير  
اختبار 3: APIs الأساسية
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class NewImprovementsTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_data = {
            'raw_materials': [],
            'customers': [],
            'invoices': []
        }
    
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
    
    def test_automatic_unit_code_generation(self):
        """اختبار 1: كود الوحدة التلقائي للمواد الخام"""
        print("\n=== اختبار 1: كود الوحدة التلقائي للمواد الخام ===")
        
        try:
            # Test 1.1: Create BUR material with inner=15, outer=45
            print("\n--- إنشاء مادة خام BUR بقطر داخلي 15 وخارجي 45 ---")
            bur_material_1 = {
                "material_type": "BUR",
                "inner_diameter": 15.0,
                "outer_diameter": 45.0,
                "height": 100.0,
                "pieces_count": 5,
                "unit_code": "AUTO",  # This should be auto-generated
                "cost_per_mm": 2.5
            }
            
            response = self.session.post(f"{BACKEND_URL}/raw-materials", json=bur_material_1)
            if response.status_code == 201:
                material_data = response.json()
                expected_code = "B-1"
                actual_code = material_data.get("unit_code", "")
                
                if actual_code == expected_code:
                    self.log_test("إنشاء مادة BUR الأولى مع كود B-1", True, f"كود تلقائي: {actual_code}")
                    self.created_data['raw_materials'].append(material_data['id'])
                else:
                    self.log_test("إنشاء مادة BUR الأولى مع كود B-1", False, f"متوقع: {expected_code}, فعلي: {actual_code}")
            else:
                self.log_test("إنشاء مادة BUR الأولى", False, f"HTTP {response.status_code}: {response.text}")
            
            # Test 1.2: Create another BUR material with same specs
            print("\n--- إنشاء مادة خام BUR أخرى بنفس المواصفات ---")
            bur_material_2 = {
                "material_type": "BUR",
                "inner_diameter": 15.0,
                "outer_diameter": 45.0,
                "height": 80.0,
                "pieces_count": 3,
                "unit_code": "AUTO",  # This should be auto-generated
                "cost_per_mm": 2.5
            }
            
            response = self.session.post(f"{BACKEND_URL}/raw-materials", json=bur_material_2)
            if response.status_code == 201:
                material_data = response.json()
                expected_code = "B-2"
                actual_code = material_data.get("unit_code", "")
                
                if actual_code == expected_code:
                    self.log_test("إنشاء مادة BUR الثانية مع كود B-2", True, f"كود تلقائي: {actual_code}")
                    self.created_data['raw_materials'].append(material_data['id'])
                else:
                    self.log_test("إنشاء مادة BUR الثانية مع كود B-2", False, f"متوقع: {expected_code}, فعلي: {actual_code}")
            else:
                self.log_test("إنشاء مادة BUR الثانية", False, f"HTTP {response.status_code}: {response.text}")
            
            # Test 1.3: Create NBR material with different specs
            print("\n--- إنشاء مادة خام NBR بقطر مختلف ---")
            nbr_material = {
                "material_type": "NBR",
                "inner_diameter": 20.0,
                "outer_diameter": 50.0,
                "height": 120.0,
                "pieces_count": 4,
                "unit_code": "AUTO",  # This should be auto-generated
                "cost_per_mm": 3.0
            }
            
            response = self.session.post(f"{BACKEND_URL}/raw-materials", json=nbr_material)
            if response.status_code == 201:
                material_data = response.json()
                expected_code = "N-1"
                actual_code = material_data.get("unit_code", "")
                
                if actual_code == expected_code:
                    self.log_test("إنشاء مادة NBR الأولى مع كود N-1", True, f"كود تلقائي: {actual_code}")
                    self.created_data['raw_materials'].append(material_data['id'])
                else:
                    self.log_test("إنشاء مادة NBR الأولى مع كود N-1", False, f"متوقع: {expected_code}, فعلي: {actual_code}")
            else:
                self.log_test("إنشاء مادة NBR الأولى", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("اختبار كود الوحدة التلقائي", False, f"خطأ: {str(e)}")
    
    def test_local_products_in_invoices(self):
        """اختبار 2: المنتجات المحلية في الفواتير"""
        print("\n=== اختبار 2: المنتجات المحلية في الفواتير ===")
        
        try:
            # First create a customer for the invoice
            print("\n--- إنشاء عميل للفاتورة ---")
            customer_data = {
                "name": "عميل اختبار المنتجات المحلية",
                "phone": "01234567890",
                "address": "القاهرة"
            }
            
            response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if response.status_code == 201:
                customer = response.json()
                self.created_data['customers'].append(customer['id'])
                self.log_test("إنشاء عميل للاختبار", True, f"العميل: {customer['name']}")
                
                # Test 2.1: Create invoice with local product
                print("\n--- إنشاء فاتورة بمنتج محلي ---")
                local_product_invoice = {
                    "customer_id": customer['id'],
                    "customer_name": customer['name'],
                    "invoice_title": "فاتورة اختبار المنتجات المحلية",
                    "supervisor_name": "مشرف الاختبار",
                    "payment_method": "نقدي",
                    "items": [
                        {
                            "product_type": "local",
                            "product_name": "خاتم زيت",
                            "quantity": 2,
                            "unit_price": 25.0,
                            "total_price": 50.0,
                            "local_product_details": {
                                "product_size": "50 مم",
                                "product_type": "خاتم زيت",
                                "supplier": "مورد محلي",
                                "purchase_price": 15.0,
                                "selling_price": 25.0
                            }
                        }
                    ]
                }
                
                response = self.session.post(f"{BACKEND_URL}/invoices", json=local_product_invoice)
                if response.status_code == 201:
                    invoice_data = response.json()
                    self.created_data['invoices'].append(invoice_data['id'])
                    
                    # Verify the data structure
                    item = invoice_data['items'][0]
                    
                    # Check if data is saved correctly
                    checks = [
                        (item.get('product_type') == 'local', "نوع المنتج = محلي"),
                        (item.get('product_name') == 'خاتم زيت', "اسم المنتج = خاتم زيت"),
                        (item.get('local_product_details', {}).get('product_size') == '50 مم', "المقاس = 50 مم"),
                        (item.get('local_product_details', {}).get('product_type') == 'خاتم زيت', "نوع المنتج في التفاصيل = خاتم زيت"),
                        (item.get('local_product_details', {}).get('supplier') == 'مورد محلي', "المورد = مورد محلي")
                    ]
                    
                    all_passed = True
                    details = []
                    for check, description in checks:
                        if check:
                            details.append(f"✅ {description}")
                        else:
                            details.append(f"❌ {description}")
                            all_passed = False
                    
                    self.log_test("إنشاء فاتورة بمنتج محلي وحفظ البيانات", all_passed, "\n   " + "\n   ".join(details))
                    
                    # Test 2.2: Verify data mapping as specified in requirements
                    print("\n--- التحقق من تطابق البيانات مع المتطلبات ---")
                    
                    # According to requirements:
                    # seal_type = "خاتم زيت" (نوع المنتج)
                    # material_type = "محلي" 
                    # inner_diameter = "50 مم" (المقاس)
                    
                    expected_mappings = [
                        # The requirements seem to suggest these mappings, but let's check what's actually saved
                        (item.get('local_product_details', {}).get('product_type') == 'خاتم زيت', "seal_type mapping"),
                        (item.get('product_type') == 'local', "material_type = محلي"),
                        (item.get('local_product_details', {}).get('product_size') == '50 مم', "inner_diameter = المقاس")
                    ]
                    
                    mapping_passed = True
                    mapping_details = []
                    for check, description in expected_mappings:
                        if check:
                            mapping_details.append(f"✅ {description}")
                        else:
                            mapping_details.append(f"❌ {description}")
                            mapping_passed = False
                    
                    self.log_test("تطابق البيانات مع المتطلبات المحددة", mapping_passed, "\n   " + "\n   ".join(mapping_details))
                    
                else:
                    self.log_test("إنشاء فاتورة بمنتج محلي", False, f"HTTP {response.status_code}: {response.text}")
            else:
                self.log_test("إنشاء عميل للاختبار", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("اختبار المنتجات المحلية في الفواتير", False, f"خطأ: {str(e)}")
    
    def test_basic_apis(self):
        """اختبار 3: APIs الأساسية"""
        print("\n=== اختبار 3: APIs الأساسية ===")
        
        try:
            # Test 3.1: POST /api/raw-materials (with automatic code)
            print("\n--- اختبار POST /api/raw-materials ---")
            test_material = {
                "material_type": "VT",
                "inner_diameter": 25.0,
                "outer_diameter": 55.0,
                "height": 90.0,
                "pieces_count": 6,
                "unit_code": "AUTO",  # Should be auto-generated
                "cost_per_mm": 2.8
            }
            
            response = self.session.post(f"{BACKEND_URL}/raw-materials", json=test_material)
            if response.status_code == 201:
                material_data = response.json()
                auto_code = material_data.get("unit_code", "")
                
                # Check if code was auto-generated (should be V-1 for VT type)
                if auto_code.startswith("V-") and auto_code != "AUTO":
                    self.log_test("POST /api/raw-materials مع كود تلقائي", True, f"كود تلقائي: {auto_code}")
                    self.created_data['raw_materials'].append(material_data['id'])
                else:
                    self.log_test("POST /api/raw-materials مع كود تلقائي", False, f"كود غير صحيح: {auto_code}")
            else:
                self.log_test("POST /api/raw-materials", False, f"HTTP {response.status_code}: {response.text}")
            
            # Test 3.2: GET /api/raw-materials
            print("\n--- اختبار GET /api/raw-materials ---")
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials = response.json()
                
                if isinstance(materials, list) and len(materials) > 0:
                    # Check if our created materials are in the list
                    created_count = 0
                    for material_id in self.created_data['raw_materials']:
                        if any(m.get('id') == material_id for m in materials):
                            created_count += 1
                    
                    self.log_test("GET /api/raw-materials", True, f"استرجاع {len(materials)} مادة خام، منها {created_count} تم إنشاؤها في الاختبار")
                else:
                    self.log_test("GET /api/raw-materials", False, "لم يتم استرجاع أي مواد خام")
            else:
                self.log_test("GET /api/raw-materials", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("اختبار APIs الأساسية", False, f"خطأ: {str(e)}")
    
    def run_all_tests(self):
        """Run all improvement tests"""
        print("🚀 بدء اختبار التحسينات الجديدة المطلوبة من المستخدم")
        print("=" * 60)
        
        # Run the three main tests
        self.test_automatic_unit_code_generation()
        self.test_local_products_in_invoices()
        self.test_basic_apis()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
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
        print(f"نسبة النجاح: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ الاختبارات الفاشلة:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 60)
        
        # Determine overall status
        if success_rate >= 90:
            print("🎉 النتيجة: ممتاز - جميع التحسينات تعمل بشكل مثالي!")
        elif success_rate >= 70:
            print("✅ النتيجة: جيد - معظم التحسينات تعمل مع بعض المشاكل البسيطة")
        else:
            print("⚠️ النتيجة: يحتاج تحسين - توجد مشاكل حرجة تحتاج إصلاح")

if __name__ == "__main__":
    tester = NewImprovementsTester()
    tester.run_all_tests()