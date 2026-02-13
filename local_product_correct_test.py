#!/usr/bin/env python3
"""
اختبار إنشاء فاتورة مع منتج محلي بالبيانات الصحيحة
Test creating invoice with local product using correct data format
"""

import requests
import json
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

def test_local_product_invoice_correct():
    """اختبار إنشاء فاتورة مع منتج محلي بالتنسيق الصحيح"""
    print("🧪 اختبار إنشاء فاتورة مع منتج محلي (التنسيق الصحيح)")
    print("=" * 70)
    
    # بيانات الاختبار بالتنسيق الصحيح للمنتجات المحلية
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
                # للمنتجات المحلية، نحتاج إلى استخدام الحقول الاختيارية فقط
                "seal_type": None,  # اختياري للمنتجات المحلية
                "material_type": None,  # اختياري للمنتجات المحلية
                "inner_diameter": None,  # اختياري للمنتجات المحلية
                "outer_diameter": None,  # اختياري للمنتجات المحلية
                "height": None,  # اختياري للمنتجات المحلية
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
                    "purchase_price": 20.0,
                    "selling_price": 25.0,
                    "product_size": "50 مم",
                    "product_type": "خاتم زيت",
                    "material_type": "محلي",
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
    print(f"   اسم المنتج: {item['product_name']}")
    print(f"   المورد: {item['supplier']}")
    print(f"   الكمية: {item['quantity']}")
    print(f"   سعر الشراء: {item['purchase_price']} ج.م")
    print(f"   سعر البيع: {item['selling_price']} ج.م")
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
            
            # التحقق من حفظ تفاصيل المنتج المحلي
            if 'items' in result and len(result['items']) > 0:
                saved_item = result['items'][0]
                print(f"   تفاصيل المنتج المحفوظ:")
                print(f"     - اسم المنتج: {saved_item.get('product_name', 'غير محدد')}")
                print(f"     - المورد: {saved_item.get('supplier', 'غير محدد')}")
                print(f"     - نوع المنتج: {saved_item.get('product_type', 'غير محدد')}")
                if 'local_product_details' in saved_item:
                    print(f"     - تفاصيل إضافية محفوظة: ✅")
                else:
                    print(f"     - تفاصيل إضافية محفوظة: ❌")
            
            return True, result
            
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
            
            return False, None
            
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {str(e)}")
        return False, None

def test_retrieve_invoice(invoice_id):
    """اختبار استرجاع الفاتورة للتحقق من حفظ البيانات"""
    print(f"🔍 اختبار استرجاع الفاتورة: {invoice_id}")
    
    try:
        response = requests.get(f"{BACKEND_URL}/invoices/{invoice_id}", timeout=10)
        
        if response.status_code == 200:
            print("✅ تم استرجاع الفاتورة بنجاح")
            invoice = response.json()
            
            # التحقق من تفاصيل المنتج المحلي
            if 'items' in invoice and len(invoice['items']) > 0:
                item = invoice['items'][0]
                print(f"📦 تفاصيل المنتج المسترجع:")
                print(f"   اسم المنتج: {item.get('product_name', 'غير محدد')}")
                print(f"   المورد: {item.get('supplier', 'غير محدد')}")
                print(f"   نوع المنتج: {item.get('product_type', 'غير محدد')}")
                
                if 'local_product_details' in item and item['local_product_details']:
                    details = item['local_product_details']
                    print(f"   تفاصيل إضافية:")
                    print(f"     - الحجم: {details.get('product_size', 'غير محدد')}")
                    print(f"     - النوع: {details.get('product_type', 'غير محدد')}")
                    print(f"     - نوع الخامة: {details.get('material_type', 'غير محدد')}")
                    return True
                else:
                    print("❌ لم يتم حفظ التفاصيل الإضافية")
                    return False
            else:
                print("❌ لا توجد عناصر في الفاتورة")
                return False
        else:
            print(f"❌ فشل في استرجاع الفاتورة - Status Code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في استرجاع الفاتورة: {str(e)}")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 اختبار شامل للمنتجات المحلية في الفواتير")
    print("=" * 70)
    print(f"🌐 عنوان الخادم: {BACKEND_URL}")
    print(f"⏰ وقت الاختبار: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # اختبار إنشاء الفاتورة
    success, invoice_data = test_local_product_invoice_correct()
    
    if success and invoice_data:
        print()
        print("-" * 50)
        
        # اختبار استرجاع الفاتورة
        retrieve_success = test_retrieve_invoice(invoice_data['id'])
        
        print()
        print("=" * 70)
        if retrieve_success:
            print("✅ اكتمل الاختبار بنجاح - المنتجات المحلية تعمل بشكل صحيح")
            print("💡 تم حفظ واسترجاع جميع تفاصيل المنتج المحلي بنجاح")
        else:
            print("⚠️ تم إنشاء الفاتورة لكن هناك مشكلة في حفظ التفاصيل")
    else:
        print()
        print("=" * 70)
        print("❌ فشل الاختبار - مشكلة في إنشاء فاتورة مع منتج محلي")
        print("💡 السبب المحتمل: مشكلة في تنسيق البيانات أو validation")

if __name__ == "__main__":
    main()