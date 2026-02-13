#!/usr/bin/env python3
"""
Focused Test for Duplicate Transaction Issue
اختبار مركز لمشكلة تضاعف معاملات الخزينة

This test specifically checks if creating a cash invoice results in duplicate treasury transactions.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class DuplicateTransactionTester:
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
    
    def get_treasury_balance(self, account: str = "cash") -> float:
        """Get current treasury balance for specific account"""
        try:
            response = self.session.get(f"{BACKEND_URL}/treasury/balances")
            if response.status_code == 200:
                balances = response.json()
                return balances.get(account, 0)
            else:
                print(f"Failed to get treasury balances: {response.status_code}")
                return 0
        except Exception as e:
            print(f"Error getting treasury balance: {str(e)}")
            return 0
    
    def get_treasury_transactions(self) -> List[Dict]:
        """Get all treasury transactions"""
        try:
            response = self.session.get(f"{BACKEND_URL}/treasury/transactions")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get treasury transactions: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting treasury transactions: {str(e)}")
            return []
    
    def create_test_customer(self) -> str:
        """Create a test customer for the invoice"""
        customer_data = {
            "name": "عميل اختبار تضاعف المعاملات",
            "phone": "01234567890",
            "address": "عنوان اختبار"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/customers", json=customer_data)
            if response.status_code == 200:
                customer = response.json()
                self.log_result("إنشاء عميل اختبار", True, f"تم إنشاء العميل: {customer['name']}")
                return customer['id']
            else:
                self.log_result("إنشاء عميل اختبار", False, f"خطأ HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log_result("إنشاء عميل اختبار", False, f"خطأ: {str(e)}")
            return None
    
    def create_cash_invoice(self, customer_id: str, amount: float = 500.0) -> Dict:
        """Create a simple cash invoice"""
        invoice_data = {
            "customer_id": customer_id,
            "customer_name": "عميل اختبار تضاعف المعاملات",
            "invoice_title": "فاتورة اختبار تضاعف المعاملات",
            "supervisor_name": "مشرف الاختبار",
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
            "notes": "فاتورة اختبار لفحص تضاعف معاملات الخزينة"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                invoice = response.json()
                self.log_result("إنشاء فاتورة نقدية", True, 
                              f"تم إنشاء الفاتورة: {invoice['invoice_number']} بقيمة {amount} ج.م")
                return invoice
            else:
                self.log_result("إنشاء فاتورة نقدية", False, 
                              f"خطأ HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_result("إنشاء فاتورة نقدية", False, f"خطأ: {str(e)}")
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
    
    def run_duplicate_transaction_test(self):
        """Run the complete duplicate transaction test"""
        print("🔍 بدء اختبار تضاعف معاملات الخزينة")
        print("=" * 60)
        
        # Step 1: Get initial cash balance
        print("\n📊 الخطوة 1: فحص الرصيد النقدي الحالي")
        initial_balance = self.get_treasury_balance("cash")
        self.log_result("فحص الرصيد الأولي", True, f"الرصيد النقدي الحالي: {initial_balance} ج.م")
        
        # Step 2: Create test customer
        print("\n👤 الخطوة 2: إنشاء عميل اختبار")
        customer_id = self.create_test_customer()
        if not customer_id:
            print("❌ فشل في إنشاء العميل - إيقاف الاختبار")
            return
        
        # Step 3: Create cash invoice for 500 ج.م
        print("\n🧾 الخطوة 3: إنشاء فاتورة نقدية بقيمة 500 ج.م")
        invoice_amount = 500.0
        invoice = self.create_cash_invoice(customer_id, invoice_amount)
        if not invoice:
            print("❌ فشل في إنشاء الفاتورة - إيقاف الاختبار")
            return
        
        invoice_id = invoice['id']
        invoice_number = invoice['invoice_number']
        
        # Step 4: Check balance after invoice creation
        print("\n💰 الخطوة 4: فحص الرصيد النقدي بعد إنشاء الفاتورة")
        final_balance = self.get_treasury_balance("cash")
        balance_increase = final_balance - initial_balance
        
        self.log_result("فحص الرصيد النهائي", True, 
                       f"الرصيد النقدي بعد الفاتورة: {final_balance} ج.م")
        self.log_result("حساب الزيادة في الرصيد", True, 
                       f"الزيادة في الرصيد: {balance_increase} ج.م")
        
        # Step 5: Find all transactions for this invoice
        print("\n🔍 الخطوة 5: البحث عن معاملات الخزينة المرتبطة بالفاتورة")
        invoice_transactions = self.find_invoice_transactions(invoice_id)
        
        self.log_result("البحث عن معاملات الفاتورة", True, 
                       f"تم العثور على {len(invoice_transactions)} معاملة مرتبطة بالفاتورة")
        
        # Display transaction details
        if invoice_transactions:
            print("\n📋 تفاصيل المعاملات المرتبطة بالفاتورة:")
            for i, transaction in enumerate(invoice_transactions, 1):
                print(f"   المعاملة {i}:")
                print(f"     - الحساب: {transaction.get('account_id')}")
                print(f"     - النوع: {transaction.get('transaction_type')}")
                print(f"     - المبلغ: {transaction.get('amount')} ج.م")
                print(f"     - الوصف: {transaction.get('description')}")
                print(f"     - المرجع: {transaction.get('reference')}")
        
        # Step 6: Check for deferred account transactions (should be none)
        print("\n🔍 الخطوة 6: فحص معاملات الحساب الآجل (يجب ألا توجد)")
        all_transactions = self.get_treasury_transactions()
        deferred_transactions = [t for t in all_transactions 
                               if t.get('account_id') == 'deferred' and f"invoice_{invoice_id}" in t.get('reference', '')]
        
        self.log_result("فحص معاملات الحساب الآجل", len(deferred_transactions) == 0, 
                       f"معاملات الحساب الآجل: {len(deferred_transactions)}")
        
        # Step 7: Analysis and Results
        print("\n📊 الخطوة 7: تحليل النتائج")
        print("=" * 60)
        
        # Check if balance increased correctly
        balance_correct = abs(balance_increase - invoice_amount) < 0.01
        self.log_result("صحة زيادة الرصيد", balance_correct,
                       f"متوقع: {invoice_amount} ج.م، فعلي: {balance_increase} ج.م")
        
        # Check number of transactions
        transaction_count_correct = len(invoice_transactions) == 1
        self.log_result("عدد المعاملات صحيح", transaction_count_correct,
                       f"متوقع: 1 معاملة، فعلي: {len(invoice_transactions)} معاملة")
        
        # Check no deferred transactions
        no_deferred_correct = len(deferred_transactions) == 0
        self.log_result("عدم وجود معاملات آجلة", no_deferred_correct,
                       f"معاملات آجلة غير مرغوبة: {len(deferred_transactions)}")
        
        # Final verdict
        print("\n🏁 النتيجة النهائية")
        print("=" * 60)
        
        if balance_increase > invoice_amount * 1.5:  # More than 150% indicates duplication
            print("🚨 تم اكتشاف مشكلة تضاعف المعاملات!")
            print(f"   المبلغ المتوقع: {invoice_amount} ج.م")
            print(f"   الزيادة الفعلية: {balance_increase} ج.م")
            print(f"   نسبة التضاعف: {balance_increase / invoice_amount:.2f}x")
            
            if len(invoice_transactions) > 1:
                print(f"   عدد المعاملات المكررة: {len(invoice_transactions)}")
            
            self.log_result("اختبار تضاعف المعاملات", False, "تم اكتشاف تضاعف في معاملات الخزينة")
            
        elif balance_correct and transaction_count_correct and no_deferred_correct:
            print("✅ النظام يعمل بشكل صحيح!")
            print(f"   تم إنشاء معاملة واحدة فقط بقيمة {invoice_amount} ج.م")
            print("   لا توجد معاملات مكررة أو آجلة غير مرغوبة")
            
            self.log_result("اختبار تضاعف المعاملات", True, "النظام يعمل بشكل صحيح بدون تضاعف")
            
        else:
            print("⚠️ توجد مشاكل في النظام:")
            if not balance_correct:
                print(f"   - زيادة الرصيد غير صحيحة: متوقع {invoice_amount}، فعلي {balance_increase}")
            if not transaction_count_correct:
                print(f"   - عدد المعاملات غير صحيح: متوقع 1، فعلي {len(invoice_transactions)}")
            if not no_deferred_correct:
                print(f"   - توجد معاملات آجلة غير مرغوبة: {len(deferred_transactions)}")
            
            self.log_result("اختبار تضاعف المعاملات", False, "توجد مشاكل في النظام")
        
        # Summary
        print(f"\n📈 ملخص الاختبار:")
        print(f"   الفاتورة: {invoice_number}")
        print(f"   المبلغ: {invoice_amount} ج.م")
        print(f"   الرصيد قبل: {initial_balance} ج.م")
        print(f"   الرصيد بعد: {final_balance} ج.م")
        print(f"   الزيادة: {balance_increase} ج.م")
        print(f"   عدد المعاملات: {len(invoice_transactions)}")
        
        return {
            'invoice_number': invoice_number,
            'invoice_amount': invoice_amount,
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'balance_increase': balance_increase,
            'transaction_count': len(invoice_transactions),
            'deferred_transactions': len(deferred_transactions),
            'duplicate_detected': balance_increase > invoice_amount * 1.5,
            'system_working_correctly': balance_correct and transaction_count_correct and no_deferred_correct
        }

def main():
    """Run the duplicate transaction test"""
    tester = DuplicateTransactionTester()
    
    print("🧪 اختبار مشكلة تضاعف معاملات الخزينة")
    print("Master Seal Treasury Duplicate Transaction Test")
    print("=" * 60)
    
    try:
        results = tester.run_duplicate_transaction_test()
        
        print(f"\n📊 تم إكمال الاختبار بنجاح")
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