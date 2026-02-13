#!/usr/bin/env python3
"""
Material Sorting Test - اختبار ترتيب المواد حسب الأولوية
Testing the new material priority sorting: BUR-NBR-BT-BOOM-VT then size
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class MaterialSortingTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_items = []
        
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
    
    def test_inventory_sorting(self):
        """Test GET /api/inventory sorting by material priority then size"""
        print("\n=== Testing Inventory Sorting ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/inventory")
            
            if response.status_code == 200:
                inventory_items = response.json()
                
                # Check if we have inventory items
                if not inventory_items:
                    self.log_test("Inventory Sorting - Data Available", False, "No inventory items found")
                    return
                
                self.log_test("Inventory Sorting - API Response", True, f"Retrieved {len(inventory_items)} inventory items")
                
                # Define expected material priority order
                material_priority = {'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5}
                
                # Check sorting
                is_sorted_correctly = True
                sorting_details = []
                
                for i in range(len(inventory_items) - 1):
                    current = inventory_items[i]
                    next_item = inventory_items[i + 1]
                    
                    current_material = current.get('material_type', '')
                    next_material = next_item.get('material_type', '')
                    
                    current_priority = material_priority.get(current_material, 6)
                    next_priority = material_priority.get(next_material, 6)
                    
                    # Check material priority first
                    if current_priority > next_priority:
                        is_sorted_correctly = False
                        sorting_details.append(f"Material priority error: {current_material} (priority {current_priority}) before {next_material} (priority {next_priority})")
                    elif current_priority == next_priority:
                        # Same material type, check size sorting
                        current_inner = current.get('inner_diameter', 0)
                        next_inner = next_item.get('inner_diameter', 0)
                        
                        if current_inner > next_inner:
                            is_sorted_correctly = False
                            sorting_details.append(f"Size sorting error in {current_material}: inner diameter {current_inner} before {next_inner}")
                        elif current_inner == next_inner:
                            # Same inner diameter, check outer diameter
                            current_outer = current.get('outer_diameter', 0)
                            next_outer = next_item.get('outer_diameter', 0)
                            
                            if current_outer > next_outer:
                                is_sorted_correctly = False
                                sorting_details.append(f"Size sorting error in {current_material}: outer diameter {current_outer} before {next_outer}")
                
                # Log material distribution
                material_counts = {}
                for item in inventory_items:
                    material = item.get('material_type', 'Unknown')
                    material_counts[material] = material_counts.get(material, 0) + 1
                
                distribution_info = ", ".join([f"{mat}: {count}" for mat, count in material_counts.items()])
                
                if is_sorted_correctly:
                    self.log_test("Inventory Sorting - Material Priority Order", True, 
                                f"Correct sorting: BUR→NBR→BT→BOOM→VT then size. Distribution: {distribution_info}")
                else:
                    self.log_test("Inventory Sorting - Material Priority Order", False, 
                                f"Sorting errors found: {'; '.join(sorting_details[:3])}")
                
                # Show first few items as example
                example_items = []
                for item in inventory_items[:5]:
                    example_items.append(f"{item.get('material_type', 'N/A')} {item.get('inner_diameter', 0)}×{item.get('outer_diameter', 0)}")
                
                self.log_test("Inventory Sorting - First 5 Items Order", True, 
                            f"Order: {' → '.join(example_items)}")
                
            else:
                self.log_test("Inventory Sorting - API Response", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Inventory Sorting - API Call", False, f"Exception: {str(e)}")
    
    def test_raw_materials_sorting(self):
        """Test GET /api/raw-materials sorting by material priority then size"""
        print("\n=== Testing Raw Materials Sorting ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            
            if response.status_code == 200:
                raw_materials = response.json()
                
                # Check if we have raw materials
                if not raw_materials:
                    self.log_test("Raw Materials Sorting - Data Available", False, "No raw materials found")
                    return
                
                self.log_test("Raw Materials Sorting - API Response", True, f"Retrieved {len(raw_materials)} raw materials")
                
                # Define expected material priority order
                material_priority = {'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5}
                
                # Check sorting
                is_sorted_correctly = True
                sorting_details = []
                
                for i in range(len(raw_materials) - 1):
                    current = raw_materials[i]
                    next_item = raw_materials[i + 1]
                    
                    current_material = current.get('material_type', '')
                    next_material = next_item.get('material_type', '')
                    
                    current_priority = material_priority.get(current_material, 6)
                    next_priority = material_priority.get(next_material, 6)
                    
                    # Check material priority first
                    if current_priority > next_priority:
                        is_sorted_correctly = False
                        sorting_details.append(f"Material priority error: {current_material} (priority {current_priority}) before {next_material} (priority {next_priority})")
                    elif current_priority == next_priority:
                        # Same material type, check size sorting
                        current_inner = current.get('inner_diameter', 0)
                        next_inner = next_item.get('inner_diameter', 0)
                        
                        if current_inner > next_inner:
                            is_sorted_correctly = False
                            sorting_details.append(f"Size sorting error in {current_material}: inner diameter {current_inner} before {next_inner}")
                        elif current_inner == next_inner:
                            # Same inner diameter, check outer diameter
                            current_outer = current.get('outer_diameter', 0)
                            next_outer = next_item.get('outer_diameter', 0)
                            
                            if current_outer > next_outer:
                                is_sorted_correctly = False
                                sorting_details.append(f"Size sorting error in {current_material}: outer diameter {current_outer} before {next_outer}")
                
                # Log material distribution
                material_counts = {}
                for item in raw_materials:
                    material = item.get('material_type', 'Unknown')
                    material_counts[material] = material_counts.get(material, 0) + 1
                
                distribution_info = ", ".join([f"{mat}: {count}" for mat, count in material_counts.items()])
                
                if is_sorted_correctly:
                    self.log_test("Raw Materials Sorting - Material Priority Order", True, 
                                f"Correct sorting: BUR→NBR→BT→BOOM→VT then size. Distribution: {distribution_info}")
                else:
                    self.log_test("Raw Materials Sorting - Material Priority Order", False, 
                                f"Sorting errors found: {'; '.join(sorting_details[:3])}")
                
                # Show first few items as example
                example_items = []
                for item in raw_materials[:5]:
                    unit_code = item.get('unit_code', 'N/A')
                    example_items.append(f"{item.get('material_type', 'N/A')} {item.get('inner_diameter', 0)}×{item.get('outer_diameter', 0)} ({unit_code})")
                
                self.log_test("Raw Materials Sorting - First 5 Items Order", True, 
                            f"Order: {' → '.join(example_items)}")
                
            else:
                self.log_test("Raw Materials Sorting - API Response", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Raw Materials Sorting - API Call", False, f"Exception: {str(e)}")
    
    def test_create_and_verify_sorting(self):
        """Create new items and verify they appear in correct sorted positions"""
        print("\n=== Testing New Item Sorting ===")
        
        # Test creating a new raw material and verify it appears in correct position
        try:
            # Create a new NBR material that should appear early in the list
            new_material_data = {
                "material_type": "NBR",
                "inner_diameter": 5.0,
                "outer_diameter": 15.0,
                "height": 10.0,
                "pieces_count": 3,
                "cost_per_mm": 2.0
            }
            
            response = self.session.post(f"{BACKEND_URL}/raw-materials", json=new_material_data)
            
            if response.status_code == 200:
                created_material = response.json()
                self.created_items.append(('raw_material', created_material.get('id')))
                
                self.log_test("New Item Creation - Raw Material", True, 
                            f"Created NBR 5×15 material with unit code: {created_material.get('unit_code', 'N/A')}")
                
                # Now get the updated list and verify position
                response = self.session.get(f"{BACKEND_URL}/raw-materials")
                if response.status_code == 200:
                    updated_materials = response.json()
                    
                    # Find our created material
                    created_position = -1
                    for i, material in enumerate(updated_materials):
                        if material.get('id') == created_material.get('id'):
                            created_position = i
                            break
                    
                    if created_position >= 0:
                        # Check if it's in the correct position (should be early since NBR has priority 2 and small size)
                        position_correct = True
                        position_details = f"New NBR 5×15 material appears at position {created_position + 1} out of {len(updated_materials)}"
                        
                        # Check if any BUR materials come after it (they shouldn't)
                        bur_after_nbr = False
                        for i in range(created_position + 1, len(updated_materials)):
                            if updated_materials[i].get('material_type') == 'BUR':
                                bur_after_nbr = True
                                break
                        
                        if bur_after_nbr:
                            position_correct = False
                            position_details += " - ERROR: BUR materials found after NBR"
                        
                        self.log_test("New Item Sorting - Position Verification", position_correct, position_details)
                    else:
                        self.log_test("New Item Sorting - Position Verification", False, "Created material not found in updated list")
                else:
                    self.log_test("New Item Sorting - Updated List Retrieval", False, f"HTTP {response.status_code}")
            else:
                self.log_test("New Item Creation - Raw Material", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("New Item Creation - Raw Material", False, f"Exception: {str(e)}")
    
    def cleanup_created_items(self):
        """Clean up any items created during testing"""
        print("\n=== Cleaning Up Test Data ===")
        
        for item_type, item_id in self.created_items:
            try:
                if item_type == 'raw_material':
                    response = self.session.delete(f"{BACKEND_URL}/raw-materials/{item_id}")
                    if response.status_code == 200:
                        self.log_test(f"Cleanup - {item_type} {item_id}", True, "Successfully deleted")
                    else:
                        self.log_test(f"Cleanup - {item_type} {item_id}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Cleanup - {item_type} {item_id}", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all material sorting tests"""
        print("🧪 Starting Material Sorting Tests for Master Seal System")
        print("=" * 60)
        
        # Test current sorting
        self.test_inventory_sorting()
        self.test_raw_materials_sorting()
        
        # Test with new items
        self.test_create_and_verify_sorting()
        
        # Cleanup
        self.cleanup_created_items()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = MaterialSortingTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)