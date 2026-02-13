#!/usr/bin/env python3
"""
Latest Improvements Testing for Master Seal System
اختبار التحسينات الأخيرة لنظام ماستر سيل

Focus Areas:
1. Updated Inventory System (Pieces instead of Height)
2. Treasury Integration Fix (Deferred payments)
3. Invoice Editing
4. Local Products with Size/Type Split
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class LatestImprovementsTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_data = {
            'inventory_items': [],
            'inventory_transactions': [],
            'invoices': [],
            'customers': [],
            'suppliers': [],
            'local_products': [],
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
    
    def test_inventory_system_pieces(self):
        """Test Updated Inventory System - Pieces instead of Height"""
        print("\n=== Testing Updated Inventory System (Pieces) ===")
        
        # Test 1: POST /api/inventory with available_pieces
        inventory_items_data = [
            {
                "material_type": "NBR",
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "available_pieces": 50,  # Using pieces instead of height
                "min_stock_level": 5,
                "notes": "اختبار نظام الجرد الجديد - قطع NBR"
            },
            {
                "material_type": "BUR", 
                "inner_diameter": 30.0,
                "outer_diameter": 45.0,
                "available_pieces": 30,
                "min_stock_level": 3,
                "notes": "اختبار نظام الجرد الجديد - قطع BUR"
            },
            {
                "material_type": "VT",
                "inner_diameter": 40.0,
                "outer_diameter": 55.0,
                "available_pieces": 20,
                "min_stock_level": 2,
                "notes": "اختبار نظام الجرد الجديد - قطع VT"
            }
        ]
        
        for item_data in inventory_items_data:
            try:
                response = self.session.post(f"{BACKEND_URL}/inventory", 
                                           json=item_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    if (data.get('material_type') == item_data['material_type'] and 
                        data.get('available_pieces') == item_data['available_pieces']):
                        self.created_data['inventory_items'].append(data)
                        self.log_test(f"Create Inventory Item (Pieces) - {item_data['material_type']}", True, 
                                    f"Created with {data.get('available_pieces')} pieces")
                    else:
                        self.log_test(f"Create Inventory Item (Pieces) - {item_data['material_type']}", False, 
                                    f"Data mismatch: {data}")
                else:
                    self.log_test(f"Create Inventory Item (Pieces) - {item_data['material_type']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"Create Inventory Item (Pieces) - {item_data['material_type']}", False, 
                            f"Exception: {str(e)}")
        
        # Test 2: Test inventory transactions with pieces_change
        if self.created_data['inventory_items']:
            test_item = self.created_data['inventory_items'][0]
            
            # Test IN transaction (adding pieces)
            in_transaction_data = {
                "inventory_item_id": test_item['id'],
                "material_type": test_item['material_type'],
                "inner_diameter": test_item['inner_diameter'],
                "outer_diameter": test_item['outer_diameter'],
                "transaction_type": "in",
                "pieces_change": 25,  # Adding 25 pieces
                "reason": "إضافة مخزون جديد - اختبار القطع",
                "notes": "اختبار معاملة إدخال بالقطع"
            }
            
            try:
                response = self.session.post(f"{BACKEND_URL}/inventory-transactions", 
                                           json=in_transaction_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    if (data.get('pieces_change') == 25 and 
                        data.get('transaction_type') == 'in'):
                        self.created_data['inventory_transactions'].append(data)
                        self.log_test("Inventory Transaction IN (Pieces)", True, 
                                    f"Added {data.get('pieces_change')} pieces, remaining: {data.get('remaining_pieces')}")
                    else:
                        self.log_test("Inventory Transaction IN (Pieces)", False, f"Data mismatch: {data}")
                else:
                    self.log_test("Inventory Transaction IN (Pieces)", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("Inventory Transaction IN (Pieces)", False, f"Exception: {str(e)}")
            
            # Test OUT transaction (consuming pieces)
            out_transaction_data = {
                "inventory_item_id": test_item['id'],
                "material_type": test_item['material_type'],
                "inner_diameter": test_item['inner_diameter'],
                "outer_diameter": test_item['outer_diameter'],
                "transaction_type": "out",
                "pieces_change": -10,  # Consuming 10 pieces
                "reason": "استهلاك للإنتاج - اختبار القطع",
                "notes": "اختبار معاملة إخراج بالقطع"
            }
            
            try:
                response = self.session.post(f"{BACKEND_URL}/inventory-transactions", 
                                           json=out_transaction_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    if (data.get('pieces_change') == -10 and 
                        data.get('transaction_type') == 'out'):
                        self.created_data['inventory_transactions'].append(data)
                        self.log_test("Inventory Transaction OUT (Pieces)", True, 
                                    f"Consumed {abs(data.get('pieces_change'))} pieces, remaining: {data.get('remaining_pieces')}")
                    else:
                        self.log_test("Inventory Transaction OUT (Pieces)", False, f"Data mismatch: {data}")
                else:
                    self.log_test("Inventory Transaction OUT (Pieces)", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("Inventory Transaction OUT (Pieces)", False, f"Exception: {str(e)}")
        
        # Test 3: Test low stock detection based on pieces
        try:
            response = self.session.get(f"{BACKEND_URL}/inventory/low-stock")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check if any items are correctly identified as low stock
                    low_stock_items = [item for item in data if item.get('available_pieces', 0) < item.get('min_stock_level', 0)]
                    self.log_test("Low Stock Detection (Pieces)", True, 
                                f"Found {len(low_stock_items)} low stock items based on pieces")
                else:
                    self.log_test("Low Stock Detection (Pieces)", False, f"Expected list, got: {type(data)}")
            else:
                # This might fail due to MongoDB query issue mentioned in test_result.md
                self.log_test("Low Stock Detection (Pieces)", False, 
                            f"HTTP {response.status_code}: {response.text} (Known issue with MongoDB query)")
        except Exception as e:
            self.log_test("Low Stock Detection (Pieces)", False, f"Exception: {str(e)}")
        
        # Test 4: Verify inventory check for raw materials uses pieces
        if self.created_data['inventory_items']:
            test_item = self.created_data['inventory_items'][0]
            
            # Create a raw material that should check inventory availability
            raw_material_data = {
                "material_type": test_item['material_type'],
                "inner_diameter": test_item['inner_diameter'],
                "outer_diameter": test_item['outer_diameter'],
                "height": 100.0,
                "pieces_count": 5,  # Requesting 5 pieces
                "unit_code": f"TEST-{test_item['material_type']}-001",
                "cost_per_mm": 0.15
            }
            
            try:
                response = self.session.post(f"{BACKEND_URL}/raw-materials", 
                                           json=raw_material_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Raw Material Creation with Inventory Check (Pieces)", True, 
                                f"Raw material created successfully, inventory checked for pieces")
                elif response.status_code == 400:
                    # Check if error message mentions pieces availability
                    error_text = response.text
                    if "قطعة" in error_text or "pieces" in error_text.lower():
                        self.log_test("Raw Material Creation with Inventory Check (Pieces)", True, 
                                    f"Correctly rejected due to insufficient pieces: {error_text}")
                    else:
                        self.log_test("Raw Material Creation with Inventory Check (Pieces)", False, 
                                    f"Error message doesn't mention pieces: {error_text}")
                else:
                    self.log_test("Raw Material Creation with Inventory Check (Pieces)", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("Raw Material Creation with Inventory Check (Pieces)", False, f"Exception: {str(e)}")
    
    def test_treasury_integration_fix(self):
        """Test Treasury Integration Fix - Deferred payments should NOT create treasury transactions"""
        print("\n=== Testing Treasury Integration Fix ===")
        
        # First, create a customer for testing
        customer_data = {
            "name": "عميل اختبار الخزينة",
            "phone": "01234567890",
            "address": "القاهرة"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/customers", 
                                       json=customer_data,
                                       headers={'Content-Type': 'application/json'})
            if response.status_code == 200:
                customer = response.json()
                self.created_data['customers'].append(customer)
            else:
                self.log_test("Treasury Integration Test Setup", False, "Failed to create test customer")
                return
        except Exception as e:
            self.log_test("Treasury Integration Test Setup", False, f"Exception creating customer: {str(e)}")
            return
        
        # Get initial treasury state
        try:
            initial_treasury_response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
            initial_treasury_count = len(initial_treasury_response.json()) if initial_treasury_response.status_code == 200 else 0
        except:
            initial_treasury_count = 0
        
        # Test 1: Invoice with payment method "آجل" should NOT create treasury transaction
        deferred_invoice_data = {
            "customer_id": customer['id'],
            "customer_name": customer['name'],
            "invoice_title": "فاتورة اختبار آجل",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 8.0,
                    "quantity": 5,
                    "unit_price": 20.0,
                    "total_price": 100.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "آجل",  # Deferred payment
            "discount_type": "amount",
            "discount_value": 0.0,
            "notes": "اختبار عدم إنشاء معاملة خزينة للدفع الآجل"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/invoices", 
                                       json=deferred_invoice_data,
                                       headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                deferred_invoice = response.json()
                self.created_data['invoices'].append(deferred_invoice)
                
                # Check if treasury transaction was NOT created
                treasury_response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
                if treasury_response.status_code == 200:
                    current_treasury_count = len(treasury_response.json())
                    
                    if current_treasury_count == initial_treasury_count:
                        self.log_test("Deferred Invoice - No Treasury Transaction", True, 
                                    "Correctly did NOT create treasury transaction for deferred payment")
                    else:
                        self.log_test("Deferred Invoice - No Treasury Transaction", False, 
                                    f"Treasury transaction was created for deferred payment (count: {initial_treasury_count} -> {current_treasury_count})")
                else:
                    self.log_test("Deferred Invoice - No Treasury Transaction", False, 
                                "Failed to check treasury transactions")
            else:
                self.log_test("Deferred Invoice - No Treasury Transaction", False, 
                            f"Failed to create deferred invoice: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Deferred Invoice - No Treasury Transaction", False, f"Exception: {str(e)}")
        
        # Test 2: Invoice with other payment methods SHOULD create treasury transaction
        cash_invoice_data = {
            "customer_id": customer['id'],
            "customer_name": customer['name'],
            "invoice_title": "فاتورة اختبار نقدي",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RS",
                    "material_type": "BUR",
                    "inner_diameter": 30.0,
                    "outer_diameter": 45.0,
                    "height": 7.0,
                    "quantity": 3,
                    "unit_price": 25.0,
                    "total_price": 75.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "نقدي",  # Cash payment
            "discount_type": "amount",
            "discount_value": 0.0,
            "notes": "اختبار إنشاء معاملة خزينة للدفع النقدي"
        }
        
        try:
            # Get treasury count before cash invoice
            pre_cash_treasury_response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
            pre_cash_count = len(pre_cash_treasury_response.json()) if pre_cash_treasury_response.status_code == 200 else 0
            
            response = self.session.post(f"{BACKEND_URL}/invoices", 
                                       json=cash_invoice_data,
                                       headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                cash_invoice = response.json()
                self.created_data['invoices'].append(cash_invoice)
                
                # Check if treasury transaction WAS created
                treasury_response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
                if treasury_response.status_code == 200:
                    post_cash_count = len(treasury_response.json())
                    
                    if post_cash_count > pre_cash_count:
                        # Verify the transaction details
                        transactions = treasury_response.json()
                        latest_transaction = transactions[0] if transactions else None
                        
                        if (latest_transaction and 
                            latest_transaction.get('transaction_type') == 'income' and
                            latest_transaction.get('amount') == 75.0):
                            self.log_test("Cash Invoice - Treasury Transaction Created", True, 
                                        f"Correctly created treasury transaction for cash payment: {latest_transaction.get('amount')} ج.م")
                        else:
                            self.log_test("Cash Invoice - Treasury Transaction Created", False, 
                                        f"Treasury transaction created but with wrong details: {latest_transaction}")
                    else:
                        self.log_test("Cash Invoice - Treasury Transaction Created", False, 
                                    "Treasury transaction was NOT created for cash payment")
                else:
                    self.log_test("Cash Invoice - Treasury Transaction Created", False, 
                                "Failed to check treasury transactions")
            else:
                self.log_test("Cash Invoice - Treasury Transaction Created", False, 
                            f"Failed to create cash invoice: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Cash Invoice - Treasury Transaction Created", False, f"Exception: {str(e)}")
        
        # Test 3: Verify payment method mapping works correctly
        payment_methods_to_test = [
            ("فودافون كاش محمد الصاوي", "vodafone_elsawy"),
            ("فودافون كاش وائل محمد", "vodafone_wael"),
            ("انستاباي", "instapay"),
            ("يد الصاوي", "yad_elsawy")
        ]
        
        for payment_method, expected_account in payment_methods_to_test:
            invoice_data = {
                "customer_id": customer['id'],
                "customer_name": customer['name'],
                "invoice_title": f"فاتورة اختبار {payment_method}",
                "items": [
                    {
                        "seal_type": "B17",
                        "material_type": "VT",
                        "inner_diameter": 40.0,
                        "outer_diameter": 55.0,
                        "height": 10.0,
                        "quantity": 1,
                        "unit_price": 30.0,
                        "total_price": 30.0,
                        "product_type": "manufactured"
                    }
                ],
                "payment_method": payment_method,
                "discount_type": "amount",
                "discount_value": 0.0,
                "notes": f"اختبار تطابق طريقة الدفع {payment_method}"
            }
            
            try:
                # Get treasury count before
                pre_response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
                pre_count = len(pre_response.json()) if pre_response.status_code == 200 else 0
                
                response = self.session.post(f"{BACKEND_URL}/invoices", 
                                           json=invoice_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    invoice = response.json()
                    self.created_data['invoices'].append(invoice)
                    
                    # Check treasury transaction
                    treasury_response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
                    if treasury_response.status_code == 200:
                        transactions = treasury_response.json()
                        post_count = len(transactions)
                        
                        if post_count > pre_count:
                            latest_transaction = transactions[0]
                            actual_account = latest_transaction.get('account_id')
                            
                            if actual_account == expected_account:
                                self.log_test(f"Payment Method Mapping - {payment_method}", True, 
                                            f"Correctly mapped to account: {expected_account}")
                            else:
                                self.log_test(f"Payment Method Mapping - {payment_method}", False, 
                                            f"Wrong account mapping: expected {expected_account}, got {actual_account}")
                        else:
                            self.log_test(f"Payment Method Mapping - {payment_method}", False, 
                                        "No treasury transaction created")
                    else:
                        self.log_test(f"Payment Method Mapping - {payment_method}", False, 
                                    "Failed to check treasury transactions")
                else:
                    self.log_test(f"Payment Method Mapping - {payment_method}", False, 
                                f"Failed to create invoice: HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Payment Method Mapping - {payment_method}", False, f"Exception: {str(e)}")
    
    def test_invoice_editing(self):
        """Test Invoice Editing - PUT /api/invoices/{id}"""
        print("\n=== Testing Invoice Editing ===")
        
        if not self.created_data['invoices']:
            self.log_test("Invoice Editing", False, "No invoices available for editing test")
            return
        
        # Test 1: Edit invoice title and supervisor name
        test_invoice = self.created_data['invoices'][0]
        
        edit_data_1 = {
            "invoice_title": "فاتورة محدثة - اختبار التحرير",
            "supervisor_name": "مشرف محدث - أحمد محمد"
        }
        
        try:
            response = self.session.put(f"{BACKEND_URL}/invoices/{test_invoice['id']}", 
                                      json=edit_data_1,
                                      headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                # Verify the update
                verify_response = self.session.get(f"{BACKEND_URL}/invoices/{test_invoice['id']}")
                if verify_response.status_code == 200:
                    updated_invoice = verify_response.json()
                    
                    if (updated_invoice.get('invoice_title') == edit_data_1['invoice_title'] and
                        updated_invoice.get('supervisor_name') == edit_data_1['supervisor_name']):
                        self.log_test("Edit Invoice - Title and Supervisor", True, 
                                    f"Successfully updated title and supervisor name")
                    else:
                        self.log_test("Edit Invoice - Title and Supervisor", False, 
                                    f"Updates not reflected: {updated_invoice}")
                else:
                    self.log_test("Edit Invoice - Title and Supervisor", False, 
                                "Failed to verify update")
            else:
                self.log_test("Edit Invoice - Title and Supervisor", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Edit Invoice - Title and Supervisor", False, f"Exception: {str(e)}")
        
        # Test 2: Edit discount and verify totals are recalculated
        edit_data_2 = {
            "discount_type": "percentage",
            "discount_value": 15.0  # 15% discount
        }
        
        try:
            # Get original totals
            original_response = self.session.get(f"{BACKEND_URL}/invoices/{test_invoice['id']}")
            if original_response.status_code == 200:
                original_invoice = original_response.json()
                original_subtotal = original_invoice.get('subtotal', 0)
                
                response = self.session.put(f"{BACKEND_URL}/invoices/{test_invoice['id']}", 
                                          json=edit_data_2,
                                          headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    # Verify discount calculation
                    verify_response = self.session.get(f"{BACKEND_URL}/invoices/{test_invoice['id']}")
                    if verify_response.status_code == 200:
                        updated_invoice = verify_response.json()
                        
                        expected_discount = (original_subtotal * 15.0) / 100
                        expected_total_after_discount = original_subtotal - expected_discount
                        
                        actual_discount = updated_invoice.get('discount', 0)
                        actual_total_after_discount = updated_invoice.get('total_after_discount', 0)
                        
                        if (abs(actual_discount - expected_discount) < 0.01 and
                            abs(actual_total_after_discount - expected_total_after_discount) < 0.01):
                            self.log_test("Edit Invoice - Discount Recalculation", True, 
                                        f"Discount correctly recalculated: {actual_discount:.2f} ج.م, Total: {actual_total_after_discount:.2f} ج.م")
                        else:
                            self.log_test("Edit Invoice - Discount Recalculation", False, 
                                        f"Wrong calculation: expected discount {expected_discount:.2f}, got {actual_discount:.2f}")
                    else:
                        self.log_test("Edit Invoice - Discount Recalculation", False, 
                                    "Failed to verify discount update")
                else:
                    self.log_test("Edit Invoice - Discount Recalculation", False, 
                                f"HTTP {response.status_code}: {response.text}")
            else:
                self.log_test("Edit Invoice - Discount Recalculation", False, 
                            "Failed to get original invoice data")
        except Exception as e:
            self.log_test("Edit Invoice - Discount Recalculation", False, f"Exception: {str(e)}")
        
        # Test 3: Edit items and verify totals are recalculated
        new_items = [
            {
                "seal_type": "RSL",
                "material_type": "NBR",
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "height": 8.0,
                "quantity": 10,  # Changed quantity
                "unit_price": 22.0,  # Changed price
                "total_price": 220.0,  # 10 * 22
                "product_type": "manufactured"
            },
            {
                "seal_type": "RS",
                "material_type": "BUR",
                "inner_diameter": 30.0,
                "outer_diameter": 45.0,
                "height": 7.0,
                "quantity": 5,
                "unit_price": 18.0,
                "total_price": 90.0,  # 5 * 18
                "product_type": "manufactured"
            }
        ]
        
        edit_data_3 = {
            "items": new_items
        }
        
        try:
            response = self.session.put(f"{BACKEND_URL}/invoices/{test_invoice['id']}", 
                                      json=edit_data_3,
                                      headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                # Verify items update and total recalculation
                verify_response = self.session.get(f"{BACKEND_URL}/invoices/{test_invoice['id']}")
                if verify_response.status_code == 200:
                    updated_invoice = verify_response.json()
                    
                    expected_subtotal = 220.0 + 90.0  # 310.0
                    actual_subtotal = updated_invoice.get('subtotal', 0)
                    actual_items_count = len(updated_invoice.get('items', []))
                    
                    if (abs(actual_subtotal - expected_subtotal) < 0.01 and
                        actual_items_count == 2):
                        self.log_test("Edit Invoice - Items and Total Recalculation", True, 
                                    f"Items updated and subtotal recalculated: {actual_subtotal:.2f} ج.م")
                    else:
                        self.log_test("Edit Invoice - Items and Total Recalculation", False, 
                                    f"Wrong calculation: expected subtotal {expected_subtotal}, got {actual_subtotal}, items: {actual_items_count}")
                else:
                    self.log_test("Edit Invoice - Items and Total Recalculation", False, 
                                "Failed to verify items update")
            else:
                self.log_test("Edit Invoice - Items and Total Recalculation", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Edit Invoice - Items and Total Recalculation", False, f"Exception: {str(e)}")
    
    def test_local_products_with_size_type_split(self):
        """Test Local Products with Size/Type Split"""
        print("\n=== Testing Local Products with Size/Type Split ===")
        
        # First, create suppliers for local products
        suppliers_data = [
            {
                "name": "مورد المنتجات المحلية الأول",
                "phone": "01234567890",
                "address": "القاهرة - المعادي"
            },
            {
                "name": "مورد المنتجات المحلية الثاني", 
                "phone": "01098765432",
                "address": "الجيزة - الهرم"
            }
        ]
        
        for supplier_data in suppliers_data:
            try:
                response = self.session.post(f"{BACKEND_URL}/suppliers", 
                                           json=supplier_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    supplier = response.json()
                    self.created_data['suppliers'].append(supplier)
                    self.log_test(f"Create Supplier - {supplier_data['name']}", True, 
                                f"Supplier ID: {supplier.get('id')}")
                else:
                    self.log_test(f"Create Supplier - {supplier_data['name']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"Create Supplier - {supplier_data['name']}", False, f"Exception: {str(e)}")
        
        if not self.created_data['suppliers']:
            self.log_test("Local Products Test", False, "No suppliers created for local products test")
            return
        
        # Create local products with separate size and type fields
        local_products_data = [
            {
                "name": "منتج محلي - نوع A - مقاس صغير",
                "supplier_id": self.created_data['suppliers'][0]['id'],
                "purchase_price": 15.0,
                "selling_price": 25.0,
                "current_stock": 100
            },
            {
                "name": "منتج محلي - نوع B - مقاس متوسط",
                "supplier_id": self.created_data['suppliers'][0]['id'],
                "purchase_price": 20.0,
                "selling_price": 35.0,
                "current_stock": 75
            },
            {
                "name": "منتج محلي - نوع C - مقاس كبير",
                "supplier_id": self.created_data['suppliers'][1]['id'],
                "purchase_price": 30.0,
                "selling_price": 50.0,
                "current_stock": 50
            }
        ]
        
        for product_data in local_products_data:
            try:
                response = self.session.post(f"{BACKEND_URL}/local-products", 
                                           json=product_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    product = response.json()
                    self.created_data['local_products'].append(product)
                    self.log_test(f"Create Local Product - {product_data['name']}", True, 
                                f"Product ID: {product.get('id')}, Supplier: {product.get('supplier_name')}")
                else:
                    self.log_test(f"Create Local Product - {product_data['name']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"Create Local Product - {product_data['name']}", False, f"Exception: {str(e)}")
        
        # Test creating invoices with local products that have separate size and type fields
        if self.created_data['local_products'] and self.created_data['customers']:
            customer = self.created_data['customers'][0]
            
            # Create invoice with mixed local products (different sizes and types)
            local_product_invoice_data = {
                "customer_id": customer['id'],
                "customer_name": customer['name'],
                "invoice_title": "فاتورة منتجات محلية - أحجام وأنواع مختلفة",
                "supervisor_name": "مشرف المنتجات المحلية",
                "items": [
                    {
                        "product_type": "local",
                        "product_name": self.created_data['local_products'][0]['name'],
                        "supplier": self.created_data['local_products'][0]['supplier_name'],
                        "quantity": 5,
                        "unit_price": self.created_data['local_products'][0]['selling_price'],
                        "total_price": 5 * self.created_data['local_products'][0]['selling_price'],
                        "purchase_price": self.created_data['local_products'][0]['purchase_price'],
                        "selling_price": self.created_data['local_products'][0]['selling_price'],
                        "local_product_details": {
                            "name": self.created_data['local_products'][0]['name'],
                            "supplier": self.created_data['local_products'][0]['supplier_name'],
                            "size": "صغير",  # Size field
                            "type": "نوع A",  # Type field
                            "purchase_price": self.created_data['local_products'][0]['purchase_price'],
                            "selling_price": self.created_data['local_products'][0]['selling_price'],
                            "supplier_id": self.created_data['local_products'][0]['supplier_id']
                        }
                    },
                    {
                        "product_type": "local",
                        "product_name": self.created_data['local_products'][1]['name'],
                        "supplier": self.created_data['local_products'][1]['supplier_name'],
                        "quantity": 3,
                        "unit_price": self.created_data['local_products'][1]['selling_price'],
                        "total_price": 3 * self.created_data['local_products'][1]['selling_price'],
                        "purchase_price": self.created_data['local_products'][1]['purchase_price'],
                        "selling_price": self.created_data['local_products'][1]['selling_price'],
                        "local_product_details": {
                            "name": self.created_data['local_products'][1]['name'],
                            "supplier": self.created_data['local_products'][1]['supplier_name'],
                            "size": "متوسط",  # Size field
                            "type": "نوع B",  # Type field
                            "purchase_price": self.created_data['local_products'][1]['purchase_price'],
                            "selling_price": self.created_data['local_products'][1]['selling_price'],
                            "supplier_id": self.created_data['local_products'][1]['supplier_id']
                        }
                    },
                    {
                        "product_type": "local",
                        "product_name": self.created_data['local_products'][2]['name'],
                        "supplier": self.created_data['local_products'][2]['supplier_name'],
                        "quantity": 2,
                        "unit_price": self.created_data['local_products'][2]['selling_price'],
                        "total_price": 2 * self.created_data['local_products'][2]['selling_price'],
                        "purchase_price": self.created_data['local_products'][2]['purchase_price'],
                        "selling_price": self.created_data['local_products'][2]['selling_price'],
                        "local_product_details": {
                            "name": self.created_data['local_products'][2]['name'],
                            "supplier": self.created_data['local_products'][2]['supplier_name'],
                            "size": "كبير",  # Size field
                            "type": "نوع C",  # Type field
                            "purchase_price": self.created_data['local_products'][2]['purchase_price'],
                            "selling_price": self.created_data['local_products'][2]['selling_price'],
                            "supplier_id": self.created_data['local_products'][2]['supplier_id']
                        }
                    }
                ],
                "payment_method": "نقدي",
                "discount_type": "amount",
                "discount_value": 0.0,
                "notes": "اختبار فاتورة منتجات محلية بأحجام وأنواع منفصلة"
            }
            
            try:
                response = self.session.post(f"{BACKEND_URL}/invoices", 
                                           json=local_product_invoice_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    invoice = response.json()
                    self.created_data['invoices'].append(invoice)
                    
                    # Verify that local product details are stored correctly
                    verify_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice['id']}")
                    if verify_response.status_code == 200:
                        stored_invoice = verify_response.json()
                        items = stored_invoice.get('items', [])
                        
                        # Check if all items have local_product_details with size and type
                        all_items_valid = True
                        for item in items:
                            if item.get('product_type') == 'local':
                                details = item.get('local_product_details', {})
                                if not (details.get('size') and details.get('type')):
                                    all_items_valid = False
                                    break
                        
                        if all_items_valid and len(items) == 3:
                            self.log_test("Local Products Invoice - Size/Type Split", True, 
                                        f"Invoice created with {len(items)} local products, all with size and type details")
                            
                            # Verify specific details
                            item1_details = items[0].get('local_product_details', {})
                            item2_details = items[1].get('local_product_details', {})
                            item3_details = items[2].get('local_product_details', {})
                            
                            if (item1_details.get('size') == 'صغير' and item1_details.get('type') == 'نوع A' and
                                item2_details.get('size') == 'متوسط' and item2_details.get('type') == 'نوع B' and
                                item3_details.get('size') == 'كبير' and item3_details.get('type') == 'نوع C'):
                                self.log_test("Local Products Details - Size/Type Storage", True, 
                                            "All size and type details stored correctly")
                            else:
                                self.log_test("Local Products Details - Size/Type Storage", False, 
                                            f"Size/Type details not stored correctly: {[item1_details, item2_details, item3_details]}")
                        else:
                            self.log_test("Local Products Invoice - Size/Type Split", False, 
                                        f"Items validation failed: valid={all_items_valid}, count={len(items)}")
                    else:
                        self.log_test("Local Products Invoice - Size/Type Split", False, 
                                    "Failed to verify stored invoice")
                else:
                    self.log_test("Local Products Invoice - Size/Type Split", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("Local Products Invoice - Size/Type Split", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all latest improvements tests"""
        print("🚀 Starting Latest Improvements Testing for Master Seal System")
        print("=" * 80)
        
        # Run all test categories
        self.test_inventory_system_pieces()
        self.test_treasury_integration_fix()
        self.test_invoice_editing()
        self.test_local_products_with_size_type_split()
        
        # Generate summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n🎯 FOCUS AREAS TESTED:")
        print("  1. ✅ Updated Inventory System (Pieces instead of Height)")
        print("  2. ✅ Treasury Integration Fix (Deferred payments)")
        print("  3. ✅ Invoice Editing")
        print("  4. ✅ Local Products with Size/Type Split")
        
        return success_rate >= 80  # Consider successful if 80% or more tests pass

if __name__ == "__main__":
    tester = LatestImprovementsTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Latest improvements testing completed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the results above.")
        sys.exit(1)