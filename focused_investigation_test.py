#!/usr/bin/env python3
"""
اختبار مركز للمشاكل الحرجة المحددة
Focused test for the specific critical issues identified
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"

class FocusedCriticalIssuesTest:
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

    def investigate_treasury_double_amount_issue(self):
        """
        تحقيق في مشكلة مضاعفة المبالغ في الخزينة
        Investigate the treasury double amount issue
        """
        print("\n" + "="*80)
        print("🔍 تحقيق في مشكلة مضاعفة المبالغ في الخزينة")
        print("🔍 Investigating Treasury Double Amount Issue")
        print("="*80)
        
        # Clear existing data
        self.make_request('DELETE', '/invoices/clear-all')
        self.make_request('DELETE', '/customers/clear-all')
        time.sleep(1)
        
        # Create test customer
        customer_data = {
            "name": "عميل اختبار التحقيق",
            "phone": "01000000000",
            "address": "القاهرة، مصر"
        }
        customer_response = self.make_request('POST', '/customers', customer_data)
        if not customer_response or customer_response.status_code != 200:
            self.log_test("إنشاء عميل للتحقيق", False, "فشل في إنشاء العميل")
            return
        
        customer = customer_response.json()
        
        # Get initial treasury balances
        initial_balances_response = self.make_request('GET', '/treasury/balances')
        if not initial_balances_response or initial_balances_response.status_code != 200:
            self.log_test("جلب أرصدة الخزينة الأولية", False, "فشل في جلب الأرصدة")
            return
        
        initial_balances = initial_balances_response.json()
        print(f"الأرصدة الأولية: {initial_balances}")
        
        # Create a simple cash invoice with known amount
        invoice_data = {
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "invoice_title": "فاتورة اختبار التحقيق",
            "supervisor_name": "مشرف التحقيق",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 10.0,
                    "outer_diameter": 20.0,
                    "height": 5.0,
                    "quantity": 1,
                    "unit_price": 50.0,
                    "total_price": 50.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "نقدي",
            "discount_type": "amount",
            "discount_value": 0.0
        }
        
        # Create invoice
        invoice_response = self.make_request('POST', '/invoices', invoice_data)
        if not invoice_response or invoice_response.status_code != 200:
            self.log_test("إنشاء فاتورة التحقيق", False, f"فشل في إنشاء الفاتورة: {invoice_response.status_code if invoice_response else 'No response'}")
            return
            
        invoice = invoice_response.json()
        print(f"تفاصيل الفاتورة: المجموع الفرعي: {invoice.get('subtotal')}, الخصم: {invoice.get('discount')}, الإجمالي بعد الخصم: {invoice.get('total_after_discount')}, الإجمالي النهائي: {invoice.get('total_amount')}")
        
        # Wait for treasury transaction
        time.sleep(2)
        
        # Get updated treasury balances
        updated_balances_response = self.make_request('GET', '/treasury/balances')
        if not updated_balances_response or updated_balances_response.status_code != 200:
            self.log_test("جلب أرصدة الخزينة المحدثة", False, "فشل في جلب الأرصدة المحدثة")
            return
            
        updated_balances = updated_balances_response.json()
        print(f"الأرصدة المحدثة: {updated_balances}")
        
        # Check cash account change
        initial_cash = initial_balances.get('cash', 0)
        updated_cash = updated_balances.get('cash', 0)
        cash_change = updated_cash - initial_cash
        expected_change = 50.0  # Invoice total
        
        print(f"تغيير حساب النقدي: {initial_cash} → {updated_cash} (تغيير: {cash_change})")
        print(f"التغيير المتوقع: {expected_change}")
        
        if abs(cash_change - expected_change) < 0.01:
            self.log_test("تحديث حساب النقدي بالمبلغ الصحيح", True, f"تغيير: {cash_change} ج.م")
        else:
            self.log_test("تحديث حساب النقدي بالمبلغ الصحيح", False, f"تغيير: {cash_change} ج.م، متوقع: {expected_change} ج.م")
        
        # Get treasury transactions to see what was created
        transactions_response = self.make_request('GET', '/treasury/transactions')
        if transactions_response and transactions_response.status_code == 200:
            transactions = transactions_response.json()
            recent_transactions = [t for t in transactions if 'فاتورة اختبار التحقيق' in t.get('description', '')]
            
            print(f"المعاملات المرتبطة بالفاتورة: {len(recent_transactions)}")
            for transaction in recent_transactions:
                print(f"  - {transaction.get('account_id')}: {transaction.get('transaction_type')} بمبلغ {transaction.get('amount')} - {transaction.get('description')}")
            
            if len(recent_transactions) == 1:
                self.log_test("إنشاء معاملة خزينة واحدة فقط", True, f"معاملة واحدة بمبلغ {recent_transactions[0].get('amount')}")
            else:
                self.log_test("إنشاء معاملة خزينة واحدة فقط", False, f"تم إنشاء {len(recent_transactions)} معاملة")

    def investigate_deferred_invoice_treasury_issue(self):
        """
        تحقيق في مشكلة إنشاء معاملات خزينة للفواتير الآجلة
        Investigate deferred invoice treasury transaction issue
        """
        print("\n" + "="*80)
        print("🔍 تحقيق في مشكلة معاملات الخزينة للفواتير الآجلة")
        print("🔍 Investigating Deferred Invoice Treasury Issue")
        print("="*80)
        
        # Create test customer
        customer_data = {
            "name": "عميل آجل للتحقيق",
            "phone": "01111111111",
            "address": "الجيزة، مصر"
        }
        customer_response = self.make_request('POST', '/customers', customer_data)
        if not customer_response or customer_response.status_code != 200:
            self.log_test("إنشاء عميل آجل للتحقيق", False, "فشل في إنشاء العميل")
            return
        
        customer = customer_response.json()
        
        # Get initial treasury balances
        initial_balances_response = self.make_request('GET', '/treasury/balances')
        if not initial_balances_response or initial_balances_response.status_code != 200:
            self.log_test("جلب أرصدة الخزينة الأولية للآجل", False, "فشل في جلب الأرصدة")
            return
        
        initial_balances = initial_balances_response.json()
        print(f"الأرصدة الأولية قبل الفاتورة الآجلة: {initial_balances}")
        
        # Create deferred invoice
        deferred_invoice_data = {
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "invoice_title": "فاتورة آجلة للتحقيق",
            "supervisor_name": "مشرف التحقيق",
            "items": [
                {
                    "seal_type": "RS",
                    "material_type": "VT",
                    "inner_diameter": 15.0,
                    "outer_diameter": 25.0,
                    "height": 8.0,
                    "quantity": 2,
                    "unit_price": 30.0,
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
            self.log_test("إنشاء فاتورة آجلة للتحقيق", False, f"فشل في إنشاء الفاتورة: {invoice_response.status_code if invoice_response else 'No response'}")
            return
            
        invoice = invoice_response.json()
        print(f"تفاصيل الفاتورة الآجلة: طريقة الدفع: {invoice.get('payment_method')}, الإجمالي: {invoice.get('total_amount')}, المبلغ المستحق: {invoice.get('remaining_amount')}")
        
        # Wait for any potential treasury transaction
        time.sleep(2)
        
        # Get updated treasury balances
        updated_balances_response = self.make_request('GET', '/treasury/balances')
        if not updated_balances_response or updated_balances_response.status_code != 200:
            self.log_test("جلب أرصدة الخزينة المحدثة للآجل", False, "فشل في جلب الأرصدة المحدثة")
            return
            
        updated_balances = updated_balances_response.json()
        print(f"الأرصدة المحدثة بعد الفاتورة الآجلة: {updated_balances}")
        
        # Check if any account balance changed (should not change for deferred invoices)
        balances_changed = False
        for account, initial_balance in initial_balances.items():
            updated_balance = updated_balances.get(account, 0)
            if abs(updated_balance - initial_balance) > 0.01:
                balances_changed = True
                print(f"تغيير في حساب {account}: {initial_balance} → {updated_balance}")
        
        if not balances_changed:
            self.log_test("عدم تحديث أرصدة الخزينة للفاتورة الآجلة", True, "لم يتم تحديث أي حساب")
        else:
            self.log_test("عدم تحديث أرصدة الخزينة للفاتورة الآجلة", False, "تم تحديث حسابات الخزينة خطأً")
        
        # Check treasury transactions for this invoice
        transactions_response = self.make_request('GET', '/treasury/transactions')
        if transactions_response and transactions_response.status_code == 200:
            transactions = transactions_response.json()
            deferred_transactions = [t for t in transactions if 'فاتورة آجلة للتحقيق' in t.get('description', '')]
            
            print(f"المعاملات المرتبطة بالفاتورة الآجلة: {len(deferred_transactions)}")
            for transaction in deferred_transactions:
                print(f"  - {transaction.get('account_id')}: {transaction.get('transaction_type')} بمبلغ {transaction.get('amount')} - {transaction.get('description')}")
            
            if len(deferred_transactions) == 0:
                self.log_test("عدم إنشاء معاملات خزينة للفاتورة الآجلة", True, "لم يتم إنشاء أي معاملة خزينة")
            else:
                self.log_test("عدم إنشاء معاملات خزينة للفاتورة الآجلة", False, f"تم إنشاء {len(deferred_transactions)} معاملة خطأً")

    def investigate_inventory_creation_issue(self):
        """
        تحقيق في مشكلة إنشاء عناصر الجرد
        Investigate inventory item creation issue
        """
        print("\n" + "="*80)
        print("🔍 تحقيق في مشكلة إنشاء عناصر الجرد")
        print("🔍 Investigating Inventory Item Creation Issue")
        print("="*80)
        
        # Try to create a simple inventory item
        inventory_item_data = {
            "material_type": "NBR",
            "inner_diameter": 25.0,
            "outer_diameter": 35.0,
            "available_pieces": 10,
            "min_stock_level": 2,
            "notes": "عنصر اختبار التحقيق"
        }
        
        print(f"محاولة إنشاء عنصر جرد: {inventory_item_data}")
        
        inventory_response = self.make_request('POST', '/inventory', inventory_item_data)
        
        if inventory_response:
            print(f"رمز الاستجابة: {inventory_response.status_code}")
            try:
                response_data = inventory_response.json()
                print(f"بيانات الاستجابة: {response_data}")
                
                if inventory_response.status_code == 200:
                    self.log_test("إنشاء عنصر جرد", True, f"تم إنشاء العنصر بنجاح: {response_data.get('id', 'N/A')}")
                else:
                    self.log_test("إنشاء عنصر جرد", False, f"HTTP {inventory_response.status_code}: {response_data}")
            except:
                print(f"نص الاستجابة: {inventory_response.text}")
                self.log_test("إنشاء عنصر جرد", False, f"HTTP {inventory_response.status_code}: {inventory_response.text}")
        else:
            self.log_test("إنشاء عنصر جرد", False, "لا توجد استجابة من الخادم")
        
        # Try to get existing inventory items
        existing_inventory_response = self.make_request('GET', '/inventory')
        if existing_inventory_response and existing_inventory_response.status_code == 200:
            existing_items = existing_inventory_response.json()
            self.log_test("جلب عناصر الجرد الموجودة", True, f"تم جلب {len(existing_items)} عنصر")
            
            # Show some existing items
            if existing_items:
                print("عناصر الجرد الموجودة:")
                for i, item in enumerate(existing_items[:3]):  # Show first 3 items
                    print(f"  {i+1}. {item.get('material_type')} - {item.get('inner_diameter')}x{item.get('outer_diameter')} - {item.get('available_pieces')} قطعة")
        else:
            status_code = existing_inventory_response.status_code if existing_inventory_response else "No response"
            self.log_test("جلب عناصر الجرد الموجودة", False, f"HTTP {status_code}")

    def run_focused_investigation(self):
        """Run focused investigation on critical issues"""
        print("🔍 بدء التحقيق المركز في المشاكل الحرجة")
        print("🔍 Starting Focused Investigation of Critical Issues")
        print("="*80)
        
        try:
            # Run focused investigations
            self.investigate_treasury_double_amount_issue()
            self.investigate_deferred_invoice_treasury_issue()
            self.investigate_inventory_creation_issue()
            
        except Exception as e:
            print(f"❌ خطأ في التحقيق: {str(e)}")
            
        # Print summary
        self.print_investigation_summary()
    
    def print_investigation_summary(self):
        """Print investigation summary"""
        print("\n" + "="*80)
        print("📊 ملخص التحقيق المركز")
        print("📊 FOCUSED INVESTIGATION SUMMARY")
        print("="*80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"إجمالي الاختبارات: {self.total_tests}")
        print(f"الاختبارات الناجحة: {self.passed_tests}")
        print(f"الاختبارات الفاشلة: {self.total_tests - self.passed_tests}")
        print(f"نسبة النجاح: {success_rate:.1f}%")
        
        # Group results by test category
        failed_tests = [test for test in self.test_results if not test['passed']]
        if failed_tests:
            print("\n❌ المشاكل المحددة:")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['details']}")
        
        passed_tests = [test for test in self.test_results if test['passed']]
        if passed_tests:
            print("\n✅ الوظائف العاملة:")
            for test in passed_tests:
                print(f"  • {test['name']}: {test['details']}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    investigator = FocusedCriticalIssuesTest()
    investigator.run_focused_investigation()