#!/usr/bin/env python3
"""
Comprehensive Backend Testing for New Features - اختبار شامل للمميزات الجديدة المنفذة
Testing the specific features mentioned in the Arabic review request:

1. Wall height for W Types (ارتفاع الحيطة للـ W Types)
2. Inventory editing (تحرير المخزون)  
3. Supplier editing (تحرير الموردين)
4. Material selection improvements (تحسينات اختيار المواد)
5. Local product display (عرض المنتجات المحلية)
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class NewFeaturesAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_data = {
            'customers': [],
            'raw_materials': [],
            'finished_products': [],
            'suppliers': [],
            'local_products': [],
            'invoices': [],
            'inventory_items': []
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
    
    def test_w_type_wall_height(self):
        """Test 1: ارتفاع الحيطة للـ W Types - Wall height for W Types"""
        print("\n=== Testing W Type Wall Height Feature ===")
        
        try:
            # Test creating a W type product with wall height
            w_product_data = {
                "seal_type": "W1",
                "material_type": "NBR", 
                "inner_diameter": 25.0,
                "outer_diameter": 45.0,
                "height": 8.0,
                "quantity": 10,
                "unit_price": 15.0
            }
            
            response = self.session.post(f"{BACKEND_URL}/finished-products", json=w_product_data)
            if response.status_code == 200:
                product = response.json()
                self.created_data['finished_products'].append(product['id'])
                
                # Check if wall height is properly saved (height field represents wall height for W types)
                if product.get('height') == 8.0 and product.get('seal_type') == 'W1':
                    self.log_test("Create W1 product with wall height", True, 
                                f"W1 product created with wall height: {product.get('height')}mm")
                else:
                    self.log_test("Create W1 product with wall height", False, 
                                f"Wall height not properly saved: {product}")
            else:
                self.log_test("Create W1 product with wall height", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create W1 product with wall height", False, f"Exception: {str(e)}")
        
        # Test creating invoice with W type to verify wall height display
        try:
            # First create a customer
            customer_data = {"name": "عميل اختبار W Type", "phone": "01234567890"}
            customer_response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if customer_response.status_code == 200:
                customer = customer_response.json()
                self.created_data['customers'].append(customer['id'])
                
                # Create invoice with W type product
                invoice_data = {
                    "customer_name": "عميل اختبار W Type",
                    "customer_id": customer['id'],
                    "invoice_title": "فاتورة اختبار W Type",
                    "supervisor_name": "مشرف الاختبار",
                    "items": [{
                        "seal_type": "W1",
                        "material_type": "NBR",
                        "inner_diameter": 25.0,
                        "outer_diameter": 45.0,
                        "height": 8.0,  # Wall height
                        "quantity": 2,
                        "unit_price": 15.0,
                        "total_price": 30.0,
                        "product_type": "manufactured"
                    }],
                    "payment_method": "نقدي"
                }
                
                invoice_response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
                if invoice_response.status_code == 200:
                    invoice = invoice_response.json()
                    self.created_data['invoices'].append(invoice['id'])
                    
                    # Check if wall height is preserved in invoice
                    item = invoice['items'][0]
                    if item.get('height') == 8.0 and item.get('seal_type') == 'W1':
                        self.log_test("W Type wall height in invoice", True, 
                                    f"Wall height preserved in invoice: {item.get('height')}mm")
                    else:
                        self.log_test("W Type wall height in invoice", False, 
                                    f"Wall height not preserved: {item}")
                else:
                    self.log_test("W Type wall height in invoice", False, 
                                f"Invoice creation failed: HTTP {invoice_response.status_code}")
            else:
                self.log_test("W Type wall height in invoice", False, 
                            f"Customer creation failed: HTTP {customer_response.status_code}")
                
        except Exception as e:
            self.log_test("W Type wall height in invoice", False, f"Exception: {str(e)}")
    
    def test_inventory_editing(self):
        """Test 2: تحرير المخزون - Inventory editing"""
        print("\n=== Testing Inventory Editing Feature ===")
        
        # Test editing raw materials
        try:
            # First create a raw material
            raw_material_data = {
                "material_type": "NBR",
                "inner_diameter": 20.0,
                "outer_diameter": 40.0,
                "height": 100.0,
                "pieces_count": 5,
                "cost_per_mm": 2.0
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/raw-materials", json=raw_material_data)
            if create_response.status_code == 200:
                material = create_response.json()
                material_id = material['id']
                self.created_data['raw_materials'].append(material_id)
                
                # Test editing the raw material
                updated_data = {
                    "material_type": "NBR",
                    "inner_diameter": 20.0,
                    "outer_diameter": 40.0,
                    "height": 120.0,  # Changed height
                    "pieces_count": 8,  # Changed pieces count
                    "cost_per_mm": 2.5  # Changed cost
                }
                
                edit_response = self.session.put(f"{BACKEND_URL}/raw-materials/{material_id}", json=updated_data)
                if edit_response.status_code == 200:
                    self.log_test("Edit raw material", True, 
                                f"Raw material updated successfully")
                    
                    # Verify the changes
                    get_response = self.session.get(f"{BACKEND_URL}/raw-materials")
                    if get_response.status_code == 200:
                        materials = get_response.json()
                        updated_material = next((m for m in materials if m['id'] == material_id), None)
                        if updated_material and updated_material['height'] == 120.0 and updated_material['pieces_count'] == 8:
                            self.log_test("Verify raw material edit", True, 
                                        f"Changes verified: height={updated_material['height']}, pieces={updated_material['pieces_count']}")
                        else:
                            self.log_test("Verify raw material edit", False, 
                                        f"Changes not reflected: {updated_material}")
                else:
                    self.log_test("Edit raw material", False, 
                                f"HTTP {edit_response.status_code}: {edit_response.text}")
            else:
                self.log_test("Edit raw material", False, 
                            f"Raw material creation failed: HTTP {create_response.status_code}")
                
        except Exception as e:
            self.log_test("Edit raw material", False, f"Exception: {str(e)}")
        
        # Test editing finished products
        try:
            # First create a finished product
            finished_product_data = {
                "seal_type": "RSL",
                "material_type": "BUR",
                "inner_diameter": 30.0,
                "outer_diameter": 50.0,
                "height": 10.0,
                "quantity": 20,
                "unit_price": 12.0
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/finished-products", json=finished_product_data)
            if create_response.status_code == 200:
                product = create_response.json()
                product_id = product['id']
                self.created_data['finished_products'].append(product_id)
                
                # Test editing the finished product
                updated_data = {
                    "seal_type": "RSL",
                    "material_type": "BUR",
                    "inner_diameter": 30.0,
                    "outer_diameter": 50.0,
                    "height": 10.0,
                    "quantity": 25,  # Changed quantity
                    "unit_price": 15.0  # Changed price
                }
                
                edit_response = self.session.put(f"{BACKEND_URL}/finished-products/{product_id}", json=updated_data)
                if edit_response.status_code == 200:
                    self.log_test("Edit finished product", True, 
                                f"Finished product updated successfully")
                    
                    # Verify the changes
                    get_response = self.session.get(f"{BACKEND_URL}/finished-products")
                    if get_response.status_code == 200:
                        products = get_response.json()
                        updated_product = next((p for p in products if p['id'] == product_id), None)
                        if updated_product and updated_product['quantity'] == 25 and updated_product['unit_price'] == 15.0:
                            self.log_test("Verify finished product edit", True, 
                                        f"Changes verified: quantity={updated_product['quantity']}, price={updated_product['unit_price']}")
                        else:
                            self.log_test("Verify finished product edit", False, 
                                        f"Changes not reflected: {updated_product}")
                else:
                    self.log_test("Edit finished product", False, 
                                f"HTTP {edit_response.status_code}: {edit_response.text}")
            else:
                self.log_test("Edit finished product", False, 
                            f"Finished product creation failed: HTTP {create_response.status_code}")
                
        except Exception as e:
            self.log_test("Edit finished product", False, f"Exception: {str(e)}")
    
    def test_supplier_editing(self):
        """Test 3: تحرير الموردين - Supplier editing"""
        print("\n=== Testing Supplier Editing Feature ===")
        
        try:
            # First create a supplier
            supplier_data = {
                "name": "مورد اختبار التحرير",
                "phone": "01111111111",
                "address": "عنوان المورد الأصلي"
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/suppliers", json=supplier_data)
            if create_response.status_code == 200:
                supplier = create_response.json()
                supplier_id = supplier['id']
                self.created_data['suppliers'].append(supplier_id)
                
                # Test editing the supplier
                updated_data = {
                    "name": "مورد اختبار التحرير المحدث",
                    "phone": "01222222222",
                    "address": "العنوان الجديد للمورد"
                }
                
                edit_response = self.session.put(f"{BACKEND_URL}/suppliers/{supplier_id}", json=updated_data)
                if edit_response.status_code == 200:
                    self.log_test("Edit supplier", True, 
                                f"Supplier updated successfully")
                    
                    # Verify the changes
                    get_response = self.session.get(f"{BACKEND_URL}/suppliers")
                    if get_response.status_code == 200:
                        suppliers = get_response.json()
                        updated_supplier = next((s for s in suppliers if s['id'] == supplier_id), None)
                        if updated_supplier and updated_supplier['name'] == "مورد اختبار التحرير المحدث":
                            self.log_test("Verify supplier edit", True, 
                                        f"Changes verified: name={updated_supplier['name']}")
                        else:
                            self.log_test("Verify supplier edit", False, 
                                        f"Changes not reflected: {updated_supplier}")
                else:
                    self.log_test("Edit supplier", False, 
                                f"HTTP {edit_response.status_code}: {edit_response.text}")
                
                # Test deleting the supplier
                delete_response = self.session.delete(f"{BACKEND_URL}/suppliers/{supplier_id}")
                if delete_response.status_code == 200:
                    self.log_test("Delete supplier", True, 
                                f"Supplier deleted successfully")
                    
                    # Verify deletion
                    get_response = self.session.get(f"{BACKEND_URL}/suppliers")
                    if get_response.status_code == 200:
                        suppliers = get_response.json()
                        deleted_supplier = next((s for s in suppliers if s['id'] == supplier_id), None)
                        if not deleted_supplier:
                            self.log_test("Verify supplier deletion", True, 
                                        f"Supplier successfully removed from database")
                            # Remove from our tracking since it's deleted
                            self.created_data['suppliers'].remove(supplier_id)
                        else:
                            self.log_test("Verify supplier deletion", False, 
                                        f"Supplier still exists: {deleted_supplier}")
                else:
                    self.log_test("Delete supplier", False, 
                                f"HTTP {delete_response.status_code}: {delete_response.text}")
            else:
                self.log_test("Edit supplier", False, 
                            f"Supplier creation failed: HTTP {create_response.status_code}")
                
        except Exception as e:
            self.log_test("Edit supplier", False, f"Exception: {str(e)}")
    
    def test_material_selection_improvements(self):
        """Test 4: تحسينات اختيار المواد - Material selection improvements"""
        print("\n=== Testing Material Selection Improvements ===")
        
        try:
            # Create multiple materials with same type but different sizes
            materials_data = [
                {
                    "material_type": "NBR",
                    "inner_diameter": 15.0,
                    "outer_diameter": 30.0,
                    "height": 80.0,
                    "pieces_count": 3,
                    "cost_per_mm": 1.8
                },
                {
                    "material_type": "NBR", 
                    "inner_diameter": 20.0,
                    "outer_diameter": 35.0,
                    "height": 90.0,
                    "pieces_count": 4,
                    "cost_per_mm": 2.0
                },
                {
                    "material_type": "NBR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 40.0,
                    "height": 100.0,
                    "pieces_count": 5,
                    "cost_per_mm": 2.2
                }
            ]
            
            created_materials = []
            for material_data in materials_data:
                response = self.session.post(f"{BACKEND_URL}/raw-materials", json=material_data)
                if response.status_code == 200:
                    material = response.json()
                    created_materials.append(material)
                    self.created_data['raw_materials'].append(material['id'])
            
            if len(created_materials) == 3:
                self.log_test("Create multiple NBR materials", True, 
                            f"Created {len(created_materials)} NBR materials with different sizes")
                
                # Test compatibility check with specific requirements
                compatibility_check = {
                    "seal_type": "RSL",
                    "inner_diameter": 20.0,
                    "outer_diameter": 35.0,
                    "height": 8.0
                }
                
                compat_response = self.session.post(f"{BACKEND_URL}/compatibility-check", json=compatibility_check)
                if compat_response.status_code == 200:
                    compat_result = compat_response.json()
                    compatible_materials = compat_result.get('compatible_materials', [])
                    
                    # Should find materials that can accommodate the seal requirements
                    suitable_materials = [m for m in compatible_materials 
                                        if m['inner_diameter'] <= 20.0 and m['outer_diameter'] >= 35.0]
                    
                    if len(suitable_materials) > 0:
                        self.log_test("Material compatibility check", True, 
                                    f"Found {len(suitable_materials)} compatible materials")
                        
                        # Test that materials are properly differentiated by size
                        sizes_found = set()
                        for material in suitable_materials:
                            size_key = f"{material['inner_diameter']}x{material['outer_diameter']}"
                            sizes_found.add(size_key)
                        
                        if len(sizes_found) > 1:
                            self.log_test("Material size differentiation", True, 
                                        f"Materials properly differentiated by size: {sizes_found}")
                        else:
                            self.log_test("Material size differentiation", False, 
                                        f"Materials not properly differentiated: {sizes_found}")
                    else:
                        self.log_test("Material compatibility check", False, 
                                    f"No suitable materials found: {compatible_materials}")
                else:
                    self.log_test("Material compatibility check", False, 
                                f"HTTP {compat_response.status_code}: {compat_response.text}")
            else:
                self.log_test("Create multiple NBR materials", False, 
                            f"Only created {len(created_materials)} out of 3 materials")
                
        except Exception as e:
            self.log_test("Material selection improvements", False, f"Exception: {str(e)}")
    
    def test_local_product_display(self):
        """Test 5: عرض المنتجات المحلية - Local product display"""
        print("\n=== Testing Local Product Display Feature ===")
        
        try:
            # First create a supplier for local products
            supplier_data = {
                "name": "مورد المنتجات المحلية",
                "phone": "01333333333",
                "address": "عنوان مورد المنتجات المحلية"
            }
            
            supplier_response = self.session.post(f"{BACKEND_URL}/suppliers", json=supplier_data)
            if supplier_response.status_code == 200:
                supplier = supplier_response.json()
                supplier_id = supplier['id']
                self.created_data['suppliers'].append(supplier_id)
                
                # Create a local product
                local_product_data = {
                    "name": "خاتم زيت محلي اختبار",
                    "supplier_id": supplier_id,
                    "purchase_price": 8.0,
                    "selling_price": 12.0,
                    "current_stock": 50
                }
                
                product_response = self.session.post(f"{BACKEND_URL}/local-products", json=local_product_data)
                if product_response.status_code == 200:
                    local_product = product_response.json()
                    self.created_data['local_products'].append(local_product['id'])
                    
                    # Create a customer for the invoice
                    customer_data = {"name": "عميل المنتجات المحلية", "phone": "01444444444"}
                    customer_response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
                    if customer_response.status_code == 200:
                        customer = customer_response.json()
                        self.created_data['customers'].append(customer['id'])
                        
                        # Create invoice with local product using new format
                        invoice_data = {
                            "customer_name": "عميل المنتجات المحلية",
                            "customer_id": customer['id'],
                            "invoice_title": "فاتورة منتجات محلية",
                            "supervisor_name": "مشرف المنتجات المحلية",
                            "items": [{
                                "product_type": "local",
                                "product_name": "خاتم زيت محلي اختبار",
                                "supplier": "مورد المنتجات المحلية",
                                "purchase_price": 8.0,
                                "selling_price": 12.0,
                                "quantity": 3,
                                "unit_price": 12.0,
                                "total_price": 36.0,
                                "local_product_details": {
                                    "name": "خاتم زيت محلي اختبار",
                                    "supplier": "مورد المنتجات المحلية",
                                    "product_type": "OR",  # Should display as OR
                                    "product_size": "100"  # Should display as 100
                                }
                            }],
                            "payment_method": "نقدي"
                        }
                        
                        invoice_response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
                        if invoice_response.status_code == 200:
                            invoice = invoice_response.json()
                            self.created_data['invoices'].append(invoice['id'])
                            
                            # Check if local product details are properly saved
                            item = invoice['items'][0]
                            local_details = item.get('local_product_details', {})
                            
                            if (local_details.get('product_type') == 'OR' and 
                                local_details.get('product_size') == '100'):
                                self.log_test("Local product display format", True, 
                                            f"Local product saved with correct format: {local_details.get('product_type')} - {local_details.get('product_size')}")
                            else:
                                self.log_test("Local product display format", False, 
                                            f"Local product format incorrect: {local_details}")
                            
                            # Test retrieving the invoice to verify persistence
                            get_invoice_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice['id']}")
                            if get_invoice_response.status_code == 200:
                                retrieved_invoice = get_invoice_response.json()
                                retrieved_item = retrieved_invoice['items'][0]
                                retrieved_details = retrieved_item.get('local_product_details', {})
                                
                                if (retrieved_details.get('product_type') == 'OR' and 
                                    retrieved_details.get('product_size') == '100'):
                                    self.log_test("Local product display persistence", True, 
                                                f"Local product format persisted correctly")
                                else:
                                    self.log_test("Local product display persistence", False, 
                                                f"Local product format not persisted: {retrieved_details}")
                            else:
                                self.log_test("Local product display persistence", False, 
                                            f"Failed to retrieve invoice: HTTP {get_invoice_response.status_code}")
                        else:
                            self.log_test("Local product display format", False, 
                                        f"Invoice creation failed: HTTP {invoice_response.status_code}")
                    else:
                        self.log_test("Local product display format", False, 
                                    f"Customer creation failed: HTTP {customer_response.status_code}")
                else:
                    self.log_test("Local product display format", False, 
                                f"Local product creation failed: HTTP {product_response.status_code}")
            else:
                self.log_test("Local product display format", False, 
                            f"Supplier creation failed: HTTP {supplier_response.status_code}")
                
        except Exception as e:
            self.log_test("Local product display format", False, f"Exception: {str(e)}")
    
    def test_complete_workflow(self):
        """Test complete workflow from product addition to printing"""
        print("\n=== Testing Complete Workflow ===")
        
        try:
            # Create a complete workflow test
            # 1. Create customer
            customer_data = {"name": "عميل سير العمل الكامل", "phone": "01555555555"}
            customer_response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            
            if customer_response.status_code == 200:
                customer = customer_response.json()
                self.created_data['customers'].append(customer['id'])
                
                # 2. Create raw material
                raw_material_data = {
                    "material_type": "BUR",
                    "inner_diameter": 18.0,
                    "outer_diameter": 38.0,
                    "height": 95.0,
                    "pieces_count": 6,
                    "cost_per_mm": 2.1
                }
                
                material_response = self.session.post(f"{BACKEND_URL}/raw-materials", json=raw_material_data)
                if material_response.status_code == 200:
                    material = material_response.json()
                    self.created_data['raw_materials'].append(material['id'])
                    
                    # 3. Check compatibility
                    compatibility_check = {
                        "seal_type": "RSL",
                        "inner_diameter": 18.0,
                        "outer_diameter": 38.0,
                        "height": 7.0
                    }
                    
                    compat_response = self.session.post(f"{BACKEND_URL}/compatibility-check", json=compatibility_check)
                    if compat_response.status_code == 200:
                        compat_result = compat_response.json()
                        
                        # 4. Create invoice with both manufactured and local products
                        invoice_data = {
                            "customer_name": "عميل سير العمل الكامل",
                            "customer_id": customer['id'],
                            "invoice_title": "فاتورة سير العمل الكامل",
                            "supervisor_name": "مشرف سير العمل",
                            "items": [
                                {
                                    "seal_type": "RSL",
                                    "material_type": "BUR",
                                    "inner_diameter": 18.0,
                                    "outer_diameter": 38.0,
                                    "height": 7.0,
                                    "quantity": 2,
                                    "unit_price": 20.0,
                                    "total_price": 40.0,
                                    "product_type": "manufactured",
                                    "material_used": material.get('unit_code', 'B-1')
                                }
                            ],
                            "payment_method": "نقدي",
                            "discount_type": "percentage",
                            "discount_value": 10.0
                        }
                        
                        invoice_response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
                        if invoice_response.status_code == 200:
                            invoice = invoice_response.json()
                            self.created_data['invoices'].append(invoice['id'])
                            
                            # 5. Check if daily work order was created
                            today = datetime.now().strftime("%Y-%m-%d")
                            work_order_response = self.session.get(f"{BACKEND_URL}/work-orders/daily/{today}")
                            
                            if work_order_response.status_code == 200:
                                work_order = work_order_response.json()
                                
                                # Check if invoice was added to work order
                                work_order_invoices = work_order.get('invoices', [])
                                invoice_in_work_order = any(inv.get('id') == invoice['id'] for inv in work_order_invoices)
                                
                                if invoice_in_work_order:
                                    self.log_test("Complete workflow integration", True, 
                                                f"Invoice successfully added to daily work order")
                                else:
                                    self.log_test("Complete workflow integration", False, 
                                                f"Invoice not found in daily work order")
                            else:
                                self.log_test("Complete workflow integration", False, 
                                            f"Daily work order not created: HTTP {work_order_response.status_code}")
                        else:
                            self.log_test("Complete workflow integration", False, 
                                        f"Invoice creation failed: HTTP {invoice_response.status_code}")
                    else:
                        self.log_test("Complete workflow integration", False, 
                                    f"Compatibility check failed: HTTP {compat_response.status_code}")
                else:
                    self.log_test("Complete workflow integration", False, 
                                f"Raw material creation failed: HTTP {material_response.status_code}")
            else:
                self.log_test("Complete workflow integration", False, 
                            f"Customer creation failed: HTTP {customer_response.status_code}")
                
        except Exception as e:
            self.log_test("Complete workflow integration", False, f"Exception: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        cleanup_count = 0
        
        # Clean up in reverse order of dependencies
        for invoice_id in self.created_data['invoices']:
            try:
                response = self.session.delete(f"{BACKEND_URL}/invoices/{invoice_id}")
                if response.status_code == 200:
                    cleanup_count += 1
            except:
                pass
        
        for product_id in self.created_data['local_products']:
            try:
                response = self.session.delete(f"{BACKEND_URL}/local-products/{product_id}")
                if response.status_code == 200:
                    cleanup_count += 1
            except:
                pass
        
        for supplier_id in self.created_data['suppliers']:
            try:
                response = self.session.delete(f"{BACKEND_URL}/suppliers/{supplier_id}")
                if response.status_code == 200:
                    cleanup_count += 1
            except:
                pass
        
        for product_id in self.created_data['finished_products']:
            try:
                response = self.session.delete(f"{BACKEND_URL}/finished-products/{product_id}")
                if response.status_code == 200:
                    cleanup_count += 1
            except:
                pass
        
        for material_id in self.created_data['raw_materials']:
            try:
                response = self.session.delete(f"{BACKEND_URL}/raw-materials/{material_id}")
                if response.status_code == 200:
                    cleanup_count += 1
            except:
                pass
        
        for customer_id in self.created_data['customers']:
            try:
                response = self.session.delete(f"{BACKEND_URL}/customers/{customer_id}")
                if response.status_code == 200:
                    cleanup_count += 1
            except:
                pass
        
        print(f"Cleaned up {cleanup_count} test records")
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY - ملخص الاختبار")
        print(f"{'='*60}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"{'='*60}")
        
        if failed_tests > 0:
            print(f"\nFAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"❌ {result['test']}: {result['details']}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'test_results': self.test_results
        }
    
    def run_all_tests(self):
        """Run all new feature tests"""
        print("Starting comprehensive testing of new features...")
        print("بدء الاختبار الشامل للمميزات الجديدة...")
        
        # Run all test categories
        self.test_w_type_wall_height()
        self.test_inventory_editing()
        self.test_supplier_editing()
        self.test_material_selection_improvements()
        self.test_local_product_display()
        self.test_complete_workflow()
        
        # Generate summary
        summary = self.generate_summary()
        
        # Cleanup
        self.cleanup_test_data()
        
        return summary

def main():
    """Main function to run the tests"""
    tester = NewFeaturesAPITester()
    
    try:
        summary = tester.run_all_tests()
        
        # Exit with appropriate code
        if summary['failed_tests'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        tester.cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        tester.cleanup_test_data()
        sys.exit(1)

if __name__ == "__main__":
    main()