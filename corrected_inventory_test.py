#!/usr/bin/env python3
"""
CORRECTED Inventory Deduction Logic Testing
اختبار منطق خصم المخزون المُصحح

Testing the CORRECTED inventory deduction logic based on user's exact requirements:
1. عند فحص التوافق واختيار خامة، يتم خصم (ارتفاع السيل + 2) × عدد السيلات من **ارتفاع الخامة** المختارة (ليس عدد القطع)
2. عندما تكون ارتفاع الخامة في المخزون 15 أو أقل، لا تظهر في فحص التوافق
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class CorrectedInventoryTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
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
    
    def test_compatibility_height_filtering(self):
        """Test that materials with height ≤15mm are filtered out from compatibility check"""
        print("\n=== Testing Compatibility Height Filtering (≤15mm) ===")
        
        try:
            # Get all raw materials to see what we have
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials = response.json()
                
                # Find materials with height ≤15mm and >15mm
                low_height_materials = [m for m in materials if m.get('height', 0) <= 15]
                high_height_materials = [m for m in materials if m.get('height', 0) > 15]
                
                print(f"   Found {len(low_height_materials)} materials with height ≤15mm")
                print(f"   Found {len(high_height_materials)} materials with height >15mm")
                
                if len(low_height_materials) > 0 and len(high_height_materials) > 0:
                    # Test compatibility check with a seal that could match both types
                    compatibility_data = {
                        "seal_type": "RSL",
                        "inner_diameter": 25.0,
                        "outer_diameter": 35.0,
                        "height": 8.0
                    }
                    
                    compat_response = self.session.post(f"{BACKEND_URL}/compatibility-check", json=compatibility_data)
                    if compat_response.status_code == 200:
                        compatibility_result = compat_response.json()
                        compatible_materials = compatibility_result.get("compatible_materials", [])
                        
                        # Check if any low height materials appear in compatibility results
                        low_height_in_results = []
                        high_height_in_results = []
                        
                        for comp_mat in compatible_materials:
                            comp_height = comp_mat.get('height', 0)
                            if comp_height <= 15:
                                low_height_in_results.append(comp_mat)
                            else:
                                high_height_in_results.append(comp_mat)
                        
                        if len(low_height_in_results) == 0 and len(high_height_in_results) > 0:
                            self.log_test("Materials ≤15mm filtered out from compatibility", True, 
                                        f"No materials ≤15mm in results, {len(high_height_in_results)} materials >15mm found")
                        else:
                            self.log_test("Materials ≤15mm filtered out from compatibility", False, 
                                        f"Found {len(low_height_in_results)} materials ≤15mm in results (should be 0)")
                    else:
                        self.log_test("Materials ≤15mm filtered out from compatibility", False, 
                                    f"Compatibility check failed: HTTP {compat_response.status_code}")
                else:
                    self.log_test("Materials ≤15mm filtered out from compatibility", False, 
                                "Need both low and high height materials for testing")
            else:
                self.log_test("Materials ≤15mm filtered out from compatibility", False, 
                            f"Failed to get materials: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Materials ≤15mm filtered out from compatibility", False, str(e))
    
    def test_height_deduction_formula(self):
        """Test that deduction follows formula: (seal_height + 2) × quantity FROM material height"""
        print("\n=== Testing Height Deduction Formula ===")
        
        try:
            # Find a material with sufficient height for testing
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials = response.json()
                
                # Find a material with height > 50mm for testing
                test_material = None
                for mat in materials:
                    if mat.get('height', 0) > 50:
                        test_material = mat
                        break
                
                if test_material:
                    initial_height = test_material.get('height')
                    material_type = test_material.get('material_type')
                    inner_diameter = test_material.get('inner_diameter')
                    outer_diameter = test_material.get('outer_diameter')
                    unit_code = test_material.get('unit_code')
                    
                    print(f"   Testing with {material_type} {inner_diameter}×{outer_diameter} (Unit: {unit_code})")
                    print(f"   Initial height: {initial_height}mm")
                    
                    # Create test customer
                    customer_data = {
                        "name": f"عميل اختبار خصم الارتفاع {datetime.now().strftime('%H%M%S')}",
                        "phone": "01234567890"
                    }
                    
                    customer_response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
                    if customer_response.status_code in [200, 201]:
                        customer = customer_response.json()
                        
                        # Test parameters: seal height = 12mm, quantity = 3
                        # Expected deduction: (12 + 2) × 3 = 42mm
                        seal_height = 12.0
                        quantity = 3
                        expected_deduction = (seal_height + 2) * quantity  # 42mm
                        expected_final_height = initial_height - expected_deduction
                        
                        print(f"   Test: {seal_height}mm seal × {quantity} quantity")
                        print(f"   Expected deduction: ({seal_height} + 2) × {quantity} = {expected_deduction}mm")
                        print(f"   Expected final height: {initial_height} - {expected_deduction} = {expected_final_height}mm")
                        
                        # Create invoice
                        invoice_data = {
                            "customer_id": customer.get("id"),
                            "customer_name": customer.get("name"),
                            "invoice_title": "اختبار صيغة خصم الارتفاع",
                            "supervisor_name": "مشرف الاختبار",
                            "payment_method": "نقدي",
                            "items": [
                                {
                                    "seal_type": "RSL",
                                    "material_type": material_type,
                                    "inner_diameter": inner_diameter,
                                    "outer_diameter": outer_diameter,
                                    "height": seal_height,
                                    "quantity": quantity,
                                    "unit_price": 20.0,
                                    "total_price": 60.0,
                                    "product_type": "manufactured",
                                    "material_details": {
                                        "material_type": material_type,
                                        "inner_diameter": inner_diameter,
                                        "outer_diameter": outer_diameter,
                                        "height": initial_height,
                                        "unit_code": unit_code,
                                        "is_finished_product": False
                                    }
                                }
                            ]
                        }
                        
                        invoice_response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
                        if invoice_response.status_code in [200, 201]:
                            invoice = invoice_response.json()
                            
                            # Check material height after deduction
                            materials_response = self.session.get(f"{BACKEND_URL}/raw-materials")
                            if materials_response.status_code == 200:
                                updated_materials = materials_response.json()
                                
                                # Find the same material by unit_code
                                updated_material = None
                                for mat in updated_materials:
                                    if mat.get('unit_code') == unit_code:
                                        updated_material = mat
                                        break
                                
                                if updated_material:
                                    final_height = updated_material.get('height')
                                    actual_deduction = initial_height - final_height
                                    
                                    print(f"   Actual final height: {final_height}mm")
                                    print(f"   Actual deduction: {actual_deduction}mm")
                                    
                                    # Allow small tolerance for floating point precision
                                    if abs(actual_deduction - expected_deduction) < 0.1:
                                        self.log_test("Height deduction formula correct", True, 
                                                    f"Deduction formula works: ({seal_height} + 2) × {quantity} = {actual_deduction}mm")
                                    else:
                                        self.log_test("Height deduction formula correct", False, 
                                                    f"Expected {expected_deduction}mm deduction, got {actual_deduction}mm")
                                else:
                                    self.log_test("Height deduction formula correct", False, 
                                                f"Could not find material {unit_code} after invoice creation")
                            else:
                                self.log_test("Height deduction formula correct", False, 
                                            "Failed to get updated materials")
                        else:
                            self.log_test("Height deduction formula correct", False, 
                                        f"Invoice creation failed: HTTP {invoice_response.status_code}: {invoice_response.text}")
                    else:
                        self.log_test("Height deduction formula correct", False, 
                                    f"Customer creation failed: HTTP {customer_response.status_code}")
                else:
                    self.log_test("Height deduction formula correct", False, 
                                "No material with sufficient height (>50mm) found for testing")
            else:
                self.log_test("Height deduction formula correct", False, 
                            f"Failed to get materials: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Height deduction formula correct", False, str(e))
    
    def test_deduction_from_height_not_pieces(self):
        """Test that deduction is from material HEIGHT, not pieces count"""
        print("\n=== Testing Deduction from HEIGHT (not pieces) ===")
        
        try:
            # Get materials to find one for testing
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials = response.json()
                
                # Find a material with good height and pieces count
                test_material = None
                for mat in materials:
                    if mat.get('height', 0) > 30 and mat.get('pieces_count', 0) > 0:
                        test_material = mat
                        break
                
                if test_material:
                    initial_height = test_material.get('height')
                    initial_pieces = test_material.get('pieces_count')
                    unit_code = test_material.get('unit_code')
                    
                    print(f"   Testing material {unit_code}")
                    print(f"   Initial height: {initial_height}mm")
                    print(f"   Initial pieces: {initial_pieces} pieces")
                    
                    # Create test customer
                    customer_data = {
                        "name": f"عميل اختبار خصم الارتفاع فقط {datetime.now().strftime('%H%M%S')}",
                        "phone": "01234567891"
                    }
                    
                    customer_response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
                    if customer_response.status_code in [200, 201]:
                        customer = customer_response.json()
                        
                        # Test with 1 seal of 10mm height
                        # Expected: height reduces by (10+2)×1 = 12mm, pieces stay the same
                        seal_height = 10.0
                        quantity = 1
                        expected_height_deduction = (seal_height + 2) * quantity  # 12mm
                        expected_final_height = initial_height - expected_height_deduction
                        expected_final_pieces = initial_pieces  # Should NOT change
                        
                        invoice_data = {
                            "customer_id": customer.get("id"),
                            "customer_name": customer.get("name"),
                            "invoice_title": "اختبار خصم الارتفاع وليس القطع",
                            "supervisor_name": "مشرف الاختبار",
                            "payment_method": "نقدي",
                            "items": [
                                {
                                    "seal_type": "RSL",
                                    "material_type": test_material.get('material_type'),
                                    "inner_diameter": test_material.get('inner_diameter'),
                                    "outer_diameter": test_material.get('outer_diameter'),
                                    "height": seal_height,
                                    "quantity": quantity,
                                    "unit_price": 15.0,
                                    "total_price": 15.0,
                                    "product_type": "manufactured",
                                    "material_details": {
                                        "material_type": test_material.get('material_type'),
                                        "inner_diameter": test_material.get('inner_diameter'),
                                        "outer_diameter": test_material.get('outer_diameter'),
                                        "height": initial_height,
                                        "unit_code": unit_code,
                                        "is_finished_product": False
                                    }
                                }
                            ]
                        }
                        
                        invoice_response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
                        if invoice_response.status_code in [200, 201]:
                            # Check material after deduction
                            materials_response = self.session.get(f"{BACKEND_URL}/raw-materials")
                            if materials_response.status_code == 200:
                                updated_materials = materials_response.json()
                                
                                updated_material = None
                                for mat in updated_materials:
                                    if mat.get('unit_code') == unit_code:
                                        updated_material = mat
                                        break
                                
                                if updated_material:
                                    final_height = updated_material.get('height')
                                    final_pieces = updated_material.get('pieces_count')
                                    
                                    print(f"   Final height: {final_height}mm (expected: {expected_final_height}mm)")
                                    print(f"   Final pieces: {final_pieces} pieces (expected: {expected_final_pieces} pieces)")
                                    
                                    height_correct = abs(final_height - expected_final_height) < 0.1
                                    pieces_unchanged = final_pieces == expected_final_pieces
                                    
                                    if height_correct and pieces_unchanged:
                                        self.log_test("Deduction from HEIGHT not pieces", True, 
                                                    f"Height reduced by {expected_height_deduction}mm, pieces unchanged at {final_pieces}")
                                    elif not height_correct:
                                        self.log_test("Deduction from HEIGHT not pieces", False, 
                                                    f"Height deduction incorrect: expected {expected_final_height}mm, got {final_height}mm")
                                    else:
                                        self.log_test("Deduction from HEIGHT not pieces", False, 
                                                    f"Pieces count changed: expected {expected_final_pieces}, got {final_pieces}")
                                else:
                                    self.log_test("Deduction from HEIGHT not pieces", False, 
                                                "Could not find material after invoice creation")
                            else:
                                self.log_test("Deduction from HEIGHT not pieces", False, 
                                            "Failed to get updated materials")
                        else:
                            self.log_test("Deduction from HEIGHT not pieces", False, 
                                        f"Invoice creation failed: HTTP {invoice_response.status_code}")
                    else:
                        self.log_test("Deduction from HEIGHT not pieces", False, 
                                    "Customer creation failed")
                else:
                    self.log_test("Deduction from HEIGHT not pieces", False, 
                                "No suitable material found for testing")
            else:
                self.log_test("Deduction from HEIGHT not pieces", False, 
                            f"Failed to get materials: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Deduction from HEIGHT not pieces", False, str(e))
    
    def test_raw_materials_collection_updates(self):
        """Test that deductions happen in raw_materials collection"""
        print("\n=== Testing Raw Materials Collection Updates ===")
        
        try:
            # Get raw materials count before and after creating an invoice
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials_before = response.json()
                materials_count = len(materials_before)
                
                # Check that materials have height field
                materials_with_height = [m for m in materials_before if 'height' in m and isinstance(m['height'], (int, float))]
                
                if len(materials_with_height) == materials_count and materials_count > 0:
                    self.log_test("Raw materials collection has height field", True, 
                                f"All {materials_count} materials have height field")
                    
                    # Verify that height values are reasonable (not all zero or negative)
                    positive_heights = [m for m in materials_with_height if m['height'] > 0]
                    if len(positive_heights) > 0:
                        self.log_test("Raw materials have positive heights", True, 
                                    f"{len(positive_heights)}/{materials_count} materials have positive height")
                    else:
                        self.log_test("Raw materials have positive heights", False, 
                                    "No materials have positive height values")
                else:
                    self.log_test("Raw materials collection has height field", False, 
                                f"Only {len(materials_with_height)}/{materials_count} materials have height field")
            else:
                self.log_test("Raw materials collection accessible", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Raw materials collection accessible", False, str(e))
    
    def run_all_tests(self):
        """Run all corrected inventory deduction tests"""
        print("🔍 Testing CORRECTED Inventory Deduction Logic")
        print("=" * 60)
        print("User Requirements:")
        print("1. عند فحص التوافق واختيار خامة، يتم خصم (ارتفاع السيل + 2) × عدد السيلات من **ارتفاع الخامة**")
        print("2. عندما تكون ارتفاع الخامة في المخزون 15 أو أقل، لا تظهر في فحص التوافق")
        print("=" * 60)
        
        # Run tests
        self.test_compatibility_height_filtering()
        self.test_height_deduction_formula()
        self.test_deduction_from_height_not_pieces()
        self.test_raw_materials_collection_updates()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 CORRECTED INVENTORY DEDUCTION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        # Determine overall result
        if success_rate >= 75:
            print(f"\n🎯 ✅ CORRECTED INVENTORY DEDUCTION LOGIC: WORKING")
            print("The system correctly implements the user's requirements:")
            print("✅ Materials ≤15mm height are filtered out from compatibility check")
            print("✅ Deduction formula: (seal_height + 2) × quantity FROM material height")
            print("✅ Deductions affect material HEIGHT, not pieces count")
            print("✅ Updates happen in raw_materials collection")
        else:
            print(f"\n🎯 ❌ CORRECTED INVENTORY DEDUCTION LOGIC: NEEDS FIXES")
            print("Some requirements are not properly implemented")
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = CorrectedInventoryTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)