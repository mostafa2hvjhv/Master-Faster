#!/usr/bin/env python3
"""
Materials Display Investigation Test
فحص مشكلة عدم عرض المواد في المخزون

This test investigates the reported issue where materials exist in storage 
but are not being displayed in the inventory interface.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class MaterialsInvestigationTester:
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
    
    def test_database_counts(self):
        """1. فحص قاعدة البيانات - تعداد المواد في المجموعات المختلفة"""
        print("\n=== 1. Database Material Counts Investigation ===")
        
        try:
            # Test raw materials count
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                raw_materials = response.json()
                raw_count = len(raw_materials)
                self.log_test("Raw Materials API Response", True, 
                            f"Found {raw_count} raw materials")
                
                # Analyze raw materials by type
                material_types = {}
                for material in raw_materials:
                    mat_type = material.get('material_type', 'Unknown')
                    material_types[mat_type] = material_types.get(mat_type, 0) + 1
                
                type_details = ", ".join([f"{k}: {v}" for k, v in material_types.items()])
                self.log_test("Raw Materials by Type", True, type_details)
                
            else:
                self.log_test("Raw Materials API Response", False, 
                            f"HTTP {response.status_code}: {response.text}")
                raw_materials = []
                raw_count = 0
        except Exception as e:
            self.log_test("Raw Materials API Response", False, str(e))
            raw_materials = []
            raw_count = 0
        
        try:
            # Test inventory items count
            response = self.session.get(f"{BACKEND_URL}/inventory")
            if response.status_code == 200:
                inventory_items = response.json()
                inventory_count = len(inventory_items)
                self.log_test("Inventory Items API Response", True, 
                            f"Found {inventory_count} inventory items")
                
                # Analyze inventory by type
                inventory_types = {}
                for item in inventory_items:
                    mat_type = item.get('material_type', 'Unknown')
                    inventory_types[mat_type] = inventory_types.get(mat_type, 0) + 1
                
                type_details = ", ".join([f"{k}: {v}" for k, v in inventory_types.items()])
                self.log_test("Inventory Items by Type", True, type_details)
                
            else:
                self.log_test("Inventory Items API Response", False, 
                            f"HTTP {response.status_code}: {response.text}")
                inventory_items = []
                inventory_count = 0
        except Exception as e:
            self.log_test("Inventory Items API Response", False, str(e))
            inventory_items = []
            inventory_count = 0
        
        # Compare counts
        self.log_test("Database Count Comparison", True, 
                     f"Raw Materials: {raw_count}, Inventory Items: {inventory_count}")
        
        return raw_materials, inventory_items
    
    def test_api_responses(self):
        """2. اختبار APIs - فحص استجابة كل API"""
        print("\n=== 2. API Response Testing ===")
        
        # Test GET /api/raw-materials
        try:
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/raw-materials", True, 
                            f"Status: {response.status_code}, Count: {len(data)}")
                
                # Check if data has required fields
                if data and len(data) > 0:
                    sample = data[0]
                    required_fields = ['id', 'material_type', 'inner_diameter', 'outer_diameter', 'unit_code']
                    missing_fields = [field for field in required_fields if field not in sample]
                    if missing_fields:
                        self.log_test("Raw Materials Data Structure", False, 
                                    f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("Raw Materials Data Structure", True, 
                                    "All required fields present")
                else:
                    self.log_test("Raw Materials Data Content", False, "No data returned")
            else:
                self.log_test("GET /api/raw-materials", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/raw-materials", False, str(e))
        
        # Test GET /api/inventory
        try:
            response = self.session.get(f"{BACKEND_URL}/inventory")
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/inventory", True, 
                            f"Status: {response.status_code}, Count: {len(data)}")
                
                # Check if data has required fields
                if data and len(data) > 0:
                    sample = data[0]
                    required_fields = ['id', 'material_type', 'inner_diameter', 'outer_diameter', 'available_pieces']
                    missing_fields = [field for field in required_fields if field not in sample]
                    if missing_fields:
                        self.log_test("Inventory Data Structure", False, 
                                    f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("Inventory Data Structure", True, 
                                    "All required fields present")
                else:
                    self.log_test("Inventory Data Content", False, "No data returned")
            else:
                self.log_test("GET /api/inventory", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/inventory", False, str(e))
    
    def test_sorting_and_filtering(self):
        """3. فحص الفلاتر والترتيب - التحقق من تأثير الترتيب الجديد"""
        print("\n=== 3. Sorting and Filtering Testing ===")
        
        try:
            # Test raw materials sorting (should be BUR-NBR-BT-BOOM-VT)
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials = response.json()
                if materials:
                    # Check sorting order
                    material_order = [mat.get('material_type') for mat in materials]
                    expected_order = ['BUR', 'NBR', 'BT', 'BOOM', 'VT']
                    
                    # Group by material type to check if sorting is working
                    type_positions = {}
                    for i, mat_type in enumerate(material_order):
                        if mat_type not in type_positions:
                            type_positions[mat_type] = i
                    
                    # Check if BUR comes before NBR, NBR before BT, etc.
                    sorting_correct = True
                    sorting_details = []
                    for i in range(len(expected_order) - 1):
                        current_type = expected_order[i]
                        next_type = expected_order[i + 1]
                        if current_type in type_positions and next_type in type_positions:
                            if type_positions[current_type] > type_positions[next_type]:
                                sorting_correct = False
                                sorting_details.append(f"{current_type} appears after {next_type}")
                    
                    if sorting_correct:
                        self.log_test("Raw Materials Sorting (BUR-NBR-BT-BOOM-VT)", True, 
                                    f"Material types found: {list(type_positions.keys())}")
                    else:
                        self.log_test("Raw Materials Sorting (BUR-NBR-BT-BOOM-VT)", False, 
                                    f"Sorting issues: {'; '.join(sorting_details)}")
                else:
                    self.log_test("Raw Materials Sorting", False, "No materials to check sorting")
            else:
                self.log_test("Raw Materials Sorting", False, f"API error: {response.status_code}")
        except Exception as e:
            self.log_test("Raw Materials Sorting", False, str(e))
        
        try:
            # Test inventory sorting
            response = self.session.get(f"{BACKEND_URL}/inventory")
            if response.status_code == 200:
                inventory = response.json()
                if inventory:
                    # Check sorting order for inventory
                    inventory_order = [item.get('material_type') for item in inventory]
                    type_positions = {}
                    for i, mat_type in enumerate(inventory_order):
                        if mat_type not in type_positions:
                            type_positions[mat_type] = i
                    
                    self.log_test("Inventory Sorting", True, 
                                f"Material types found: {list(type_positions.keys())}")
                else:
                    self.log_test("Inventory Sorting", False, "No inventory items to check sorting")
            else:
                self.log_test("Inventory Sorting", False, f"API error: {response.status_code}")
        except Exception as e:
            self.log_test("Inventory Sorting", False, str(e))
    
    def test_hidden_data_investigation(self):
        """4. فحص البيانات المخفية - البحث عن مواد قد تكون مفلترة عن طريق الخطأ"""
        print("\n=== 4. Hidden Data Investigation ===")
        
        try:
            # Get raw materials and check for potential issues
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials = response.json()
                
                # Check for materials with null or invalid values
                null_unit_codes = [mat for mat in materials if not mat.get('unit_code')]
                null_material_types = [mat for mat in materials if not mat.get('material_type')]
                invalid_dimensions = [mat for mat in materials 
                                    if not mat.get('inner_diameter') or not mat.get('outer_diameter')]
                
                self.log_test("Materials with Missing Unit Codes", 
                            len(null_unit_codes) == 0, 
                            f"Found {len(null_unit_codes)} materials without unit codes")
                
                self.log_test("Materials with Missing Material Types", 
                            len(null_material_types) == 0, 
                            f"Found {len(null_material_types)} materials without material types")
                
                self.log_test("Materials with Invalid Dimensions", 
                            len(invalid_dimensions) == 0, 
                            f"Found {len(invalid_dimensions)} materials with invalid dimensions")
                
                # Check for duplicate unit codes
                unit_codes = [mat.get('unit_code') for mat in materials if mat.get('unit_code')]
                duplicate_codes = []
                seen_codes = set()
                for code in unit_codes:
                    if code in seen_codes:
                        duplicate_codes.append(code)
                    seen_codes.add(code)
                
                self.log_test("Duplicate Unit Codes Check", 
                            len(duplicate_codes) == 0, 
                            f"Found duplicate codes: {duplicate_codes}" if duplicate_codes else "No duplicates found")
                
            else:
                self.log_test("Hidden Data Investigation", False, f"API error: {response.status_code}")
        except Exception as e:
            self.log_test("Hidden Data Investigation", False, str(e))
    
    def test_detailed_comparison(self):
        """5. مقارنة العد - إحصائية دقيقة لعدد المواد في كل collection"""
        print("\n=== 5. Detailed Count Comparison ===")
        
        try:
            # Get detailed statistics
            raw_response = self.session.get(f"{BACKEND_URL}/raw-materials")
            inventory_response = self.session.get(f"{BACKEND_URL}/inventory")
            
            if raw_response.status_code == 200 and inventory_response.status_code == 200:
                raw_materials = raw_response.json()
                inventory_items = inventory_response.json()
                
                # Detailed analysis
                print(f"\n📊 DETAILED STATISTICS:")
                print(f"   Raw Materials Total: {len(raw_materials)}")
                print(f"   Inventory Items Total: {len(inventory_items)}")
                
                # Analyze by material type
                raw_by_type = {}
                inventory_by_type = {}
                
                for mat in raw_materials:
                    mat_type = mat.get('material_type', 'Unknown')
                    raw_by_type[mat_type] = raw_by_type.get(mat_type, 0) + 1
                
                for item in inventory_items:
                    mat_type = item.get('material_type', 'Unknown')
                    inventory_by_type[mat_type] = inventory_by_type.get(mat_type, 0) + 1
                
                print(f"\n📋 BY MATERIAL TYPE:")
                all_types = set(list(raw_by_type.keys()) + list(inventory_by_type.keys()))
                for mat_type in sorted(all_types):
                    raw_count = raw_by_type.get(mat_type, 0)
                    inv_count = inventory_by_type.get(mat_type, 0)
                    print(f"   {mat_type}: Raw={raw_count}, Inventory={inv_count}")
                
                # Check for materials that exist in raw but not in inventory
                raw_specs = set()
                inv_specs = set()
                
                for mat in raw_materials:
                    spec = f"{mat.get('material_type')}-{mat.get('inner_diameter')}-{mat.get('outer_diameter')}"
                    raw_specs.add(spec)
                
                for item in inventory_items:
                    spec = f"{item.get('material_type')}-{item.get('inner_diameter')}-{item.get('outer_diameter')}"
                    inv_specs.add(spec)
                
                missing_in_inventory = raw_specs - inv_specs
                missing_in_raw = inv_specs - raw_specs
                
                self.log_test("Materials Missing in Inventory", 
                            len(missing_in_inventory) == 0,
                            f"Raw materials not in inventory: {len(missing_in_inventory)}")
                
                self.log_test("Inventory Items Missing in Raw Materials", 
                            len(missing_in_raw) == 0,
                            f"Inventory items not in raw materials: {len(missing_in_raw)}")
                
                if missing_in_inventory:
                    print(f"   Missing in inventory: {list(missing_in_inventory)[:5]}...")
                
                if missing_in_raw:
                    print(f"   Missing in raw materials: {list(missing_in_raw)[:5]}...")
                
                # Overall assessment
                total_materials = len(raw_materials) + len(inventory_items)
                if total_materials > 0:
                    self.log_test("Overall Material Visibility", True, 
                                f"Total materials found: {total_materials}")
                else:
                    self.log_test("Overall Material Visibility", False, 
                                "No materials found in either collection")
                
            else:
                self.log_test("Detailed Comparison", False, 
                            f"API errors - Raw: {raw_response.status_code}, Inventory: {inventory_response.status_code}")
        except Exception as e:
            self.log_test("Detailed Comparison", False, str(e))
    
    def run_investigation(self):
        """Run complete materials display investigation"""
        print("🔍 MATERIALS DISPLAY INVESTIGATION")
        print("=" * 50)
        print("Investigating reported issue: Materials exist in storage but not displayed in inventory interface")
        print("التحقيق في المشكلة المبلغ عنها: يوجد خامات في المخزن لكن لا يتم عرضها في واجهة المخزون")
        
        # Run all investigation tests
        raw_materials, inventory_items = self.test_database_counts()
        self.test_api_responses()
        self.test_sorting_and_filtering()
        self.test_hidden_data_investigation()
        self.test_detailed_comparison()
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 INVESTIGATION SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Key findings
        print(f"\n🔍 KEY FINDINGS:")
        if failed_tests > 0:
            print("❌ Issues found that may explain the missing materials problem:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        else:
            print("✅ No obvious issues found in backend APIs")
            print("   The problem may be in the frontend display logic")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = MaterialsInvestigationTester()
    passed, failed = tester.run_investigation()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)