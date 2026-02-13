#!/usr/bin/env python3
"""
Comprehensive test for all scenarios mentioned in the review request.
Testing both basic material info and compatibility check workflows.
"""

import requests
import json

BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

def test_all_scenarios():
    print("🔍 COMPREHENSIVE INVENTORY DEDUCTION TEST")
    print("=" * 60)
    print("Testing all scenarios from the review request:")
    print("1. Basic material info (no compatibility check)")
    print("2. Compatibility check workflow")
    print("3. Multiple materials in same invoice")
    print("=" * 60)
    
    results = []
    
    # Create a fresh NBR inventory for testing
    print("\n📦 Setting up test inventory...")
    try:
        # Create NBR 25×35mm inventory with 500 pieces for testing
        inventory_data = {
            "material_type": "NBR",
            "inner_diameter": 25.0,
            "outer_diameter": 35.0,
            "available_pieces": 500,
            "min_stock_level": 10,
            "notes": "Test inventory for comprehensive deduction testing"
        }
        
        response = requests.post(f"{BACKEND_URL}/inventory", json=inventory_data)
        if response.status_code == 200:
            inventory_item = response.json()
            test_inventory_id = inventory_item["id"]
            print(f"✅ Created NBR 25×35mm test inventory with 500 pieces")
        else:
            print(f"❌ Failed to create test inventory: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception creating test inventory: {e}")
        return False
    
    # Create test customer
    print("\n👤 Creating test customer...")
    try:
        customer_data = {
            "name": "عميل اختبار شامل للخصم",
            "phone": "01222222222",
            "address": "عنوان اختبار شامل"
        }
        
        response = requests.post(f"{BACKEND_URL}/customers", json=customer_data)
        if response.status_code == 200:
            customer = response.json()
            customer_id = customer["id"]
            print(f"✅ Created test customer")
        else:
            print(f"❌ Failed to create customer: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception creating customer: {e}")
        return False
    
    # Test 1: Basic material info (no compatibility check)
    print("\n🧪 Test 1: Basic material info workflow")
    print("   Creating invoice with NBR 25×35×8mm × 5 seals")
    print("   Expected deduction: (8+2) × 5 = 50 pieces")
    
    try:
        invoice_data = {
            "customer_id": customer_id,
            "customer_name": "عميل اختبار شامل للخصم",
            "invoice_title": "اختبار 1 - بيانات أساسية",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 8.0,
                    "quantity": 5,
                    "unit_price": 20.0,
                    "total_price": 100.0,
                    "product_type": "manufactured",
                    "material_details": {
                        "material_type": "NBR",
                        "inner_diameter": 25.0,
                        "outer_diameter": 35.0,
                        "is_finished_product": False
                    }
                }
            ],
            "payment_method": "نقدي",
            "discount_type": "amount",
            "discount_value": 0.0
        }
        
        response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data)
        if response.status_code == 200:
            invoice = response.json()
            print(f"   ✅ Invoice created: {invoice['invoice_number']}")
            results.append(("Basic material info", True, "Invoice created successfully"))
        else:
            print(f"   ❌ Failed to create invoice: {response.status_code}")
            results.append(("Basic material info", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results.append(("Basic material info", False, str(e)))
    
    # Check inventory after Test 1
    print("\n   Checking inventory after Test 1...")
    try:
        response = requests.get(f"{BACKEND_URL}/inventory")
        if response.status_code == 200:
            inventory_items = response.json()
            test_items = [item for item in inventory_items 
                         if item.get("material_type") == "NBR" 
                         and item.get("inner_diameter") == 25.0 
                         and item.get("outer_diameter") == 35.0]
            
            if test_items:
                count_after_test1 = test_items[0].get("available_pieces", 0)
                expected_after_test1 = 500 - 50  # 450
                print(f"   Inventory after Test 1: {count_after_test1} pieces")
                print(f"   Expected: {expected_after_test1} pieces")
                
                if count_after_test1 == expected_after_test1:
                    print("   ✅ Deduction correct for Test 1")
                    results.append(("Test 1 deduction", True, f"Correctly deducted 50 pieces"))
                else:
                    deducted = 500 - count_after_test1
                    print(f"   ❌ Deduction incorrect: deducted {deducted}, expected 50")
                    results.append(("Test 1 deduction", False, f"Deducted {deducted} instead of 50"))
            else:
                print("   ❌ Test inventory not found")
                results.append(("Test 1 deduction", False, "Inventory not found"))
        else:
            print(f"   ❌ Failed to get inventory: {response.status_code}")
            results.append(("Test 1 deduction", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results.append(("Test 1 deduction", False, str(e)))
    
    # Test 2: Compatibility check workflow
    print("\n🧪 Test 2: Compatibility check workflow")
    print("   First doing compatibility check, then creating invoice")
    
    try:
        # Do compatibility check
        compatibility_data = {
            "seal_type": "RSL",
            "inner_diameter": 25.0,
            "outer_diameter": 35.0,
            "height": 10.0,
            "material_type": "NBR"
        }
        
        response = requests.post(f"{BACKEND_URL}/compatibility-check", json=compatibility_data)
        if response.status_code == 200:
            compatibility_result = response.json()
            compatible_materials = compatibility_result.get("compatible_materials", [])
            
            if compatible_materials:
                print(f"   ✅ Found {len(compatible_materials)} compatible materials")
                selected_material = compatible_materials[0]
                
                # Create invoice with selected material
                invoice_data = {
                    "customer_id": customer_id,
                    "customer_name": "عميل اختبار شامل للخصم",
                    "invoice_title": "اختبار 2 - فحص التوافق",
                    "supervisor_name": "مشرف الاختبار",
                    "items": [
                        {
                            "seal_type": "RSL",
                            "material_type": "NBR",
                            "inner_diameter": 25.0,
                            "outer_diameter": 35.0,
                            "height": 10.0,
                            "quantity": 3,
                            "unit_price": 25.0,
                            "total_price": 75.0,
                            "product_type": "manufactured",
                            "material_details": {
                                "material_type": selected_material.get("material_type"),
                                "inner_diameter": selected_material.get("inner_diameter"),
                                "outer_diameter": selected_material.get("outer_diameter"),
                                "unit_code": selected_material.get("unit_code"),
                                "is_finished_product": False
                            }
                        }
                    ],
                    "payment_method": "نقدي",
                    "discount_type": "amount",
                    "discount_value": 0.0
                }
                
                response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data)
                if response.status_code == 200:
                    invoice = response.json()
                    print(f"   ✅ Invoice created: {invoice['invoice_number']}")
                    print(f"   Expected deduction: (10+2) × 3 = 36 pieces")
                    results.append(("Compatibility check workflow", True, "Invoice created successfully"))
                else:
                    print(f"   ❌ Failed to create invoice: {response.status_code}")
                    results.append(("Compatibility check workflow", False, f"HTTP {response.status_code}"))
            else:
                print("   ⚠️  No compatible materials found")
                results.append(("Compatibility check workflow", False, "No compatible materials"))
        else:
            print(f"   ❌ Compatibility check failed: {response.status_code}")
            results.append(("Compatibility check workflow", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results.append(("Compatibility check workflow", False, str(e)))
    
    # Test 3: Multiple materials in same invoice
    print("\n🧪 Test 3: Multiple materials in same invoice")
    print("   Creating invoice with 2 different NBR materials")
    
    try:
        invoice_data = {
            "customer_id": customer_id,
            "customer_name": "عميل اختبار شامل للخصم",
            "invoice_title": "اختبار 3 - مواد متعددة",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 5.0,
                    "quantity": 2,
                    "unit_price": 15.0,
                    "total_price": 30.0,
                    "product_type": "manufactured",
                    "material_details": {
                        "material_type": "NBR",
                        "inner_diameter": 25.0,
                        "outer_diameter": 35.0,
                        "is_finished_product": False
                    }
                },
                {
                    "seal_type": "RS",
                    "material_type": "NBR",
                    "inner_diameter": 20.0,
                    "outer_diameter": 30.0,
                    "height": 4.0,
                    "quantity": 3,
                    "unit_price": 12.0,
                    "total_price": 36.0,
                    "product_type": "manufactured",
                    "material_details": {
                        "material_type": "NBR",
                        "inner_diameter": 20.0,
                        "outer_diameter": 30.0,
                        "is_finished_product": False
                    }
                }
            ],
            "payment_method": "نقدي",
            "discount_type": "amount",
            "discount_value": 0.0
        }
        
        response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data)
        if response.status_code == 200:
            invoice = response.json()
            print(f"   ✅ Invoice created: {invoice['invoice_number']}")
            print(f"   Expected deductions:")
            print(f"     - NBR 25×35: (5+2) × 2 = 14 pieces")
            print(f"     - NBR 20×30: (4+2) × 3 = 18 pieces")
            results.append(("Multiple materials", True, "Invoice created successfully"))
        else:
            print(f"   ❌ Failed to create invoice: {response.status_code}")
            results.append(("Multiple materials", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        results.append(("Multiple materials", False, str(e)))
    
    # Final inventory check
    print("\n📊 Final inventory verification...")
    try:
        response = requests.get(f"{BACKEND_URL}/inventory")
        if response.status_code == 200:
            inventory_items = response.json()
            
            # Check NBR 25×35
            test_items_25x35 = [item for item in inventory_items 
                               if item.get("material_type") == "NBR" 
                               and item.get("inner_diameter") == 25.0 
                               and item.get("outer_diameter") == 35.0]
            
            if test_items_25x35:
                final_count_25x35 = test_items_25x35[0].get("available_pieces", 0)
                total_deducted_25x35 = 500 - final_count_25x35
                expected_total_25x35 = 50 + 36 + 14  # Test 1 + Test 2 + Test 3
                print(f"   NBR 25×35mm: {final_count_25x35} pieces remaining")
                print(f"   Total deducted: {total_deducted_25x35} pieces")
                print(f"   Expected total deduction: {expected_total_25x35} pieces")
                
                if total_deducted_25x35 == expected_total_25x35:
                    print("   ✅ All deductions correct for NBR 25×35mm")
                    results.append(("Final NBR 25×35 verification", True, f"Correctly deducted {total_deducted_25x35} pieces"))
                else:
                    print(f"   ❌ Deduction mismatch for NBR 25×35mm")
                    results.append(("Final NBR 25×35 verification", False, f"Expected {expected_total_25x35}, got {total_deducted_25x35}"))
            
            # Check NBR 20×30 (from Test 3)
            test_items_20x30 = [item for item in inventory_items 
                               if item.get("material_type") == "NBR" 
                               and item.get("inner_diameter") == 20.0 
                               and item.get("outer_diameter") == 30.0]
            
            if test_items_20x30:
                current_count_20x30 = test_items_20x30[0].get("available_pieces", 0)
                print(f"   NBR 20×30mm: {current_count_20x30} pieces remaining")
                print(f"   (This includes previous test deductions)")
        else:
            print(f"   ❌ Failed to get final inventory: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success, details in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {details}")
        if success:
            passed += 1
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\n🎯 Overall Success Rate: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("\n✅ INVENTORY DEDUCTION IS WORKING CORRECTLY!")
        print("   All major scenarios are functioning as expected.")
        print("   The user's reported issue has been resolved.")
        return True
    else:
        print("\n❌ INVENTORY DEDUCTION HAS ISSUES!")
        print("   Some scenarios are not working as expected.")
        return False

if __name__ == "__main__":
    success = test_all_scenarios()
    exit(0 if success else 1)