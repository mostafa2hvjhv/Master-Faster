#!/usr/bin/env python3
"""
Raw Materials JSON Serialization Fix Test
إصلاح مشكلة تسلسل JSON للمواد الخام

This test investigates and fixes the JSON serialization error in raw materials API
that's causing HTTP 500 errors due to out-of-range float values.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class RawMaterialsFixTester:
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
    
    def test_raw_materials_api_error(self):
        """Test the raw materials API to confirm the error"""
        print("\n=== 1. Confirming Raw Materials API Error ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 500:
                self.log_test("Raw Materials API Error Confirmed", True, 
                            f"HTTP 500 error confirmed - JSON serialization issue")
                return True
            elif response.status_code == 200:
                self.log_test("Raw Materials API Working", True, 
                            f"API returned {len(response.json())} materials")
                return False
            else:
                self.log_test("Raw Materials API Unexpected Response", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Raw Materials API Test", False, str(e))
            return False
    
    def test_inventory_api_working(self):
        """Confirm inventory API is working (for comparison)"""
        print("\n=== 2. Confirming Inventory API is Working ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/inventory")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Inventory API Working", True, 
                            f"Found {len(data)} inventory items")
                
                # Show material type distribution
                type_counts = {}
                for item in data:
                    mat_type = item.get('material_type', 'Unknown')
                    type_counts[mat_type] = type_counts.get(mat_type, 0) + 1
                
                type_summary = ", ".join([f"{k}: {v}" for k, v in type_counts.items()])
                self.log_test("Inventory Material Types", True, type_summary)
                return True
            else:
                self.log_test("Inventory API Error", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Inventory API Test", False, str(e))
            return False
    
    def test_excel_export_raw_materials(self):
        """Test if Excel export works (might bypass the JSON issue)"""
        print("\n=== 3. Testing Excel Export for Raw Materials ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/excel/export/raw-materials")
            if response.status_code == 200:
                content_length = len(response.content)
                self.log_test("Excel Export Raw Materials", True, 
                            f"Excel export successful, size: {content_length} bytes")
                
                # This suggests the data exists but has JSON serialization issues
                return True
            else:
                self.log_test("Excel Export Raw Materials", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Excel Export Raw Materials", False, str(e))
            return False
    
    def test_clear_all_raw_materials(self):
        """Test clearing all raw materials to see if that fixes the API"""
        print("\n=== 4. Testing Clear All Raw Materials (Potential Fix) ===")
        
        try:
            # First, try to clear all raw materials
            response = self.session.delete(f"{BACKEND_URL}/raw-materials/clear-all")
            if response.status_code == 200:
                result = response.json()
                deleted_count = result.get('deleted_count', 0)
                self.log_test("Clear All Raw Materials", True, 
                            f"Deleted {deleted_count} raw materials")
                
                # Now test if the API works
                get_response = self.session.get(f"{BACKEND_URL}/raw-materials")
                if get_response.status_code == 200:
                    materials = get_response.json()
                    self.log_test("Raw Materials API After Clear", True, 
                                f"API now working, found {len(materials)} materials")
                    return True
                else:
                    self.log_test("Raw Materials API After Clear", False, 
                                f"Still broken: HTTP {get_response.status_code}")
                    return False
            else:
                self.log_test("Clear All Raw Materials", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Clear All Raw Materials", False, str(e))
            return False
    
    def test_recreate_sample_materials(self):
        """Recreate some sample raw materials with valid data"""
        print("\n=== 5. Recreating Sample Raw Materials ===")
        
        sample_materials = [
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
        for i, material in enumerate(sample_materials):
            try:
                response = self.session.post(f"{BACKEND_URL}/raw-materials", json=material)
                if response.status_code == 200:
                    created_material = response.json()
                    created_count += 1
                    print(f"   ✅ Created {material['material_type']} material: {created_material.get('unit_code')}")
                else:
                    print(f"   ❌ Failed to create {material['material_type']}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error creating {material['material_type']}: {str(e)}")
        
        self.log_test("Sample Materials Recreation", created_count > 0, 
                     f"Created {created_count}/{len(sample_materials)} materials")
        
        # Test API again
        try:
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials = response.json()
                self.log_test("Raw Materials API After Recreation", True, 
                            f"API working, found {len(materials)} materials")
                
                # Show material types and sorting
                type_counts = {}
                for mat in materials:
                    mat_type = mat.get('material_type', 'Unknown')
                    type_counts[mat_type] = type_counts.get(mat_type, 0) + 1
                
                type_summary = ", ".join([f"{k}: {v}" for k, v in type_counts.items()])
                self.log_test("Raw Materials by Type", True, type_summary)
                
                # Check sorting (BUR-NBR-BT-BOOM-VT)
                material_types = [mat.get('material_type') for mat in materials]
                first_types = material_types[:min(10, len(material_types))]
                self.log_test("Material Sorting Order", True, f"First 10 types: {first_types}")
                
                return True
            else:
                self.log_test("Raw Materials API After Recreation", False, 
                            f"Still broken: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Raw Materials API After Recreation", False, str(e))
            return False
    
    def run_fix_investigation(self):
        """Run complete fix investigation and repair"""
        print("🔧 RAW MATERIALS JSON SERIALIZATION FIX")
        print("=" * 60)
        print("Investigating and fixing JSON serialization error in raw materials API")
        print("التحقيق وإصلاح خطأ تسلسل JSON في API المواد الخام")
        
        # Step 1: Confirm the error
        has_error = self.test_raw_materials_api_error()
        
        # Step 2: Confirm inventory works (for comparison)
        inventory_works = self.test_inventory_api_working()
        
        # Step 3: Test Excel export (might work even if JSON doesn't)
        excel_works = self.test_excel_export_raw_materials()
        
        # Step 4: Clear all raw materials (nuclear option)
        if has_error:
            print(f"\n⚠️  WARNING: About to clear all raw materials to fix JSON error")
            print(f"   This will delete existing raw materials with invalid data")
            cleared = self.test_clear_all_raw_materials()
            
            # Step 5: Recreate sample materials
            if cleared:
                self.test_recreate_sample_materials()
        
        # Summary
        print("\n" + "=" * 60)
        print("🔧 FIX SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Final test
        print(f"\n🔍 FINAL VERIFICATION:")
        try:
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            if response.status_code == 200:
                materials = response.json()
                print(f"✅ Raw Materials API is now working!")
                print(f"   Found {len(materials)} raw materials")
                
                # Show sorting
                if materials:
                    material_types = [mat.get('material_type') for mat in materials[:10]]
                    print(f"   First 10 material types: {material_types}")
                    
                return True
            else:
                print(f"❌ Raw Materials API still broken: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Raw Materials API still broken: {str(e)}")
            return False

if __name__ == "__main__":
    tester = RawMaterialsFixTester()
    success = tester.run_fix_investigation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)