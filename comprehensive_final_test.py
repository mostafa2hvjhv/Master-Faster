#!/usr/bin/env python3
"""
اختبار نهائي شامل للتأكد من حل جميع المشاكل الحرجة
Comprehensive Final Test for Critical Issues Resolution

This test focuses on the 5 main areas mentioned in the Arabic review request:
1. Payment method matching with treasury accounts (enum serialization fix)
2. Inventory transactions API (compatibility with old data)  
3. Inventory integration with raw materials (was working previously)
4. Deferred invoices (was working previously)
5. Discount calculation in invoices (was working previously)
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"

class ComprehensiveFinalTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        print(result)
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'details': details
        })
        
    def make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request error for {method} {endpoint}: {str(e)}")
            return None

    def test_1_payment_method_treasury_matching(self):
        """
        اختبار 1: تطابق طرق الدفع مع حسابات الخزينة
        Test payment method matching with treasury accounts
        """
        print("\n" + "="*80)
        print("اختبار 1: تطابق طرق الدفع مع حسابات الخزينة")
        print("Test 1: Payment Method Treasury Account Matching")
        print("="*80)
        
        # Clear existing data first
        self.make_request('DELETE', '/invoices/clear-all')
        self.make_request('DELETE', '/customers/clear-all')
        time.sleep(1)
        
        # Create test customer
        customer_data = {
            "name": "أحمد محمد الصاوي",
            "phone": "01234567890",
            "address": "القاهرة، مصر"
        }
        customer_response = self.make_request('POST', '/customers', customer_data)
        if not customer_response or customer_response.status_code != 200:
            self.log_test("إنشاء عميل اختبار", False, "فشل في إنشاء العميل")
            return
        
        customer = customer_response.json()
        
        # Test payment methods and their expected treasury accounts
        payment_methods_test = [
            {
                "payment_method": "نقدي",
                "expected_account": "cash",
                "test_name": "فاتورة نقدي → حساب cash"
            },
            {
                "payment_method": "فودافون كاش محمد الصاوي", 
                "expected_account": "vodafone_elsawy",
                "test_name": "فاتورة فودافون كاش محمد الصاوي → حساب vodafone_elsawy"
            },
            {
                "payment_method": "انستاباي",
                "expected_account": "instapay", 
                "test_name": "فاتورة انستاباي → حساب instapay"
            },
            {
                "payment_method": "يد الصاوي",
                "expected_account": "yad_elsawy",
                "test_name": "فاتورة يد الصاوي → حساب yad_elsawy"
            }
        ]
        
        # Get initial treasury balances
        initial_balances_response = self.make_request('GET', '/treasury/balances')
        if not initial_balances_response or initial_balances_response.status_code != 200:
            self.log_test("جلب أرصدة الخزينة الأولية", False, "فشل في جلب الأرصدة")
            return
        
        initial_balances = initial_balances_response.json()
        
        for i, payment_test in enumerate(payment_methods_test):
            # Create invoice with specific payment method
            invoice_data = {
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "invoice_title": f"فاتورة اختبار {payment_test['payment_method']}",
                "supervisor_name": "مشرف الاختبار",
                "items": [
                    {
                        "seal_type": "RSL",
                        "material_type": "NBR", 
                        "inner_diameter": 25.0,
                        "outer_diameter": 35.0,
                        "height": 10.0,
                        "quantity": 2,
                        "unit_price": 15.0,
                        "total_price": 30.0,
                        "product_type": "manufactured"
                    }
                ],
                "payment_method": payment_test["payment_method"],
                "discount_type": "amount",
                "discount_value": 0.0
            }
            
            # Create invoice
            invoice_response = self.make_request('POST', '/invoices', invoice_data)
            if not invoice_response or invoice_response.status_code != 200:
                self.log_test(f"إنشاء {payment_test['test_name']}", False, f"فشل في إنشاء الفاتورة: {invoice_response.status_code if invoice_response else 'No response'}")
                continue
                
            invoice = invoice_response.json()
            
            # Wait for treasury transaction to be created
            time.sleep(1)
            
            # Get updated treasury balances
            updated_balances_response = self.make_request('GET', '/treasury/balances')
            if not updated_balances_response or updated_balances_response.status_code != 200:
                self.log_test(f"جلب أرصدة محدثة لـ {payment_test['test_name']}", False, "فشل في جلب الأرصدة المحدثة")
                continue
                
            updated_balances = updated_balances_response.json()
            
            # Check if the correct account was credited
            expected_account = payment_test["expected_account"]
            expected_increase = 30.0  # Invoice total
            
            initial_balance = initial_balances.get(expected_account, 0)
            updated_balance = updated_balances.get(expected_account, 0)
            actual_increase = updated_balance - initial_balance
            
            # Check if the increase matches expected amount
            if abs(actual_increase - expected_increase) < 0.01:
                self.log_test(payment_test['test_name'], True, f"رصيد {expected_account}: {initial_balance} → {updated_balance} (+{actual_increase})")
            else:
                self.log_test(payment_test['test_name'], False, f"رصيد {expected_account}: {initial_balance} → {updated_balance} (+{actual_increase}), متوقع: +{expected_increase}")
            
            # Update initial balances for next test
            initial_balances = updated_balances

    def test_2_inventory_transactions_api(self):
        """
        اختبار 2: API معاملات الجرد
        Test inventory transactions API compatibility
        """
        print("\n" + "="*80)
        print("اختبار 2: API معاملات الجرد (التوافق مع البيانات القديمة)")
        print("Test 2: Inventory Transactions API (Old Data Compatibility)")
        print("="*80)
        
        # Test GET /api/inventory-transactions - should work without HTTP 500
        transactions_response = self.make_request('GET', '/inventory-transactions')
        if transactions_response and transactions_response.status_code == 200:
            transactions = transactions_response.json()
            self.log_test("GET /api/inventory-transactions", True, f"استرجع {len(transactions)} معاملة بنجاح")
        else:
            status_code = transactions_response.status_code if transactions_response else "No response"
            self.log_test("GET /api/inventory-transactions", False, f"HTTP {status_code} - مشكلة في التوافق مع البيانات القديمة")
        
        # Test creating new inventory item first
        inventory_item_data = {
            "material_type": "NBR",
            "inner_diameter": 30.0,
            "outer_diameter": 40.0,
            "available_pieces": 20,
            "min_stock_level": 5,
            "notes": "عنصر اختبار معاملات الجرد"
        }
        
        inventory_response = self.make_request('POST', '/inventory', inventory_item_data)
        if not inventory_response or inventory_response.status_code != 200:
            self.log_test("إنشاء عنصر جرد للاختبار", False, f"فشل في إنشاء عنصر الجرد: {inventory_response.status_code if inventory_response else 'No response'}")
            return
            
        inventory_item = inventory_response.json()
        
        # Test POST /api/inventory-transactions - create new transactions
        transaction_data = {
            "inventory_item_id": inventory_item["id"],
            "material_type": "NBR",
            "inner_diameter": 30.0,
            "outer_diameter": 40.0,
            "transaction_type": "in",
            "pieces_change": 10,
            "reason": "إضافة مخزون جديد - اختبار",
            "notes": "اختبار إنشاء معاملة جرد جديدة"
        }
        
        create_transaction_response = self.make_request('POST', '/inventory-transactions', transaction_data)
        if create_transaction_response and create_transaction_response.status_code == 200:
            transaction = create_transaction_response.json()
            self.log_test("POST /api/inventory-transactions", True, f"تم إنشاء معاملة جرد: {transaction.get('reason', 'N/A')}")
        else:
            status_code = create_transaction_response.status_code if create_transaction_response else "No response"
            self.log_test("POST /api/inventory-transactions", False, f"HTTP {status_code} - فشل في إنشاء معاملة جديدة")
        
        # Test GET /api/inventory-transactions/{item_id} - get transactions for specific item
        item_transactions_response = self.make_request('GET', f'/inventory-transactions/{inventory_item["id"]}')
        if item_transactions_response and item_transactions_response.status_code == 200:
            item_transactions = item_transactions_response.json()
            self.log_test(f"GET /api/inventory-transactions/{inventory_item['id']}", True, f"استرجع {len(item_transactions)} معاملة للعنصر")
        else:
            status_code = item_transactions_response.status_code if item_transactions_response else "No response"
            self.log_test(f"GET /api/inventory-transactions/{{item_id}}", False, f"HTTP {status_code} - فشل في استرجاع معاملات العنصر")

    def test_3_inventory_raw_materials_integration(self):
        """
        اختبار 3: تكامل الجرد مع المواد الخام
        Test inventory integration with raw materials
        """
        print("\n" + "="*80)
        print("اختبار 3: تكامل الجرد مع المواد الخام")
        print("Test 3: Inventory Integration with Raw Materials")
        print("="*80)
        
        # Create inventory item with sufficient stock
        inventory_item_data = {
            "material_type": "BUR",
            "inner_diameter": 20.0,
            "outer_diameter": 30.0,
            "available_pieces": 15,
            "min_stock_level": 3,
            "notes": "عنصر اختبار تكامل المواد الخام"
        }
        
        inventory_response = self.make_request('POST', '/inventory', inventory_item_data)
        if not inventory_response or inventory_response.status_code != 200:
            self.log_test("إنشاء عنصر جرد", False, f"فشل في إنشاء عنصر الجرد: {inventory_response.status_code if inventory_response else 'No response'}")
            return
            
        inventory_item = inventory_response.json()
        initial_pieces = inventory_item["available_pieces"]
        self.log_test("إنشاء عنصر جرد", True, f"تم إنشاء عنصر بـ {initial_pieces} قطعة")
        
        # Create raw material that should deduct from inventory
        raw_material_data = {
            "material_type": "BUR",
            "inner_diameter": 20.0,
            "outer_diameter": 30.0,
            "height": 8.0,
            "pieces_count": 3,
            "unit_code": "BUR-20x30-TEST",
            "cost_per_mm": 0.5
        }
        
        raw_material_response = self.make_request('POST', '/raw-materials', raw_material_data)
        if raw_material_response and raw_material_response.status_code == 200:
            raw_material = raw_material_response.json()
            self.log_test("إنشاء مادة خام", True, f"تم إنشاء مادة خام: {raw_material.get('unit_code', 'N/A')}")
            
            # Check if inventory was deducted correctly
            time.sleep(1)
            updated_inventory_response = self.make_request('GET', f'/inventory/{inventory_item["id"]}')
            if updated_inventory_response and updated_inventory_response.status_code == 200:
                updated_inventory = updated_inventory_response.json()
                final_pieces = updated_inventory["available_pieces"]
                expected_pieces = initial_pieces - raw_material_data["pieces_count"]
                
                if final_pieces == expected_pieces:
                    self.log_test("خصم الجرد التلقائي", True, f"الجرد: {initial_pieces} → {final_pieces} قطعة (خصم {raw_material_data['pieces_count']} قطعة)")
                else:
                    self.log_test("خصم الجرد التلقائي", False, f"الجرد: {initial_pieces} → {final_pieces} قطعة، متوقع: {expected_pieces}")
            else:
                self.log_test("التحقق من خصم الجرد", False, "فشل في جلب بيانات الجرد المحدثة")
        else:
            status_code = raw_material_response.status_code if raw_material_response else "No response"
            self.log_test("إنشاء مادة خام", False, f"HTTP {status_code} - فشل في إنشاء المادة الخام")

    def test_4_deferred_invoices(self):
        """
        اختبار 4: الفواتير الآجلة
        Test deferred invoices (should not create treasury transactions)
        """
        print("\n" + "="*80)
        print("اختبار 4: الفواتير الآجلة")
        print("Test 4: Deferred Invoices")
        print("="*80)
        
        # Create test customer
        customer_data = {
            "name": "عميل آجل للاختبار",
            "phone": "01111111111",
            "address": "الجيزة، مصر"
        }
        customer_response = self.make_request('POST', '/customers', customer_data)
        if not customer_response or customer_response.status_code != 200:
            self.log_test("إنشاء عميل للفواتير الآجلة", False, "فشل في إنشاء العميل")
            return
        
        customer = customer_response.json()
        
        # Get initial treasury balances
        initial_balances_response = self.make_request('GET', '/treasury/balances')
        if not initial_balances_response or initial_balances_response.status_code != 200:
            self.log_test("جلب أرصدة الخزينة الأولية", False, "فشل في جلب الأرصدة")
            return
        
        initial_balances = initial_balances_response.json()
        
        # Create deferred invoice
        deferred_invoice_data = {
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "invoice_title": "فاتورة آجلة للاختبار",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RS",
                    "material_type": "VT",
                    "inner_diameter": 15.0,
                    "outer_diameter": 25.0,
                    "height": 8.0,
                    "quantity": 5,
                    "unit_price": 12.0,
                    "total_price": 60.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "آجل",
            "discount_type": "amount",
            "discount_value": 0.0
        }
        
        # Create deferred invoice
        invoice_response = self.make_request('POST', '/invoices', deferred_invoice_data)
        if not invoice_response or invoice_response.status_code != 200:
            self.log_test("إنشاء فاتورة آجلة", False, f"فشل في إنشاء الفاتورة: {invoice_response.status_code if invoice_response else 'No response'}")
            return
            
        invoice = invoice_response.json()
        
        # Check that remaining_amount equals total_amount for deferred invoices
        if invoice.get("remaining_amount") == invoice.get("total_amount"):
            self.log_test("حساب المبلغ المستحق للفاتورة الآجلة", True, f"المبلغ المستحق: {invoice.get('remaining_amount')} ج.م")
        else:
            self.log_test("حساب المبلغ المستحق للفاتورة الآجلة", False, f"المبلغ المستحق: {invoice.get('remaining_amount')}، الإجمالي: {invoice.get('total_amount')}")
        
        # Wait and check that no treasury transaction was created
        time.sleep(1)
        updated_balances_response = self.make_request('GET', '/treasury/balances')
        if updated_balances_response and updated_balances_response.status_code == 200:
            updated_balances = updated_balances_response.json()
            
            # Check that all account balances remained the same (no treasury transaction created)
            balances_unchanged = True
            for account, initial_balance in initial_balances.items():
                updated_balance = updated_balances.get(account, 0)
                if abs(updated_balance - initial_balance) > 0.01:
                    balances_unchanged = False
                    break
            
            if balances_unchanged:
                self.log_test("عدم إنشاء معاملة خزينة للفاتورة الآجلة", True, "لم يتم تحديث أي حساب خزينة")
            else:
                self.log_test("عدم إنشاء معاملة خزينة للفاتورة الآجلة", False, "تم تحديث حسابات الخزينة خطأً")
        else:
            self.log_test("التحقق من عدم تحديث الخزينة", False, "فشل في جلب أرصدة الخزينة المحدثة")

    def test_5_invoice_discount_calculation(self):
        """
        اختبار 5: حساب الخصم في الفواتير
        Test discount calculation in invoices
        """
        print("\n" + "="*80)
        print("اختبار 5: حساب الخصم في الفواتير")
        print("Test 5: Invoice Discount Calculation")
        print("="*80)
        
        # Create test customer
        customer_data = {
            "name": "عميل اختبار الخصم",
            "phone": "01222222222",
            "address": "الإسكندرية، مصر"
        }
        customer_response = self.make_request('POST', '/customers', customer_data)
        if not customer_response or customer_response.status_code != 200:
            self.log_test("إنشاء عميل لاختبار الخصم", False, "فشل في إنشاء العميل")
            return
        
        customer = customer_response.json()
        
        # Test 1: Fixed amount discount
        fixed_discount_invoice = {
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "invoice_title": "فاتورة خصم ثابت",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "B17",
                    "material_type": "NBR",
                    "inner_diameter": 20.0,
                    "outer_diameter": 30.0,
                    "height": 12.0,
                    "quantity": 4,
                    "unit_price": 25.0,
                    "total_price": 100.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "نقدي",
            "discount_type": "amount",
            "discount_value": 15.0
        }
        
        # Create invoice with fixed discount
        invoice_response = self.make_request('POST', '/invoices', fixed_discount_invoice)
        if invoice_response and invoice_response.status_code == 200:
            invoice = invoice_response.json()
            
            expected_subtotal = 100.0
            expected_discount = 15.0
            expected_total_after_discount = 85.0
            
            subtotal_correct = abs(invoice.get("subtotal", 0) - expected_subtotal) < 0.01
            discount_correct = abs(invoice.get("discount", 0) - expected_discount) < 0.01
            total_correct = abs(invoice.get("total_after_discount", 0) - expected_total_after_discount) < 0.01
            
            if subtotal_correct and discount_correct and total_correct:
                self.log_test("حساب الخصم الثابت", True, f"المجموع الفرعي: {invoice.get('subtotal')}، الخصم: {invoice.get('discount')}، الإجمالي بعد الخصم: {invoice.get('total_after_discount')}")
            else:
                self.log_test("حساب الخصم الثابت", False, f"المجموع الفرعي: {invoice.get('subtotal')} (متوقع: {expected_subtotal})، الخصم: {invoice.get('discount')} (متوقع: {expected_discount})، الإجمالي: {invoice.get('total_after_discount')} (متوقع: {expected_total_after_discount})")
        else:
            status_code = invoice_response.status_code if invoice_response else "No response"
            self.log_test("إنشاء فاتورة خصم ثابت", False, f"HTTP {status_code}")
        
        # Test 2: Percentage discount
        percentage_discount_invoice = {
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "invoice_title": "فاتورة خصم نسبة مئوية",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RSE",
                    "material_type": "BT",
                    "inner_diameter": 35.0,
                    "outer_diameter": 45.0,
                    "height": 15.0,
                    "quantity": 2,
                    "unit_price": 50.0,
                    "total_price": 100.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "نقدي",
            "discount_type": "percentage",
            "discount_value": 20.0
        }
        
        # Create invoice with percentage discount
        invoice_response = self.make_request('POST', '/invoices', percentage_discount_invoice)
        if invoice_response and invoice_response.status_code == 200:
            invoice = invoice_response.json()
            
            expected_subtotal = 100.0
            expected_discount = 20.0  # 20% of 100
            expected_total_after_discount = 80.0
            
            subtotal_correct = abs(invoice.get("subtotal", 0) - expected_subtotal) < 0.01
            discount_correct = abs(invoice.get("discount", 0) - expected_discount) < 0.01
            total_correct = abs(invoice.get("total_after_discount", 0) - expected_total_after_discount) < 0.01
            
            if subtotal_correct and discount_correct and total_correct:
                self.log_test("حساب الخصم النسبي", True, f"المجموع الفرعي: {invoice.get('subtotal')}، الخصم: {invoice.get('discount')}، الإجمالي بعد الخصم: {invoice.get('total_after_discount')}")
            else:
                self.log_test("حساب الخصم النسبي", False, f"المجموع الفرعي: {invoice.get('subtotal')} (متوقع: {expected_subtotal})، الخصم: {invoice.get('discount')} (متوقع: {expected_discount})، الإجمالي: {invoice.get('total_after_discount')} (متوقع: {expected_total_after_discount})")
        else:
            status_code = invoice_response.status_code if invoice_response else "No response"
            self.log_test("إنشاء فاتورة خصم نسبي", False, f"HTTP {status_code}")
        
        # Test 3: Edit invoice and change discount
        if invoice_response and invoice_response.status_code == 200:
            invoice_id = invoice_response.json()["id"]
            
            # Update invoice with different discount
            update_data = {
                "invoice_title": "فاتورة خصم محدثة",
                "discount_type": "amount",
                "discount_value": 25.0,
                "items": [
                    {
                        "seal_type": "RSE",
                        "material_type": "BT",
                        "inner_diameter": 35.0,
                        "outer_diameter": 45.0,
                        "height": 15.0,
                        "quantity": 2,
                        "unit_price": 50.0,
                        "total_price": 100.0,
                        "product_type": "manufactured"
                    }
                ]
            }
            
            update_response = self.make_request('PUT', f'/invoices/{invoice_id}', update_data)
            if update_response and update_response.status_code == 200:
                # Get updated invoice
                updated_invoice_response = self.make_request('GET', f'/invoices/{invoice_id}')
                if updated_invoice_response and updated_invoice_response.status_code == 200:
                    updated_invoice = updated_invoice_response.json()
                    
                    expected_discount_after_update = 25.0
                    expected_total_after_update = 75.0
                    
                    discount_updated = abs(updated_invoice.get("discount", 0) - expected_discount_after_update) < 0.01
                    total_updated = abs(updated_invoice.get("total_after_discount", 0) - expected_total_after_update) < 0.01
                    
                    if discount_updated and total_updated:
                        self.log_test("تحرير الفاتورة وإعادة حساب الخصم", True, f"الخصم المحدث: {updated_invoice.get('discount')}، الإجمالي المحدث: {updated_invoice.get('total_after_discount')}")
                    else:
                        self.log_test("تحرير الفاتورة وإعادة حساب الخصم", False, f"الخصم: {updated_invoice.get('discount')} (متوقع: {expected_discount_after_update})، الإجمالي: {updated_invoice.get('total_after_discount')} (متوقع: {expected_total_after_update})")
                else:
                    self.log_test("جلب الفاتورة المحدثة", False, "فشل في جلب الفاتورة بعد التحديث")
            else:
                status_code = update_response.status_code if update_response else "No response"
                self.log_test("تحرير الفاتورة", False, f"HTTP {status_code}")

    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 بدء الاختبار النهائي الشامل للمشاكل الحرجة")
        print("🚀 Starting Comprehensive Final Test for Critical Issues")
        print("="*80)
        
        try:
            # Run all test suites
            self.test_1_payment_method_treasury_matching()
            self.test_2_inventory_transactions_api()
            self.test_3_inventory_raw_materials_integration()
            self.test_4_deferred_invoices()
            self.test_5_invoice_discount_calculation()
            
        except Exception as e:
            print(f"❌ خطأ في تشغيل الاختبارات: {str(e)}")
            
        # Print final summary
        self.print_final_summary()
    
    def print_final_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("📊 ملخص الاختبار النهائي الشامل")
        print("📊 COMPREHENSIVE FINAL TEST SUMMARY")
        print("="*80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"إجمالي الاختبارات: {self.total_tests}")
        print(f"الاختبارات الناجحة: {self.passed_tests}")
        print(f"الاختبارات الفاشلة: {self.total_tests - self.passed_tests}")
        print(f"نسبة النجاح: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 ممتاز! جميع المشاكل الحرجة تم حلها بنجاح")
        elif success_rate >= 75:
            print("✅ جيد! معظم المشاكل تم حلها مع بعض المشاكل الطفيفة")
        elif success_rate >= 50:
            print("⚠️ متوسط! بعض المشاكل الحرجة لا تزال موجودة")
        else:
            print("❌ ضعيف! مشاكل حرجة متعددة تحتاج إصلاح فوري")
        
        # Group results by test category
        failed_tests = [test for test in self.test_results if not test['passed']]
        if failed_tests:
            print("\n❌ الاختبارات الفاشلة:")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['details']}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    tester = ComprehensiveFinalTest()
    tester.run_all_tests()