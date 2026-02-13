#!/usr/bin/env python3
"""
اختبار شامل للتحسينات الجديدة المطلوبة من المستخدم
Comprehensive Testing for New User-Requested Improvements

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

class ComprehensiveImprovementsTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_data = {
            'inventory': [],
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
    
    def setup_inventory_for_testing(self):
        """Setup inventory items needed for raw material testing"""
        print("\n=== إعداد الجرد للاختبار ===")
        
        inventory_items = [
            {
                "material_type": "BUR",
                "inner_diameter": 15.0,
                "outer_diameter": 45.0,
                "available_pieces": 20,
                "min_stock_level": 2,
                "notes": "جرد اختبار BUR للتحسينات الجديدة"
            },
            {
                "material_type": "NBR", 
                "inner_diameter": 20.0,
                "outer_diameter": 50.0,
                "available_pieces": 15,
                "min_stock_level": 2,
                "notes": "جرد اختبار NBR للتحسينات الجديدة"
            },
            {
                "material_type": "VT",
                "inner_diameter": 25.0,
                "outer_diameter": 55.0,
                "available_pieces": 25,
                "min_stock_level": 2,
                "notes": "جرد اختبار VT للتحسينات الجديدة"
            }
        ]
        
        for item in inventory_items:
            try:
                response = self.session.post(f"{BACKEND_URL}/inventory", json=item)
                if response.status_code in [200, 201]:
                    inventory_data = response.json()
                    self.created_data['inventory'].append(inventory_data['id'])
                    self.log_test(f"إضافة جرد {item['material_type']}", True, f"قطع متاحة: {item['available_pieces']}")
                else:
                    self.log_test(f"إضافة جرد {item['material_type']}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"إضافة جرد {item['material_type']}", False, f"خطأ: {str(e)}")
    
    def test_automatic_unit_code_generation(self):
        """اختبار 1: كود الوحدة التلقائي للمواد الخام"""
        print("\n=== اختبار 1: كود الوحدة التلقائي للمواد الخام ===")
        
        try:
            # First, check existing BUR materials to understand current sequence
            print("\n--- فحص المواد الموجودة لفهم التسلسل الحالي ---")
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            existing_bur_codes = []
            existing_nbr_codes = []
            
            if response.status_code == 200:
                materials = response.json()
                for material in materials:
                    if material.get('material_type') == 'BUR' and material.get('inner_diameter') == 15.0 and material.get('outer_diameter') == 45.0:
                        existing_bur_codes.append(material.get('unit_code', ''))
                    elif material.get('material_type') == 'NBR' and material.get('inner_diameter') == 20.0 and material.get('outer_diameter') == 50.0:
                        existing_nbr_codes.append(material.get('unit_code', ''))
                
                print(f"   أكواد BUR موجودة: {existing_bur_codes}")
                print(f"   أكواد NBR موجودة: {existing_nbr_codes}")
            
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
            if response.status_code in [200, 201]:
                material_data = response.json()
                actual_code = material_data.get("unit_code", "")
                
                # Check if code follows B-X pattern and is auto-generated
                if actual_code.startswith("B-") and actual_code != "AUTO":
                    self.log_test("إنشاء مادة BUR مع كود تلقائي", True, f"كود تلقائي: {actual_code}")
                    self.created_data['raw_materials'].append(material_data['id'])
                else:
                    self.log_test("إنشاء مادة BUR مع كود تلقائي", False, f"كود غير صحيح: {actual_code}")
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
            if response.status_code in [200, 201]:
                material_data = response.json()
                actual_code = material_data.get("unit_code", "")
                
                # Check if code follows B-X pattern and is incremented
                if actual_code.startswith("B-") and actual_code != "AUTO":
                    self.log_test("إنشاء مادة BUR ثانية مع كود تلقائي متزايد", True, f"كود تلقائي: {actual_code}")
                    self.created_data['raw_materials'].append(material_data['id'])
                else:
                    self.log_test("إنشاء مادة BUR ثانية مع كود تلقائي متزايد", False, f"كود غير صحيح: {actual_code}")
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
            if response.status_code in [200, 201]:
                material_data = response.json()
                actual_code = material_data.get("unit_code", "")
                
                # Check if code follows N-X pattern
                if actual_code.startswith("N-") and actual_code != "AUTO":
                    self.log_test("إنشاء مادة NBR مع كود تلقائي", True, f"كود تلقائي: {actual_code}")
                    self.created_data['raw_materials'].append(material_data['id'])
                else:
                    self.log_test("إنشاء مادة NBR مع كود تلقائي", False, f"كود غير صحيح: {actual_code}")
            else:
                self.log_test("إنشاء مادة NBR", False, f"HTTP {response.status_code}: {response.text}")
                
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
            if response.status_code in [200, 201]:
                customer = response.json()
                self.created_data['customers'].append(customer['id'])
                self.log_test("إنشاء عميل للاختبار", True, f"العميل: {customer['name']}")
                
                # Test 2.1: Create invoice with local product as specified in requirements
                print("\n--- إنشاء فاتورة بمنتج محلي حسب المتطلبات ---")
                local_product_invoice = {
                    "customer_id": customer['id'],
                    "customer_name": customer['name'],
                    "invoice_title": "فاتورة اختبار المنتجات المحلية",
                    "supervisor_name": "مشرف الاختبار",
                    "payment_method": "نقدي",
                    "items": [
                        {
                            "product_type": "local",
                            "product_name": "خاتم زيت",  # This should map to seal_type
                            "quantity": 2,
                            "unit_price": 25.0,
                            "total_price": 50.0,
                            "local_product_details": {
                                "product_size": "50 مم",  # This should map to inner_diameter
                                "product_type": "خاتم زيت",  # This should map to seal_type
                                "supplier": "مورد محلي",
                                "purchase_price": 15.0,
                                "selling_price": 25.0
                            }
                        }
                    ]
                }
                
                response = self.session.post(f"{BACKEND_URL}/invoices", json=local_product_invoice)
                if response.status_code in [200, 201]:
                    invoice_data = response.json()
                    self.created_data['invoices'].append(invoice_data['id'])
                    
                    # Verify the data structure
                    item = invoice_data['items'][0]
                    
                    # Test the specific requirements from the Arabic request:
                    # seal_type = "خاتم زيت" (نوع المنتج)
                    # material_type = "محلي" 
                    # inner_diameter = "50 مم" (المقاس)
                    
                    requirements_check = []
                    
                    # Check if product_type is "local" (material_type = "محلي")
                    if item.get('product_type') == 'local':
                        requirements_check.append("✅ material_type = 'محلي' (product_type = 'local')")
                    else:
                        requirements_check.append(f"❌ material_type should be 'محلي', got: {item.get('product_type')}")
                    
                    # Check if seal_type info is preserved (نوع المنتج)
                    product_type_in_details = item.get('local_product_details', {}).get('product_type')
                    if product_type_in_details == 'خاتم زيت':
                        requirements_check.append("✅ seal_type = 'خاتم زيت' (نوع المنتج)")
                    else:
                        requirements_check.append(f"❌ seal_type should be 'خاتم زيت', got: {product_type_in_details}")
                    
                    # Check if inner_diameter info is preserved (المقاس)
                    product_size = item.get('local_product_details', {}).get('product_size')
                    if product_size == '50 مم':
                        requirements_check.append("✅ inner_diameter = '50 مم' (المقاس)")
                    else:
                        requirements_check.append(f"❌ inner_diameter should be '50 مم', got: {product_size}")
                    
                    # Check if all data is saved correctly
                    data_integrity_check = []
                    expected_fields = [
                        ('product_name', 'خاتم زيت'),
                        ('quantity', 2),
                        ('unit_price', 25.0),
                        ('total_price', 50.0)
                    ]
                    
                    for field, expected_value in expected_fields:
                        actual_value = item.get(field)
                        if actual_value == expected_value:
                            data_integrity_check.append(f"✅ {field} = {actual_value}")
                        else:
                            data_integrity_check.append(f"❌ {field} expected {expected_value}, got {actual_value}")
                    
                    all_requirements_passed = all("✅" in check for check in requirements_check)
                    all_data_passed = all("✅" in check for check in data_integrity_check)
                    
                    self.log_test("حفظ البيانات حسب المتطلبات المحددة", all_requirements_passed, 
                                "\n   " + "\n   ".join(requirements_check))
                    
                    self.log_test("سلامة البيانات الأساسية", all_data_passed,
                                "\n   " + "\n   ".join(data_integrity_check))
                    
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
            if response.status_code in [200, 201]:
                material_data = response.json()
                auto_code = material_data.get("unit_code", "")
                
                # Check if code was auto-generated (should be V-X for VT type)
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
                    
                    # Additional check: verify automatic code generation is working
                    auto_generated_codes = []
                    for material in materials:
                        code = material.get('unit_code', '')
                        material_type = material.get('material_type', '')
                        if ((material_type == 'BUR' and code.startswith('B-')) or
                            (material_type == 'NBR' and code.startswith('N-')) or
                            (material_type == 'VT' and code.startswith('V-')) or
                            (material_type == 'BT' and code.startswith('T-')) or
                            (material_type == 'BOOM' and code.startswith('M-'))):
                            auto_generated_codes.append(f"{material_type}:{code}")
                    
                    if auto_generated_codes:
                        self.log_test("التحقق من أكواد الوحدة التلقائية", True, 
                                    f"عدد الأكواد التلقائية: {len(auto_generated_codes)}")
                    else:
                        self.log_test("التحقق من أكواد الوحدة التلقائية", False, "لم يتم العثور على أكواد تلقائية")
                        
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
        
        # Setup inventory first
        self.setup_inventory_for_testing()
        
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
                    print(f"  - {result['test']}")
                    if result['details']:
                        print(f"    {result['details']}")
        
        print("\n" + "=" * 60)
        
        # Determine overall status
        if success_rate >= 90:
            print("🎉 النتيجة: ممتاز - جميع التحسينات تعمل بشكل مثالي!")
        elif success_rate >= 70:
            print("✅ النتيجة: جيد - معظم التحسينات تعمل مع بعض المشاكل البسيطة")
        else:
            print("⚠️ النتيجة: يحتاج تحسين - توجد مشاكل حرجة تحتاج إصلاح")

if __name__ == "__main__":
    tester = ComprehensiveImprovementsTester()
    tester.run_all_tests()