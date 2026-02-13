#!/usr/bin/env python3
"""
Final Comprehensive Duplicate Transaction Test
الاختبار النهائي الشامل لمشكلة تضاعف معاملات الخزينة

This test provides a definitive answer about the duplicate transaction issue
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class FinalDuplicateTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, step: str, success: bool, details: str = ""):
        """Log test step results"""
        status = "✅" if success else "❌"
        print(f"{status} {step}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            'step': step,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_treasury_balance(self, account: str) -> float:
        """Get current treasury balance for specific account"""
        try:
            response = self.session.get(f"{BACKEND_URL}/treasury/balances")
            if response.status_code == 200:
                balances = response.json()
                return balances.get(account, 0)
            else:
                return 0
        except Exception as e:
            return 0
    
    def get_treasury_transactions(self) -> List[Dict]:
        """Get all treasury transactions"""
        try:
            response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception as e:
            return []
    
    def create_test_customer(self, name: str) -> str:
        """Create a test customer for the invoice"""
        customer_data = {
            "name": name,
            "phone": "01234567890",
            "address": "عنوان اختبار نهائي"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if response.status_code == 200:
                customer = response.json()
                return customer['id']
            else:
                return None
        except Exception as e:
            return None
    
    def create_cash_invoice(self, customer_id: str, customer_name: str, amount: float = 500.0) -> Dict:
        """Create a cash invoice"""
        invoice_data = {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "invoice_title": "فاتورة اختبار نهائي",
            "supervisor_name": "مشرف الاختبار النهائي",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 7.0,
                    "quantity": 1,
                    "unit_price": amount,
                    "total_price": amount,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "نقدي",
            "discount_type": "amount",
            "discount_value": 0.0,
            "notes": "فاتورة اختبار نهائي لفحص تضاعف معاملات الخزينة"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to create invoice: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating invoice: {str(e)}")
            return None
    
    def find_invoice_transactions(self, invoice_id: str) -> List[Dict]:
        """Find all treasury transactions related to a specific invoice"""
        all_transactions = self.get_treasury_transactions()
        invoice_transactions = []
        
        for transaction in all_transactions:
            reference = transaction.get('reference', '')
            if f"invoice_{invoice_id}" in reference:
                invoice_transactions.append(transaction)
        
        return invoice_transactions
    
    def run_final_test(self):
        """Run the final definitive test"""
        print("🔍 الاختبار النهائي لمشكلة تضاعف معاملات الخزينة")
        print("Final Definitive Test for Treasury Duplicate Transaction Issue")
        print("=" * 70)
        
        # Test scenario exactly as requested in the review
        print("\n📋 سيناريو الاختبار المطلوب:")
        print("1. فحص الرصيد النقدي الحالي")
        print("2. إنشاء فاتورة نقدية بقيمة 500 ج.م")
        print("3. فحص معاملات الخزينة فوراً بعد الإنشاء")
        print("4. فحص زيادة الرصيد النقدي")
        print("5. عرض جميع المعاملات المرتبطة بالفاتورة")
        
        # Step 1: Check initial cash balance
        print(f"\n💰 الخطوة 1: فحص الرصيد النقدي الحالي")
        initial_cash_balance = self.get_treasury_balance("cash")
        self.log_result("فحص الرصيد الأولي", True, f"الرصيد النقدي: {initial_cash_balance} ج.م")
        
        # Step 2: Create test customer
        print(f"\n👤 الخطوة 2: إنشاء عميل اختبار")
        customer_name = "عميل الاختبار النهائي"
        customer_id = self.create_test_customer(customer_name)
        if not customer_id:
            self.log_result("إنشاء العميل", False, "فشل في إنشاء العميل")
            return False
        self.log_result("إنشاء العميل", True, f"تم إنشاء العميل: {customer_name}")
        
        # Step 3: Create cash invoice for exactly 500 ج.م
        print(f"\n🧾 الخطوة 3: إنشاء فاتورة نقدية بقيمة 500 ج.م")
        invoice_amount = 500.0
        invoice = self.create_cash_invoice(customer_id, customer_name, invoice_amount)
        if not invoice:
            self.log_result("إنشاء الفاتورة", False, "فشل في إنشاء الفاتورة")
            return False
        
        invoice_id = invoice['id']
        invoice_number = invoice['invoice_number']
        self.log_result("إنشاء الفاتورة", True, f"تم إنشاء الفاتورة: {invoice_number}")
        
        # Step 4: Check cash balance immediately after creation
        print(f"\n💰 الخطوة 4: فحص الرصيد النقدي فوراً بعد إنشاء الفاتورة")
        final_cash_balance = self.get_treasury_balance("cash")
        balance_increase = final_cash_balance - initial_cash_balance
        
        self.log_result("فحص الرصيد النهائي", True, f"الرصيد النقدي: {final_cash_balance} ج.م")
        self.log_result("حساب الزيادة", True, f"الزيادة في الرصيد: {balance_increase} ج.م")
        
        # Step 5: Find all treasury transactions for this invoice
        print(f"\n🔍 الخطوة 5: البحث عن جميع معاملات الخزينة المرتبطة بالفاتورة")
        invoice_transactions = self.find_invoice_transactions(invoice_id)
        
        self.log_result("البحث عن المعاملات", True, 
                       f"تم العثور على {len(invoice_transactions)} معاملة")
        
        # Display detailed transaction information
        if invoice_transactions:
            print(f"\n📊 تفاصيل المعاملات المرتبطة بالفاتورة {invoice_number}:")
            for i, transaction in enumerate(invoice_transactions, 1):
                print(f"   المعاملة {i}:")
                print(f"     - ID: {transaction.get('id')}")
                print(f"     - الحساب: {transaction.get('account_id')}")
                print(f"     - النوع: {transaction.get('transaction_type')}")
                print(f"     - المبلغ: {transaction.get('amount')} ج.م")
                print(f"     - الوصف: {transaction.get('description')}")
                print(f"     - المرجع: {transaction.get('reference')}")
                print(f"     - التاريخ: {transaction.get('date')}")
        else:
            print(f"   لا توجد معاملات مرتبطة بالفاتورة!")
        
        # Step 6: Check for any deferred account transactions (should be none)
        print(f"\n🔍 الخطوة 6: فحص معاملات الحساب الآجل (يجب ألا توجد)")
        all_transactions = self.get_treasury_transactions()
        deferred_transactions = [t for t in all_transactions 
                               if t.get('account_id') == 'deferred' and f"invoice_{invoice_id}" in t.get('reference', '')]
        
        self.log_result("فحص المعاملات الآجلة", len(deferred_transactions) == 0,
                       f"معاملات آجلة غير مرغوبة: {len(deferred_transactions)}")
        
        # Step 7: Final Analysis
        print(f"\n📊 الخطوة 7: التحليل النهائي")
        print("=" * 70)
        
        # Expected results if working correctly
        expected_balance_increase = invoice_amount  # Should be exactly 500
        expected_transaction_count = 1  # Should be exactly 1
        expected_deferred_count = 0  # Should be 0
        
        # Check results
        balance_correct = abs(balance_increase - expected_balance_increase) < 0.01
        transaction_count_correct = len(invoice_transactions) == expected_transaction_count
        no_deferred_correct = len(deferred_transactions) == expected_deferred_count
        
        print(f"📈 النتائج المتوقعة إذا كان النظام يعمل بشكل صحيح:")
        print(f"   - زيادة الرصيد النقدي: {expected_balance_increase} ج.م")
        print(f"   - عدد معاملات الخزينة: {expected_transaction_count}")
        print(f"   - معاملات الحساب الآجل: {expected_deferred_count}")
        
        print(f"\n📊 النتائج الفعلية:")
        print(f"   - زيادة الرصيد النقدي: {balance_increase} ج.م")
        print(f"   - عدد معاملات الخزينة: {len(invoice_transactions)}")
        print(f"   - معاملات الحساب الآجل: {len(deferred_transactions)}")
        
        # Check for duplication
        duplicate_detected = False
        if balance_increase > expected_balance_increase * 1.5:
            duplicate_detected = True
            print(f"\n🚨 تم اكتشاف مشكلة تضاعف المعاملات!")
            print(f"   الرصيد زاد بـ {balance_increase} ج.م بدلاً من {expected_balance_increase} ج.م")
            print(f"   نسبة التضاعف: {balance_increase / expected_balance_increase:.2f}x")
        
        if len(invoice_transactions) > expected_transaction_count:
            duplicate_detected = True
            print(f"\n🚨 تم اكتشاف معاملات مكررة!")
            print(f"   عدد المعاملات: {len(invoice_transactions)} بدلاً من {expected_transaction_count}")
        
        if len(deferred_transactions) > 0:
            print(f"\n⚠️ توجد معاملات آجلة غير مرغوبة!")
            print(f"   عدد المعاملات الآجلة: {len(deferred_transactions)}")
        
        # Final verdict
        print(f"\n🏁 الحكم النهائي")
        print("=" * 70)
        
        if duplicate_detected:
            print("❌ توجد مشكلة تضاعف معاملات الخزينة!")
            self.log_result("الاختبار النهائي", False, "تم اكتشاف تضاعف في معاملات الخزينة")
            
            print(f"\n🔧 التوصيات:")
            print(f"   1. فحص منطق إنشاء معاملات الخزينة في الكود")
            print(f"   2. التأكد من عدم استدعاء دالة إنشاء المعاملات أكثر من مرة")
            print(f"   3. فحص حساب الأرصدة في get_account_balances()")
            
        elif balance_correct and transaction_count_correct and no_deferred_correct:
            print("✅ النظام يعمل بشكل صحيح تماماً!")
            print(f"   - تم إنشاء معاملة خزينة واحدة فقط")
            print(f"   - الرصيد النقدي زاد بالمبلغ الصحيح ({invoice_amount} ج.م)")
            print(f"   - لا توجد معاملات مكررة أو آجلة غير مرغوبة")
            self.log_result("الاختبار النهائي", True, "النظام يعمل بشكل صحيح بدون تضاعف")
            
        else:
            print("⚠️ توجد مشاكل أخرى في النظام:")
            if not balance_correct:
                print(f"   - زيادة الرصيد غير صحيحة")
            if not transaction_count_correct:
                print(f"   - عدد المعاملات غير صحيح")
            if not no_deferred_correct:
                print(f"   - توجد معاملات آجلة غير مرغوبة")
            self.log_result("الاختبار النهائي", False, "توجد مشاكل أخرى في النظام")
        
        # Summary for the user
        print(f"\n📋 ملخص للمستخدم:")
        print(f"   الفاتورة المنشأة: {invoice_number}")
        print(f"   طريقة الدفع: نقدي")
        print(f"   المبلغ: {invoice_amount} ج.م")
        print(f"   الرصيد قبل الإنشاء: {initial_cash_balance} ج.م")
        print(f"   الرصيد بعد الإنشاء: {final_cash_balance} ج.م")
        print(f"   الزيادة الفعلية: {balance_increase} ج.م")
        print(f"   عدد معاملات الخزينة: {len(invoice_transactions)}")
        
        return {
            'invoice_number': invoice_number,
            'invoice_amount': invoice_amount,
            'initial_balance': initial_cash_balance,
            'final_balance': final_cash_balance,
            'balance_increase': balance_increase,
            'transaction_count': len(invoice_transactions),
            'deferred_transactions': len(deferred_transactions),
            'duplicate_detected': duplicate_detected,
            'system_working_correctly': balance_correct and transaction_count_correct and no_deferred_correct,
            'transactions': invoice_transactions
        }

def main():
    """Run the final duplicate transaction test"""
    tester = FinalDuplicateTest()
    
    try:
        results = tester.run_final_test()
        
        print(f"\n✅ تم إكمال الاختبار النهائي بنجاح")
        print(f"عدد الخطوات المنفذة: {len(tester.test_results)}")
        
        # Count successful steps
        successful_steps = sum(1 for result in tester.test_results if result['success'])
        print(f"الخطوات الناجحة: {successful_steps}/{len(tester.test_results)}")
        
        return results
        
    except Exception as e:
        print(f"❌ خطأ في تنفيذ الاختبار: {str(e)}")
        return None

if __name__ == "__main__":
    main()