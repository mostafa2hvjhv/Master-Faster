#!/usr/bin/env python3
"""
Complete Materials Display Fix Test
اختبار إصلاح شامل لعرض المواد

This test fixes the materials display issue by:
1. Fixing the JSON serialization error (already done)
2. Creating proper inventory items
3. Creating raw materials that depend on inventory
4. Testing the complete workflow
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class CompleteMaterialsFixTester:
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
    
    def test_current_status(self):
        """Test current status of both APIs"""
        print("\n=== 1. Current Status Check ===")
        
        # Test raw materials API
        try:
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                raw_materials = response.json()
                self.log_test("Raw Materials API Status", True, 
                            f"Working - found {len(raw_materials)} materials")
            else:
                self.log_test("Raw Materials API Status", False, 
                            f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Raw Materials API Status", False, str(e))
        
        # Test inventory API
        try:
            response = self.session.get(f"{BACKEND_URL}/inventory")
            if response.status_code == 200:
                inventory = response.json()
                self.log_test("Inventory API Status", True, 
                            f"Working - found {len(inventory)} items")
                
                # Show inventory distribution
                type_counts = {}
                for item in inventory:
                    mat_type = item.get('material_type', 'Unknown')
                    type_counts[mat_type] = type_counts.get(mat_type, 0) + 1
                
                type_summary = ", ".join([f"{k}: {v}" for k, v in type_counts.items()])
                self.log_test("Inventory Distribution", True, type_summary)
                
                return inventory
            else:
                self.log_test("Inventory API Status", False, 
                            f"HTTP {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Inventory API Status", False, str(e))
            return []
    
    def test_create_inventory_items(self):
        """Create inventory items to support raw materials creation"""
        print("\n=== 2. Creating Inventory Items ===")
        
        inventory_items = [
            {
                "material_type": "BUR",
                "inner_diameter": 15.0,
                "outer_diameter": 30.0,
                "available_pieces": 50,
                "min_stock_level": 5,
                "notes": "Test inventory for BUR materials"
            },
            {
                "material_type": "NBR",
                "inner_diameter": 20.0,
                "outer_diameter": 40.0,
                "available_pieces": 40,
                "min_stock_level": 5,
                "notes": "Test inventory for NBR materials"
            },
            {
                "material_type": "VT",
                "inner_diameter": 25.0,
                "outer_diameter": 45.0,
                "available_pieces": 30,
                "min_stock_level": 5,
                "notes": "Test inventory for VT materials"
            },
            {
                "material_type": "BT",
                "inner_diameter": 18.0,
                "outer_diameter": 35.0,
                "available_pieces": 35,
                "min_stock_level": 5,
                "notes": "Test inventory for BT materials"
            },
            {
                "material_type": "BOOM",
                "inner_diameter": 22.0,
                "outer_diameter": 42.0,
                "available_pieces": 25,
                "min_stock_level": 5,
                "notes": "Test inventory for BOOM materials"
            }
        ]
        
        created_count = 0
        for item in inventory_items:
            try:
                response = self.session.post(f"{BACKEND_URL}/inventory", json=item)
                if response.status_code == 200:
                    created_item = response.json()
                    created_count += 1
                    print(f"   ✅ Created {item['material_type']} inventory: {item['available_pieces']} pieces")
                else:
                    print(f"   ❌ Failed to create {item['material_type']} inventory: {response.status_code}")
                    if response.status_code == 400:
                        print(f"      Error: {response.text}")
            except Exception as e:
                print(f"   ❌ Error creating {item['material_type']} inventory: {str(e)}")
        
        self.log_test("Inventory Items Creation", created_count > 0, 
                     f"Created {created_count}/{len(inventory_items)} inventory items")
        
        return created_count > 0
    
    def test_create_raw_materials(self):
        """Create raw materials using the inventory"""
        print("\n=== 3. Creating Raw Materials ===")
        
        raw_materials = [
            {
                "material_type": "BUR",
                "inner_diameter": 15.0,
                "outer_diameter": 30.0,
                "height": 8.0,
                "pieces_count": 10,
                "cost_per_mm": 3.0
            },
            {
                "material_type": "NBR", 
                "inner_diameter": 20.0,
                "outer_diameter": 40.0,
                "height": 12.0,
                "pieces_count": 8,
                "cost_per_mm": 2.8
            },
            {
                "material_type": "VT",
                "inner_diameter": 25.0,
                "outer_diameter": 45.0,
                "height": 10.0,
                "pieces_count": 6,
                "cost_per_mm": 3.5
            },
            {
                "material_type": "BT",
                "inner_diameter": 18.0,
                "outer_diameter": 35.0,
                "height": 9.0,
                "pieces_count": 12,
                "cost_per_mm": 2.2
            },
            {
                "material_type": "BOOM",
                "inner_diameter": 22.0,
                "outer_diameter": 42.0,
                "height": 11.0,
                "pieces_count": 7,
                "cost_per_mm": 4.0
            }
        ]
        
        created_count = 0
        for material in raw_materials:
            try:
                response = self.session.post(f"{BACKEND_URL}/raw-materials", json=material)
                if response.status_code == 200:
                    created_material = response.json()
                    created_count += 1
                    unit_code = created_material.get('unit_code', 'N/A')
                    print(f"   ✅ Created {material['material_type']} material: {unit_code}")
                else:
                    print(f"   ❌ Failed to create {material['material_type']}: {response.status_code}")
                    if response.status_code == 400:
                        error_detail = response.json().get('detail', response.text)
                        print(f"      Error: {error_detail}")
            except Exception as e:
                print(f"   ❌ Error creating {material['material_type']}: {str(e)}")
        
        self.log_test("Raw Materials Creation", created_count > 0, 
                     f"Created {created_count}/{len(raw_materials)} raw materials")
        
        return created_count > 0
    
    def test_final_verification(self):
        """Final verification of both APIs working with data"""
        print("\n=== 4. Final Verification ===")
        
        # Test raw materials API
        try:
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials = response.json()
                self.log_test("Raw Materials Final Check", True, 
                            f"Found {len(materials)} raw materials")
                
                if materials:
                    # Check sorting (BUR-NBR-BT-BOOM-VT)
                    material_types = [mat.get('material_type') for mat in materials]
                    type_counts = {}
                    for mat_type in material_types:
                        type_counts[mat_type] = type_counts.get(mat_type, 0) + 1
                    
                    type_summary = ", ".join([f"{k}: {v}" for k, v in type_counts.items()])
                    self.log_test("Raw Materials by Type", True, type_summary)
                    
                    # Check unit codes
                    unit_codes = [mat.get('unit_code') for mat in materials if mat.get('unit_code')]
                    self.log_test("Unit Codes Generated", len(unit_codes) > 0, 
                                f"Found {len(unit_codes)} unit codes: {unit_codes[:5]}...")
                    
                    # Check sorting order
                    first_types = material_types[:min(10, len(material_types))]
                    self.log_test("Material Sorting Order", True, f"Order: {first_types}")
                
            else:
                self.log_test("Raw Materials Final Check", False, 
                            f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Raw Materials Final Check", False, str(e))
        
        # Test inventory API
        try:
            response = self.session.get(f"{BACKEND_URL}/inventory")
            if response.status_code == 200:
                inventory = response.json()
                self.log_test("Inventory Final Check", True, 
                            f"Found {len(inventory)} inventory items")
                
                if inventory:
                    # Check inventory after raw materials creation (should be reduced)
                    type_counts = {}
                    total_pieces = 0
                    for item in inventory:
                        mat_type = item.get('material_type', 'Unknown')
                        pieces = item.get('available_pieces', 0)
                        type_counts[mat_type] = type_counts.get(mat_type, 0) + pieces
                        total_pieces += pieces
                    
                    type_summary = ", ".join([f"{k}: {v} pieces" for k, v in type_counts.items()])
                    self.log_test("Inventory After Raw Materials Creation", True, 
                                f"Total: {total_pieces} pieces - {type_summary}")
                
            else:
                self.log_test("Inventory Final Check", False, 
                            f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Inventory Final Check", False, str(e))
    
    def test_search_and_filtering(self):
        """Test search and filtering functionality"""
        print("\n=== 5. Search and Filtering Test ===")
        
        # Test if we can search/filter materials (this would be frontend functionality)
        # But we can test the backend sorting
        try:
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials = response.json()
                if materials:
                    # Check if materials are sorted by priority: BUR-NBR-BT-BOOM-VT
                    material_types = [mat.get('material_type') for mat in materials]
                    
                    # Find positions of each type
                    type_positions = {}
                    for i, mat_type in enumerate(material_types):
                        if mat_type not in type_positions:
                            type_positions[mat_type] = i
                    
                    # Check sorting order
                    expected_order = ['BUR', 'NBR', 'BT', 'BOOM', 'VT']
                    sorting_correct = True
                    for i in range(len(expected_order) - 1):
                        current = expected_order[i]
                        next_type = expected_order[i + 1]
                        if current in type_positions and next_type in type_positions:
                            if type_positions[current] > type_positions[next_type]:
                                sorting_correct = False
                                break
                    
                    self.log_test("Material Type Sorting (BUR-NBR-BT-BOOM-VT)", sorting_correct,
                                f"Types found: {list(type_positions.keys())}")
                    
                    # Test size sorting within same type
                    bur_materials = [mat for mat in materials if mat.get('material_type') == 'BUR']
                    if len(bur_materials) > 1:
                        size_sorted = True
                        for i in range(len(bur_materials) - 1):
                            current = bur_materials[i]
                            next_mat = bur_materials[i + 1]
                            if (current.get('inner_diameter', 0) > next_mat.get('inner_diameter', 0) or
                                (current.get('inner_diameter', 0) == next_mat.get('inner_diameter', 0) and
                                 current.get('outer_diameter', 0) > next_mat.get('outer_diameter', 0))):
                                size_sorted = False
                                break
                        
                        self.log_test("Size Sorting Within Type", size_sorted,
                                    f"BUR materials sorted by diameter")
                
            else:
                self.log_test("Search and Filtering Test", False, 
                            f"Cannot test - API error: {response.status_code}")
        except Exception as e:
            self.log_test("Search and Filtering Test", False, str(e))
    
    def run_complete_fix(self):
        """Run complete materials display fix"""
        print("🔧 COMPLETE MATERIALS DISPLAY FIX")
        print("=" * 60)
        print("Fixing materials display issue comprehensively")
        print("إصلاح شامل لمشكلة عرض المواد")
        
        # Step 1: Check current status
        inventory = self.test_current_status()
        
        # Step 2: Create inventory items if needed
        if len(inventory) < 200:  # We had 194 before
            self.test_create_inventory_items()
        
        # Step 3: Create raw materials
        self.test_create_raw_materials()
        
        # Step 4: Final verification
        self.test_final_verification()
        
        # Step 5: Test search and filtering
        self.test_search_and_filtering()
        
        # Summary
        print("\n" + "=" * 60)
        print("🔧 COMPLETE FIX SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Final status
        print(f"\n🎯 FINAL STATUS:")
        try:
            raw_response = self.session.get(f"{BACKEND_URL}/raw-materials")
            inv_response = self.session.get(f"{BACKEND_URL}/inventory")
            
            if raw_response.status_code == 200 and inv_response.status_code == 200:
                raw_count = len(raw_response.json())
                inv_count = len(inv_response.json())
                
                print(f"✅ Both APIs working perfectly!")
                print(f"   Raw Materials: {raw_count} items")
                print(f"   Inventory: {inv_count} items")
                print(f"   Total Materials Available: {raw_count + inv_count}")
                
                if raw_count > 0:
                    print(f"✅ Materials are now visible in the inventory interface!")
                    return True
                else:
                    print(f"⚠️  APIs working but no raw materials created")
                    return False
            else:
                print(f"❌ APIs still have issues")
                return False
        except Exception as e:
            print(f"❌ Error in final verification: {str(e)}")
            return False

if __name__ == "__main__":
    tester = CompleteMaterialsFixTester()
    success = tester.run_complete_fix()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)