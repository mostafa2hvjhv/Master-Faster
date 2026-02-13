#!/usr/bin/env python3
"""
اختبار سريع للتأكد من تطبيق الترتيب حسب المقاس في الخلفية
Quick test to verify size-based sorting implementation in backend
"""

import requests
import json
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

def test_inventory_sorting():
    """اختبار ترتيب عناصر الجرد حسب المقاس"""
    print("🔍 اختبار ترتيب عناصر الجرد...")
    
    try:
        # 1. Get current inventory to see existing sorting
        response = requests.get(f"{BACKEND_URL}/inventory")
        if response.status_code == 200:
            inventory_items = response.json()
            print(f"✅ تم استرجاع {len(inventory_items)} عنصر من الجرد")
            
            # Display first 5 items to check sorting
            print("📋 أول 5 عناصر في الجرد (للتحقق من الترتيب):")
            for i, item in enumerate(inventory_items[:5]):
                inner = item.get('inner_diameter', 0)
                outer = item.get('outer_diameter', 0)
                material = item.get('material_type', 'N/A')
                pieces = item.get('available_pieces', 0)
                print(f"   {i+1}. {material} - قطر داخلي: {inner}, قطر خارجي: {outer}, قطع: {pieces}")
            
            # Check if sorting is applied (inner_diameter ascending, then outer_diameter)
            is_sorted = True
            for i in range(len(inventory_items) - 1):
                current = inventory_items[i]
                next_item = inventory_items[i + 1]
                
                current_inner = current.get('inner_diameter', 0)
                current_outer = current.get('outer_diameter', 0)
                next_inner = next_item.get('inner_diameter', 0)
                next_outer = next_item.get('outer_diameter', 0)
                
                # Check sorting logic: inner_diameter first, then outer_diameter
                if current_inner > next_inner:
                    is_sorted = False
                    break
                elif current_inner == next_inner and current_outer > next_outer:
                    is_sorted = False
                    break
            
            if is_sorted:
                print("✅ الجرد مرتب بشكل صحيح حسب القطر الداخلي ثم الخارجي")
            else:
                print("❌ الجرد غير مرتب بشكل صحيح")
                
        else:
            print(f"❌ فشل في استرجاع الجرد: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في اختبار ترتيب الجرد: {str(e)}")
        return False
    
    # 2. Create new inventory item with smaller size (NBR 5×15)
    print("\n🔧 إنشاء عنصر جرد جديد بمقاس أصغر (NBR 5×15)...")
    
    try:
        new_inventory_item = {
            "material_type": "NBR",
            "inner_diameter": 5.0,
            "outer_diameter": 15.0,
            "available_pieces": 10,
            "min_stock_level": 2,
            "notes": "اختبار الترتيب - يجب أن يظهر أولاً"
        }
        
        response = requests.post(f"{BACKEND_URL}/inventory", json=new_inventory_item)
        if response.status_code == 200:
            print("✅ تم إنشاء عنصر الجرد الجديد بنجاح")
            
            # Get inventory again to check new position
            response = requests.get(f"{BACKEND_URL}/inventory")
            if response.status_code == 200:
                updated_inventory = response.json()
                
                # Check if the new item appears first (smallest inner_diameter)
                first_item = updated_inventory[0]
                if (first_item.get('inner_diameter') == 5.0 and 
                    first_item.get('outer_diameter') == 15.0 and
                    first_item.get('material_type') == 'NBR'):
                    print("✅ العنصر الجديد يظهر في المقدمة كما هو متوقع")
                    return True
                else:
                    print("❌ العنصر الجديد لا يظهر في المقدمة")
                    print(f"   العنصر الأول: {first_item.get('material_type')} {first_item.get('inner_diameter')}×{first_item.get('outer_diameter')}")
                    return False
            else:
                print(f"❌ فشل في استرجاع الجرد المحدث: {response.status_code}")
                return False
        else:
            print(f"❌ فشل في إنشاء عنصر الجرد: {response.status_code}")
            if response.text:
                print(f"   الخطأ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في إنشاء عنصر الجرد: {str(e)}")
        return False

