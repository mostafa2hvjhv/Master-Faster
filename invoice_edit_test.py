#!/usr/bin/env python3
"""
Invoice Editing Functionality Test
اختبار وظيفة تحرير الفواتير

Testing specific user-reported issues:
1. Product type field cannot be edited (حقل نوع المنتج لا يمكن التعتيل)
2. When saving invoice edits, all invoices disappear (عند حفظ تعديل الفاتوره تختفي كل الفواتير)
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class InvoiceEditTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_data = {
            'customers': [],
            'suppliers': [],
            'local_products': [],
            'invoices': []
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
    
    def setup_test_data(self):
        """Create test data needed for invoice editing tests"""
        print("\n=== Setting Up Test Data ===")
        
        # Create test customer
        try:
            customer_data = {
                "name": "عميل اختبار تحرير الفواتير",
                "phone": "01234567890",
                "address": "عنوان اختبار"
            }
            response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if response.status_code == 200:
                customer = response.json()
                self.created_data['customers'].append(customer)
                self.log_test("Create test customer", True, f"Customer ID: {customer['id']}")
            else:
                self.log_test("Create test customer", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create test customer", False, str(e))
            return False
        
        # Create test supplier for local products
        try:
            supplier_data = {
                "name": "مورد اختبار تحرير الفواتير",
                "phone": "01111111111",
                "address": "عنوان المورد"
            }
            response = self.session.post(f"{BACKEND_URL}/suppliers", json=supplier_data)
            if response.status_code == 200:
                supplier = response.json()
                self.created_data['suppliers'].append(supplier)
                self.log_test("Create test supplier", True, f"Supplier ID: {supplier['id']}")
            else:
                self.log_test("Create test supplier", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create test supplier", False, str(e))
            return False
        
        # Create test local product
        try:
            local_product_data = {
                "name": "منتج محلي اختبار تحرير",
                "supplier_id": self.created_data['suppliers'][0]['id'],
                "purchase_price": 25.0,
                "selling_price": 40.0,
                "current_stock": 100
            }
            response = self.session.post(f"{BACKEND_URL}/local-products", json=local_product_data)
            if response.status_code == 200:
                local_product = response.json()
                self.created_data['local_products'].append(local_product)
                self.log_test("Create test local product", True, f"Product ID: {local_product['id']}")
            else:
                self.log_test("Create test local product", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create test local product", False, str(e))
            return False
        
        return True
    
    def create_test_invoice_with_mixed_products(self):
        """Create a test invoice with both manufactured and local products"""
        print("\n=== Creating Test Invoice with Mixed Products ===")
        
        try:
            # Create invoice with both manufactured and local products
            invoice_data = {
                "customer_id": self.created_data['customers'][0]['id'],
                "customer_name": self.created_data['customers'][0]['name'],
                "invoice_title": "فاتورة اختبار تحرير مختلطة",
                "supervisor_name": "مشرف الاختبار",
                "payment_method": "نقدي",
                "discount_type": "amount",
                "discount_value": 10.0,
                "items": [
                    {
                        # Manufactured product
                        "seal_type": "RSL",
                        "material_type": "NBR",
                        "inner_diameter": 20.0,
                        "outer_diameter": 40.0,
                        "height": 10.0,
                        "quantity": 2,
                        "unit_price": 15.0,
                        "total_price": 30.0,
                        "product_type": "manufactured",
                        "material_used": "N-1"
                    },
                    {
                        # Local product
                        "product_name": "منتج محلي اختبار تحرير",
                        "quantity": 3,
                        "unit_price": 40.0,
                        "total_price": 120.0,
                        "product_type": "local",
                        "supplier": self.created_data['suppliers'][0]['name'],
                        "purchase_price": 25.0,
                        "selling_price": 40.0,
                        "local_product_details": {
                            "name": "منتج محلي اختبار تحرير",
                            "supplier": self.created_data['suppliers'][0]['name'],
                            "product_size": "50 مم",
                            "product_type": "خاتم زيت"
                        }
                    }
                ]
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                invoice = response.json()
                self.created_data['invoices'].append(invoice)
                self.log_test("Create mixed invoice", True, 
                            f"Invoice: {invoice['invoice_number']}, Total: {invoice['total_amount']} ج.م")
                return invoice
            else:
                self.log_test("Create mixed invoice", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            self.log_test("Create mixed invoice", False, str(e))
            return None
    
    def test_get_invoices_before_edit(self):
        """Test GET /api/invoices endpoint before editing"""
        print("\n=== Testing GET /api/invoices Before Edit ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            if response.status_code == 200:
                invoices = response.json()
                invoice_count = len(invoices)
                self.log_test("GET /api/invoices before edit", True, 
                            f"Found {invoice_count} invoices")
                
                # Verify our test invoice is in the list
                test_invoice_found = False
                for invoice in invoices:
                    if invoice.get('invoice_title') == 'فاتورة اختبار تحرير مختلطة':
                        test_invoice_found = True
                        self.log_test("Test invoice found in list", True, 
                                    f"Invoice: {invoice['invoice_number']}")
                        break
                
                if not test_invoice_found:
                    self.log_test("Test invoice found in list", False, 
                                "Test invoice not found in invoice list")
                
                return invoice_count
            else:
                self.log_test("GET /api/invoices before edit", False, 
                            f"Status: {response.status_code}")
                return 0
        except Exception as e:
            self.log_test("GET /api/invoices before edit", False, str(e))
            return 0
    
    def test_get_single_invoice(self, invoice_id: str):
        """Test GET /api/invoices/{id} endpoint"""
        print("\n=== Testing GET /api/invoices/{id} ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if response.status_code == 200:
                invoice = response.json()
                self.log_test("GET single invoice", True, 
                            f"Invoice: {invoice['invoice_number']}, Items: {len(invoice['items'])}")
                
                # Verify both product types are present
                manufactured_items = [item for item in invoice['items'] if item.get('product_type') == 'manufactured']
                local_items = [item for item in invoice['items'] if item.get('product_type') == 'local']
                
                self.log_test("Manufactured items present", len(manufactured_items) > 0, 
                            f"Found {len(manufactured_items)} manufactured items")
                self.log_test("Local items present", len(local_items) > 0, 
                            f"Found {len(local_items)} local items")
                
                return invoice
            else:
                self.log_test("GET single invoice", False, 
                            f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("GET single invoice", False, str(e))
            return None
    
    def test_edit_invoice_product_types(self, invoice_id: str):
        """Test editing invoice with focus on product type changes"""
        print("\n=== Testing Invoice Edit - Product Type Changes ===")
        
        try:
            # First get the current invoice
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if response.status_code != 200:
                self.log_test("Get invoice for editing", False, f"Status: {response.status_code}")
                return False
            
            current_invoice = response.json()
            
            # Modify the invoice - change product types and details
            updated_items = []
            for item in current_invoice['items']:
                if item.get('product_type') == 'manufactured':
                    # Try to change manufactured product details
                    updated_item = item.copy()
                    updated_item['seal_type'] = 'RS'  # Change seal type
                    updated_item['material_type'] = 'BUR'  # Change material type
                    updated_item['inner_diameter'] = 25.0  # Change diameter
                    updated_item['quantity'] = 3  # Change quantity
                    updated_item['unit_price'] = 20.0  # Change price
                    updated_item['total_price'] = 60.0  # Update total
                    updated_items.append(updated_item)
                elif item.get('product_type') == 'local':
                    # Try to change local product details
                    updated_item = item.copy()
                    updated_item['product_name'] = 'منتج محلي معدل'  # Change name
                    updated_item['quantity'] = 5  # Change quantity
                    updated_item['unit_price'] = 45.0  # Change price
                    updated_item['total_price'] = 225.0  # Update total
                    # Try to change product type details
                    if 'local_product_details' in updated_item:
                        updated_item['local_product_details']['product_size'] = '60 مم'
                        updated_item['local_product_details']['product_type'] = 'حلقة مطاطية'
                    updated_items.append(updated_item)
            
            # Update invoice data
            update_data = {
                'invoice_title': 'فاتورة اختبار تحرير معدلة',
                'supervisor_name': 'مشرف معدل',
                'items': updated_items,
                'discount_type': 'percentage',
                'discount_value': 15.0
            }
            
            # Send PUT request to update invoice
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            if response.status_code == 200:
                self.log_test("PUT /api/invoices/{id} - Edit invoice", True, 
                            "Invoice updated successfully")
                
                # Verify the changes were saved
                response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
                if response.status_code == 200:
                    updated_invoice = response.json()
                    
                    # Check if title was updated
                    title_updated = updated_invoice.get('invoice_title') == 'فاتورة اختبار تحرير معدلة'
                    self.log_test("Invoice title updated", title_updated, 
                                f"New title: {updated_invoice.get('invoice_title')}")
                    
                    # Check if supervisor was updated
                    supervisor_updated = updated_invoice.get('supervisor_name') == 'مشرف معدل'
                    self.log_test("Supervisor name updated", supervisor_updated, 
                                f"New supervisor: {updated_invoice.get('supervisor_name')}")
                    
                    # Check if product types can be edited
                    for item in updated_invoice['items']:
                        if item.get('product_type') == 'manufactured':
                            seal_updated = item.get('seal_type') == 'RS'
                            material_updated = item.get('material_type') == 'BUR'
                            self.log_test("Manufactured product type editable", 
                                        seal_updated and material_updated,
                                        f"Seal: {item.get('seal_type')}, Material: {item.get('material_type')}")
                        elif item.get('product_type') == 'local':
                            name_updated = item.get('product_name') == 'منتج محلي معدل'
                            details_updated = False
                            if 'local_product_details' in item:
                                details_updated = (item['local_product_details'].get('product_size') == '60 مم' and
                                                 item['local_product_details'].get('product_type') == 'حلقة مطاطية')
                            self.log_test("Local product type editable", 
                                        name_updated and details_updated,
                                        f"Name: {item.get('product_name')}, Details updated: {details_updated}")
                    
                    return True
                else:
                    self.log_test("Verify invoice changes", False, 
                                f"Status: {response.status_code}")
                    return False
            else:
                self.log_test("PUT /api/invoices/{id} - Edit invoice", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Edit invoice product types", False, str(e))
            return False
    
    def test_get_invoices_after_edit(self, original_count: int):
        """Test GET /api/invoices endpoint after editing to ensure invoices don't disappear"""
        print("\n=== Testing GET /api/invoices After Edit ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            if response.status_code == 200:
                invoices = response.json()
                new_count = len(invoices)
                
                # Critical test: invoices should not disappear after editing
                invoices_preserved = new_count >= original_count
                self.log_test("Invoices preserved after edit", invoices_preserved, 
                            f"Before: {original_count}, After: {new_count}")
                
                if not invoices_preserved:
                    self.log_test("CRITICAL ISSUE", False, 
                                "Invoices disappeared after editing - this matches user report!")
                    return False
                
                # Verify our edited invoice is still in the list
                edited_invoice_found = False
                for invoice in invoices:
                    if invoice.get('invoice_title') == 'فاتورة اختبار تحرير معدلة':
                        edited_invoice_found = True
                        self.log_test("Edited invoice found in list", True, 
                                    f"Invoice: {invoice['invoice_number']}")
                        break
                
                if not edited_invoice_found:
                    self.log_test("Edited invoice found in list", False, 
                                "Edited invoice not found in invoice list")
                
                return True
            else:
                self.log_test("GET /api/invoices after edit", False, 
                            f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("GET /api/invoices after edit", False, str(e))
            return False
    
    def test_add_new_item_to_invoice(self, invoice_id: str):
        """Test adding a new item to existing invoice during edit"""
        print("\n=== Testing Add New Item During Edit ===")
        
        try:
            # Get current invoice
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if response.status_code != 200:
                self.log_test("Get invoice for adding item", False, f"Status: {response.status_code}")
                return False
            
            current_invoice = response.json()
            current_items = current_invoice['items'].copy()
            
            # Add a new manufactured item
            new_item = {
                "seal_type": "B17",
                "material_type": "VT",
                "inner_diameter": 30.0,
                "outer_diameter": 50.0,
                "height": 8.0,
                "quantity": 1,
                "unit_price": 25.0,
                "total_price": 25.0,
                "product_type": "manufactured",
                "material_used": "V-1"
            }
            
            current_items.append(new_item)
            
            # Update invoice with new item
            update_data = {
                'items': current_items,
                'invoice_title': 'فاتورة اختبار مع عنصر جديد'
            }
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            if response.status_code == 200:
                self.log_test("Add new item to invoice", True, "New item added successfully")
                
                # Verify the new item was added
                response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
                if response.status_code == 200:
                    updated_invoice = response.json()
                    item_count = len(updated_invoice['items'])
                    expected_count = len(current_invoice['items']) + 1
                    
                    item_added = item_count == expected_count
                    self.log_test("New item count correct", item_added, 
                                f"Expected: {expected_count}, Actual: {item_count}")
                    
                    # Check if the new item has correct details
                    new_item_found = False
                    for item in updated_invoice['items']:
                        if (item.get('seal_type') == 'B17' and 
                            item.get('material_type') == 'VT' and
                            item.get('inner_diameter') == 30.0):
                            new_item_found = True
                            break
                    
                    self.log_test("New item details correct", new_item_found, 
                                "New B17/VT item found with correct specifications")
                    
                    return True
                else:
                    self.log_test("Verify new item added", False, f"Status: {response.status_code}")
                    return False
            else:
                self.log_test("Add new item to invoice", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Add new item to invoice", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all invoice editing tests"""
        print("🔧 Starting Invoice Editing Functionality Tests")
        print("=" * 60)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return
        
        # Create test invoice
        test_invoice = self.create_test_invoice_with_mixed_products()
        if not test_invoice:
            print("❌ Failed to create test invoice. Aborting tests.")
            return
        
        invoice_id = test_invoice['id']
        
        # Test 1: Get invoices before edit
        original_count = self.test_get_invoices_before_edit()
        
        # Test 2: Get single invoice
        single_invoice = self.test_get_single_invoice(invoice_id)
        if not single_invoice:
            print("❌ Failed to get single invoice. Aborting remaining tests.")
            return
        
        # Test 3: Edit invoice (focus on product types)
        edit_success = self.test_edit_invoice_product_types(invoice_id)
        
        # Test 4: Critical test - ensure invoices don't disappear after edit
        self.test_get_invoices_after_edit(original_count)
        
        # Test 5: Add new item during edit
        self.test_add_new_item_to_invoice(invoice_id)
        
        # Final verification
        self.test_get_invoices_after_edit(original_count)
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['details']}")
        
        # Check for critical issues matching user reports
        critical_issues = []
        for result in self.test_results:
            if not result['success']:
                if 'product type' in result['test'].lower() or 'editable' in result['test'].lower():
                    critical_issues.append(f"Product type editing issue: {result['test']}")
                elif 'preserved' in result['test'].lower() or 'disappear' in result['details'].lower():
                    critical_issues.append(f"Invoice disappearing issue: {result['test']}")
        
        if critical_issues:
            print("\n🔥 CRITICAL ISSUES MATCHING USER REPORTS:")
            for issue in critical_issues:
                print(f"   🔥 {issue}")
        else:
            print("\n✅ No critical issues found matching user reports!")

if __name__ == "__main__":
    tester = InvoiceEditTester()
    tester.run_all_tests()