#!/usr/bin/env python3
"""
User Requested Improvements Test - اختبار التحسينات المطلوبة من المستخدم
Testing both improvements:
1. Material sorting by priority: BUR-NBR-BT-BOOM-VT then size
2. Local product display in work orders (backend verification)
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class UserImprovementsTester:
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
    
    def test_inventory_material_priority_sorting(self):
        """Test GET /api/inventory sorting by material priority: BUR-NBR-BT-BOOM-VT then size"""
        print("\n=== Testing Inventory Material Priority Sorting ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/inventory")
            
            if response.status_code == 200:
                inventory_items = response.json()
                
                if not inventory_items:
                    self.log_test("Inventory Priority Sorting - Data Available", False, "No inventory items found")
                    return
                
                self.log_test("Inventory Priority Sorting - API Response", True, f"Retrieved {len(inventory_items)} inventory items")
                
                # Define expected material priority order: BUR-NBR-BT-BOOM-VT
                material_priority = {'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5}
                
                # Verify priority-based sorting
                is_priority_sorted = True
                priority_errors = []
                
                for i in range(len(inventory_items) - 1):
                    current = inventory_items[i]
                    next_item = inventory_items[i + 1]
                    
                    current_material = current.get('material_type', '')
                    next_material = next_item.get('material_type', '')
                    
                    current_priority = material_priority.get(current_material, 6)
                    next_priority = material_priority.get(next_material, 6)
                    
                    # Check material priority order
                    if current_priority > next_priority:
                        is_priority_sorted = False
                        priority_errors.append(f"{current_material} (priority {current_priority}) before {next_material} (priority {next_priority})")
                        break  # Stop at first error
                
                # Check size sorting within same material type
                size_sorted_correctly = True
                size_errors = []
                
                current_material_group = []
                for item in inventory_items:
                    if not current_material_group or current_material_group[-1].get('material_type') == item.get('material_type'):
                        current_material_group.append(item)
                    else:
                        # Check sorting of completed group
                        if len(current_material_group) > 1:
                            for j in range(len(current_material_group) - 1):
                                curr = current_material_group[j]
                                next_item = current_material_group[j + 1]
                                
                                if (curr.get('inner_diameter', 0) > next_item.get('inner_diameter', 0) or
                                    (curr.get('inner_diameter', 0) == next_item.get('inner_diameter', 0) and 
                                     curr.get('outer_diameter', 0) > next_item.get('outer_diameter', 0))):
                                    size_sorted_correctly = False
                                    size_errors.append(f"{curr.get('material_type')} size error: {curr.get('inner_diameter')}×{curr.get('outer_diameter')} before {next_item.get('inner_diameter')}×{next_item.get('outer_diameter')}")
                        
                        current_material_group = [item]
                
                # Log results
                if is_priority_sorted:
                    self.log_test("Inventory Priority Sorting - Material Priority Order", True, 
                                "Correct priority order: BUR → NBR → BT → BOOM → VT")
                else:
                    self.log_test("Inventory Priority Sorting - Material Priority Order", False, 
                                f"Priority order error: {priority_errors[0] if priority_errors else 'Unknown error'}")
                
                if size_sorted_correctly:
                    self.log_test("Inventory Priority Sorting - Size Order Within Material", True, 
                                "Correct size sorting within each material type")
                else:
                    self.log_test("Inventory Priority Sorting - Size Order Within Material", False, 
                                f"Size sorting error: {size_errors[0] if size_errors else 'Unknown error'}")
                
                # Show material distribution
                material_counts = {}
                for item in inventory_items:
                    material = item.get('material_type', 'Unknown')
                    material_counts[material] = material_counts.get(material, 0) + 1
                
                distribution = ", ".join([f"{mat}: {count}" for mat, count in sorted(material_counts.items(), key=lambda x: material_priority.get(x[0], 6))])
                self.log_test("Inventory Priority Sorting - Material Distribution", True, distribution)
                
            else:
                self.log_test("Inventory Priority Sorting - API Response", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Inventory Priority Sorting - API Call", False, f"Exception: {str(e)}")
    
    def test_raw_materials_material_priority_sorting(self):
        """Test GET /api/raw-materials sorting by material priority: BUR-NBR-BT-BOOM-VT then size"""
        print("\n=== Testing Raw Materials Material Priority Sorting ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/raw-materials")
            
            if response.status_code == 200:
                raw_materials = response.json()
                
                if not raw_materials:
                    self.log_test("Raw Materials Priority Sorting - Data Available", False, "No raw materials found")
                    return
                
                self.log_test("Raw Materials Priority Sorting - API Response", True, f"Retrieved {len(raw_materials)} raw materials")
                
                # Define expected material priority order: BUR-NBR-BT-BOOM-VT
                material_priority = {'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5}
                
                # Verify priority-based sorting
                is_priority_sorted = True
                priority_errors = []
                
                for i in range(len(raw_materials) - 1):
                    current = raw_materials[i]
                    next_item = raw_materials[i + 1]
                    
                    current_material = current.get('material_type', '')
                    next_material = next_item.get('material_type', '')
                    
                    current_priority = material_priority.get(current_material, 6)
                    next_priority = material_priority.get(next_material, 6)
                    
                    # Check material priority order
                    if current_priority > next_priority:
                        is_priority_sorted = False
                        priority_errors.append(f"{current_material} (priority {current_priority}) before {next_material} (priority {next_priority})")
                        break  # Stop at first error
                
                # Log results
                if is_priority_sorted:
                    self.log_test("Raw Materials Priority Sorting - Material Priority Order", True, 
                                "Correct priority order: BUR → NBR → BT → BOOM → VT")
                else:
                    self.log_test("Raw Materials Priority Sorting - Material Priority Order", False, 
                                f"Priority order error: {priority_errors[0] if priority_errors else 'Unknown error'}")
                
                # Show material distribution and first few items
                material_counts = {}
                for item in raw_materials:
                    material = item.get('material_type', 'Unknown')
                    material_counts[material] = material_counts.get(material, 0) + 1
                
                distribution = ", ".join([f"{mat}: {count}" for mat, count in sorted(material_counts.items(), key=lambda x: material_priority.get(x[0], 6))])
                self.log_test("Raw Materials Priority Sorting - Material Distribution", True, distribution)
                
                # Show first few items as example
                example_items = []
                for item in raw_materials[:5]:
                    unit_code = item.get('unit_code', 'N/A')
                    example_items.append(f"{item.get('material_type', 'N/A')} {item.get('inner_diameter', 0)}×{item.get('outer_diameter', 0)} ({unit_code})")
                
                if example_items:
                    self.log_test("Raw Materials Priority Sorting - First 5 Items", True, 
                                f"Order: {' → '.join(example_items)}")
                
            else:
                self.log_test("Raw Materials Priority Sorting - API Response", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Raw Materials Priority Sorting - API Call", False, f"Exception: {str(e)}")
    
    def test_local_product_in_work_order(self):
        """Test local product display in work orders (backend data verification)"""
        print("\n=== Testing Local Product in Work Order ===")
        
        try:
            # First, create a supplier for our test
            supplier_data = {
                "name": "مورد اختبار للمنتجات المحلية",
                "phone": "01234567890",
                "address": "عنوان المورد"
            }
            
            supplier_response = self.session.post(f"{BACKEND_URL}/suppliers", json=supplier_data)
            if supplier_response.status_code != 200:
                self.log_test("Local Product Test - Supplier Creation", False, f"HTTP {supplier_response.status_code}")
                return
            
            supplier = supplier_response.json()
            self.created_items.append(('supplier', supplier.get('id')))
            self.log_test("Local Product Test - Supplier Creation", True, f"Created supplier: {supplier.get('name')}")
            
            # Create a local product
            local_product_data = {
                "name": "منتج محلي اختبار OR",
                "supplier_id": supplier.get('id'),
                "purchase_price": 25.0,
                "selling_price": 50.0,
                "current_stock": 10
            }
            
            product_response = self.session.post(f"{BACKEND_URL}/local-products", json=local_product_data)
            if product_response.status_code != 200:
                self.log_test("Local Product Test - Product Creation", False, f"HTTP {product_response.status_code}")
                return
            
            local_product = product_response.json()
            self.created_items.append(('local_product', local_product.get('id')))
            self.log_test("Local Product Test - Product Creation", True, f"Created local product: {local_product.get('name')}")
            
            # Create a customer for the invoice
            customer_data = {
                "name": "عميل اختبار المنتج المحلي",
                "phone": "01111111111"
            }
            
            customer_response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if customer_response.status_code != 200:
                self.log_test("Local Product Test - Customer Creation", False, f"HTTP {customer_response.status_code}")
                return
            
            customer = customer_response.json()
            self.created_items.append(('customer', customer.get('id')))
            self.log_test("Local Product Test - Customer Creation", True, f"Created customer: {customer.get('name')}")
            
            # Create an invoice with local product
            invoice_data = {
                "customer_id": customer.get('id'),
                "customer_name": customer.get('name'),
                "invoice_title": "فاتورة اختبار المنتج المحلي",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "product_type": "local",
                        "product_name": "منتج محلي اختبار OR",
                        "quantity": 2,
                        "unit_price": 50.0,
                        "total_price": 100.0,
                        "supplier": supplier.get('name'),
                        "purchase_price": 25.0,
                        "selling_price": 50.0,
                        "local_product_details": {
                            "name": "منتج محلي اختبار OR",
                            "supplier": supplier.get('name'),
                            "purchase_price": 25.0,
                            "selling_price": 50.0,
                            "product_size": "100",
                            "product_type": "OR"
                        },
                        # These should be null for local products but set for work order display
                        "seal_type": None,
                        "material_type": None,
                        "inner_diameter": None,
                        "outer_diameter": None,
                        "height": None
                    }
                ],
                "payment_method": "نقدي",
                "discount_type": "amount",
                "discount_value": 0.0
            }
            
            invoice_response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if invoice_response.status_code != 200:
                self.log_test("Local Product Test - Invoice Creation", False, f"HTTP {invoice_response.status_code}: {invoice_response.text}")
                return
            
            invoice = invoice_response.json()
            self.created_items.append(('invoice', invoice.get('id')))
            self.log_test("Local Product Test - Invoice Creation", True, f"Created invoice: {invoice.get('invoice_number')}")
            
            # Verify the invoice contains correct local product data
            invoice_item = invoice.get('items', [{}])[0]
            
            # Check that local product fields are properly set
            local_details = invoice_item.get('local_product_details', {})
            
            if local_details.get('product_type') == 'OR' and local_details.get('product_size') == '100':
                self.log_test("Local Product Test - Work Order Data Structure", True, 
                            f"Local product details correctly stored: type='{local_details.get('product_type')}', size='{local_details.get('product_size')}'")
            else:
                self.log_test("Local Product Test - Work Order Data Structure", False, 
                            f"Local product details incorrect: type='{local_details.get('product_type')}', size='{local_details.get('product_size')}'")
            
            # Check that manufactured product fields are null
            manufactured_fields_null = (
                invoice_item.get('seal_type') is None and
                invoice_item.get('material_type') is None and
                invoice_item.get('inner_diameter') is None
            )
            
            if manufactured_fields_null:
                self.log_test("Local Product Test - Manufactured Fields Null", True, 
                            "Manufactured product fields correctly set to null for local product")
            else:
                self.log_test("Local Product Test - Manufactured Fields Null", False, 
                            f"Manufactured fields not null: seal_type={invoice_item.get('seal_type')}, material_type={invoice_item.get('material_type')}")
            
            # Get today's work order to verify the invoice was added
            today = datetime.now().strftime("%Y-%m-%d")
            work_order_response = self.session.get(f"{BACKEND_URL}/work-orders/daily/{today}")
            
            if work_order_response.status_code == 200:
                work_order = work_order_response.json()
                
                # Check if our invoice is in the work order
                invoice_in_work_order = False
                work_order_invoice = None
                
                for wo_invoice in work_order.get('invoices', []):
                    if wo_invoice.get('id') == invoice.get('id'):
                        invoice_in_work_order = True
                        work_order_invoice = wo_invoice
                        break
                
                if invoice_in_work_order and work_order_invoice:
                    self.log_test("Local Product Test - Work Order Integration", True, 
                                f"Invoice with local product added to daily work order")
                    
                    # Verify the local product data is preserved in work order
                    wo_item = work_order_invoice.get('items', [{}])[0]
                    wo_local_details = wo_item.get('local_product_details', {})
                    
                    if wo_local_details.get('product_type') == 'OR' and wo_local_details.get('product_size') == '100':
                        self.log_test("Local Product Test - Work Order Data Preservation", True, 
                                    "Local product data correctly preserved in work order for display as: نوع السيل=OR, المقاس=100, الخامة=محلي")
                    else:
                        self.log_test("Local Product Test - Work Order Data Preservation", False, 
                                    f"Local product data not preserved correctly in work order")
                else:
                    self.log_test("Local Product Test - Work Order Integration", False, 
                                "Invoice with local product not found in daily work order")
            else:
                self.log_test("Local Product Test - Work Order Retrieval", False, 
                            f"HTTP {work_order_response.status_code}")
                
        except Exception as e:
            self.log_test("Local Product Test - Exception", False, f"Exception: {str(e)}")
    
    def cleanup_created_items(self):
        """Clean up any items created during testing"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Cleanup in reverse order to handle dependencies
        for item_type, item_id in reversed(self.created_items):
            try:
                if item_type == 'supplier':
                    response = self.session.delete(f"{BACKEND_URL}/suppliers/{item_id}")
                elif item_type == 'local_product':
                    response = self.session.delete(f"{BACKEND_URL}/local-products/{item_id}")
                elif item_type == 'customer':
                    response = self.session.delete(f"{BACKEND_URL}/customers/{item_id}")
                elif item_type == 'invoice':
                    response = self.session.delete(f"{BACKEND_URL}/invoices/{item_id}")
                else:
                    continue
                
                if response.status_code == 200:
                    self.log_test(f"Cleanup - {item_type} {item_id[:8]}...", True, "Successfully deleted")
                else:
                    self.log_test(f"Cleanup - {item_type} {item_id[:8]}...", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Cleanup - {item_type} {item_id[:8]}...", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all user improvement tests"""
        print("🧪 Starting User Requested Improvements Tests")
        print("=" * 60)
        
        # Test 1: Material priority sorting for inventory and raw materials
        self.test_inventory_material_priority_sorting()
        self.test_raw_materials_material_priority_sorting()
        
        # Test 2: Local product display in work orders (backend verification)
        self.test_local_product_in_work_order()
        
        # Cleanup
        self.cleanup_created_items()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 USER IMPROVEMENTS TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Categorize results
        sorting_tests = [r for r in self.test_results if 'Priority Sorting' in r['test']]
        local_product_tests = [r for r in self.test_results if 'Local Product Test' in r['test']]
        
        sorting_passed = sum(1 for r in sorting_tests if r['success'])
        local_product_passed = sum(1 for r in local_product_tests if r['success'])
        
        print(f"\n📈 Results by Category:")
        print(f"Material Priority Sorting: {sorting_passed}/{len(sorting_tests)} ✅")
        print(f"Local Product in Work Order: {local_product_passed}/{len(local_product_tests)} ✅")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = UserImprovementsTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)