#!/usr/bin/env python3
"""
Invoice Editing Functionality Test for Master Seal System
اختبار وظيفة تحرير الفواتير لنظام ماستر سيل

Focus Areas:
1. Test invoice list fetching (GET /api/invoices)
2. Test invoice update (PUT /api/invoices/{invoice_id})
3. Test invoice fetch after update
4. Test edge cases with different discount types, empty fields
5. Verify invoices don't "disappear" from frontend after editing
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class InvoiceEditingTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_invoices = []
        self.created_customers = []
        
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
        """Create test customers and invoices for editing tests"""
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
                self.created_customers.append(customer)
                self.log_test("Create test customer", True, f"Customer ID: {customer['id']}")
            else:
                self.log_test("Create test customer", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create test customer", False, str(e))
            return False
        
        # Create multiple test invoices with different configurations
        invoice_configs = [
            {
                "title": "فاتورة اختبار تحرير - منتج مصنع",
                "items": [{
                    "seal_type": "RSL",
                    "material_type": "NBR", 
                    "inner_diameter": 20.0,
                    "outer_diameter": 40.0,
                    "height": 10.0,
                    "quantity": 5,
                    "unit_price": 15.0,
                    "total_price": 75.0,
                    "product_type": "manufactured"
                }],
                "payment_method": "نقدي",
                "discount_type": "amount",
                "discount_value": 5.0
            },
            {
                "title": "فاتورة اختبار تحرير - منتج محلي",
                "items": [{
                    "product_name": "خاتم زيت محلي",
                    "quantity": 3,
                    "unit_price": 25.0,
                    "total_price": 75.0,
                    "product_type": "local",
                    "supplier": "مورد اختبار",
                    "purchase_price": 20.0,
                    "selling_price": 25.0,
                    "local_product_details": {
                        "name": "خاتم زيت محلي",
                        "supplier": "مورد اختبار",
                        "purchase_price": 20.0,
                        "selling_price": 25.0,
                        "product_size": "30 مم",
                        "product_type": "خاتم زيت"
                    }
                }],
                "payment_method": "آجل",
                "discount_type": "percentage", 
                "discount_value": 10.0
            },
            {
                "title": "فاتورة اختبار تحرير - مختلطة",
                "items": [
                    {
                        "seal_type": "RS",
                        "material_type": "BUR",
                        "inner_diameter": 15.0,
                        "outer_diameter": 35.0,
                        "height": 8.0,
                        "quantity": 2,
                        "unit_price": 20.0,
                        "total_price": 40.0,
                        "product_type": "manufactured"
                    },
                    {
                        "product_name": "منتج محلي مختلط",
                        "quantity": 1,
                        "unit_price": 30.0,
                        "total_price": 30.0,
                        "product_type": "local",
                        "local_product_details": {
                            "name": "منتج محلي مختلط",
                            "supplier": "مورد آخر",
                            "product_size": "25 مم",
                            "product_type": "حلقة"
                        }
                    }
                ],
                "payment_method": "فودافون كاش وائل محمد",
                "discount_type": "amount",
                "discount_value": 0.0
            }
        ]
        
        for i, config in enumerate(invoice_configs):
            try:
                invoice_data = {
                    "customer_id": customer['id'],
                    "customer_name": customer['name'],
                    "invoice_title": config["title"],
                    "supervisor_name": f"مشرف اختبار {i+1}",
                    "items": config["items"],
                    "payment_method": config["payment_method"],
                    "discount_type": config["discount_type"],
                    "discount_value": config["discount_value"],
                    "notes": f"فاتورة اختبار رقم {i+1} لتحرير الفواتير"
                }
                
                response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
                if response.status_code == 200:
                    invoice = response.json()
                    self.created_invoices.append(invoice)
                    self.log_test(f"Create test invoice {i+1}", True, 
                                f"Invoice: {invoice['invoice_number']}, Total: {invoice.get('total_amount', 0)}")
                else:
                    self.log_test(f"Create test invoice {i+1}", False, 
                                f"Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Create test invoice {i+1}", False, str(e))
        
        return len(self.created_invoices) > 0
    
    def test_invoice_list_fetching(self):
        """Test GET /api/invoices - ensure it returns invoices properly"""
        print("\n=== Testing Invoice List Fetching ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            
            if response.status_code == 200:
                invoices = response.json()
                
                # Check if we get a list
                if isinstance(invoices, list):
                    self.log_test("Invoice list returns array", True, f"Found {len(invoices)} invoices")
                    
                    # Check if our test invoices are in the list
                    test_invoice_numbers = [inv['invoice_number'] for inv in self.created_invoices]
                    found_invoices = [inv for inv in invoices if inv.get('invoice_number') in test_invoice_numbers]
                    
                    if len(found_invoices) == len(self.created_invoices):
                        self.log_test("All test invoices found in list", True, 
                                    f"Found {len(found_invoices)}/{len(self.created_invoices)} test invoices")
                    else:
                        self.log_test("All test invoices found in list", False,
                                    f"Found {len(found_invoices)}/{len(self.created_invoices)} test invoices")
                    
                    # Check invoice structure
                    if invoices:
                        sample_invoice = invoices[0]
                        required_fields = ['id', 'invoice_number', 'customer_name', 'total_amount', 'items']
                        missing_fields = [field for field in required_fields if field not in sample_invoice]
                        
                        if not missing_fields:
                            self.log_test("Invoice structure complete", True, "All required fields present")
                        else:
                            self.log_test("Invoice structure complete", False, f"Missing fields: {missing_fields}")
                    
                else:
                    self.log_test("Invoice list returns array", False, f"Expected list, got {type(invoices)}")
            else:
                self.log_test("Invoice list API call", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Invoice list API call", False, str(e))
    
    def test_invoice_update_basic(self):
        """Test basic invoice update functionality"""
        print("\n=== Testing Basic Invoice Update ===")
        
        if not self.created_invoices:
            self.log_test("Invoice update test", False, "No test invoices available")
            return
        
        # Test updating the first invoice
        test_invoice = self.created_invoices[0]
        invoice_id = test_invoice['id']
        
        try:
            # Update invoice title and supervisor name
            update_data = {
                "invoice_title": "فاتورة محدثة - اختبار التحرير",
                "supervisor_name": "مشرف محدث",
                "notes": "تم تحديث هذه الفاتورة في الاختبار"
            }
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            
            if response.status_code == 200:
                self.log_test("Basic invoice update", True, "Invoice title and supervisor updated")
                
                # Verify the update by fetching the invoice
                get_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
                if get_response.status_code == 200:
                    updated_invoice = get_response.json()
                    
                    # Check if updates were applied
                    title_updated = updated_invoice.get('invoice_title') == update_data['invoice_title']
                    supervisor_updated = updated_invoice.get('supervisor_name') == update_data['supervisor_name']
                    notes_updated = updated_invoice.get('notes') == update_data['notes']
                    
                    if title_updated and supervisor_updated and notes_updated:
                        self.log_test("Invoice update verification", True, "All fields updated correctly")
                    else:
                        self.log_test("Invoice update verification", False, 
                                    f"Title: {title_updated}, Supervisor: {supervisor_updated}, Notes: {notes_updated}")
                else:
                    self.log_test("Invoice update verification", False, f"Get status: {get_response.status_code}")
            else:
                self.log_test("Basic invoice update", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Basic invoice update", False, str(e))
    
    def test_invoice_discount_update(self):
        """Test updating invoice with different discount types"""
        print("\n=== Testing Invoice Discount Update ===")
        
        if len(self.created_invoices) < 2:
            self.log_test("Discount update test", False, "Need at least 2 test invoices")
            return
        
        # Test updating discount on second invoice
        test_invoice = self.created_invoices[1]
        invoice_id = test_invoice['id']
        
        try:
            # Update with fixed amount discount
            update_data = {
                "discount_type": "amount",
                "discount_value": 15.0,
                "notes": "تحديث خصم ثابت"
            }
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            
            if response.status_code == 200:
                self.log_test("Fixed amount discount update", True, "Discount updated to 15.0 fixed")
                
                # Verify discount calculation
                get_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
                if get_response.status_code == 200:
                    updated_invoice = get_response.json()
                    
                    discount = updated_invoice.get('discount', 0)
                    discount_type = updated_invoice.get('discount_type')
                    discount_value = updated_invoice.get('discount_value')
                    
                    if discount == 15.0 and discount_type == "amount" and discount_value == 15.0:
                        self.log_test("Fixed discount calculation", True, f"Discount: {discount}")
                    else:
                        self.log_test("Fixed discount calculation", False, 
                                    f"Expected 15.0, got {discount}, type: {discount_type}")
                        
            else:
                self.log_test("Fixed amount discount update", False, f"Status: {response.status_code}")
            
            # Test updating to percentage discount
            update_data = {
                "discount_type": "percentage", 
                "discount_value": 20.0,
                "notes": "تحديث خصم نسبة مئوية"
            }
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            
            if response.status_code == 200:
                self.log_test("Percentage discount update", True, "Discount updated to 20% percentage")
                
                # Verify percentage calculation
                get_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
                if get_response.status_code == 200:
                    updated_invoice = get_response.json()
                    
                    subtotal = updated_invoice.get('subtotal', 0)
                    discount = updated_invoice.get('discount', 0)
                    expected_discount = (subtotal * 20.0) / 100
                    
                    if abs(discount - expected_discount) < 0.01:  # Allow small floating point differences
                        self.log_test("Percentage discount calculation", True, 
                                    f"Subtotal: {subtotal}, Discount: {discount} (20%)")
                    else:
                        self.log_test("Percentage discount calculation", False,
                                    f"Expected {expected_discount}, got {discount}")
            else:
                self.log_test("Percentage discount update", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Invoice discount update", False, str(e))
    
    def test_invoice_items_update(self):
        """Test updating invoice items"""
        print("\n=== Testing Invoice Items Update ===")
        
        if len(self.created_invoices) < 3:
            self.log_test("Items update test", False, "Need at least 3 test invoices")
            return
        
        # Test updating items on third invoice (mixed invoice)
        test_invoice = self.created_invoices[2]
        invoice_id = test_invoice['id']
        
        try:
            # Update items - modify quantities and add new item
            updated_items = [
                {
                    "seal_type": "RS",
                    "material_type": "BUR",
                    "inner_diameter": 15.0,
                    "outer_diameter": 35.0,
                    "height": 8.0,
                    "quantity": 5,  # Changed from 2 to 5
                    "unit_price": 20.0,
                    "total_price": 100.0,  # Updated total
                    "product_type": "manufactured"
                },
                {
                    "product_name": "منتج محلي محدث",
                    "quantity": 2,  # Changed from 1 to 2
                    "unit_price": 30.0,
                    "total_price": 60.0,  # Updated total
                    "product_type": "local",
                    "local_product_details": {
                        "name": "منتج محلي محدث",
                        "supplier": "مورد آخر",
                        "product_size": "25 مم",
                        "product_type": "حلقة"
                    }
                },
                {
                    "seal_type": "RSE",
                    "material_type": "NBR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 45.0,
                    "height": 12.0,
                    "quantity": 1,
                    "unit_price": 35.0,
                    "total_price": 35.0,
                    "product_type": "manufactured"
                }
            ]
            
            update_data = {
                "items": updated_items,
                "notes": "تحديث عناصر الفاتورة - تغيير الكميات وإضافة عنصر جديد"
            }
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            
            if response.status_code == 200:
                self.log_test("Invoice items update", True, "Items updated successfully")
                
                # Verify the update
                get_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
                if get_response.status_code == 200:
                    updated_invoice = get_response.json()
                    
                    items = updated_invoice.get('items', [])
                    if len(items) == 3:
                        self.log_test("Items count verification", True, f"Found {len(items)} items")
                        
                        # Check if totals were recalculated
                        expected_subtotal = sum(item['total_price'] for item in updated_items)
                        actual_subtotal = updated_invoice.get('subtotal', 0)
                        
                        if abs(actual_subtotal - expected_subtotal) < 0.01:
                            self.log_test("Subtotal recalculation", True, f"Subtotal: {actual_subtotal}")
                        else:
                            self.log_test("Subtotal recalculation", False, 
                                        f"Expected {expected_subtotal}, got {actual_subtotal}")
                    else:
                        self.log_test("Items count verification", False, f"Expected 3, got {len(items)}")
                else:
                    self.log_test("Items update verification", False, f"Get status: {get_response.status_code}")
            else:
                self.log_test("Invoice items update", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Invoice items update", False, str(e))
    
    def test_invoice_list_after_updates(self):
        """Test that invoice list still works correctly after updates and shows updated data"""
        print("\n=== Testing Invoice List After Updates ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            
            if response.status_code == 200:
                invoices = response.json()
                
                if isinstance(invoices, list):
                    self.log_test("Invoice list after updates", True, f"Retrieved {len(invoices)} invoices")
                    
                    # Check if our test invoices are still there
                    test_invoice_ids = [inv['id'] for inv in self.created_invoices]
                    found_invoices = [inv for inv in invoices if inv.get('id') in test_invoice_ids]
                    
                    if len(found_invoices) == len(self.created_invoices):
                        self.log_test("Test invoices still present", True, 
                                    f"All {len(self.created_invoices)} test invoices found")
                        
                        # Check if updates are reflected
                        updated_invoice = next((inv for inv in found_invoices 
                                              if inv.get('invoice_title') == "فاتورة محدثة - اختبار التحرير"), None)
                        
                        if updated_invoice:
                            self.log_test("Updated data reflected in list", True, 
                                        f"Found updated invoice: {updated_invoice['invoice_number']}")
                        else:
                            self.log_test("Updated data reflected in list", False, 
                                        "Updated invoice title not found in list")
                    else:
                        self.log_test("Test invoices still present", False,
                                    f"Found {len(found_invoices)}/{len(self.created_invoices)} test invoices")
                        
                        # This is the critical issue - invoices disappearing!
                        missing_ids = [inv_id for inv_id in test_invoice_ids 
                                     if not any(inv.get('id') == inv_id for inv in invoices)]
                        self.log_test("CRITICAL: Invoices disappeared", False, 
                                    f"Missing invoice IDs: {missing_ids}")
                else:
                    self.log_test("Invoice list after updates", False, f"Expected list, got {type(invoices)}")
            else:
                self.log_test("Invoice list after updates", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Invoice list after updates", False, str(e))
    
    def test_edge_cases(self):
        """Test edge cases with empty fields, null values, etc."""
        print("\n=== Testing Edge Cases ===")
        
        if not self.created_invoices:
            self.log_test("Edge cases test", False, "No test invoices available")
            return
        
        test_invoice = self.created_invoices[0]
        invoice_id = test_invoice['id']
        
        # Test 1: Update with empty/null fields
        try:
            update_data = {
                "invoice_title": "",  # Empty title
                "supervisor_name": None,  # Null supervisor
                "notes": "",  # Empty notes
                "discount_value": 0.0  # Zero discount
            }
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            
            if response.status_code == 200:
                self.log_test("Empty/null fields update", True, "Handled empty fields gracefully")
            else:
                self.log_test("Empty/null fields update", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Empty/null fields update", False, str(e))
        
        # Test 2: Update with invalid discount type
        try:
            update_data = {
                "discount_type": "invalid_type",
                "discount_value": 10.0
            }
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            
            # This should either handle gracefully or return appropriate error
            if response.status_code in [200, 400, 422]:
                self.log_test("Invalid discount type handling", True, f"Status: {response.status_code}")
            else:
                self.log_test("Invalid discount type handling", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid discount type handling", False, str(e))
        
        # Test 3: Update non-existent invoice
        try:
            fake_id = "non-existent-invoice-id"
            update_data = {"invoice_title": "Test"}
            
            response = self.session.put(f"{BACKEND_URL}/invoices/{fake_id}", json=update_data)
            
            if response.status_code == 404:
                self.log_test("Non-existent invoice update", True, "Correctly returned 404")
            else:
                self.log_test("Non-existent invoice update", False, f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Non-existent invoice update", False, str(e))
    
    def test_individual_invoice_fetch(self):
        """Test fetching individual invoices by ID"""
        print("\n=== Testing Individual Invoice Fetch ===")
        
        for i, invoice in enumerate(self.created_invoices):
            try:
                response = self.session.get(f"{BACKEND_URL}/invoices/{invoice['id']}")
                
                if response.status_code == 200:
                    fetched_invoice = response.json()
                    
                    # Verify essential fields
                    if (fetched_invoice.get('id') == invoice['id'] and 
                        fetched_invoice.get('invoice_number') == invoice['invoice_number']):
                        self.log_test(f"Individual invoice fetch {i+1}", True, 
                                    f"Invoice {invoice['invoice_number']} fetched correctly")
                    else:
                        self.log_test(f"Individual invoice fetch {i+1}", False, 
                                    "Invoice data mismatch")
                else:
                    self.log_test(f"Individual invoice fetch {i+1}", False, 
                                f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Individual invoice fetch {i+1}", False, str(e))
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Delete test invoices
        for invoice in self.created_invoices:
            try:
                response = self.session.delete(f"{BACKEND_URL}/invoices/{invoice['id']}")
                if response.status_code == 200:
                    self.log_test(f"Delete invoice {invoice['invoice_number']}", True, "Deleted successfully")
                else:
                    self.log_test(f"Delete invoice {invoice['invoice_number']}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Delete invoice {invoice['invoice_number']}", False, str(e))
        
        # Delete test customers
        for customer in self.created_customers:
            try:
                response = self.session.delete(f"{BACKEND_URL}/customers/{customer['id']}")
                if response.status_code == 200:
                    self.log_test(f"Delete customer {customer['name']}", True, "Deleted successfully")
                else:
                    self.log_test(f"Delete customer {customer['name']}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Delete customer {customer['name']}", False, str(e))
    
    def run_all_tests(self):
        """Run all invoice editing tests"""
        print("🔍 Starting Invoice Editing Functionality Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return
        
        # Core tests
        self.test_invoice_list_fetching()
        self.test_invoice_update_basic()
        self.test_invoice_discount_update()
        self.test_invoice_items_update()
        self.test_invoice_list_after_updates()
        self.test_individual_invoice_fetch()
        self.test_edge_cases()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 INVOICE EDITING TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n🚨 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['details']}")
        
        # Critical issues analysis
        critical_issues = []
        for result in self.test_results:
            if not result['success']:
                if "disappeared" in result['test'].lower() or "missing" in result['details'].lower():
                    critical_issues.append(result)
        
        if critical_issues:
            print(f"\n🔥 CRITICAL ISSUES DETECTED:")
            for issue in critical_issues:
                print(f"   🚨 {issue['test']}: {issue['details']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = InvoiceEditingTester()
    tester.run_all_tests()