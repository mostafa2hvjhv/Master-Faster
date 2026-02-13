#!/usr/bin/env python3
"""
اختبار إنشاء فاتورة مع منتج محلي لتحديد سبب رسالة الخطأ
Test creating invoice with local product to identify error message cause
"""

import requests
import json
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

def test_local_product_invoice():
    """اختبار إنشاء فاتورة مع منتج محلي"""
    print("🧪 اختبار إنشاء فاتورة مع منتج محلي")
    print("=" * 60)
    
    # بيانات الاختبار كما هو مطلوب
    invoice_data = {
        "customer_name": "عميل اختبار محلي",
        "customer_id": None,
        "invoice_title": "فاتورة اختبار منتج محلي",
        "supervisor_name": "مشرف الاختبار",
        "payment_method": "نقدي",
        "discount_type": "amount",
        "discount_value": 0.0,
        "notes": "اختبار إنشاء فاتورة مع منتج محلي",
        "items": [
            {
                # المنتج المحلي بالمواصفات المطلوبة
                "seal_type": "خاتم زيت",
                "material_type": "محلي",
                "inner_diameter": "50 مم",  # كنص كما هو مطلوب
                "outer_diameter": 0,
                "height": 0,
                "quantity": 2,
                "unit_price": 25.0,
                "total_price": 50.0,
                "product_type": "local",
                "local_product_details": {
                    "name": "خاتم زيت محلي 50 مم",
                    "supplier": "مورد محلي للاختبار",
                    "purchase_price": 20.0,
                    "selling_price": 25.0,
                    "product_size": "50 مم",
                    "product_category": "خواتم زيت",
                    "notes": "منتج محلي للاختبار"
                }
            }
        ]
    }
    
    print(f"📋 بيانات الفاتورة:")
    print(f"   العميل: {invoice_data['customer_name']}")
    print(f"   عنوان الفاتورة: {invoice_data['invoice_title']}")
    print(f"   طريقة الدفع: {invoice_data['payment_method']}")
    print(f"   عدد العناصر: {len(invoice_data['items'])}")
    print()
    
    print(f"📦 تفاصيل المنتج المحلي:")
    item = invoice_data['items'][0]
    print(f"   نوع السيل: {item['seal_type']}")
    print(f"   نوع الخامة: {item['material_type']}")
    print(f"   القطر الداخلي: {item['inner_diameter']}")
    print(f"   الكمية: {item['quantity']}")
    print(f"   سعر الوحدة: {item['unit_price']} ج.م")
    print(f"   الإجمالي: {item['total_price']} ج.م")
    print(f"   نوع المنتج: {item['product_type']}")
    print()
    
    try:
        print("🚀 إرسال طلب إنشاء الفاتورة...")
        
        # إرسال الطلب مع تسجيل تفصيلي
        response = requests.post(
            f"{BACKEND_URL}/invoices",
            json=invoice_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30
        )
        
        print(f"📊 معلومات الاستجابة:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Response Time: {response.elapsed.total_seconds():.2f}s")
        print()
        
        # تحليل الاستجابة
        if response.status_code == 200 or response.status_code == 201:
            print("✅ تم إنشاء الفاتورة بنجاح!")
            result = response.json()
            print(f"   رقم الفاتورة: {result.get('invoice_number', 'غير محدد')}")
            print(f"   معرف الفاتورة: {result.get('id', 'غير محدد')}")
            print(f"   إجمالي المبلغ: {result.get('total_amount', 0)} ج.م")
            print(f"   حالة الفاتورة: {result.get('status', 'غير محدد')}")
            return True
            
        else:
            print(f"❌ فشل في إنشاء الفاتورة - Status Code: {response.status_code}")
            
            # محاولة قراءة رسالة الخطأ
            try:
                error_data = response.json()
                print(f"📋 تفاصيل الخطأ (JSON):")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(f"📋 رسالة الخطأ (نص):")
                print(response.text)
            
            print()
            print(f"🔍 تحليل الخطأ:")
            
            if response.status_code == 400:
                print("   - خطأ في البيانات المرسلة (Bad Request)")
            elif response.status_code == 422:
                print("   - خطأ في التحقق من صحة البيانات (Validation Error)")
            elif response.status_code == 500:
                print("   - خطأ داخلي في الخادم (Internal Server Error)")
            else:
                print(f"   - خطأ غير متوقع: {response.status_code}")
            
            return False
            
    except requests.exceptions.Timeout:
        print("❌ انتهت مهلة الطلب (Timeout)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ خطأ في الاتصال بالخادم")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {str(e)}")
        return False

def test_backend_connection():
    """اختبار الاتصال بالخادم"""
    print("🔗 اختبار الاتصال بالخادم...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/dashboard/stats", timeout=10)
        if response.status_code == 200:
            print("✅ الاتصال بالخادم يعمل بشكل طبيعي")
            return True
        else:
            print(f"⚠️ الخادم يستجيب لكن بحالة: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ فشل الاتصال بالخادم: {str(e)}")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 اختبار إنشاء فاتورة مع منتج محلي")
    print("=" * 60)
    print(f"🌐 عنوان الخادم: {BACKEND_URL}")
    print(f"⏰ وقت الاختبار: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # اختبار الاتصال أولاً
    if not test_backend_connection():
        print("❌ فشل في الاتصال بالخادم. توقف الاختبار.")
        sys.exit(1)
    
    print()
    
    # اختبار إنشاء الفاتورة
    success = test_local_product_invoice()
    
    print()
    print("=" * 60)
    if success:
        print("✅ اكتمل الاختبار بنجاح - لا توجد مشاكل في إنشاء فاتورة مع منتج محلي")
    else:
        print("❌ فشل الاختبار - تم تحديد مشكلة في إنشاء فاتورة مع منتج محلي")
        print("💡 يرجى مراجعة تفاصيل الخطأ أعلاه لتحديد السبب الدقيق")

if __name__ == "__main__":
    main()