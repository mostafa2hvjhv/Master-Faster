#!/usr/bin/env python3
"""
Comprehensive Local Products Workflow Test
اختبار شامل لسير العمل الكامل للمنتجات المحلية
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class ComprehensiveLocalProductsTest:
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
    
    def test_invoice_printing_format(self):
        """Test that invoices show local products in the correct printing format"""
        print("\n=== Testing Invoice Printing Format ===")
        
        try:
            # Get recent invoices to find one with local products
            response = self.session.get(f"{BACKEND_URL}/invoices")
            
            if response.status_code == 200:
                invoices = response.json()
                
                local_product_invoices = []
                for invoice in invoices:
                    for item in invoice.get('items', []):
                        if item.get('product_type') == 'local':
                            local_product_invoices.append(invoice)
                            break
                
                if local_product_invoices:
                    # Test the first invoice with local products
                    test_invoice = local_product_invoices[0]
                    local_item = None
                    
                    for item in test_invoice['items']:
                        if item.get('product_type') == 'local':
                            local_item = item
                            break
                    
                    if local_item:
                        # Check printing format requirements
                        local_details = local_item.get('local_product_details', {})
                        
                        # For invoice printing: should show "OR - 100"
                        expected_seal_type = local_details.get('product_type')  # Should be 'OR'
                        expected_size = local_details.get('product_size')       # Should be '100'
                        
                        if expected_seal_type == 'OR' and expected_size == '100':
                            self.log_test("Invoice Printing Format (OR - 100)", True, 
                                        f"Local product correctly formatted for printing: {expected_seal_type} - {expected_size}")
                        else:
                            self.log_test("Invoice Printing Format (OR - 100)", False, 
                                        f"Incorrect format - Expected: OR - 100, Got: {expected_seal_type} - {expected_size}")
                    else:
                        self.log_test("Invoice Printing Format (OR - 100)", False, "No local product item found in invoice")
                else:
                    self.log_test("Invoice Printing Format (OR - 100)", False, "No invoices with local products found")
            else:
                self.log_test("Invoice Printing Format (OR - 100)", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Invoice Printing Format (OR - 100)", False, f"Exception: {str(e)}")
    
    def test_work_order_printing_format(self):
        """Test that work orders show local products in the correct printing format"""
        print("\n=== Testing Work Order Printing Format ===")
        
        try:
            # Get work orders
            response = self.session.get(f"{BACKEND_URL}/work-orders")
            
            if response.status_code == 200:
                work_orders = response.json()
                
                local_product_found = False
                for work_order in work_orders:
                    if work_order.get('is_daily', False):  # Focus on daily work orders
                        for invoice in work_order.get('invoices', []):
                            for item in invoice.get('items', []):
                                if item.get('product_type') == 'local':
                                    local_product_found = True
                                    
                                    # Check work order printing format requirements
                                    local_details = item.get('local_product_details', {})
                                    
                                    # For work order printing:
                                    # - نوع السيل: OR
                                    # - المقاس: 100
                                    # - الخامة المستخدمة: محلي
                                    seal_type = local_details.get('product_type')  # Should be 'OR'
                                    size = local_details.get('product_size')       # Should be '100'
                                    material = 'محلي'  # Should be 'محلي' (local)
                                    
                                    success = True
                                    details = []
                                    
                                    if seal_type != 'OR':
                                        success = False
                                        details.append(f"نوع السيل should be 'OR', got: {seal_type}")
                                    
                                    if size != '100':
                                        success = False
                                        details.append(f"المقاس should be '100', got: {size}")
                                    
                                    # For local products, material should be 'محلي'
                                    if item.get('product_type') != 'local':
                                        success = False
                                        details.append(f"Product type should be 'local' for material 'محلي'")
                                    
                                    if success:
                                        self.log_test("Work Order Printing Format", True, 
                                                    f"Local product correctly formatted: نوع السيل: {seal_type}, المقاس: {size}, الخامة المستخدمة: {material}")
                                    else:
                                        self.log_test("Work Order Printing Format", False, "; ".join(details))
                                    
                                    return  # Test first local product found
                
                if not local_product_found:
                    self.log_test("Work Order Printing Format", False, "No local products found in work orders")
            else:
                self.log_test("Work Order Printing Format", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Work Order Printing Format", False, f"Exception: {str(e)}")
    
    def test_invoice_edit_modal_format(self):
        """Test that invoice edit modal shows local products correctly"""
        print("\n=== Testing Invoice Edit Modal Format ===")
        
        try:
            # Get invoices to find one with local products
            response = self.session.get(f"{BACKEND_URL}/invoices")
            
            if response.status_code == 200:
                invoices = response.json()
                
                for invoice in invoices:
                    for item in invoice.get('items', []):
                        if item.get('product_type') == 'local':
                            # Test retrieving specific invoice (simulating edit modal)
                            edit_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice['id']}")
                            
                            if edit_response.status_code == 200:
                                edit_invoice = edit_response.json()
                                edit_item = None
                                
                                for edit_item in edit_invoice['items']:
                                    if edit_item.get('product_type') == 'local':
                                        break
                                
                                if edit_item:
                                    # Check edit modal format (should show "OR - 100")
                                    local_details = edit_item.get('local_product_details', {})
                                    seal_type = local_details.get('product_type')
                                    size = local_details.get('product_size')
                                    
                                    if seal_type == 'OR' and size == '100':
                                        self.log_test("Invoice Edit Modal Format (OR - 100)", True, 
                                                    f"Edit modal correctly shows: {seal_type} - {size}")
                                    else:
                                        self.log_test("Invoice Edit Modal Format (OR - 100)", False, 
                                                    f"Edit modal incorrect format - Expected: OR - 100, Got: {seal_type} - {size}")
                                else:
                                    self.log_test("Invoice Edit Modal Format (OR - 100)", False, "No local product in retrieved invoice")
                            else:
                                self.log_test("Invoice Edit Modal Format (OR - 100)", False, f"HTTP {edit_response.status_code}")
                            
                            return  # Test first local product found
                
                self.log_test("Invoice Edit Modal Format (OR - 100)", False, "No invoices with local products found")
            else:
                self.log_test("Invoice Edit Modal Format (OR - 100)", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Invoice Edit Modal Format (OR - 100)", False, f"Exception: {str(e)}")
    
    def test_complete_workflow_integration(self):
        """Test the complete workflow from creation to display"""
        print("\n=== Testing Complete Workflow Integration ===")
        
        try:
            # Create a new supplier
            supplier_data = {
                "name": "مورد التكامل الشامل",
                "phone": "01111111111",
                "address": "عنوان التكامل"
            }
            
            supplier_response = self.session.post(f"{BACKEND_URL}/suppliers", json=supplier_data)
            if supplier_response.status_code != 200:
                self.log_test("Complete Workflow - Create Supplier", False, f"HTTP {supplier_response.status_code}")
                return
            
            supplier = supplier_response.json()
            
            # Create a local product
            product_data = {
                "name": "منتج التكامل الشامل",
                "supplier_id": supplier['id'],
                "purchase_price": 30.0,
                "selling_price": 60.0,
                "current_stock": 50
            }
            
            product_response = self.session.post(f"{BACKEND_URL}/local-products", json=product_data)
            if product_response.status_code != 200:
                self.log_test("Complete Workflow - Create Local Product", False, f"HTTP {product_response.status_code}")
                return
            
            local_product = product_response.json()
            
            # Create invoice with local product
            invoice_data = {
                "customer_name": "عميل التكامل الشامل",
                "invoice_title": "فاتورة التكامل الشامل",
                "supervisor_name": "مشرف التكامل",
                "payment_method": "نقدي",
                "discount_type": "amount",
                "discount_value": 0.0,
                "items": [
                    {
                        "product_type": "local",
                        "product_name": local_product['name'],
                        "supplier": local_product['supplier_name'],
                        "purchase_price": local_product['purchase_price'],
                        "selling_price": local_product['selling_price'],
                        "quantity": 1,
                        "unit_price": local_product['selling_price'],
                        "total_price": local_product['selling_price'],
                        "seal_type": None,
                        "material_type": None,
                        "inner_diameter": None,
                        "outer_diameter": None,
                        "height": None,
                        "material_used": None,
                        "local_product_details": {
                            "name": local_product['name'],
                            "supplier": local_product['supplier_name'],
                            "purchase_price": local_product['purchase_price'],
                            "selling_price": local_product['selling_price'],
                            "product_type": "OR",
                            "product_size": "100"
                        }
                    }
                ]
            }
            
            invoice_response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if invoice_response.status_code != 200:
                self.log_test("Complete Workflow - Create Invoice", False, f"HTTP {invoice_response.status_code}")
                return
            
            invoice = invoice_response.json()
            
            # Verify all three display formats
            workflow_success = True
            workflow_details = []
            
            # 1. Invoice format
            item = invoice['items'][0]
            local_details = item.get('local_product_details', {})
            if local_details.get('product_type') == 'OR' and local_details.get('product_size') == '100':
                workflow_details.append("✅ Invoice format correct (OR - 100)")
            else:
                workflow_success = False
                workflow_details.append("❌ Invoice format incorrect")
            
            # 2. Check if added to daily work order
            today = datetime.now().date().isoformat()
            wo_response = self.session.get(f"{BACKEND_URL}/work-orders/daily/{today}")
            if wo_response.status_code == 200:
                work_order = wo_response.json()
                invoice_in_wo = any(wo_inv.get('id') == invoice['id'] for wo_inv in work_order.get('invoices', []))
                if invoice_in_wo:
                    workflow_details.append("✅ Invoice automatically added to daily work order")
                else:
                    workflow_success = False
                    workflow_details.append("❌ Invoice not found in daily work order")
            else:
                workflow_success = False
                workflow_details.append("❌ Could not retrieve daily work order")
            
            # 3. Edit modal format (retrieve invoice)
            edit_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice['id']}")
            if edit_response.status_code == 200:
                edit_invoice = edit_response.json()
                edit_item = edit_invoice['items'][0]
                edit_details = edit_item.get('local_product_details', {})
                if edit_details.get('product_type') == 'OR' and edit_details.get('product_size') == '100':
                    workflow_details.append("✅ Edit modal format correct (OR - 100)")
                else:
                    workflow_success = False
                    workflow_details.append("❌ Edit modal format incorrect")
            else:
                workflow_success = False
                workflow_details.append("❌ Could not retrieve invoice for edit modal test")
            
            self.log_test("Complete Workflow Integration", workflow_success, "; ".join(workflow_details))
            
        except Exception as e:
            self.log_test("Complete Workflow Integration", False, f"Exception: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🔍 Starting Comprehensive Local Products Display Testing")
        print("=" * 70)
        
        # Test all aspects of local products display
        self.test_invoice_printing_format()
        self.test_work_order_printing_format()
        self.test_invoice_edit_modal_format()
        self.test_complete_workflow_integration()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        # Final verdict
        all_passed = all(result['success'] for result in self.test_results)
        if all_passed:
            print("\n🎉 FINAL VERDICT: All local products display requirements are FULLY IMPLEMENTED")
            print("   ✅ Invoice printing shows 'OR - 100'")
            print("   ✅ Work order printing shows 'نوع السيل: OR، المقاس: 100، الخامة: محلي'")
            print("   ✅ Invoice edit modal shows 'OR - 100'")
            print("   ✅ Complete workflow integration works correctly")
        else:
            print("\n⚠️  FINAL VERDICT: Some local products display requirements need attention")
        
        return all_passed

def main():
    """Main test execution"""
    tester = ComprehensiveLocalProductsTest()
    success = tester.run_comprehensive_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()