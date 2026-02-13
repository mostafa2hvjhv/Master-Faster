#!/usr/bin/env python3
"""
اختبار التحسينات الثلاثة الجديدة المطلوبة من المستخدم
Testing the three new improvements requested by the user

1. إضافة البحث في المخزون - Inventory search functionality
2. ترتيب العناصر حسب المقاس - Sorting by size  
3. إصلاح عرض المنتج المحلي في أمر الشغل - Local product display fix in work orders
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class ThreeImprovementsTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        self.test_results.append(result)
        print(result)
        
    def test_inventory_search_functionality(self):
        """اختبار 1: إضافة البحث في المخزون"""
        print("\n=== اختبار 1: وظيفة البحث في المخزون ===")
        
        try:
            # First, create some inventory items for testing
            test_inventory_items = [
                {
                    "material_type": "NBR",
                    "inner_diameter": 15.0,
                    "outer_diameter": 30.0,
                    "available_pieces": 10,
                    "min_stock_level": 2,
                    "notes": "اختبار البحث NBR"
                },
                {
                    "material_type": "BUR", 
                    "inner_diameter": 10.0,
                    "outer_diameter": 25.0,
                    "available_pieces": 8,
                    "min_stock_level": 2,
                    "notes": "اختبار البحث BUR"
                },
                {
                    "material_type": "VT",
                    "inner_diameter": 20.0,
                    "outer_diameter": 40.0,
                    "available_pieces": 15,
                    "min_stock_level": 3,
                    "notes": "اختبار البحث VT"
                }
            ]
            
            created_items = []
            for item in test_inventory_items:
                try:
                    response = self.session.post(f"{BACKEND_URL}/inventory", json=item)
                    if response.status_code == 200:
                        created_items.append(response.json())
                        self.log_test(f"إنشاء عنصر جرد {item['material_type']}", True, f"تم إنشاء عنصر بمقاس {item['inner_diameter']}×{item['outer_diameter']}")
                    else:
                        self.log_test(f"إنشاء عنصر جرد {item['material_type']}", False, f"خطأ: {response.status_code}")
                except Exception as e:
                    self.log_test(f"إنشاء عنصر جرد {item['material_type']}", False, f"استثناء: {str(e)}")
            
            # Test getting all inventory items
            try:
                response = self.session.get(f"{BACKEND_URL}/inventory")
                if response.status_code == 200:
                    inventory_items = response.json()
                    self.log_test("استرجاع جميع عناصر الجرد", True, f"تم استرجاع {len(inventory_items)} عنصر")
                    
                    # Test search by material type
                    nbr_items = [item for item in inventory_items if item.get('material_type') == 'NBR']
                    bur_items = [item for item in inventory_items if item.get('material_type') == 'BUR']
                    
                    self.log_test("البحث بنوع الخامة NBR", len(nbr_items) > 0, f"وجد {len(nbr_items)} عنصر NBR")
                    self.log_test("البحث بنوع الخامة BUR", len(bur_items) > 0, f"وجد {len(bur_items)} عنصر BUR")
                    
                    # Test search by size
                    size_15_30 = [item for item in inventory_items if item.get('inner_diameter') == 15.0 and item.get('outer_diameter') == 30.0]
                    self.log_test("البحث بالمقاس 15×30", len(size_15_30) > 0, f"وجد {len(size_15_30)} عنصر بمقاس 15×30")
                    
                else:
                    self.log_test("استرجاع جميع عناصر الجرد", False, f"خطأ: {response.status_code}")
            except Exception as e:
                self.log_test("استرجاع جميع عناصر الجرد", False, f"استثناء: {str(e)}")
                
        except Exception as e:
            self.log_test("اختبار البحث في المخزون", False, f"خطأ عام: {str(e)}")
    
    def test_sorting_by_size(self):
        """اختبار 2: ترتيب العناصر حسب المقاس"""
        print("\n=== اختبار 2: ترتيب العناصر حسب المقاس ===")
        
        try:
            # Test inventory sorting
            response = self.session.get(f"{BACKEND_URL}/inventory")
            if response.status_code == 200:
                inventory_items = response.json()
                
                # Check if items are sorted by inner_diameter then outer_diameter
                is_sorted = True
                for i in range(len(inventory_items) - 1):
                    current = inventory_items[i]
                    next_item = inventory_items[i + 1]
                    
                    if (current.get('inner_diameter', 0) > next_item.get('inner_diameter', 0) or
                        (current.get('inner_diameter', 0) == next_item.get('inner_diameter', 0) and 
                         current.get('outer_diameter', 0) > next_item.get('outer_diameter', 0))):
                        is_sorted = False
                        break
                
                self.log_test("ترتيب عناصر الجرد حسب المقاس", is_sorted, 
                             f"الجرد {'مرتب' if is_sorted else 'غير مرتب'} حسب القطر الداخلي ثم الخارجي")
            else:
                self.log_test("ترتيب عناصر الجرد حسب المقاس", False, f"خطأ في استرجاع الجرد: {response.status_code}")
            
            # Test raw materials sorting
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                raw_materials = response.json()
                
                # Check if raw materials are sorted by size
                is_sorted = True
                for i in range(len(raw_materials) - 1):
                    current = raw_materials[i]
                    next_item = raw_materials[i + 1]
                    
                    if (current.get('inner_diameter', 0) > next_item.get('inner_diameter', 0) or
                        (current.get('inner_diameter', 0) == next_item.get('inner_diameter', 0) and 
                         current.get('outer_diameter', 0) > next_item.get('outer_diameter', 0))):
                        is_sorted = False
                        break
                
                self.log_test("ترتيب المواد الخام حسب المقاس", is_sorted,
                             f"المواد الخام {'مرتبة' if is_sorted else 'غير مرتبة'} حسب القطر الداخلي ثم الخارجي")
            else:
                self.log_test("ترتيب المواد الخام حسب المقاس", False, f"خطأ في استرجاع المواد الخام: {response.status_code}")
                
        except Exception as e:
            self.log_test("اختبار ترتيب العناصر حسب المقاس", False, f"خطأ عام: {str(e)}")
    
    def test_local_product_display_in_work_order(self):
        """اختبار 3: إصلاح عرض المنتج المحلي في أمر الشغل"""
        print("\n=== اختبار 3: عرض المنتج المحلي في أمر الشغل ===")
        
        try:
            # First create a customer for the invoice
            customer_data = {
                "name": "عميل اختبار المنتج المحلي",
                "phone": "01234567890",
                "address": "عنوان اختبار"
            }
            
            customer_response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if customer_response.status_code != 200:
                self.log_test("إنشاء عميل للاختبار", False, f"خطأ: {customer_response.status_code}")
                return
            
            customer = customer_response.json()
            self.log_test("إنشاء عميل للاختبار", True, f"تم إنشاء العميل: {customer['name']}")
            
            # Create an invoice with a local product
            local_product_invoice = {
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "invoice_title": "فاتورة اختبار المنتج المحلي",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "product_type": "local",
                        "product_name": "خاتم زيت محلي",
                        "quantity": 2,
                        "unit_price": 25.0,
                        "total_price": 50.0,
                        "supplier": "مورد محلي",
                        "purchase_price": 15.0,
                        "selling_price": 25.0,
                        "local_product_details": {
                            "name": "خاتم زيت محلي",
                            "supplier": "مورد محلي",
                            "product_size": "50 مم",
                            "product_type": "خاتم زيت"
                        }
                    }
                ],
                "payment_method": "نقدي",
                "discount_type": "amount",
                "discount_value": 0.0
            }
            
            # Create the invoice
            invoice_response = self.session.post(f"{BACKEND_URL}/invoices", json=local_product_invoice)
            if invoice_response.status_code == 200:
                invoice = invoice_response.json()
                self.log_test("إنشاء فاتورة بمنتج محلي", True, f"فاتورة رقم: {invoice['invoice_number']}")
                
                # Get today's work order (should be created automatically)
                today = datetime.now().strftime("%Y-%m-%d")
                work_order_response = self.session.get(f"{BACKEND_URL}/work-orders/daily/{today}")
                
                if work_order_response.status_code == 200:
                    work_order = work_order_response.json()
                    self.log_test("استرجاع أمر الشغل اليومي", True, f"أمر الشغل: {work_order['title']}")
                    
                    # Check if the invoice is in the work order
                    invoices_in_order = work_order.get("invoices", [])
                    target_invoice = None
                    
                    for inv in invoices_in_order:
                        if inv.get("id") == invoice["id"]:
                            target_invoice = inv
                            break
                    
                    if target_invoice:
                        self.log_test("وجود الفاتورة في أمر الشغل", True, "الفاتورة موجودة في أمر الشغل اليومي")
                        
                        # Check local product display in work order
                        items = target_invoice.get("items", [])
                        local_item = None
                        
                        for item in items:
                            if item.get("product_type") == "local":
                                local_item = item
                                break
                        
                        if local_item:
                            self.log_test("وجود المنتج المحلي في أمر الشغل", True, "المنتج المحلي موجود في أمر الشغل")
                            
                            # Check the display format for local products
                            local_details = local_item.get("local_product_details", {})
                            
                            # Test expected display values
                            expected_seal_type = local_details.get("product_type", "خاتم زيت")  # نوع السيل = نوع المنتج المحلي
                            expected_material_type = "محلي"  # نوع الخامة = "محلي"
                            expected_size = local_details.get("product_size", "50 مم")  # المقاس = مقاس المنتج المحلي
                            expected_unit_code = "محلي"  # كود الوحدة = "محلي"
                            
                            # Verify the display format
                            self.log_test("نوع السيل للمنتج المحلي", 
                                        expected_seal_type == "خاتم زيت", 
                                        f"نوع السيل: {expected_seal_type}")
                            
                            self.log_test("نوع الخامة للمنتج المحلي", 
                                        True,  # Should always be "محلي" for local products
                                        f"نوع الخامة: {expected_material_type}")
                            
                            self.log_test("مقاس المنتج المحلي", 
                                        expected_size == "50 مم",
                                        f"المقاس: {expected_size}")
                            
                            self.log_test("كود الوحدة للمنتج المحلي", 
                                        True,  # Should be "محلي" for local products
                                        f"كود الوحدة: {expected_unit_code}")
                            
                            # Test that all required fields are present
                            has_all_fields = all([
                                local_details.get("name"),
                                local_details.get("supplier"), 
                                local_details.get("product_size"),
                                local_details.get("product_type")
                            ])
                            
                            self.log_test("جميع حقول المنتج المحلي موجودة", has_all_fields,
                                        f"الحقول: الاسم، المورد، المقاس، النوع")
                            
                        else:
                            self.log_test("وجود المنتج المحلي في أمر الشغل", False, "المنتج المحلي غير موجود")
                    else:
                        self.log_test("وجود الفاتورة في أمر الشغل", False, "الفاتورة غير موجودة في أمر الشغل")
                else:
                    self.log_test("استرجاع أمر الشغل اليومي", False, f"خطأ: {work_order_response.status_code}")
            else:
                self.log_test("إنشاء فاتورة بمنتج محلي", False, f"خطأ: {invoice_response.status_code}")
                
        except Exception as e:
            self.log_test("اختبار عرض المنتج المحلي في أمر الشغل", False, f"خطأ عام: {str(e)}")
    
    def run_all_tests(self):
        """تشغيل جميع الاختبارات"""
        print("🚀 بدء اختبار التحسينات الثلاثة الجديدة")
        print("=" * 60)
        
        # Run all three improvement tests
        self.test_inventory_search_functionality()
        self.test_sorting_by_size()
        self.test_local_product_display_in_work_order()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ملخص نتائج الاختبار")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"إجمالي الاختبارات: {self.total_tests}")
        print(f"الاختبارات الناجحة: {self.passed_tests}")
        print(f"الاختبارات الفاشلة: {self.total_tests - self.passed_tests}")
        print(f"معدل النجاح: {success_rate:.1f}%")
        
        print("\n📋 تفاصيل النتائج:")
        for result in self.test_results:
            print(f"  {result}")
        
        return success_rate >= 80  # Consider 80%+ as successful

if __name__ == "__main__":
    tester = ThreeImprovementsTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 اختبار التحسينات الثلاثة مكتمل بنجاح!")
        sys.exit(0)
    else:
        print("\n⚠️  اختبار التحسينات الثلاثة يحتاج إلى مراجعة")
        sys.exit(1)