#!/usr/bin/env python3
"""
Focused Invoice Editing Test - User Reported Issues
اختبار مركز لمشاكل تحرير الفواتير المبلغ عنها من المستخدم

Specific Issues to Test:
1. "حقل نوع المنتج لا يمكن التعتيل" (product type field cannot be edited)
2. "عند حفظ تعديل الفاتوره تختفي كل الفواتير" (when saving invoice edits, all invoices disappear)
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class FocusedInvoiceEditTester:
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
            'details': details
        })
    
    def test_user_reported_issues(self):
        """Test the specific issues reported by the user"""
        print("🔍 Testing User Reported Issues")
        print("=" * 50)
        
        # Step 1: Get current invoice count
        print("\n1️⃣ Getting current invoice count...")
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            if response.status_code == 200:
                initial_invoices = response.json()
                initial_count = len(initial_invoices)
                self.log_test("Get initial invoice count", True, f"Found {initial_count} invoices")
                
                if initial_count == 0:
                    print("⚠️ No invoices found. Creating a test invoice first...")
                    return self.create_and_test_invoice()
                
                # Use the first invoice for testing
                test_invoice = initial_invoices[0]
                invoice_id = test_invoice['id']
                print(f"📋 Using invoice: {test_invoice['invoice_number']} for testing")
                
            else:
                self.log_test("Get initial invoice count", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get initial invoice count", False, str(e))
            return False
        
        # Step 2: Test product type editing (Issue #1)
        print(f"\n2️⃣ Testing product type editing (Issue #1)...")
        success = self.test_product_type_editing(invoice_id)
        
        # Step 3: Test invoice preservation after edit (Issue #2)
        print(f"\n3️⃣ Testing invoice preservation after edit (Issue #2)...")
        self.test_invoice_preservation_after_edit(initial_count)
        
        return success
    
    def test_product_type_editing(self, invoice_id: str):
        """Test if product type fields can be edited"""
        try:
            # Get current invoice
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if response.status_code != 200:
                self.log_test("Get invoice for product type test", False, f"Status: {response.status_code}")
                return False
            
            original_invoice = response.json()
            print(f"   Original invoice has {len(original_invoice['items'])} items")
            
            # Test editing different product type fields
            updated_items = []
            product_type_changes_made = False
            
            for i, item in enumerate(original_invoice['items']):
                updated_item = item.copy()
                
                if item.get('product_type') == 'manufactured':
                    print(f"   📦 Testing manufactured product editing (Item {i+1})")
                    # Try to change manufactured product fields
                    if 'seal_type' in item:
                        original_seal = item['seal_type']
                        new_seal = 'B17' if original_seal != 'B17' else 'RSL'
                        updated_item['seal_type'] = new_seal
                        print(f"      Changing seal_type: {original_seal} → {new_seal}")
                        product_type_changes_made = True
                    
                    if 'material_type' in item:
                        original_material = item['material_type']
                        new_material = 'BUR' if original_material != 'BUR' else 'NBR'
                        updated_item['material_type'] = new_material
                        print(f"      Changing material_type: {original_material} → {new_material}")
                        product_type_changes_made = True
                
                elif item.get('product_type') == 'local':
                    print(f"   🏪 Testing local product editing (Item {i+1})")
                    # Try to change local product fields
                    if 'product_name' in item:
                        original_name = item['product_name']
                        new_name = f"{original_name} - معدل"
                        updated_item['product_name'] = new_name
                        print(f"      Changing product_name: {original_name} → {new_name}")
                        product_type_changes_made = True
                    
                    # Try to change local product details
                    if 'local_product_details' in item and item['local_product_details']:
                        details = updated_item['local_product_details'].copy()
                        if 'product_type' in details:
                            original_type = details['product_type']
                            new_type = 'نوع معدل'
                            details['product_type'] = new_type
                            updated_item['local_product_details'] = details
                            print(f"      Changing local product_type: {original_type} → {new_type}")
                            product_type_changes_made = True
                
                updated_items.append(updated_item)
            
            if not product_type_changes_made:
                self.log_test("Product type changes attempted", False, "No product type fields found to modify")
                return False
            
            # Send update request
            update_data = {
                'items': updated_items,
                'invoice_title': f"{original_invoice.get('invoice_title', 'فاتورة')} - اختبار تحرير نوع المنتج"
            }
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            if response.status_code == 200:
                self.log_test("Product type edit request", True, "Update request successful")
                
                # Verify changes were saved
                response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
                if response.status_code == 200:
                    updated_invoice = response.json()
                    
                    # Check if product type changes were preserved
                    changes_preserved = True
                    for i, (original_item, updated_item) in enumerate(zip(original_invoice['items'], updated_invoice['items'])):
                        if original_item.get('product_type') == 'manufactured':
                            if (original_item.get('seal_type') != updated_item.get('seal_type') or
                                original_item.get('material_type') != updated_item.get('material_type')):
                                print(f"      ✅ Manufactured product changes preserved (Item {i+1})")
                            else:
                                print(f"      ❌ Manufactured product changes NOT preserved (Item {i+1})")
                                changes_preserved = False
                        
                        elif original_item.get('product_type') == 'local':
                            if original_item.get('product_name') != updated_item.get('product_name'):
                                print(f"      ✅ Local product name change preserved (Item {i+1})")
                            else:
                                print(f"      ❌ Local product name change NOT preserved (Item {i+1})")
                                changes_preserved = False
                    
                    self.log_test("Product type fields can be edited", changes_preserved, 
                                "Product type changes were preserved" if changes_preserved else "Product type changes were NOT preserved")
                    
                    return changes_preserved
                else:
                    self.log_test("Verify product type changes", False, f"Status: {response.status_code}")
                    return False
            else:
                self.log_test("Product type edit request", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Product type editing test", False, str(e))
            return False
    
    def test_invoice_preservation_after_edit(self, initial_count: int):
        """Test if invoices disappear after editing (Critical Issue #2)"""
        try:
            # Get invoice count after editing
            response = self.session.get(f"{BACKEND_URL}/invoices")
            if response.status_code == 200:
                current_invoices = response.json()
                current_count = len(current_invoices)
                
                # This is the critical test - invoices should NOT disappear
                invoices_preserved = current_count >= initial_count
                
                if invoices_preserved:
                    self.log_test("CRITICAL: Invoices preserved after edit", True, 
                                f"Before: {initial_count}, After: {current_count} - No invoices disappeared ✅")
                else:
                    self.log_test("CRITICAL: Invoices preserved after edit", False, 
                                f"Before: {initial_count}, After: {current_count} - INVOICES DISAPPEARED! 🚨")
                    print("   🔥 This matches the user's report: 'عند حفظ تعديل الفاتوره تختفي كل الفواتير'")
                
                # Additional check: verify all original invoices are still there
                if current_count == initial_count:
                    print("   ✅ Invoice count maintained - no invoices lost")
                elif current_count > initial_count:
                    print(f"   ℹ️ Invoice count increased by {current_count - initial_count} (possibly new test invoices)")
                else:
                    print(f"   🚨 Invoice count decreased by {initial_count - current_count} - INVOICES LOST!")
                
                return invoices_preserved
            else:
                self.log_test("Get invoices after edit", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Invoice preservation test", False, str(e))
            return False
    
    def create_and_test_invoice(self):
        """Create a test invoice and then test editing"""
        print("📝 Creating test invoice for editing tests...")
        
        try:
            # Create a simple test customer first
            customer_data = {
                "name": "عميل اختبار تحرير سريع",
                "phone": "01000000000"
            }
            response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if response.status_code != 200:
                self.log_test("Create test customer", False, f"Status: {response.status_code}")
                return False
            
            customer = response.json()
            
            # Create test invoice with mixed products
            invoice_data = {
                "customer_id": customer['id'],
                "customer_name": customer['name'],
                "invoice_title": "فاتورة اختبار تحرير سريع",
                "payment_method": "نقدي",
                "items": [
                    {
                        "seal_type": "RSL",
                        "material_type": "NBR",
                        "inner_diameter": 20.0,
                        "outer_diameter": 40.0,
                        "height": 10.0,
                        "quantity": 1,
                        "unit_price": 15.0,
                        "total_price": 15.0,
                        "product_type": "manufactured"
                    }
                ]
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                invoice = response.json()
                self.log_test("Create test invoice", True, f"Invoice: {invoice['invoice_number']}")
                
                # Now test with this invoice
                return self.test_user_reported_issues()
            else:
                self.log_test("Create test invoice", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create and test invoice", False, str(e))
            return False
    
    def print_summary(self):
        """Print test summary focusing on user issues"""
        print("\n" + "=" * 60)
        print("📋 USER ISSUE TESTING SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        # Check specific user issues
        product_type_issue = False
        invoice_disappear_issue = False
        
        for result in self.test_results:
            if 'product type' in result['test'].lower() and not result['success']:
                product_type_issue = True
            if 'preserved after edit' in result['test'].lower() and not result['success']:
                invoice_disappear_issue = True
        
        print("\n🔍 USER REPORTED ISSUES STATUS:")
        print(f"1️⃣ Product type editing issue: {'❌ CONFIRMED' if product_type_issue else '✅ NOT FOUND'}")
        print(f"2️⃣ Invoices disappearing issue: {'❌ CONFIRMED' if invoice_disappear_issue else '✅ NOT FOUND'}")
        
        if product_type_issue or invoice_disappear_issue:
            print("\n🚨 CRITICAL FINDINGS:")
            if product_type_issue:
                print("   - Product type fields cannot be edited (matches user report)")
            if invoice_disappear_issue:
                print("   - Invoices disappear after editing (matches user report)")
        else:
            print("\n✅ GOOD NEWS: Both reported issues appear to be resolved!")

if __name__ == "__main__":
    tester = FocusedInvoiceEditTester()
    success = tester.test_user_reported_issues()
    tester.print_summary()