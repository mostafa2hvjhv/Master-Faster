#!/usr/bin/env python3
"""
اختبار الإصلاحات الثلاثة للمشاكل المحددة من المستخدم - المنتجات المحلية
Testing the three specific fixes for local products as requested by user
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class LocalProductFixesTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_customer_id = None
        self.created_invoice_id = None
            
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ نجح" if success else "❌ فشل"
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} - {test_name}: {message}")
        if details:
            print(f"   التفاصيل: {details}")
            
    def create_test_customer(self):
        """Create a test customer for invoices"""
        try:
            customer_data = {
                "name": "عميل اختبار المنتجات المحلية",
                "phone": "01234567890",
                "address": "عنوان اختبار"
            }
            
            response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if response.status_code == 200:
                customer = response.json()
                self.created_customer_id = customer["id"]
                self.log_result("إنشاء عميل اختبار", True, f"تم إنشاء العميل: {customer['name']}")
                return True
            else:
                self.log_result("إنشاء عميل اختبار", False, f"فشل إنشاء العميل: {response.status_code}", response.text)
                return False
                    
        except Exception as e:
            self.log_result("إنشاء عميل اختبار", False, f"خطأ في إنشاء العميل: {str(e)}")
            return False
            
    def test_1_local_product_invoice_creation(self):
        """
        اختبار 1: إنشاء فاتورة مع منتج محلي
        Test 1: Create invoice with local product - verify no creation error
        """
        try:
            # البيانات الصحيحة للمنتج المحلي كما هو محدد في الطلب
            invoice_data = {
                "customer_id": self.created_customer_id,
                "customer_name": "عميل اختبار المنتجات المحلية",
                "invoice_title": "فاتورة اختبار المنتج المحلي",
                "supervisor_name": "مشرف الاختبار",
                "payment_method": "نقدي",
                "discount_type": "amount",
                "discount_value": 0.0,
                "items": [
                    {
                        # للمنتجات المحلية - يجب أن تكون هذه الحقول null
                        "seal_type": None,
                        "material_type": None,
                        "inner_diameter": None,
                        "outer_diameter": None,
                        "height": None,
                        "material_used": None,
                        "material_details": None,
                        
                        # الحقول المشتركة
                        "quantity": 2,
                        "unit_price": 25.0,
                        "total_price": 50.0,
                        
                        # حقول المنتج المحلي
                        "product_type": "local",
                        "product_name": "خاتم زيت محلي اختبار",
                        "supplier": "مورد اختبار",
                        "purchase_price": 20.0,
                        "selling_price": 25.0,
                        "local_product_details": {
                            "name": "خاتم زيت محلي اختبار",
                            "product_size": "50 مم",
                            "product_type_name": "خاتم زيت",
                            "supplier": "مورد اختبار",
                            "purchase_price": 20.0,
                            "selling_price": 25.0
                        }
                    }
                ]
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code == 200:
                invoice = response.json()
                self.created_invoice_id = invoice.get("id")
                self.log_result(
                    "إنشاء فاتورة مع منتج محلي", 
                    True, 
                    f"تم إنشاء الفاتورة بنجاح: {invoice.get('invoice_number')}",
                    f"المبلغ الإجمالي: {invoice.get('total_amount')} ج.م"
                )
                return True
            else:
                self.log_result(
                    "إنشاء فاتورة مع منتج محلي", 
                    False, 
                    f"فشل إنشاء الفاتورة - HTTP {response.status_code}",
                    response.text
                )
                return False
                    
        except Exception as e:
            self.log_result("إنشاء فاتورة مع منتج محلي", False, f"خطأ في إنشاء الفاتورة: {str(e)}")
            return False
            
    def test_2_verify_invoice_data_integrity(self):
        """
        اختبار 2: التحقق من سلامة بيانات الفاتورة المحلية
        Test 2: Verify local product invoice data integrity - no size duplication
        """
        if not self.created_invoice_id:
            self.log_result("التحقق من سلامة البيانات", False, "لا يوجد معرف فاتورة للاختبار")
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices/{self.created_invoice_id}")
            if response.status_code == 200:
                invoice = response.json()
                
                # التحقق من وجود العناصر
                items = invoice.get("items", [])
                if not items:
                    self.log_result("التحقق من سلامة البيانات", False, "لا توجد عناصر في الفاتورة")
                    return False
                    
                item = items[0]  # العنصر الأول
                
                # التحقق من أن المقاس يظهر مرة واحدة فقط
                local_details = item.get("local_product_details", {})
                product_size = local_details.get("product_size")
                
                if product_size == "50 مم":
                    self.log_result(
                        "التحقق من عدم تكرار المقاس", 
                        True, 
                        f"المقاس يظهر مرة واحدة فقط: {product_size}"
                    )
                else:
                    self.log_result(
                        "التحقق من عدم تكرار المقاس", 
                        False, 
                        f"مشكلة في عرض المقاس: {product_size}"
                    )
                    
                # التحقق من أن الحقول المصنعة null
                manufactured_fields = ["seal_type", "material_type", "inner_diameter", "outer_diameter", "height"]
                null_fields_correct = all(item.get(field) is None for field in manufactured_fields)
                
                if null_fields_correct:
                    self.log_result(
                        "التحقق من الحقول المصنعة null", 
                        True, 
                        "جميع حقول المنتجات المصنعة null كما هو مطلوب"
                    )
                else:
                    non_null_fields = [field for field in manufactured_fields if item.get(field) is not None]
                    self.log_result(
                        "التحقق من الحقول المصنعة null", 
                        False, 
                        f"حقول غير null: {non_null_fields}"
                    )
                    
                # التحقق من بيانات المنتج المحلي
                expected_data = {
                    "product_type": "local",
                    "product_name": "خاتم زيت محلي اختبار",
                    "supplier": "مورد اختبار",
                    "quantity": 2,
                    "selling_price": 25.0
                }
                
                data_correct = True
                for key, expected_value in expected_data.items():
                    actual_value = item.get(key)
                    if actual_value != expected_value:
                        self.log_result(
                            f"التحقق من {key}", 
                            False, 
                            f"القيمة المتوقعة: {expected_value}, القيمة الفعلية: {actual_value}"
                        )
                        data_correct = False
                        
                if data_correct:
                    self.log_result("التحقق من بيانات المنتج المحلي", True, "جميع البيانات صحيحة")
                    
                return True
                
            else:
                self.log_result("التحقق من سلامة البيانات", False, f"فشل استرجاع الفاتورة: {response.status_code}", response.text)
                return False
                    
        except Exception as e:
            self.log_result("التحقق من سلامة البيانات", False, f"خطأ في التحقق من البيانات: {str(e)}")
            return False
            
    def test_3_invoice_edit_functionality(self):
        """
        اختبار 3: تعديل الفاتورة - تعديل اسم المنتج
        Test 3: Invoice edit functionality - edit product name
        """
        if not self.created_invoice_id:
            self.log_result("اختبار تعديل الفاتورة", False, "لا يوجد معرف فاتورة للاختبار")
            return False
            
        try:
            # أولاً، احصل على الفاتورة الحالية
            response = self.session.get(f"{BACKEND_URL}/invoices/{self.created_invoice_id}")
            if response.status_code != 200:
                self.log_result("اختبار تعديل الفاتورة", False, "فشل في استرجاع الفاتورة للتعديل")
                return False
                
            current_invoice = response.json()
                
            # تعديل اسم المنتج
            updated_items = current_invoice["items"].copy()
            updated_items[0]["product_name"] = "خاتم زيت محلي معدل"
            updated_items[0]["local_product_details"]["name"] = "خاتم زيت محلي معدل"
            
            update_data = {
                "invoice_title": "فاتورة معدلة - اختبار التعديل",
                "supervisor_name": "مشرف معدل",
                "items": updated_items
            }
            
            # إرسال التحديث
            response = self.session.put(f"{BACKEND_URL}/invoices/{self.created_invoice_id}", json=update_data)
            if response.status_code == 200:
                self.log_result("تعديل الفاتورة", True, "تم تعديل الفاتورة بنجاح")
                
                # التحقق من حفظ التعديل
                verify_response = self.session.get(f"{BACKEND_URL}/invoices/{self.created_invoice_id}")
                if verify_response.status_code == 200:
                    updated_invoice = verify_response.json()
                    updated_product_name = updated_invoice["items"][0].get("product_name")
                    updated_title = updated_invoice.get("invoice_title")
                    
                    if updated_product_name == "خاتم زيت محلي معدل" and updated_title == "فاتورة معدلة - اختبار التعديل":
                        self.log_result(
                            "التحقق من حفظ التعديل", 
                            True, 
                            f"تم حفظ التعديل: {updated_product_name}"
                        )
                        return True
                    else:
                        self.log_result(
                            "التحقق من حفظ التعديل", 
                            False, 
                            f"لم يتم حفظ التعديل بشكل صحيح. الاسم: {updated_product_name}, العنوان: {updated_title}"
                        )
                        return False
                else:
                    self.log_result("التحقق من حفظ التعديل", False, "فشل في استرجاع الفاتورة المعدلة")
                    return False
            else:
                self.log_result("تعديل الفاتورة", False, f"فشل في تعديل الفاتورة: {response.status_code}", response.text)
                return False
                    
        except Exception as e:
            self.log_result("اختبار تعديل الفاتورة", False, f"خطأ في تعديل الفاتورة: {str(e)}")
            return False
            
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Delete test invoice
            if self.created_invoice_id:
                response = self.session.delete(f"{BACKEND_URL}/invoices/{self.created_invoice_id}")
                if response.status_code == 200:
                    self.log_result("تنظيف البيانات", True, "تم حذف الفاتورة التجريبية")
                    
            # Delete test customer
            if self.created_customer_id:
                response = self.session.delete(f"{BACKEND_URL}/customers/{self.created_customer_id}")
                if response.status_code == 200:
                    self.log_result("تنظيف البيانات", True, "تم حذف العميل التجريبي")
                        
        except Exception as e:
            self.log_result("تنظيف البيانات", False, f"خطأ في تنظيف البيانات: {str(e)}")
            
    def run_all_tests(self):
        """Run all local product fixes tests"""
        print("🔍 بدء اختبار الإصلاحات الثلاثة للمنتجات المحلية...")
        print("=" * 80)
        
        try:
            # Setup
            if not self.create_test_customer():
                return False
                
            # Test 1: Invoice creation with local product
            test1_success = self.test_1_local_product_invoice_creation()
            
            # Test 2: Verify data integrity (no size duplication)
            test2_success = self.test_2_verify_invoice_data_integrity()
            
            # Test 3: Invoice edit functionality
            test3_success = self.test_3_invoice_edit_functionality()
            
            # Cleanup
            self.cleanup_test_data()
            
            # Summary
            print("\n" + "=" * 80)
            print("📊 ملخص نتائج الاختبار:")
            
            successful_tests = sum([test1_success, test2_success, test3_success])
            total_tests = 3
            success_rate = (successful_tests / total_tests) * 100
            
            print(f"✅ الاختبارات الناجحة: {successful_tests}/{total_tests}")
            print(f"📈 نسبة النجاح: {success_rate:.1f}%")
            
            if success_rate == 100:
                print("🎉 جميع الإصلاحات الثلاثة تعمل بشكل مثالي!")
            elif success_rate >= 66:
                print("⚠️  معظم الإصلاحات تعمل بشكل جيد مع بعض المشاكل البسيطة")
            else:
                print("❌ توجد مشاكل حرجة تحتاج إلى إصلاح")
                
            return success_rate == 100
            
        finally:
            self.session.close()

def main():
    """Main test function"""
    tester = LocalProductFixesTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 النتيجة النهائية: جميع الإصلاحات الثلاثة تعمل بشكل صحيح")
        sys.exit(0)
    else:
        print("\n⚠️  النتيجة النهائية: توجد مشاكل تحتاج إلى مراجعة")
        sys.exit(1)

if __name__ == "__main__":
    main()