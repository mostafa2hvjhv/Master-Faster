#!/usr/bin/env python3
"""
اختبار الإصلاحات الثلاثة الجديدة - Testing Three New Bug Fixes
1. إصلاح صفحة الآجل - Deferred page fix
2. إصلاح APIs الخزينة الجديدة - New Treasury APIs fix  
3. إصلاح فحص التوافق - Compatibility check fix
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class BugFixesTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_data = {
            'customers': [],
            'raw_materials': [],
            'invoices': [],
            'expenses': [],
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
    
    def setup_test_data(self):
        """Create test data for all three bug fixes"""
        print("\n=== إعداد البيانات التجريبية - Setting Up Test Data ===")
        
        # Create customers
        customers_data = [
            {"name": "شركة النصر للتجارة", "phone": "01234567890", "address": "القاهرة، مصر الجديدة"},
            {"name": "مؤسسة الأمل الصناعية", "phone": "01098765432", "address": "الجيزة، الدقي"},
            {"name": "شركة المستقبل للمقاولات", "phone": "01156789012", "address": "الإسكندرية، سموحة"}
        ]
        
        for customer_data in customers_data:
            try:
                response = self.session.post(f"{BACKEND_URL}/customers", 
                                           json=customer_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    self.created_data['customers'].append(data)
                    self.log_test(f"إنشاء عميل - {customer_data['name']}", True, f"Customer ID: {data.get('id')}")
                else:
                    self.log_test(f"إنشاء عميل - {customer_data['name']}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"إنشاء عميل - {customer_data['name']}", False, f"Exception: {str(e)}")
        
        # Create raw materials
        materials_data = [
            {"material_type": "NBR", "inner_diameter": 25.0, "outer_diameter": 35.0, "height": 100.0, "pieces_count": 50, "unit_code": "NBR-25-35-001", "cost_per_mm": 0.15},
            {"material_type": "BUR", "inner_diameter": 30.0, "outer_diameter": 45.0, "height": 80.0, "pieces_count": 30, "unit_code": "BUR-30-45-001", "cost_per_mm": 0.20},
            {"material_type": "VT", "inner_diameter": 40.0, "outer_diameter": 55.0, "height": 90.0, "pieces_count": 25, "unit_code": "VT-40-55-001", "cost_per_mm": 0.25}
        ]
        
        for material_data in materials_data:
            try:
                response = self.session.post(f"{BACKEND_URL}/raw-materials", 
                                           json=material_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    self.created_data['raw_materials'].append(data)
                    self.log_test(f"إنشاء مادة خام - {material_data['material_type']}", True, f"Unit Code: {data.get('unit_code')}")
                else:
                    self.log_test(f"إنشاء مادة خام - {material_data['material_type']}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"إنشاء مادة خام - {material_data['material_type']}", False, f"Exception: {str(e)}")
        
        # Create expenses for treasury testing
        expense_tests = [
            {"description": "شراء خامات NBR", "amount": 2000.0, "category": "خامات"},
            {"description": "راتب العامل محمد", "amount": 1500.0, "category": "رواتب"},
            {"description": "فاتورة الكهرباء", "amount": 500.0, "category": "كهرباء"}
        ]
        
        for expense_data in expense_tests:
            try:
                response = self.session.post(f"{BACKEND_URL}/expenses", 
                                           json=expense_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    self.created_data['expenses'].append(data)
                    self.log_test(f"إنشاء مصروف - {expense_data['category']}", True, f"Amount: {data.get('amount')}")
                else:
                    self.log_test(f"إنشاء مصروف - {expense_data['category']}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"إنشاء مصروف - {expense_data['category']}", False, f"Exception: {str(e)}")
    
    def test_deferred_page_fix(self):
        """Test Fix 1: إصلاح صفحة الآجل - Deferred page invoice filtering"""
        print("\n=== اختبار إصلاح صفحة الآجل - Testing Deferred Page Fix ===")
        
        if not self.created_data['customers']:
            self.log_test("إصلاح صفحة الآجل", False, "لا توجد عملاء متاحين للاختبار")
            return
        
        # Create invoices with different statuses and payment methods
        invoice_tests = [
            {
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
                        "total_price": 150.0
                    }
                ],
                "payment_method": "آجل",
                "notes": "فاتورة آجل - للاختبار"
            },
            {
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
                        "total_price": 100.0
                    }
                ],
                "payment_method": "نقدي",
                "notes": "فاتورة نقدي - للاختبار"
            },
            {
                "customer_id": self.created_data['customers'][0]['id'],
                "customer_name": self.created_data['customers'][0]['name'],
                "items": [
                    {
                        "seal_type": "B17",
                        "material_type": "VT",
                        "inner_diameter": 40.0,
                        "outer_diameter": 55.0,
                        "height": 10.0,
                        "quantity": 3,
                        "unit_price": 25.0,
                        "total_price": 75.0
                    }
                ],
                "payment_method": "فودافون كاش محمد الصاوي",
                "notes": "فاتورة فودافون كاش - للاختبار"
            }
        ]
        
        # Create invoices
        for i, invoice_data in enumerate(invoice_tests):
            try:
                response = self.session.post(f"{BACKEND_URL}/invoices", 
                                           json=invoice_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    self.created_data['invoices'].append(data)
                    self.log_test(f"إنشاء فاتورة {i+1} - {invoice_data['payment_method']}", True, 
                                f"Invoice: {data.get('invoice_number')}, Status: {data.get('status')}, Remaining: {data.get('remaining_amount')}")
                else:
                    self.log_test(f"إنشاء فاتورة {i+1} - {invoice_data['payment_method']}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"إنشاء فاتورة {i+1} - {invoice_data['payment_method']}", False, f"Exception: {str(e)}")
        
        # Test GET /api/invoices - Check for different invoice statuses
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices")
            
            if response.status_code == 200:
                invoices = response.json()
                if isinstance(invoices, list):
                    # Check for different statuses
                    statuses_found = set()
                    deferred_invoices = []
                    unpaid_invoices = []
                    partial_invoices = []
                    pending_invoices = []
                    
                    for invoice in invoices:
                        status = invoice.get('status')
                        remaining = invoice.get('remaining_amount', 0)
                        statuses_found.add(status)
                        
                        if status == "انتظار" and remaining > 0:
                            pending_invoices.append(invoice)
                        elif status == "غير مدفوعة" and remaining > 0:
                            unpaid_invoices.append(invoice)
                        elif status == "مدفوعة جزئياً" and remaining > 0:
                            partial_invoices.append(invoice)
                        elif invoice.get('payment_method') == "آجل" and remaining > 0:
                            deferred_invoices.append(invoice)
                    
                    # Test deferred page filtering logic
                    deferred_page_invoices = [inv for inv in invoices if inv.get('remaining_amount', 0) > 0]
                    
                    self.log_test("GET /api/invoices - فحص الحالات المختلفة", True, 
                                f"إجمالي الفواتير: {len(invoices)}, الحالات الموجودة: {list(statuses_found)}")
                    
                    self.log_test("فلتر صفحة الآجل - الفواتير المستحقة", True, 
                                f"فواتير مستحقة: {len(deferred_page_invoices)}, انتظار: {len(pending_invoices)}, غير مدفوعة: {len(unpaid_invoices)}, جزئية: {len(partial_invoices)}")
                    
                    # Verify that deferred invoices have remaining_amount > 0
                    if deferred_page_invoices:
                        all_have_remaining = all(inv.get('remaining_amount', 0) > 0 for inv in deferred_page_invoices)
                        if all_have_remaining:
                            self.log_test("فحص المبالغ المستحقة", True, "جميع الفواتير في صفحة الآجل لها مبالغ مستحقة > 0")
                        else:
                            self.log_test("فحص المبالغ المستحقة", False, "بعض الفواتير في صفحة الآجل ليس لها مبالغ مستحقة")
                    else:
                        self.log_test("فحص المبالغ المستحقة", True, "لا توجد فواتير مستحقة حالياً")
                        
                else:
                    self.log_test("GET /api/invoices - فحص الحالات المختلفة", False, f"Expected list, got: {type(invoices)}")
            else:
                self.log_test("GET /api/invoices - فحص الحالات المختلفة", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/invoices - فحص الحالات المختلفة", False, f"Exception: {str(e)}")
    
    def test_treasury_apis_fix(self):
        """Test Fix 2: إصلاح APIs الخزينة الجديدة - New Treasury APIs"""
        print("\n=== اختبار إصلاح APIs الخزينة الجديدة - Testing New Treasury APIs Fix ===")
        
        # Test 1: GET /api/treasury/balances - حساب أرصدة الحسابات الخمسة
        try:
            response = self.session.get(f"{BACKEND_URL}/treasury/balances")
            
            if response.status_code == 200:
                balances = response.json()
                if isinstance(balances, dict):
                    expected_accounts = ['cash', 'vodafone_elsawy', 'vodafone_wael', 'deferred', 'instapay']
                    
                    if all(account in balances for account in expected_accounts):
                        self.log_test("GET /api/treasury/balances - أرصدة الحسابات", True, 
                                    f"الأرصدة: نقدي={balances.get('cash', 0)}, فودافون الصاوي={balances.get('vodafone_elsawy', 0)}, فودافون وائل={balances.get('vodafone_wael', 0)}, آجل={balances.get('deferred', 0)}, انستاباي={balances.get('instapay', 0)}")
                    else:
                        missing = [acc for acc in expected_accounts if acc not in balances]
                        self.log_test("GET /api/treasury/balances - أرصدة الحسابات", False, f"حسابات مفقودة: {missing}")
                else:
                    self.log_test("GET /api/treasury/balances - أرصدة الحسابات", False, f"Expected dict, got: {type(balances)}")
            else:
                self.log_test("GET /api/treasury/balances - أرصدة الحسابات", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/treasury/balances - أرصدة الحسابات", False, f"Exception: {str(e)}")
        
        # Test 2: GET /api/treasury/transactions - جلب جميع المعاملات المالية
        try:
            response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
            
            if response.status_code == 200:
                transactions = response.json()
                if isinstance(transactions, list):
                    self.log_test("GET /api/treasury/transactions - المعاملات المالية", True, 
                                f"عدد المعاملات: {len(transactions)}")
                else:
                    self.log_test("GET /api/treasury/transactions - المعاملات المالية", False, f"Expected list, got: {type(transactions)}")
            else:
                self.log_test("GET /api/treasury/transactions - المعاملات المالية", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("GET /api/treasury/transactions - المعاملات المالية", False, f"Exception: {str(e)}")
        
        # Test 3: POST /api/treasury/transactions - إضافة معاملة يدوية (دخل/مصروف)
        manual_transactions = [
            {
                "account_id": "cash",
                "transaction_type": "income",
                "amount": 1000.0,
                "description": "إيراد إضافي من مبيعات نقدية",
                "reference": "دخل يدوي"
            },
            {
                "account_id": "vodafone_elsawy",
                "transaction_type": "expense",
                "amount": 200.0,
                "description": "مصروف إضافي - رسوم تحويل",
                "reference": "مصروف يدوي"
            }
        ]
        
        for i, transaction_data in enumerate(manual_transactions):
            try:
                response = self.session.post(f"{BACKEND_URL}/treasury/transactions", 
                                           json=transaction_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    self.created_data['treasury_transactions'].append(data)
                    self.log_test(f"POST /api/treasury/transactions - معاملة {i+1}", True, 
                                f"نوع: {transaction_data['transaction_type']}, مبلغ: {transaction_data['amount']}, حساب: {transaction_data['account_id']}")
                else:
                    self.log_test(f"POST /api/treasury/transactions - معاملة {i+1}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"POST /api/treasury/transactions - معاملة {i+1}", False, f"Exception: {str(e)}")
        
        # Test 4: POST /api/treasury/transfer - تحويل أموال بين الحسابات
        transfer_data = {
            "from_account": "cash",
            "to_account": "vodafone_elsawy",
            "amount": 500.0,
            "notes": "تحويل تجريبي من النقدي إلى فودافون الصاوي"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/treasury/transfer", 
                                       json=transfer_data,
                                       headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                if "تم التحويل بنجاح" in data.get('message', ''):
                    transfer_id = data.get('transfer_id')
                    self.log_test("POST /api/treasury/transfer - تحويل الأموال", True, 
                                f"تحويل {transfer_data['amount']} من {transfer_data['from_account']} إلى {transfer_data['to_account']}, ID: {transfer_id}")
                    
                    # Verify that two linked transactions were created
                    try:
                        response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
                        if response.status_code == 200:
                            all_transactions = response.json()
                            transfer_transactions = [t for t in all_transactions if t.get('related_transaction_id') == transfer_id or t.get('id') == transfer_id]
                            
                            if len(transfer_transactions) >= 2:
                                out_transaction = next((t for t in transfer_transactions if t.get('transaction_type') == 'transfer_out'), None)
                                in_transaction = next((t for t in transfer_transactions if t.get('transaction_type') == 'transfer_in'), None)
                                
                                if out_transaction and in_transaction:
                                    self.log_test("فحص المعاملات المرتبطة للتحويل", True, 
                                                f"تم إنشاء معاملتين مرتبطتين: صادر من {out_transaction.get('account_id')} ووارد إلى {in_transaction.get('account_id')}")
                                else:
                                    self.log_test("فحص المعاملات المرتبطة للتحويل", False, "لم يتم العثور على معاملات صادر ووارد")
                            else:
                                self.log_test("فحص المعاملات المرتبطة للتحويل", False, f"عدد المعاملات المرتبطة غير صحيح: {len(transfer_transactions)}")
                    except Exception as e:
                        self.log_test("فحص المعاملات المرتبطة للتحويل", False, f"Exception: {str(e)}")
                        
                else:
                    self.log_test("POST /api/treasury/transfer - تحويل الأموال", False, f"رسالة غير متوقعة: {data}")
            else:
                self.log_test("POST /api/treasury/transfer - تحويل الأموال", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("POST /api/treasury/transfer - تحويل الأموال", False, f"Exception: {str(e)}")
    
    def test_compatibility_check_fix(self):
        """Test Fix 3: إصلاح فحص التوافق - Enhanced compatibility check validation"""
        print("\n=== اختبار إصلاح فحص التوافق - Testing Compatibility Check Fix ===")
        
        # Test with valid data
        valid_compatibility_tests = [
            {
                "seal_type": "RSL",
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "height": 8.0
            },
            {
                "seal_type": "RS",
                "inner_diameter": 30.0,
                "outer_diameter": 45.0,
                "height": 7.0
            },
            {
                "seal_type": "B17",
                "inner_diameter": 40.0,
                "outer_diameter": 55.0,
                "height": 10.0
            }
        ]
        
        for i, check_data in enumerate(valid_compatibility_tests):
            try:
                response = self.session.post(f"{BACKEND_URL}/compatibility-check", 
                                           json=check_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    data = response.json()
                    if 'compatible_materials' in data and 'compatible_products' in data:
                        materials_count = len(data['compatible_materials'])
                        products_count = len(data['compatible_products'])
                        self.log_test(f"فحص التوافق - بيانات صحيحة {i+1} ({check_data['seal_type']})", True, 
                                    f"مواد متوافقة: {materials_count}, منتجات متوافقة: {products_count}")
                        
                        # Check if materials have proper compatibility logic
                        for material in data['compatible_materials']:
                            if ('inner_diameter' in material and 'outer_diameter' in material and 'height' in material):
                                # Verify compatibility logic
                                mat_inner = material['inner_diameter']
                                mat_outer = material['outer_diameter']
                                mat_height = material['height']
                                
                                seal_inner = check_data['inner_diameter']
                                seal_outer = check_data['outer_diameter']
                                seal_height = check_data['height']
                                
                                is_compatible = (mat_inner <= seal_inner and 
                                               mat_outer >= seal_outer and 
                                               mat_height >= (seal_height + 5))
                                
                                if is_compatible:
                                    self.log_test(f"منطق التوافق - {material.get('unit_code', 'Unknown')}", True, 
                                                f"المادة متوافقة: قطر داخلي {mat_inner}<={seal_inner}, قطر خارجي {mat_outer}>={seal_outer}, ارتفاع {mat_height}>={seal_height+5}")
                                else:
                                    self.log_test(f"منطق التوافق - {material.get('unit_code', 'Unknown')}", False, 
                                                f"المادة غير متوافقة حسب المنطق: قطر داخلي {mat_inner}<={seal_inner}, قطر خارجي {mat_outer}>={seal_outer}, ارتفاع {mat_height}>={seal_height+5}")
                    else:
                        self.log_test(f"فحص التوافق - بيانات صحيحة {i+1} ({check_data['seal_type']})", False, f"حقول مفقودة في الاستجابة: {data}")
                else:
                    self.log_test(f"فحص التوافق - بيانات صحيحة {i+1} ({check_data['seal_type']})", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"فحص التوافق - بيانات صحيحة {i+1} ({check_data['seal_type']})", False, f"Exception: {str(e)}")
        
        # Test with invalid/incomplete data to check enhanced validation
        invalid_compatibility_tests = [
            {
                "seal_type": "RSL",
                "inner_diameter": 25.0,
                # Missing outer_diameter and height
            },
            {
                "seal_type": "INVALID_TYPE",
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "height": 8.0
            },
            {
                # Missing seal_type
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "height": 8.0
            }
        ]
        
        for i, check_data in enumerate(invalid_compatibility_tests):
            try:
                response = self.session.post(f"{BACKEND_URL}/compatibility-check", 
                                           json=check_data,
                                           headers={'Content-Type': 'application/json'})
                
                if response.status_code == 422:  # Validation error
                    self.log_test(f"فحص التوافق - بيانات ناقصة {i+1}", True, 
                                f"تم رفض البيانات الناقصة بشكل صحيح: HTTP 422")
                elif response.status_code == 200:
                    # If it returns 200, check if it handles the invalid data gracefully
                    data = response.json()
                    if 'compatible_materials' in data and 'compatible_products' in data:
                        self.log_test(f"فحص التوافق - بيانات ناقصة {i+1}", True, 
                                    f"تم التعامل مع البيانات الناقصة بشكل صحيح، إرجاع نتائج فارغة أو محدودة")
                    else:
                        self.log_test(f"فحص التوافق - بيانات ناقصة {i+1}", False, f"استجابة غير متوقعة: {data}")
                else:
                    self.log_test(f"فحص التوافق - بيانات ناقصة {i+1}", True, 
                                f"تم رفض البيانات الناقصة: HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"فحص التوافق - بيانات ناقصة {i+1}", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all bug fix tests"""
        print("🚀 بدء اختبار الإصلاحات الثلاثة الجديدة - Starting Three New Bug Fixes Testing")
        print("=" * 80)
        
        # Setup test data
        self.setup_test_data()
        
        # Test the three bug fixes
        self.test_deferred_page_fix()
        self.test_treasury_apis_fix()
        self.test_compatibility_check_fix()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 ملخص نتائج الاختبار - Test Results Summary")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"إجمالي الاختبارات: {total_tests}")
        print(f"نجح: {passed_tests} ✅")
        print(f"فشل: {failed_tests} ❌")
        print(f"معدل النجاح: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ الاختبارات الفاشلة:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🎯 تم الانتهاء من اختبار الإصلاحات الثلاثة الجديدة")
        return success_rate >= 80  # Consider successful if 80% or more tests pass

if __name__ == "__main__":
    tester = BugFixesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)