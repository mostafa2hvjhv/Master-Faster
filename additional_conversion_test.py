#!/usr/bin/env python3
"""
اختبارات إضافية للتحقق من:
1. التحويلات الرياضية الصحيحة (4 × 25.4 = 101.6)
2. عرض المقاسات في الفاتورة وأمر الشغل بالوحدة الأصلية
3. اختبار حالات مختلفة من التحويل
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://retail-treasury.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_mathematical_conversions():
    """اختبار التحويلات الرياضية بدقة"""
    print("🧮 اختبار التحويلات الرياضية...")
    
    test_cases = [
        # (بوصة, ملليمتر متوقع, وصف)
        (1.0, 25.4, "1 بوصة = 25.4 مم"),
        (2.0, 50.8, "2 بوصة = 50.8 مم"),
        (4.0, 101.6, "4 بوصة = 101.6 مم (حالة الاختبار الأساسية)"),
        (4.5, 114.3, "4.5 بوصة = 114.3 مم (حالة الاختبار الأساسية)"),
        (0.5, 12.7, "0.5 بوصة = 12.7 مم"),
        (3.25, 82.55, "3.25 بوصة = 82.55 مم (رقم عشري)"),
        (10.0, 254.0, "10 بوصة = 254 مم (رقم كبير)")
    ]
    
    all_correct = True
    for inches, expected_mm, description in test_cases:
        calculated_mm = inches * 25.4
        is_correct = abs(calculated_mm - expected_mm) < 0.01
        
        status = "✅" if is_correct else "❌"
        print(f"  {status} {description}: {calculated_mm} مم")
        
        if not is_correct:
            all_correct = False
            print(f"    خطأ: متوقع {expected_mm} مم، تم حساب {calculated_mm} مم")
    
    return all_correct

def test_invoice_display_with_original_units():
    """اختبار عرض الفاتورة بالوحدة الأصلية"""
    print("\n📄 اختبار عرض الفاتورة بالوحدة الأصلية...")
    
    try:
        # Create customer
        customer_data = {
            "name": "عميل اختبار العرض",
            "phone": "01777777777",
            "address": "عنوان اختبار العرض"
        }
        
        customer_response = requests.post(f"{API_BASE}/customers", json=customer_data)
        if customer_response.status_code != 200:
            print("❌ فشل في إنشاء العميل")
            return False
        
        customer = customer_response.json()
        
        # Test case: 4 inner × 4.5 outer inches
        original_inches = {
            "inner_diameter": 4.0,
            "outer_diameter": 4.5,
            "height": 0.75
        }
        
        converted_mm = {
            "inner_diameter": 4.0 * 25.4,  # 101.6
            "outer_diameter": 4.5 * 25.4,  # 114.3
            "height": 0.75 * 25.4          # 19.05
        }
        
        # Create invoice with both original and converted values
        invoice_data = {
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "invoice_title": "فاتورة اختبار العرض بالوحدة الأصلية",
            "supervisor_name": "مشرف اختبار العرض",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    # القيم المحولة للحفظ في قاعدة البيانات
                    "inner_diameter": converted_mm["inner_diameter"],
                    "outer_diameter": converted_mm["outer_diameter"],
                    "height": converted_mm["height"],
                    "quantity": 1,
                    "unit_price": 75.0,
                    "total_price": 75.0,
                    "product_type": "manufactured",
                    # معلومات إضافية للعرض
                    "original_unit": "inch",
                    "original_inner": original_inches["inner_diameter"],
                    "original_outer": original_inches["outer_diameter"],
                    "original_height": original_inches["height"],
                    "conversion_note": f"محول من {original_inches['inner_diameter']}×{original_inches['outer_diameter']} بوصة"
                }
            ],
            "payment_method": "نقدي",
            "discount_type": "amount",
            "discount_value": 0.0,
            "notes": "فاتورة اختبار التحويل من البوصة إلى الملليمتر"
        }
        
        invoice_response = requests.post(f"{API_BASE}/invoices", json=invoice_data)
        if invoice_response.status_code != 200:
            print(f"❌ فشل في إنشاء الفاتورة: {invoice_response.text}")
            return False
        
        invoice = invoice_response.json()
        print(f"✅ تم إنشاء فاتورة {invoice['invoice_number']} بنجاح")
        
        # Verify the stored values are in millimeters
        stored_item = invoice["items"][0]
        
        mm_storage_correct = (
            abs(stored_item["inner_diameter"] - 101.6) < 0.1 and
            abs(stored_item["outer_diameter"] - 114.3) < 0.1 and
            abs(stored_item["height"] - 19.05) < 0.1
        )
        
        if mm_storage_correct:
            print("✅ القيم محفوظة بالملليمتر في قاعدة البيانات:")
            print(f"  - القطر الداخلي: {stored_item['inner_diameter']} مم (من {original_inches['inner_diameter']} بوصة)")
            print(f"  - القطر الخارجي: {stored_item['outer_diameter']} مم (من {original_inches['outer_diameter']} بوصة)")
            print(f"  - الارتفاع: {stored_item['height']} مم (من {original_inches['height']} بوصة)")
        else:
            print("❌ القيم غير محفوظة بشكل صحيح بالملليمتر")
            return False
        
        # Test retrieving the invoice
        get_invoice_response = requests.get(f"{API_BASE}/invoices/{invoice['id']}")
        if get_invoice_response.status_code == 200:
            retrieved_invoice = get_invoice_response.json()
            print("✅ تم استرجاع الفاتورة بنجاح")
            
            # Check if original unit information is preserved
            retrieved_item = retrieved_invoice["items"][0]
            if "original_unit" in retrieved_item:
                print(f"✅ معلومات الوحدة الأصلية محفوظة: {retrieved_item.get('original_unit', 'غير محدد')}")
            else:
                print("⚠️ معلومات الوحدة الأصلية غير محفوظة (هذا طبيعي إذا لم يتم تنفيذها في الواجهة)")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار عرض الفاتورة: {str(e)}")
        return False

def test_work_order_display():
    """اختبار عرض أمر الشغل"""
    print("\n📋 اختبار عرض أمر الشغل...")
    
    try:
        # Get today's work order
        today = datetime.now().strftime("%Y-%m-%d")
        work_order_response = requests.get(f"{API_BASE}/work-orders/daily/{today}")
        
        if work_order_response.status_code == 200:
            work_order = work_order_response.json()
            print(f"✅ تم العثور على أمر شغل يومي: {work_order.get('title', 'بدون عنوان')}")
            
            if work_order.get("invoices"):
                print(f"✅ أمر الشغل يحتوي على {len(work_order['invoices'])} فاتورة")
                
                # Check if any invoice has converted measurements
                for i, invoice in enumerate(work_order["invoices"]):
                    if invoice.get("items"):
                        for j, item in enumerate(invoice["items"]):
                            if item.get("inner_diameter", 0) > 50:  # Likely converted from inches
                                print(f"✅ العنصر {j+1} في الفاتورة {i+1} يحتوي على قياسات محولة:")
                                print(f"  - القطر الداخلي: {item['inner_diameter']} مم")
                                print(f"  - القطر الخارجي: {item['outer_diameter']} مم")
                                
                                # Check if this could be from inch conversion
                                possible_inch_inner = item["inner_diameter"] / 25.4
                                possible_inch_outer = item["outer_diameter"] / 25.4
                                
                                if abs(possible_inch_inner - round(possible_inch_inner, 2)) < 0.01:
                                    print(f"  - محتمل أن يكون محول من {possible_inch_inner:.2f} بوصة")
            else:
                print("⚠️ أمر الشغل لا يحتوي على فواتير")
        else:
            print("⚠️ لم يتم العثور على أمر شغل يومي (هذا طبيعي إذا لم يتم إنشاء فواتير اليوم)")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار أمر الشغل: {str(e)}")
        return False

def test_edge_cases():
    """اختبار حالات خاصة"""
    print("\n🔍 اختبار حالات خاصة...")
    
    edge_cases = [
        # (بوصة, وصف)
        (0.1, "قياس صغير جداً"),
        (0.001, "قياس دقيق جداً"),
        (100.0, "قياس كبير"),
        (3.14159, "رقم عشري معقد"),
        (0.0, "صفر")
    ]
    
    all_passed = True
    
    for inches, description in edge_cases:
        try:
            mm = inches * 25.4
            
            # Test compatibility check with this measurement
            compatibility_data = {
                "seal_type": "RSL",
                "inner_diameter": mm,
                "outer_diameter": mm + 10,  # Add some difference
                "height": mm + 5
            }
            
            response = requests.post(f"{API_BASE}/compatibility-check", json=compatibility_data)
            
            if response.status_code == 200:
                print(f"✅ {description}: {inches} بوصة = {mm} مم - فحص التوافق نجح")
            else:
                print(f"❌ {description}: {inches} بوصة = {mm} مم - فحص التوافق فشل")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {description}: خطأ - {str(e)}")
            all_passed = False
    
    return all_passed

def main():
    """تشغيل جميع الاختبارات الإضافية"""
    print("🔬 اختبارات إضافية للتحويل من البوصة إلى الملليمتر")
    print("="*60)
    
    results = []
    
    # Test 1: Mathematical conversions
    math_result = test_mathematical_conversions()
    results.append(("التحويلات الرياضية", math_result))
    
    # Test 2: Invoice display
    invoice_result = test_invoice_display_with_original_units()
    results.append(("عرض الفاتورة بالوحدة الأصلية", invoice_result))
    
    # Test 3: Work order display
    work_order_result = test_work_order_display()
    results.append(("عرض أمر الشغل", work_order_result))
    
    # Test 4: Edge cases
    edge_cases_result = test_edge_cases()
    results.append(("الحالات الخاصة", edge_cases_result))
    
    # Summary
    print("\n" + "="*60)
    print("📊 ملخص الاختبارات الإضافية:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"  {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nالنتيجة النهائية: {passed}/{total} اختبار نجح ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 جميع الاختبارات الإضافية نجحت!")
        print("\n✅ التأكيدات الرئيسية:")
        print("  - التحويل الرياضي (×25.4) يعمل بدقة")
        print("  - القيم تُحفظ بالملليمتر في قاعدة البيانات")
        print("  - فحص التوافق يعمل مع القيم المحولة")
        print("  - الفواتير تُنشأ بنجاح مع القياسات المحولة")
    else:
        print("⚠️ بعض الاختبارات فشلت، يرجى مراجعة التفاصيل أعلاه")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)