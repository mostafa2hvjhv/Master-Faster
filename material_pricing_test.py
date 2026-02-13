#!/usr/bin/env python3
"""
Material Pricing System Backend Test
Testing the new Material Pricing APIs with CRUD operations and price calculations
"""

import requests
import json
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class MaterialPricingTester:
    def __init__(self):
        self.test_results = []
        self.created_pricing_ids = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "success": success,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def test_create_material_pricing(self):
        """Test creating material pricing entries"""
        print("\n=== Testing Material Pricing Creation ===")
        
        # Test data for NBR 20x30mm material
        test_pricing = {
            "material_type": "NBR",
            "inner_diameter": 20.0,
            "outer_diameter": 30.0,
            "price_per_mm": 1.5,
            "manufacturing_cost_client1": 5.0,
            "manufacturing_cost_client2": 7.0,
            "manufacturing_cost_client3": 10.0,
            "notes": "Test pricing for NBR 20x30mm"
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/material-pricing", json=test_pricing)
            
            if response.status_code == 200:
                data = response.json()
                self.created_pricing_ids.append(data["id"])
                self.log_test(
                    "Create NBR 20x30mm pricing entry",
                    True,
                    f"Created pricing ID: {data['id']}"
                )
                return data["id"]
            else:
                self.log_test(
                    "Create NBR 20x30mm pricing entry",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Create NBR 20x30mm pricing entry", False, str(e))
            return None
    
    def test_get_all_pricing(self):
        """Test retrieving all material pricing entries"""
        print("\n=== Testing Get All Material Pricing ===")
        
        try:
            response = requests.get(f"{BACKEND_URL}/material-pricing")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Get all material pricing entries",
                    True,
                    f"Retrieved {len(data)} pricing entries"
                )
                return data
            else:
                self.log_test(
                    "Get all material pricing entries",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_test("Get all material pricing entries", False, str(e))
            return []
    
    def test_update_pricing(self, pricing_id):
        """Test updating a pricing entry"""
        print("\n=== Testing Material Pricing Update ===")
        
        if not pricing_id:
            self.log_test("Update pricing entry", False, "No pricing ID available")
            return
        
        # Updated pricing data
        updated_pricing = {
            "id": pricing_id,
            "material_type": "NBR",
            "inner_diameter": 20.0,
            "outer_diameter": 30.0,
            "price_per_mm": 2.0,  # Updated price
            "manufacturing_cost_client1": 6.0,  # Updated cost
            "manufacturing_cost_client2": 8.0,  # Updated cost
            "manufacturing_cost_client3": 12.0,  # Updated cost
            "notes": "Updated test pricing for NBR 20x30mm"
        }
        
        try:
            response = requests.put(f"{BACKEND_URL}/material-pricing/{pricing_id}", json=updated_pricing)
            
            if response.status_code == 200:
                self.log_test(
                    "Update pricing entry",
                    True,
                    "Successfully updated pricing with new values"
                )
            else:
                self.log_test(
                    "Update pricing entry",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Update pricing entry", False, str(e))
    
    def test_price_calculation(self):
        """Test price calculation API with different scenarios"""
        print("\n=== Testing Price Calculation API ===")
        
        # Test scenario 1: Client type 1
        self.test_single_price_calculation(
            material_type="NBR",
            inner_diameter=20.0,
            outer_diameter=30.0,
            height=6.0,
            client_type=1,
            expected_total=18.0,  # (2.0 * 6) + 6.0 = 18.0 (using updated values)
            scenario="Client Type 1"
        )
        
        # Test scenario 2: Client type 2
        self.test_single_price_calculation(
            material_type="NBR",
            inner_diameter=20.0,
            outer_diameter=30.0,
            height=6.0,
            client_type=2,
            expected_total=20.0,  # (2.0 * 6) + 8.0 = 20.0
            scenario="Client Type 2"
        )
        
        # Test scenario 3: Client type 3
        self.test_single_price_calculation(
            material_type="NBR",
            inner_diameter=20.0,
            outer_diameter=30.0,
            height=6.0,
            client_type=3,
            expected_total=24.0,  # (2.0 * 6) + 12.0 = 24.0
            scenario="Client Type 3"
        )
    
    def test_single_price_calculation(self, material_type, inner_diameter, outer_diameter, height, client_type, expected_total, scenario):
        """Test a single price calculation scenario"""
        try:
            params = {
                "material_type": material_type,
                "inner_diameter": inner_diameter,
                "outer_diameter": outer_diameter,
                "height": height,
                "client_type": client_type
            }
            
            response = requests.post(f"{BACKEND_URL}/calculate-price", params=params)
            
            if response.status_code == 200:
                data = response.json()
                calculated_total = data["total_price"]
                
                # Check if calculation is correct
                if abs(calculated_total - expected_total) < 0.01:  # Allow small floating point differences
                    self.log_test(
                        f"Price calculation - {scenario}",
                        True,
                        f"Expected: {expected_total}, Got: {calculated_total}"
                    )
                else:
                    self.log_test(
                        f"Price calculation - {scenario}",
                        False,
                        f"Expected: {expected_total}, Got: {calculated_total}"
                    )
            else:
                self.log_test(
                    f"Price calculation - {scenario}",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test(f"Price calculation - {scenario}", False, str(e))
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n=== Testing Error Handling ===")
        
        # Test 1: Non-existent material combination
        try:
            params = {
                "material_type": "NBR",
                "inner_diameter": 999.0,  # Non-existent combination
                "outer_diameter": 999.0,
                "height": 6.0,
                "client_type": 1
            }
            
            response = requests.post(f"{BACKEND_URL}/calculate-price", params=params)
            
            if response.status_code == 404:
                self.log_test(
                    "Error handling - Non-existent material",
                    True,
                    "Correctly returned 404 for non-existent material combination"
                )
            else:
                self.log_test(
                    "Error handling - Non-existent material",
                    False,
                    f"Expected 404, got {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Error handling - Non-existent material", False, str(e))
        
        # Test 2: Invalid client type
        try:
            params = {
                "material_type": "NBR",
                "inner_diameter": 20.0,
                "outer_diameter": 30.0,
                "height": 6.0,
                "client_type": 5  # Invalid client type
            }
            
            response = requests.post(f"{BACKEND_URL}/calculate-price", params=params)
            
            if response.status_code == 400:
                self.log_test(
                    "Error handling - Invalid client type",
                    True,
                    "Correctly returned 400 for invalid client type"
                )
            else:
                self.log_test(
                    "Error handling - Invalid client type",
                    False,
                    f"Expected 400, got {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Error handling - Invalid client type", False, str(e))
        
        # Test 3: Missing parameters
        try:
            params = {
                "material_type": "NBR",
                "inner_diameter": 20.0,
                # Missing outer_diameter, height, client_type
            }
            
            response = requests.post(f"{BACKEND_URL}/calculate-price", params=params)
            
            if response.status_code in [400, 422]:  # 422 for validation errors
                self.log_test(
                    "Error handling - Missing parameters",
                    True,
                    f"Correctly returned {response.status_code} for missing parameters"
                )
            else:
                self.log_test(
                    "Error handling - Missing parameters",
                    False,
                    f"Expected 400/422, got {response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Error handling - Missing parameters", False, str(e))
    
    def test_delete_pricing(self, pricing_id):
        """Test deleting a pricing entry"""
        print("\n=== Testing Material Pricing Deletion ===")
        
        if not pricing_id:
            self.log_test("Delete pricing entry", False, "No pricing ID available")
            return
        
        try:
            response = requests.delete(f"{BACKEND_URL}/material-pricing/{pricing_id}")
            
            if response.status_code == 200:
                self.log_test(
                    "Delete pricing entry",
                    True,
                    "Successfully deleted pricing entry"
                )
            else:
                self.log_test(
                    "Delete pricing entry",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Delete pricing entry", False, str(e))
    
    def run_all_tests(self):
        """Run all Material Pricing tests"""
        print("🧪 Starting Material Pricing System Backend Tests")
        print("=" * 60)
        
        # Test CRUD operations
        pricing_id = self.test_create_material_pricing()
        self.test_get_all_pricing()
        self.test_update_pricing(pricing_id)
        
        # Test price calculations
        self.test_price_calculation()
        
        # Test error handling
        self.test_error_handling()
        
        # Clean up - delete test data
        if pricing_id:
            self.test_delete_pricing(pricing_id)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 MATERIAL PRICING SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"  - {result['test']}")
        
        return success_rate >= 80  # Consider 80%+ as overall success

if __name__ == "__main__":
    tester = MaterialPricingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Material Pricing System tests completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Some Material Pricing System tests failed!")
        sys.exit(1)