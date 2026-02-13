#!/usr/bin/env python3
"""
Focused Backend Testing for Latest Bug Fixes
اختبار مركز للإصلاحات الأخيرة

Testing Focus:
1. Payment method matching with treasury accounts
2. Inventory transactions API
3. Inventory integration with raw materials
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class FocusedAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_data = {
            'customers': [],
            'inventory_items': [],
            'raw_materials': [],
            'invoices': [],
            'treasury_transactions': []
        }
    
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
    
    def make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None):
        """Make HTTP request with error handling"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params)
            
            return response
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None

    def test_payment_method_treasury_mapping(self):
        """Test 1: Payment method matching with treasury accounts"""
        print("\n=== Test 1: Payment Method Treasury Mapping ===")
        
        # Create a test customer first
        customer_data = {
            "name": "عميل اختبار الخزينة",
            "phone": "01234567890",
            "address": "القاهرة"
        }
        
        customer_response = self.make_request("POST", "/customers", customer_data)
        if customer_response and customer_response.status_code == 200:
            customer = customer_response.json()
            self.created_data['customers'].append(customer['id'])
            print(f"Created test customer: {customer['name']}")
        else:
            self.log_test("Create test customer", False, "Failed to create customer for testing")
            return
        
        # Test different payment methods and their treasury account mapping
        payment_methods_to_test = [
            {
                "method": "فودافون كاش محمد الصاوي",
                "expected_account": "vodafone_elsawy",
                "description": "Vodafone Cash Mohamed Elsawy"
            },
            {
                "method": "انستاباي", 
                "expected_account": "instapay",
                "description": "InstaPay"
            },
            {
                "method": "يد الصاوي",
                "expected_account": "yad_elsawy", 
                "description": "Yad Elsawy"
            },
            {
                "method": "نقدي",
                "expected_account": "cash",
                "description": "Cash"
            }
        ]
        
        for payment_test in payment_methods_to_test:
            print(f"\nTesting payment method: {payment_test['method']}")
            
            # Get treasury balances before invoice
            balances_before = self.make_request("GET", "/treasury/balances")
            if not balances_before or balances_before.status_code != 200:
                self.log_test(f"Get treasury balances before - {payment_test['description']}", False, "Failed to get balances")
                continue
                
            before_balance = balances_before.json().get(payment_test['expected_account'], 0)
            print(f"Balance before in {payment_test['expected_account']}: {before_balance}")
            
            # Create invoice with specific payment method
            invoice_data = {
                "customer_id": customer['id'],
                "customer_name": customer['name'],
                "invoice_title": f"فاتورة اختبار {payment_test['description']}",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "seal_type": "RSL",
                        "material_type": "NBR",
                        "inner_diameter": 25.0,
                        "outer_diameter": 35.0,
                        "height": 10.0,
                        "quantity": 2,
                        "unit_price": 50.0,
                        "total_price": 100.0,
                        "product_type": "manufactured"
                    }
                ],
                "payment_method": payment_test['method'],
                "discount_type": "amount",
                "discount_value": 0.0
            }
            
            invoice_response = self.make_request("POST", "/invoices", invoice_data)
            if invoice_response and invoice_response.status_code == 200:
                invoice = invoice_response.json()
                self.created_data['invoices'].append(invoice['id'])
                print(f"Created invoice: {invoice['invoice_number']} with payment method: {payment_test['method']}")
                
                # Get treasury balances after invoice
                balances_after = self.make_request("GET", "/treasury/balances")
                if balances_after and balances_after.status_code == 200:
                    after_balance = balances_after.json().get(payment_test['expected_account'], 0)
                    print(f"Balance after in {payment_test['expected_account']}: {after_balance}")
                    
                    expected_increase = 100.0  # Invoice total
                    actual_increase = after_balance - before_balance
                    
                    if abs(actual_increase - expected_increase) < 0.01:
                        self.log_test(f"Payment method mapping - {payment_test['description']}", True, 
                                    f"Correctly mapped to {payment_test['expected_account']}, balance increased by {actual_increase}")
                    else:
                        self.log_test(f"Payment method mapping - {payment_test['description']}", False,
                                    f"Expected increase {expected_increase} in {payment_test['expected_account']}, got {actual_increase}")
                        
                        # Check if it went to cash instead (common bug)
                        cash_after = balances_after.json().get('cash', 0)
                        cash_before = balances_before.json().get('cash', 0)
                        cash_increase = cash_after - cash_before
                        if abs(cash_increase - expected_increase) < 0.01:
                            print(f"   BUG DETECTED: Payment went to 'cash' account instead of '{payment_test['expected_account']}'")
                else:
                    self.log_test(f"Get treasury balances after - {payment_test['description']}", False, "Failed to get balances after invoice")
            else:
                error_msg = invoice_response.text if invoice_response else "No response"
                self.log_test(f"Create invoice - {payment_test['description']}", False, f"Failed to create invoice: {error_msg}")

    def test_inventory_transactions_api(self):
        """Test 2: Inventory transactions API"""
        print("\n=== Test 2: Inventory Transactions API ===")
        
        # First create an inventory item
        inventory_item_data = {
            "material_type": "NBR",
            "inner_diameter": 30.0,
            "outer_diameter": 40.0,
            "available_pieces": 10,
            "min_stock_level": 2,
            "notes": "اختبار معاملات الجرد"
        }
        
        inventory_response = self.make_request("POST", "/inventory", inventory_item_data)
        if not inventory_response or inventory_response.status_code != 200:
            self.log_test("Create inventory item for transactions test", False, 
                         f"Failed to create inventory item: {inventory_response.text if inventory_response else 'No response'}")
            return
            
        inventory_item = inventory_response.json()
        self.created_data['inventory_items'].append(inventory_item['id'])
        print(f"Created inventory item: {inventory_item['id']} with {inventory_item['available_pieces']} pieces")
        
        # Test 1: Create IN transaction (adding stock)
        in_transaction_data = {
            "inventory_item_id": inventory_item['id'],
            "material_type": "NBR",
            "inner_diameter": 30.0,
            "outer_diameter": 40.0,
            "transaction_type": "in",
            "pieces_change": 5,
            "reason": "إضافة مخزون جديد - اختبار",
            "notes": "اختبار معاملة إدخال"
        }
        
        in_transaction_response = self.make_request("POST", "/inventory-transactions", in_transaction_data)
        if in_transaction_response and in_transaction_response.status_code == 200:
            in_transaction = in_transaction_response.json()
            self.log_test("Create IN inventory transaction", True, 
                         f"Created IN transaction: +{in_transaction_data['pieces_change']} pieces")
            
            # Verify inventory was updated
            updated_inventory = self.make_request("GET", f"/inventory/{inventory_item['id']}")
            if updated_inventory and updated_inventory.status_code == 200:
                updated_item = updated_inventory.json()
                expected_pieces = inventory_item['available_pieces'] + 5
                if updated_item['available_pieces'] == expected_pieces:
                    self.log_test("Inventory update after IN transaction", True,
                                 f"Pieces correctly updated to {updated_item['available_pieces']}")
                else:
                    self.log_test("Inventory update after IN transaction", False,
                                 f"Expected {expected_pieces} pieces, got {updated_item['available_pieces']}")
            else:
                self.log_test("Get updated inventory after IN transaction", False, "Failed to get updated inventory")
        else:
            error_msg = in_transaction_response.text if in_transaction_response else "No response"
            self.log_test("Create IN inventory transaction", False, f"HTTP 500 or other error: {error_msg}")
        
        # Test 2: Create OUT transaction (removing stock)
        out_transaction_data = {
            "inventory_item_id": inventory_item['id'],
            "material_type": "NBR", 
            "inner_diameter": 30.0,
            "outer_diameter": 40.0,
            "transaction_type": "out",
            "pieces_change": -3,
            "reason": "استهلاك للإنتاج - اختبار",
            "notes": "اختبار معاملة إخراج"
        }
        
        out_transaction_response = self.make_request("POST", "/inventory-transactions", out_transaction_data)
        if out_transaction_response and out_transaction_response.status_code == 200:
            out_transaction = out_transaction_response.json()
            self.log_test("Create OUT inventory transaction", True,
                         f"Created OUT transaction: {out_transaction_data['pieces_change']} pieces")
            
            # Verify inventory was updated
            updated_inventory = self.make_request("GET", f"/inventory/{inventory_item['id']}")
            if updated_inventory and updated_inventory.status_code == 200:
                updated_item = updated_inventory.json()
                # Should be original (10) + IN (5) + OUT (-3) = 12
                expected_pieces = 10 + 5 - 3
                if updated_item['available_pieces'] == expected_pieces:
                    self.log_test("Inventory update after OUT transaction", True,
                                 f"Pieces correctly updated to {updated_item['available_pieces']}")
                else:
                    self.log_test("Inventory update after OUT transaction", False,
                                 f"Expected {expected_pieces} pieces, got {updated_item['available_pieces']}")
            else:
                self.log_test("Get updated inventory after OUT transaction", False, "Failed to get updated inventory")
        else:
            error_msg = out_transaction_response.text if out_transaction_response else "No response"
            self.log_test("Create OUT inventory transaction", False, f"HTTP 500 or other error: {error_msg}")
        
        # Test 3: Get all inventory transactions
        all_transactions_response = self.make_request("GET", "/inventory-transactions")
        if all_transactions_response and all_transactions_response.status_code == 200:
            transactions = all_transactions_response.json()
            self.log_test("Get all inventory transactions", True, f"Retrieved {len(transactions)} transactions")
        else:
            error_msg = all_transactions_response.text if all_transactions_response else "No response"
            self.log_test("Get all inventory transactions", False, f"HTTP 500 or other error: {error_msg}")

    def test_inventory_raw_materials_integration(self):
        """Test 3: Inventory integration with raw materials"""
        print("\n=== Test 3: Inventory Integration with Raw Materials ===")
        
        # Create inventory item for raw material testing
        inventory_item_data = {
            "material_type": "BUR",
            "inner_diameter": 20.0,
            "outer_diameter": 30.0,
            "available_pieces": 15,
            "min_stock_level": 3,
            "notes": "اختبار تكامل المواد الخام"
        }
        
        inventory_response = self.make_request("POST", "/inventory", inventory_item_data)
        if not inventory_response or inventory_response.status_code != 200:
            self.log_test("Create inventory item for raw materials test", False,
                         f"Failed to create inventory item: {inventory_response.text if inventory_response else 'No response'}")
            return
            
        inventory_item = inventory_response.json()
        self.created_data['inventory_items'].append(inventory_item['id'])
        initial_pieces = inventory_item['available_pieces']
        print(f"Created inventory item with {initial_pieces} pieces")
        
        # Test check_inventory_availability function
        print("\nTesting inventory availability check...")
        
        # Test 1: Check availability for available quantity
        available_check_data = {
            "seal_type": "RSL",
            "inner_diameter": 20.0,
            "outer_diameter": 30.0,
            "height": 8.0
        }
        
        compatibility_response = self.make_request("POST", "/compatibility-check", available_check_data)
        if compatibility_response and compatibility_response.status_code == 200:
            compatibility_result = compatibility_response.json()
            compatible_materials = compatibility_result.get('compatible_materials', [])
            
            if any(mat['material_type'] == 'BUR' and 
                   mat['inner_diameter'] == 20.0 and 
                   mat['outer_diameter'] == 30.0 
                   for mat in compatible_materials):
                self.log_test("Inventory availability check - available item", True,
                             "Item correctly identified as available in compatibility check")
            else:
                self.log_test("Inventory availability check - available item", False,
                             "Item not found in compatibility check results")
        else:
            error_msg = compatibility_response.text if compatibility_response else "No response"
            self.log_test("Inventory availability check", False, f"Compatibility check failed: {error_msg}")
        
        # Test 2: Create raw material and verify inventory deduction
        print(f"\nCreating raw material to test inventory deduction...")
        print(f"Inventory before raw material creation: {initial_pieces} pieces")
        
        raw_material_data = {
            "material_type": "BUR",
            "inner_diameter": 20.0,
            "outer_diameter": 30.0,
            "height": 12.0,
            "pieces_count": 3,  # Should deduct 3 pieces from inventory
            "unit_code": "BUR-20x30-TEST",
            "cost_per_mm": 2.5
        }
        
        raw_material_response = self.make_request("POST", "/raw-materials", raw_material_data)
        if raw_material_response and raw_material_response.status_code == 200:
            raw_material = raw_material_response.json()
            self.created_data['raw_materials'].append(raw_material['id'])
            self.log_test("Create raw material", True, f"Created raw material: {raw_material['unit_code']}")
            
            # Check inventory after raw material creation
            updated_inventory = self.make_request("GET", f"/inventory/{inventory_item['id']}")
            if updated_inventory and updated_inventory.status_code == 200:
                updated_item = updated_inventory.json()
                final_pieces = updated_item['available_pieces']
                expected_pieces = initial_pieces - raw_material_data['pieces_count']  # Should decrease
                
                print(f"Inventory after raw material creation: {final_pieces} pieces")
                print(f"Expected pieces: {expected_pieces}")
                
                if final_pieces == expected_pieces:
                    self.log_test("Inventory deduction after raw material creation", True,
                                 f"Inventory correctly decreased from {initial_pieces} to {final_pieces} pieces")
                elif final_pieces > initial_pieces:
                    self.log_test("Inventory deduction after raw material creation", False,
                                 f"BUG: Inventory INCREASED from {initial_pieces} to {final_pieces} instead of decreasing")
                else:
                    self.log_test("Inventory deduction after raw material creation", False,
                                 f"Incorrect deduction: expected {expected_pieces}, got {final_pieces}")
            else:
                self.log_test("Get inventory after raw material creation", False, "Failed to get updated inventory")
        else:
            error_msg = raw_material_response.text if raw_material_response else "No response"
            self.log_test("Create raw material", False, f"Failed to create raw material: {error_msg}")
        
        # Test 3: Try to create raw material with insufficient inventory
        print(f"\nTesting insufficient inventory scenario...")
        
        insufficient_raw_material_data = {
            "material_type": "BUR",
            "inner_diameter": 20.0,
            "outer_diameter": 30.0,
            "height": 15.0,
            "pieces_count": 50,  # More than available
            "unit_code": "BUR-20x30-INSUFFICIENT",
            "cost_per_mm": 2.5
        }
        
        insufficient_response = self.make_request("POST", "/raw-materials", insufficient_raw_material_data)
        if insufficient_response and insufficient_response.status_code == 400:
            self.log_test("Raw material creation with insufficient inventory", True,
                         "Correctly rejected raw material creation due to insufficient inventory")
        elif insufficient_response and insufficient_response.status_code == 200:
            self.log_test("Raw material creation with insufficient inventory", False,
                         "BUG: Raw material created despite insufficient inventory")
        else:
            error_msg = insufficient_response.text if insufficient_response else "No response"
            self.log_test("Raw material creation with insufficient inventory", False,
                         f"Unexpected response: {error_msg}")

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n=== Cleaning up test data ===")
        
        # Delete invoices
        for invoice_id in self.created_data['invoices']:
            response = self.make_request("DELETE", f"/invoices/{invoice_id}")
            if response and response.status_code == 200:
                print(f"Deleted invoice: {invoice_id}")
        
        # Delete raw materials
        for material_id in self.created_data['raw_materials']:
            response = self.make_request("DELETE", f"/raw-materials/{material_id}")
            if response and response.status_code == 200:
                print(f"Deleted raw material: {material_id}")
        
        # Delete inventory items
        for item_id in self.created_data['inventory_items']:
            response = self.make_request("DELETE", f"/inventory/{item_id}")
            if response and response.status_code == 200:
                print(f"Deleted inventory item: {item_id}")
        
        # Delete customers
        for customer_id in self.created_data['customers']:
            response = self.make_request("DELETE", f"/customers/{customer_id}")
            if response and response.status_code == 200:
                print(f"Deleted customer: {customer_id}")

    def run_focused_tests(self):
        """Run all focused tests"""
        print("🔍 Starting Focused Backend Testing for Latest Bug Fixes")
        print("=" * 60)
        
        try:
            # Run the three focused tests
            self.test_payment_method_treasury_mapping()
            self.test_inventory_transactions_api()
            self.test_inventory_raw_materials_integration()
            
        except Exception as e:
            print(f"Critical error during testing: {str(e)}")
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 FOCUSED TEST SUMMARY")
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
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = FocusedAPITester()
    success = tester.run_focused_tests()
    sys.exit(0 if success else 1)