def test_raw_materials_sorting():
    """اختبار ترتيب المواد الخام حسب المقاس"""
    print("\n🔍 اختبار ترتيب المواد الخام...")
    
    try:
        # 1. Get current raw materials to see existing sorting
        response = requests.get(f"{BACKEND_URL}/raw-materials")
        if response.status_code == 200:
            raw_materials = response.json()
            print(f"✅ تم استرجاع {len(raw_materials)} مادة خام")
            
            # Display first 5 items to check sorting
            print("📋 أول 5 مواد خام (للتحقق من الترتيب):")
            for i, item in enumerate(raw_materials[:5]):
                inner = item.get('inner_diameter', 0)
                outer = item.get('outer_diameter', 0)
                material = item.get('material_type', 'N/A')
                unit_code = item.get('unit_code', 'N/A')
                print(f"   {i+1}. {unit_code} ({material}) - قطر داخلي: {inner}, قطر خارجي: {outer}")
            
            # Check if sorting is applied
            is_sorted = True
            for i in range(len(raw_materials) - 1):
                current = raw_materials[i]
                next_item = raw_materials[i + 1]
                
                current_inner = current.get('inner_diameter', 0)
                current_outer = current.get('outer_diameter', 0)
                next_inner = next_item.get('inner_diameter', 0)
                next_outer = next_item.get('outer_diameter', 0)
                
                # Check sorting logic: inner_diameter first, then outer_diameter
                if current_inner > next_inner:
                    is_sorted = False
                    break
                elif current_inner == next_inner and current_outer > next_outer:
                    is_sorted = False
                    break
            
            if is_sorted:
                print("✅ المواد الخام مرتبة بشكل صحيح حسب القطر الداخلي ثم الخارجي")
            else:
                print("❌ المواد الخام غير مرتبة بشكل صحيح")
                
        else:
            print(f"❌ فشل في استرجاع المواد الخام: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في اختبار ترتيب المواد الخام: {str(e)}")
        return False
    
    # 2. Create new raw material with smaller size (NBR 5×15)
    print("\n🔧 إنشاء مادة خام جديدة بمقاس أصغر (NBR 5×15)...")
    
    try:
        new_raw_material = {
            "material_type": "NBR",
            "inner_diameter": 5.0,
            "outer_diameter": 15.0,
            "height": 10.0,
            "pieces_count": 5,
            "cost_per_mm": 2.0
        }
        
        response = requests.post(f"{BACKEND_URL}/raw-materials", json=new_raw_material)
        if response.status_code == 200:
            print("✅ تم إنشاء المادة الخام الجديدة بنجاح")
            created_material = response.json()
            unit_code = created_material.get('unit_code', 'N/A')
            print(f"   كود الوحدة المولد: {unit_code}")
            
            # Get raw materials again to check new position
            response = requests.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                updated_materials = response.json()
                
                # Check if the new item appears first (smallest inner_diameter)
                first_item = updated_materials[0]
                if (first_item.get('inner_diameter') == 5.0 and 
                    first_item.get('outer_diameter') == 15.0 and
                    first_item.get('material_type') == 'NBR'):
                    print("✅ المادة الخام الجديدة تظهر في المقدمة كما هو متوقع")
                    return True
                else:
                    print("❌ المادة الخام الجديدة لا تظهر في المقدمة")
                    print(f"   المادة الأولى: {first_item.get('unit_code')} ({first_item.get('material_type')}) {first_item.get('inner_diameter')}×{first_item.get('outer_diameter')}")
                    return False
            else:
                print(f"❌ فشل في استرجاع المواد الخام المحدثة: {response.status_code}")
                return False
        else:
            print(f"❌ فشل في إنشاء المادة الخام: {response.status_code}")
            if response.text:
                print(f"   الخطأ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في إنشاء المادة الخام: {str(e)}")
        return False

def main():
    """تشغيل جميع اختبارات الترتيب"""
    print("=" * 60)
    print("🧪 اختبار سريع للتأكد من تطبيق الترتيب حسب المقاس في الخلفية")
    print("=" * 60)
    
    results = []
    
    # Test inventory sorting
    inventory_result = test_inventory_sorting()
    results.append(("ترتيب الجرد", inventory_result))
    
    # Test raw materials sorting  
    raw_materials_result = test_raw_materials_sorting()
    results.append(("ترتيب المواد الخام", raw_materials_result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ملخص نتائج الاختبار:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nالنتيجة النهائية: {passed}/{total} اختبار نجح ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 جميع اختبارات الترتيب نجحت! الترتيب يتم في الخلفية بشكل صحيح.")
    else:
        print("⚠️  بعض اختبارات الترتيب فشلت. يحتاج إصلاح في الخلفية.")
    
    return passed == total

if __name__ == "__main__":
    main()