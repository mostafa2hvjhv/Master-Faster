#!/usr/bin/env python3
"""
Local Products Display Testing - اختبار عرض المنتجات المحلية
Testing the specific issue reported by user about local products not displaying correctly in invoices and work orders
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class LocalProductsDisplayTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_data = {
            'suppliers': [],
            'local_products': [],
            'invoices': [],
            'work_orders': []
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
    
    def test_create_supplier(self):
        """Create a test supplier for local products"""
        print("\n=== Creating Test Supplier ===")
        
        supplier_data = {
            "name": "مورد اختبار المنتجات المحلية",
            "phone": "01234567890",
            "address": "عنوان المورد الاختباري"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/suppliers", json=supplier_data)
            
            if response.status_code == 200:
                supplier = response.json()
                self.created_data['suppliers'].append(supplier)
                self.log_test("Create Test Supplier", True, f"Created supplier: {supplier['name']} with ID: {supplier['id']}")
                return supplier
            else:
                self.log_test("Create Test Supplier", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Test Supplier", False, f"Exception: {str(e)}")
            return None
    
    def test_create_local_product(self, supplier_id: str):
        """Create a test local product"""
        print("\n=== Creating Test Local Product ===")
        
        product_data = {
            "name": "منتج محلي اختبار - خاتم زيت",
            "supplier_id": supplier_id,
            "purchase_price": 25.0,
            "selling_price": 50.0,
            "current_stock": 100
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/local-products", json=product_data)
            
            if response.status_code == 200:
                product = response.json()
                self.created_data['local_products'].append(product)
                self.log_test("Create Test Local Product", True, f"Created product: {product['name']} with ID: {product['id']}")
                return product
            else:
                self.log_test("Create Test Local Product", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Test Local Product", False, f"Exception: {str(e)}")
            return None
    
    def test_create_invoice_with_local_product(self, local_product: dict):
        """Create an invoice containing a local product"""
        print("\n=== Creating Invoice with Local Product ===")
        
        # Create invoice with local product using the expected format
        invoice_data = {
            "customer_name": "عميل اختبار المنتجات المحلية",
            "invoice_title": "فاتورة اختبار المنتجات المحلية",
            "supervisor_name": "مشرف الاختبار",
            "payment_method": "نقدي",
            "discount_type": "amount",
            "discount_value": 0.0,
            "items": [
                {
                    # Local product fields
                    "product_type": "local",
                    "product_name": local_product['name'],
                    "supplier": local_product['supplier_name'],
                    "purchase_price": local_product['purchase_price'],
                    "selling_price": local_product['selling_price'],
                    "quantity": 2,
                    "unit_price": local_product['selling_price'],
                    "total_price": local_product['selling_price'] * 2,
                    # Manufactured product fields should be null for local products
                    "seal_type": None,
                    "material_type": None,
                    "inner_diameter": None,
                    "outer_diameter": None,
                    "height": None,
                    "material_used": None,
                    # Local product details for work order display
                    "local_product_details": {
                        "name": local_product['name'],
                        "supplier": local_product['supplier_name'],
                        "purchase_price": local_product['purchase_price'],
                        "selling_price": local_product['selling_price'],
                        "product_type": "OR",  # This should display as seal type in work order
                        "product_size": "100"  # This should display as size in work order
                    }
                }
            ]
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code == 200:
                invoice = response.json()
                self.created_data['invoices'].append(invoice)
                self.log_test("Create Invoice with Local Product", True, 
                            f"Created invoice: {invoice['invoice_number']} with {len(invoice['items'])} local product(s)")
                
                # Verify local product data in invoice
                item = invoice['items'][0]
                if (item.get('product_type') == 'local' and 
                    item.get('product_name') == local_product['name'] and
                    item.get('local_product_details', {}).get('product_type') == 'OR' and
                    item.get('local_product_details', {}).get('product_size') == '100'):
                    self.log_test("Verify Local Product Data in Invoice", True, 
                                "Local product data correctly saved with OR type and 100 size")
                else:
                    self.log_test("Verify Local Product Data in Invoice", False, 
                                f"Local product data incorrect: {json.dumps(item, indent=2)}")
                
                return invoice
            else:
                self.log_test("Create Invoice with Local Product", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Invoice with Local Product", False, f"Exception: {str(e)}")
            return None
    
    def test_verify_invoice_display(self, invoice: dict):
        """Verify the invoice displays local products correctly"""
        print("\n=== Verifying Invoice Display ===")
        
        try:
            # Get the invoice back from API
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice['id']}")
            
            if response.status_code == 200:
                retrieved_invoice = response.json()
                
                # Check if local product displays correctly
                item = retrieved_invoice['items'][0]
                
                # According to the update, local products should display as "OR - 100" in invoices
                expected_display_data = {
                    'product_type': 'local',
                    'local_product_details': {
                        'product_type': 'OR',
                        'product_size': '100'
                    }
                }
                
                success = True
                details = []
                
                if item.get('product_type') != 'local':
                    success = False
                    details.append(f"Product type should be 'local', got: {item.get('product_type')}")
                
                local_details = item.get('local_product_details', {})
                if local_details.get('product_type') != 'OR':
                    success = False
                    details.append(f"Product type in details should be 'OR', got: {local_details.get('product_type')}")
                
                if local_details.get('product_size') != '100':
                    success = False
                    details.append(f"Product size should be '100', got: {local_details.get('product_size')}")
                
                # Check that manufactured product fields are null
                manufactured_fields = ['seal_type', 'material_type', 'inner_diameter', 'outer_diameter', 'height']
                for field in manufactured_fields:
                    if item.get(field) is not None:
                        success = False
                        details.append(f"Manufactured field '{field}' should be null for local products, got: {item.get(field)}")
                
                if success:
                    self.log_test("Verify Invoice Local Product Display", True, 
                                "Local product correctly displays with OR type and 100 size, manufactured fields are null")
                else:
                    self.log_test("Verify Invoice Local Product Display", False, 
                                "; ".join(details))
                
                return success
            else:
                self.log_test("Verify Invoice Local Product Display", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify Invoice Local Product Display", False, f"Exception: {str(e)}")
            return False
    
    def test_verify_daily_work_order(self, invoice: dict):
        """Verify the invoice was added to daily work order and local product displays correctly"""
        print("\n=== Verifying Daily Work Order ===")
        
        try:
            # Get today's date for work order
            today = datetime.now().date().isoformat()
            
            # Get daily work order for today
            response = self.session.get(f"{BACKEND_URL}/work-orders/daily/{today}")
            
            if response.status_code == 200:
                work_order = response.json()
                
                # Check if our invoice is in the work order
                invoice_found = False
                local_product_correct = False
                
                for wo_invoice in work_order.get('invoices', []):
                    if wo_invoice.get('id') == invoice['id']:
                        invoice_found = True
                        
                        # Check local product display in work order
                        item = wo_invoice['items'][0]
                        local_details = item.get('local_product_details', {})
                        
                        # According to the update, work order should show:
                        # - نوع السيل: OR
                        # - المقاس: 100  
                        # - الخامة المستخدمة: محلي
                        if (local_details.get('product_type') == 'OR' and 
                            local_details.get('product_size') == '100' and
                            item.get('product_type') == 'local'):
                            local_product_correct = True
                        break
                
                if invoice_found and local_product_correct:
                    self.log_test("Verify Daily Work Order Local Product Display", True, 
                                "Invoice found in daily work order with correct local product display (OR, 100, محلي)")
                elif invoice_found:
                    self.log_test("Verify Daily Work Order Local Product Display", False, 
                                "Invoice found but local product display is incorrect")
                else:
                    self.log_test("Verify Daily Work Order Local Product Display", False, 
                                "Invoice not found in daily work order")
                
                return invoice_found and local_product_correct
            else:
                self.log_test("Verify Daily Work Order Local Product Display", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verify Daily Work Order Local Product Display", False, f"Exception: {str(e)}")
            return False
    
    def test_get_work_orders_list(self):
        """Get all work orders to verify structure"""
        print("\n=== Getting Work Orders List ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/work-orders")
            
            if response.status_code == 200:
                work_orders = response.json()
                self.log_test("Get Work Orders List", True, f"Retrieved {len(work_orders)} work orders")
                
                # Find daily work orders with local products
                daily_orders_with_locals = 0
                for wo in work_orders:
                    if wo.get('is_daily', False):
                        for invoice in wo.get('invoices', []):
                            for item in invoice.get('items', []):
                                if item.get('product_type') == 'local':
                                    daily_orders_with_locals += 1
                                    break
                
                if daily_orders_with_locals > 0:
                    self.log_test("Find Daily Work Orders with Local Products", True, 
                                f"Found {daily_orders_with_locals} daily work orders containing local products")
                else:
                    self.log_test("Find Daily Work Orders with Local Products", False, 
                                "No daily work orders with local products found")
                
                return work_orders
            else:
                self.log_test("Get Work Orders List", False, f"HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            self.log_test("Get Work Orders List", False, f"Exception: {str(e)}")
            return []
    
    def run_complete_test(self):
        """Run the complete test workflow"""
        print("🔍 Starting Local Products Display Testing")
        print("=" * 60)
        
        # Step 1: Create test supplier
        supplier = self.test_create_supplier()
        if not supplier:
            print("❌ Cannot continue without supplier")
            return False
        
        # Step 2: Create test local product
        local_product = self.test_create_local_product(supplier['id'])
        if not local_product:
            print("❌ Cannot continue without local product")
            return False
        
        # Step 3: Create invoice with local product
        invoice = self.test_create_invoice_with_local_product(local_product)
        if not invoice:
            print("❌ Cannot continue without invoice")
            return False
        
        # Step 4: Verify invoice display
        invoice_display_ok = self.test_verify_invoice_display(invoice)
        
        # Step 5: Verify daily work order
        work_order_display_ok = self.test_verify_daily_work_order(invoice)
        
        # Step 6: Get work orders list for additional verification
        self.test_get_work_orders_list()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        # Key findings
        print("\n🔍 KEY FINDINGS:")
        if invoice_display_ok:
            print("✅ Local products display correctly in invoices (OR - 100)")
        else:
            print("❌ Local products do NOT display correctly in invoices")
        
        if work_order_display_ok:
            print("✅ Local products display correctly in work orders (نوع السيل: OR، المقاس: 100، الخامة: محلي)")
        else:
            print("❌ Local products do NOT display correctly in work orders")
        
        # Overall result
        overall_success = invoice_display_ok and work_order_display_ok
        if overall_success:
            print("\n🎉 OVERALL RESULT: Local products display issue is RESOLVED")
        else:
            print("\n⚠️  OVERALL RESULT: Local products display issue is NOT RESOLVED")
        
        return overall_success

def main():
    """Main test execution"""
    tester = LocalProductsDisplayTester()
    success = tester.run_complete_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()