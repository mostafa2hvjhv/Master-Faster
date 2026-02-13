#!/usr/bin/env python3
"""
تقرير شامل: اختبار إنشاء فاتورة مع منتج محلي وتحديد سبب رسالة الخطأ
Comprehensive Report: Testing local product invoice creation and identifying error cause
"""

import requests
import json
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

def test_problematic_data():
    """اختبار البيانات التي تسبب المشكلة (كما في الطلب الأصلي)"""
    print("❌ اختبار البيانات المشكلة (كما في الطلب الأصلي)")
    print("-" * 60)
    
    # البيانات كما هي في الطلب الأصلي
    problematic_data = {
        "customer_name": "عميل اختبار محلي",
        "payment_method": "نقدي",
        "items": [
            {
                "seal_type": "خاتم زيت",  # مشكلة: نص عربي بدلاً من enum
                "material_type": "محلي",  # مشكلة: نص عربي بدلاً من enum
                "inner_diameter": "50 مم",  # مشكلة: نص بدلاً من رقم
                "outer_diameter": 0,
                "height": 0,
                "quantity": 2,
                "unit_price": 25.0,
                "total_price": 50.0,
                "product_type": "local",
                "local_product_details": {
                    "name": "خاتم زيت محلي",
                    "supplier": "مورد محلي"
                }
            }
        ]
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/invoices", json=problematic_data, timeout=10)
        
        if response.status_code == 422:
            error_data = response.json()
            print("📋 الأخطاء المحددة:")
            for error in error_data.get('detail', []):
                field = ' -> '.join(str(x) for x in error['loc'])
                print(f"   🔸 الحقل: {field}")
                print(f"     الخطأ: {error['msg']}")
                print(f"     القيمة المرسلة: {error['input']}")
                print()
            return False
        else:
            print(f"⚠️ استجابة غير متوقعة: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الطلب: {str(e)}")
        return False

def test_correct_data():
    """اختبار البيانات الصحيحة للمنتجات المحلية"""
    print("✅ اختبار البيانات الصحيحة للمنتجات المحلية")
    print("-" * 60)
    
    # البيانات الصحيحة
    correct_data = {
        "customer_name": "عميل اختبار محلي",
        "payment_method": "نقدي",
        "items": [
            {
                # للمنتجات المحلية: الحقول الاختيارية يجب أن تكون None أو غير موجودة
                "seal_type": None,
                "material_type": None,
                "inner_diameter": None,
                "outer_diameter": None,
                "height": None,
                "quantity": 2,
                "unit_price": 25.0,
                "total_price": 50.0,
                "product_type": "local",
                "product_name": "خاتم زيت محلي 50 مم",
                "supplier": "مورد محلي للاختبار",
                "purchase_price": 20.0,
                "selling_price": 25.0,
                "local_product_details": {
                    "name": "خاتم زيت محلي 50 مم",
                    "supplier": "مورد محلي للاختبار",
                    "product_size": "50 مم",
                    "product_type": "خاتم زيت",
                    "material_type": "محلي"
                }
            }
        ]
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/invoices", json=correct_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ تم إنشاء الفاتورة بنجاح!")
            print(f"   رقم الفاتورة: {result.get('invoice_number')}")
            print(f"   إجمالي المبلغ: {result.get('total_amount')} ج.م")
            return True, result
        else:
            print(f"❌ فشل في إنشاء الفاتورة: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   تفاصيل الخطأ: {error_data}")
            except:
                print(f"   رسالة الخطأ: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ خطأ في الطلب: {str(e)}")
        return False, None

def main():
    """التقرير الشامل"""
    print("📊 تقرير شامل: اختبار إنشاء فاتورة مع منتج محلي")
    print("=" * 80)
    print(f"🌐 عنوان الخادم: {BACKEND_URL}")
    print(f"⏰ وقت الاختبار: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🔍 تحليل المشكلة:")
    print("=" * 80)
    
    # اختبار البيانات المشكلة
    test_problematic_data()
    
    print()
    
    # اختبار البيانات الصحيحة
    success, result = test_correct_data()
    
    print()
    print("📋 الخلاصة والتوصيات:")
    print("=" * 80)
    
    print("🔸 سبب رسالة الخطأ 'حدث خطأ في إنشاء الفاتورة':")
    print("   1. استخدام نصوص عربية في حقول enum (seal_type, material_type)")
    print("   2. إرسال نص '50 مم' بدلاً من رقم في inner_diameter")
    print("   3. عدم فهم الفرق بين المنتجات المصنعة والمحلية")
    print()
    
    print("🔸 الحل الصحيح للمنتجات المحلية:")
    print("   1. جعل حقول المنتجات المصنعة (seal_type, material_type, etc.) = None")
    print("   2. استخدام حقول المنتجات المحلية (product_name, supplier, etc.)")
    print("   3. وضع التفاصيل العربية في local_product_details")
    print()
    
    if success:
        print("✅ النتيجة: المنتجات المحلية تعمل بشكل صحيح عند استخدام التنسيق المناسب")
        print("💡 التوصية: تحديث واجهة المستخدم لإرسال البيانات بالتنسيق الصحيح")
    else:
        print("❌ النتيجة: لا تزال هناك مشاكل تحتاج إلى حل")
    
    print()
    print("🛠️ إرشادات للمطور:")
    print("   - للمنتجات المصنعة: استخدم enum values (RSL, NBR, etc.)")
    print("   - للمنتجات المحلية: استخدم product_type='local' مع الحقول المخصصة")
    print("   - تأكد من إرسال الأرقام كـ numbers وليس strings")
    print("   - استخدم local_product_details لحفظ المعلومات العربية")

if __name__ == "__main__":
    main()