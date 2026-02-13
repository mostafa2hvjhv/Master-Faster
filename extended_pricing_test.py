#!/usr/bin/env python3
"""
Extended Material Pricing System Tests
Additional comprehensive testing scenarios
"""

import requests
import json
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class ExtendedPricingTester:
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
    
    def test_multiple_material_types(self):
        """Test creating pricing for different material types"""
        print("\n=== Testing Multiple Material Types ===")
        
        materials = [
            {"type": "NBR", "inner": 15.0, "outer": 25.0, "price": 1.2, "c1": 4.0, "c2": 6.0, "c3": 8.0},
            {"type": "BUR", "inner": 20.0, "outer": 30.0, "price": 1.8, "c1": 5.5, "c2": 7.5, "c3": 9.5},
            {"type": "VT", "inner": 25.0, "outer": 35.0, "price": 2.1, "c1": 6.0, "c2": 8.0, "c3": 10.0},
            {"type": "BT", "inner": 30.0, "outer": 40.0, "price": 1.9, "c1": 5.0, "c2": 7.0, "c3": 9.0},
            {"type": "BOOM", "inner": 35.0, "outer": 45.0, "price": 2.5, "c1": 7.0, "c2": 9.0, "c3": 11.0}
        ]
        
        for material in materials:
            pricing_data = {
                "material_type": material["type"],
                "inner_diameter": material["inner"],
                "outer_diameter": material["outer"],
                "price_per_mm": material["price"],
                "manufacturing_cost_client1": material["c1"],
                "manufacturing_cost_client2": material["c2"],
                "manufacturing_cost_client3": material["c3"],
                "notes": f"Test pricing for {material['type']} {material['inner']}x{material['outer']}mm"
            }
            
            try:
                response = requests.post(f"{BACKEND_URL}/material-pricing", json=pricing_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.created_pricing_ids.append(data["id"])
                    self.log_test(
                        f"Create {material['type']} pricing",
                        True,
                        f"Created {material['type']} {material['inner']}x{material['outer']}mm pricing"
                    )
                else:
                    self.log_test(
                        f"Create {material['type']} pricing",
                        False,
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(f"Create {material['type']} pricing", False, str(e))
    
    def test_complex_price_calculations(self):
        """Test price calculations with different heights and client types"""
        print("\n=== Testing Complex Price Calculations ===")
        
        # Test different heights
        test_cases = [
            {"height": 5.0, "client": 1, "expected_base": 6.0},  # 1.2 * 5 = 6.0
            {"height": 10.0, "client": 2, "expected_base": 12.0},  # 1.2 * 10 = 12.0
            {"height": 15.0, "client": 3, "expected_base": 18.0},  # 1.2 * 15 = 18.0
            {"height": 2.5, "client": 1, "expected_base": 3.0},   # 1.2 * 2.5 = 3.0
            {"height": 7.8, "client": 2, "expected_base": 9.36},  # 1.2 * 7.8 = 9.36
        ]
        
        for i, case in enumerate(test_cases):
            # Calculate expected total based on NBR 15x25 pricing (price_per_mm=1.2, costs: 4.0, 6.0, 8.0)
            manufacturing_costs = {1: 4.0, 2: 6.0, 3: 8.0}
            expected_total = case["expected_base"] + manufacturing_costs[case["client"]]
            
            try:
                params = {
                    "material_type": "NBR",
                    "inner_diameter": 15.0,
                    "outer_diameter": 25.0,
                    "height": case["height"],
                    "client_type": case["client"]
                }
                
                response = requests.post(f"{BACKEND_URL}/calculate-price", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    calculated_total = data["total_price"]
                    
                    if abs(calculated_total - expected_total) < 0.01:
                        self.log_test(
                            f"Complex calculation {i+1}",
                            True,
                            f"Height {case['height']}mm, Client {case['client']}: Expected {expected_total}, Got {calculated_total}"
                        )
                    else:
                        self.log_test(
                            f"Complex calculation {i+1}",
                            False,
                            f"Height {case['height']}mm, Client {case['client']}: Expected {expected_total}, Got {calculated_total}"
                        )
                else:
                    self.log_test(
                        f"Complex calculation {i+1}",
                        False,
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(f"Complex calculation {i+1}", False, str(e))
    
    def test_database_persistence(self):
        """Test that pricing data persists correctly"""
        print("\n=== Testing Database Persistence ===")
        
        try:
            # Get all pricing entries
            response = requests.get(f"{BACKEND_URL}/material-pricing")
            
            if response.status_code == 200:
                data = response.json()
                
                # Should have at least the 5 materials we created
                if len(data) >= 5:
                    self.log_test(
                        "Database persistence",
                        True,
                        f"Found {len(data)} pricing entries in database"
                    )
                    
                    # Verify specific material types exist
                    material_types = [item["material_type"] for item in data]
                    expected_types = ["NBR", "BUR", "VT", "BT", "BOOM"]
                    
                    found_types = [t for t in expected_types if t in material_types]
                    
                    if len(found_types) == len(expected_types):
                        self.log_test(
                            "All material types present",
                            True,
                            f"Found all expected material types: {found_types}"
                        )
                    else:
                        missing_types = [t for t in expected_types if t not in material_types]
                        self.log_test(
                            "All material types present",
                            False,
                            f"Missing material types: {missing_types}"
                        )
                else:
                    self.log_test(
                        "Database persistence",
                        False,
                        f"Expected at least 5 entries, found {len(data)}"
                    )
            else:
                self.log_test(
                    "Database persistence",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Database persistence", False, str(e))
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("\n=== Testing Edge Cases ===")
        
        # Test very small height
        try:
            params = {
                "material_type": "NBR",
                "inner_diameter": 15.0,
                "outer_diameter": 25.0,
                "height": 0.1,  # Very small height
                "client_type": 1
            }
            
            response = requests.post(f"{BACKEND_URL}/calculate-price", params=params)
            
            if response.status_code == 200:
                data = response.json()
                # Should be 1.2 * 0.1 + 4.0 = 4.12
                expected = 4.12
                if abs(data["total_price"] - expected) < 0.01:
                    self.log_test(
                        "Edge case - Very small height",
                        True,
                        f"Correctly calculated price for 0.1mm height: {data['total_price']}"
                    )
                else:
                    self.log_test(
                        "Edge case - Very small height",
                        False,
                        f"Expected {expected}, got {data['total_price']}"
                    )
            else:
                self.log_test(
                    "Edge case - Very small height",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Edge case - Very small height", False, str(e))
        
        # Test large height
        try:
            params = {
                "material_type": "NBR",
                "inner_diameter": 15.0,
                "outer_diameter": 25.0,
                "height": 100.0,  # Large height
                "client_type": 3
            }
            
            response = requests.post(f"{BACKEND_URL}/calculate-price", params=params)
            
            if response.status_code == 200:
                data = response.json()
                # Should be 1.2 * 100 + 8.0 = 128.0
                expected = 128.0
                if abs(data["total_price"] - expected) < 0.01:
                    self.log_test(
                        "Edge case - Large height",
                        True,
                        f"Correctly calculated price for 100mm height: {data['total_price']}"
                    )
                else:
                    self.log_test(
                        "Edge case - Large height",
                        False,
                        f"Expected {expected}, got {data['total_price']}"
                    )
            else:
                self.log_test(
                    "Edge case - Large height",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Edge case - Large height", False, str(e))
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        deleted_count = 0
        for pricing_id in self.created_pricing_ids:
            try:
                response = requests.delete(f"{BACKEND_URL}/material-pricing/{pricing_id}")
                if response.status_code == 200:
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting {pricing_id}: {e}")
        
        self.log_test(
            "Cleanup test data",
            True,
            f"Deleted {deleted_count} test pricing entries"
        )
    
    def run_all_tests(self):
        """Run all extended tests"""
        print("🧪 Starting Extended Material Pricing System Tests")
        print("=" * 60)
        
        # Run all test suites
        self.test_multiple_material_types()
        self.test_complex_price_calculations()
        self.test_database_persistence()
        self.test_edge_cases()
        
        # Clean up
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 EXTENDED MATERIAL PRICING TEST SUMMARY")
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
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = ExtendedPricingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Extended Material Pricing tests completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Some extended tests failed!")
        sys.exit(1)