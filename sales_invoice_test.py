#!/usr/bin/env python3
"""
Focused Backend API Testing for Sales and Invoice Functionality
اختبار مركز لوظائف المبيعات والفواتير بعد إصلاح JSX
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class SalesInvoiceAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_data = {
            'customers': [],
            'raw_materials': [],
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
    
    def test_customers_for_sales_dropdown(self):
        """Test GET /api/customers - retrieving customers for sales page dropdown"""
        print("\n=== Testing GET /api/customers for Sales Dropdown ===")
        
        # First create some customers for testing
        customers_data = [
            {"name": "شركة الأهرام للتجارة", "phone": "01234567890", "address": "القاهرة، مصر الجديدة"},
            {"name": "مؤسسة النيل للصناعات", "phone": "01098765432", "address": "الجيزة، الدقي"},
            {"name": "شركة الفجر للمقاولات", "phone": "01156789012", "address": "الإسكندرية، سموحة"}
        ]
        
        for customer_data in customers_data:
            try:
                response = self.session.post(f"{BACKEND_URL}/customers", 
                                           json=customer_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    self.created_data['customers'].append(data)
                    self.log_test(f"Create Customer for Dropdown - {customer_data['name']}", True, f"Customer ID: {data.get('id')}")
                else:
                    self.log_test(f"Create Customer for Dropdown - {customer_data['name']}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"Create Customer for Dropdown - {customer_data['name']}", False, f"Exception: {str(e)}")
        
        # Test GET /api/customers for dropdown
        try:
            response = self.session.get(f"{BACKEND_URL}/customers")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) >= 3:
                    # Check if customers have required fields for dropdown
                    required_fields = ['id', 'name']
                    all_have_fields = all(all(field in customer for field in required_fields) for customer in data)
                    
                    if all_have_fields:
                        self.log_test("GET Customers for Sales Dropdown", True, 
                                    f"Retrieved {len(data)} customers with required fields (id, name)")
                    else:
                        self.log_test("GET Customers for Sales Dropdown", False, 
                                    "Some customers missing required fields for dropdown")
                else:
                    self.log_test("GET Customers for Sales Dropdown", False, 
                                f"Expected list with at least 3 customers, got: {len(data) if isinstance(data, list) else type(data)}")
            else:
                self.log_test("GET Customers for Sales Dropdown", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET Customers for Sales Dropdown", False, f"Exception: {str(e)}")
    
    def test_compatibility_check_for_sales(self):
        """Test POST /api/compatibility-check - checking material compatibility for sales"""
        print("\n=== Testing POST /api/compatibility-check for Sales ===")
        
        # First create some raw materials for compatibility testing
        materials_data = [
            {"material_type": "NBR", "inner_diameter": 20.0, "outer_diameter": 40.0, "height": 100.0, "pieces_count": 50, "unit_code": "NBR-20-40-001", "cost_per_mm": 0.15},
            {"material_type": "BUR", "inner_diameter": 25.0, "outer_diameter": 50.0, "height": 80.0, "pieces_count": 30, "unit_code": "BUR-25-50-001", "cost_per_mm": 0.20},
            {"material_type": "VT", "inner_diameter": 30.0, "outer_diameter": 60.0, "height": 120.0, "pieces_count": 25, "unit_code": "VT-30-60-001", "cost_per_mm": 0.25}
        ]
        
        for material_data in materials_data:
            try:
                response = self.session.post(f"{BACKEND_URL}/raw-materials", 
                                           json=material_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    self.created_data['raw_materials'].append(data)
                    self.log_test(f"Create Raw Material for Compatibility - {material_data['material_type']}", True, 
                                f"Unit Code: {data.get('unit_code')}")
                else:
                    self.log_test(f"Create Raw Material for Compatibility - {material_data['material_type']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"Create Raw Material for Compatibility - {material_data['material_type']}", False, f"Exception: {str(e)}")
        
        # Test compatibility checks for different seal specifications
        compatibility_tests = [
            {
                "name": "RSL Seal Compatibility",
                "data": {"seal_type": "RSL", "inner_diameter": 25.0, "outer_diameter": 35.0, "height": 8.0}
            },
            {
                "name": "RS Seal Compatibility", 
                "data": {"seal_type": "RS", "inner_diameter": 30.0, "outer_diameter": 45.0, "height": 7.0}
            },
            {
                "name": "B17 Seal Compatibility",
                "data": {"seal_type": "B17", "inner_diameter": 35.0, "outer_diameter": 55.0, "height": 10.0}
            }
        ]
        
        for test_case in compatibility_tests:
            try:
                response = self.session.post(f"{BACKEND_URL}/compatibility-check", 
                                           json=test_case["data"],
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    if 'compatible_materials' in data and 'compatible_products' in data:
                        materials_count = len(data['compatible_materials'])
                        products_count = len(data['compatible_products'])
                        
                        # Check if materials have required fields for sales interface
                        if materials_count > 0:
                            material = data['compatible_materials'][0]
                            required_fields = ['id', 'material_type', 'unit_code', 'inner_diameter', 'outer_diameter', 'height', 'cost_per_mm']
                            has_required_fields = all(field in material for field in required_fields)
                            
                            if has_required_fields:
                                self.log_test(f"Compatibility Check - {test_case['name']}", True, 
                                            f"Found {materials_count} compatible materials, {products_count} products with required fields")
                            else:
                                missing_fields = [field for field in required_fields if field not in material]
                                self.log_test(f"Compatibility Check - {test_case['name']}", False, 
                                            f"Materials missing required fields: {missing_fields}")
                        else:
                            self.log_test(f"Compatibility Check - {test_case['name']}", True, 
                                        f"No compatible materials found (expected for some seal types)")
                    else:
                        self.log_test(f"Compatibility Check - {test_case['name']}", False, 
                                    f"Missing response fields: {data}")
                else:
                    self.log_test(f"Compatibility Check - {test_case['name']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"Compatibility Check - {test_case['name']}", False, f"Exception: {str(e)}")
    
    def test_invoice_creation_with_products(self):
        """Test POST /api/invoices - creating invoices with products (Add to Invoice functionality)"""
        print("\n=== Testing POST /api/invoices - Creating Invoices with Products ===")
        
        if not self.created_data['customers']:
            self.log_test("Invoice Creation", False, "No customers available for invoice testing")
            return
        
        # Test different invoice scenarios that would be used from sales interface
        invoice_scenarios = [
            {
                "name": "Single Product Invoice - Cash Payment",
                "data": {
                    "customer_id": self.created_data['customers'][0]['id'],
                    "customer_name": self.created_data['customers'][0]['name'],
                    "items": [
                        {
                            "seal_type": "RSL",
                            "material_type": "NBR", 
                            "inner_diameter": 25.0,
                            "outer_diameter": 35.0,
                            "height": 8.0,
                            "quantity": 10,
                            "unit_price": 15.0,
                            "total_price": 150.0,
                            "material_used": "NBR-20-40-001" if self.created_data['raw_materials'] else None,
                            "material_details": {
                                "unit_code": "NBR-20-40-001",
                                "material_type": "NBR",
                                "cost_per_mm": 0.15,
                                "inner_diameter": 20.0,
                                "outer_diameter": 40.0,
                                "height": 100.0
                            } if self.created_data['raw_materials'] else None
                        }
                    ],
                    "payment_method": "نقدي",
                    "discount_type": "amount",
                    "discount_value": 0.0,
                    "notes": "فاتورة اختبار - منتج واحد - دفع نقدي"
                }
            },
            {
                "name": "Multiple Products Invoice - Deferred Payment",
                "data": {
                    "customer_id": self.created_data['customers'][1]['id'] if len(self.created_data['customers']) > 1 else self.created_data['customers'][0]['id'],
                    "customer_name": self.created_data['customers'][1]['name'] if len(self.created_data['customers']) > 1 else self.created_data['customers'][0]['name'],
                    "items": [
                        {
                            "seal_type": "RS",
                            "material_type": "BUR",
                            "inner_diameter": 30.0,
                            "outer_diameter": 45.0,
                            "height": 7.0,
                            "quantity": 5,
                            "unit_price": 20.0,
                            "total_price": 100.0,
                            "material_used": "BUR-25-50-001" if len(self.created_data['raw_materials']) > 1 else None
                        },
                        {
                            "seal_type": "B17",
                            "material_type": "VT",
                            "inner_diameter": 35.0,
                            "outer_diameter": 55.0,
                            "height": 10.0,
                            "quantity": 3,
                            "unit_price": 25.0,
                            "total_price": 75.0,
                            "material_used": "VT-30-60-001" if len(self.created_data['raw_materials']) > 2 else None
                        }
                    ],
                    "payment_method": "آجل",
                    "discount_type": "percentage",
                    "discount_value": 10.0,
                    "notes": "فاتورة اختبار - منتجات متعددة - دفع آجل مع خصم 10%"
                }
            },
            {
                "name": "Invoice with Vodafone Cash Payment",
                "data": {
                    "customer_id": self.created_data['customers'][0]['id'],
                    "customer_name": self.created_data['customers'][0]['name'],
                    "items": [
                        {
                            "seal_type": "RSE",
                            "material_type": "NBR",
                            "inner_diameter": 20.0,
                            "outer_diameter": 30.0,
                            "height": 6.0,
                            "quantity": 8,
                            "unit_price": 12.0,
                            "total_price": 96.0
                        }
                    ],
                    "payment_method": "فودافون كاش محمد الصاوي",
                    "discount_type": "amount",
                    "discount_value": 6.0,
                    "notes": "فاتورة اختبار - فودافون كاش مع خصم ثابت"
                }
            }
        ]
        
        for scenario in invoice_scenarios:
            try:
                response = self.session.post(f"{BACKEND_URL}/invoices", 
                                           json=scenario["data"],
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify invoice has all required fields
                    required_fields = ['id', 'invoice_number', 'customer_name', 'items', 'total_amount', 'payment_method', 'status']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        # Verify discount calculations if applicable
                        discount_correct = True
                        if scenario["data"].get("discount_value", 0) > 0:
                            subtotal = sum(item["total_price"] for item in scenario["data"]["items"])
                            expected_discount = scenario["data"]["discount_value"]
                            if scenario["data"]["discount_type"] == "percentage":
                                expected_discount = (subtotal * expected_discount) / 100
                            
                            expected_total = subtotal - expected_discount
                            actual_total = data.get("total_amount", 0)
                            
                            if abs(actual_total - expected_total) > 0.01:  # Allow small floating point differences
                                discount_correct = False
                        
                        if discount_correct:
                            self.created_data['invoices'].append(data)
                            self.log_test(f"Create Invoice - {scenario['name']}", True, 
                                        f"Invoice: {data.get('invoice_number')}, Amount: {data.get('total_amount')}, Status: {data.get('status')}")
                        else:
                            self.log_test(f"Create Invoice - {scenario['name']}", False, 
                                        f"Discount calculation incorrect. Expected: {expected_total}, Got: {actual_total}")
                    else:
                        self.log_test(f"Create Invoice - {scenario['name']}", False, 
                                    f"Missing required fields: {missing_fields}")
                else:
                    self.log_test(f"Create Invoice - {scenario['name']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"Create Invoice - {scenario['name']}", False, f"Exception: {str(e)}")
    
    def test_invoice_retrieval_apis(self):
        """Test invoice retrieval APIs used by sales interface"""
        print("\n=== Testing Invoice Retrieval APIs ===")
        
        # Test GET /api/invoices
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check if invoices have all fields needed for sales interface
                    if len(data) > 0:
                        invoice = data[0]
                        required_fields = ['id', 'invoice_number', 'customer_name', 'items', 'total_amount', 'payment_method', 'status', 'date']
                        missing_fields = [field for field in required_fields if field not in invoice]
                        
                        if not missing_fields:
                            self.log_test("GET All Invoices", True, 
                                        f"Retrieved {len(data)} invoices with all required fields")
                        else:
                            self.log_test("GET All Invoices", False, 
                                        f"Invoices missing required fields: {missing_fields}")
                    else:
                        self.log_test("GET All Invoices", True, "No invoices found (empty list)")
                else:
                    self.log_test("GET All Invoices", False, f"Expected list, got: {type(data)}")
            else:
                self.log_test("GET All Invoices", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET All Invoices", False, f"Exception: {str(e)}")
        
        # Test GET /api/invoices/{id} for specific invoice
        if self.created_data['invoices']:
            invoice_id = self.created_data['invoices'][0]['id']
            try:
                response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('id') == invoice_id:
                        # Check if material_details are preserved
                        has_material_details = any(
                            item.get('material_details') is not None 
                            for item in data.get('items', [])
                        )
                        
                        self.log_test("GET Specific Invoice", True, 
                                    f"Retrieved invoice: {data.get('invoice_number')}, Has material details: {has_material_details}")
                    else:
                        self.log_test("GET Specific Invoice", False, f"ID mismatch: {data}")
                else:
                    self.log_test("GET Specific Invoice", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("GET Specific Invoice", False, f"Exception: {str(e)}")
    
    def test_sales_workflow_integration(self):
        """Test complete sales workflow integration"""
        print("\n=== Testing Complete Sales Workflow Integration ===")
        
        # Simulate complete sales workflow:
        # 1. Get customers for dropdown
        # 2. Check material compatibility
        # 3. Create invoice with selected material
        # 4. Verify invoice creation
        
        workflow_success = True
        workflow_details = []
        
        # Step 1: Get customers
        try:
            response = self.session.get(f"{BACKEND_URL}/customers")
            if response.status_code == 200 and len(response.json()) > 0:
                customers = response.json()
                selected_customer = customers[0]
                workflow_details.append(f"✓ Step 1: Retrieved {len(customers)} customers")
            else:
                workflow_success = False
                workflow_details.append("✗ Step 1: Failed to retrieve customers")
        except Exception as e:
            workflow_success = False
            workflow_details.append(f"✗ Step 1: Exception - {str(e)}")
        
        # Step 2: Check compatibility
        if workflow_success:
            try:
                compatibility_data = {"seal_type": "RSL", "inner_diameter": 25.0, "outer_diameter": 35.0, "height": 8.0}
                response = self.session.post(f"{BACKEND_URL}/compatibility-check", 
                                           json=compatibility_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    compatibility_result = response.json()
                    compatible_materials = compatibility_result.get('compatible_materials', [])
                    workflow_details.append(f"✓ Step 2: Found {len(compatible_materials)} compatible materials")
                    
                    # Select first compatible material if available
                    selected_material = compatible_materials[0] if compatible_materials else None
                else:
                    workflow_success = False
                    workflow_details.append("✗ Step 2: Compatibility check failed")
            except Exception as e:
                workflow_success = False
                workflow_details.append(f"✗ Step 2: Exception - {str(e)}")
        
        # Step 3: Create invoice with selected material
        if workflow_success:
            try:
                invoice_data = {
                    "customer_id": selected_customer['id'],
                    "customer_name": selected_customer['name'],
                    "items": [
                        {
                            "seal_type": "RSL",
                            "material_type": "NBR",
                            "inner_diameter": 25.0,
                            "outer_diameter": 35.0,
                            "height": 8.0,
                            "quantity": 5,
                            "unit_price": 18.0,
                            "total_price": 90.0,
                            "material_used": selected_material['unit_code'] if selected_material else None,
                            "material_details": {
                                "unit_code": selected_material['unit_code'],
                                "material_type": selected_material['material_type'],
                                "cost_per_mm": selected_material['cost_per_mm']
                            } if selected_material else None
                        }
                    ],
                    "payment_method": "نقدي",
                    "notes": "فاتورة اختبار سير العمل المتكامل"
                }
                
                response = self.session.post(f"{BACKEND_URL}/invoices", 
                                           json=invoice_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    invoice = response.json()
                    workflow_details.append(f"✓ Step 3: Created invoice {invoice.get('invoice_number')}")
                else:
                    workflow_success = False
                    workflow_details.append(f"✗ Step 3: Invoice creation failed - {response.status_code}")
            except Exception as e:
                workflow_success = False
                workflow_details.append(f"✗ Step 3: Exception - {str(e)}")
        
        # Step 4: Verify invoice was created correctly
        if workflow_success:
            try:
                response = self.session.get(f"{BACKEND_URL}/invoices")
                if response.status_code == 200:
                    invoices = response.json()
                    workflow_invoice = next((inv for inv in invoices if inv.get('notes') == 'فاتورة اختبار سير العمل المتكامل'), None)
                    
                    if workflow_invoice:
                        workflow_details.append("✓ Step 4: Invoice verification successful")
                    else:
                        workflow_success = False
                        workflow_details.append("✗ Step 4: Created invoice not found in list")
                else:
                    workflow_success = False
                    workflow_details.append("✗ Step 4: Failed to retrieve invoices for verification")
            except Exception as e:
                workflow_success = False
                workflow_details.append(f"✗ Step 4: Exception - {str(e)}")
        
        self.log_test("Complete Sales Workflow Integration", workflow_success, 
                    f"Workflow steps: {' | '.join(workflow_details)}")
    
    def run_all_tests(self):
        """Run all sales and invoice functionality tests"""
        print("🚀 Starting Sales and Invoice Functionality Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Run focused tests for sales and invoice functionality
        self.test_customers_for_sales_dropdown()
        self.test_compatibility_check_for_sales()
        self.test_invoice_creation_with_products()
        self.test_invoice_retrieval_apis()
        self.test_sales_workflow_integration()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 SALES & INVOICE FUNCTIONALITY TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n📋 CREATED TEST DATA:")
        for key, items in self.created_data.items():
            print(f"  - {key}: {len(items)} items")
        
        return success_rate >= 90  # Consider test successful if 90% or more pass

if __name__ == "__main__":
    tester = SalesInvoiceAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)