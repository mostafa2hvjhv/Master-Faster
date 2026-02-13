#!/usr/bin/env python3
"""
Comprehensive Duplicate Transaction Test
اختبار شامل لمشكلة تضاعف معاملات الخزينة

Tests multiple payment methods to ensure no duplication occurs
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

class ComprehensiveDuplicateTest:
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
    
    def create_test_customer(self, name_suffix: str) -> str:
        """Create a test customer for the invoice"""
        customer_data = {
            "name": f"عميل اختبار {name_suffix}",
            "phone": "01234567890",
            "address": "عنوان اختبار"
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
    
    def create_invoice_with_payment_method(self, customer_id: str, payment_method: str, amount: float = 300.0) -> Dict:
        """Create an invoice with specific payment method"""
        invoice_data = {
            "customer_id": customer_id,
            "customer_name": f"عميل اختبار {payment_method}",
            "invoice_title": f"فاتورة اختبار {payment_method}",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 20.0,
                    "outer_diameter": 30.0,
                    "height": 6.0,
                    "quantity": 1,
                    "unit_price": amount,
                    "total_price": amount,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": payment_method,
            "discount_type": "amount",
            "discount_value": 0.0,
            "notes": f"فاتورة اختبار تضاعف المعاملات - {payment_method}"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
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
    
    def test_payment_method(self, payment_method: str, account_id: str, amount: float = 300.0):
        """Test a specific payment method for duplicate transactions"""
        print(f"\n🧪 اختبار طريقة الدفع: {payment_method}")
        print("-" * 50)
        
        # Get initial balance
        initial_balance = self.get_treasury_balance(account_id)
        print(f"الرصيد الأولي لحساب {account_id}: {initial_balance} ج.م")
        
        # Create customer
        customer_id = self.create_test_customer(payment_method)
        if not customer_id:
            self.log_result(f"إنشاء عميل لـ {payment_method}", False, "فشل في إنشاء العميل")
            return False
        
        # Create invoice
        invoice = self.create_invoice_with_payment_method(customer_id, payment_method, amount)
        if not invoice:
            self.log_result(f"إنشاء فاتورة {payment_method}", False, "فشل في إنشاء الفاتورة")
            return False
        
        invoice_id = invoice['id']
        invoice_number = invoice['invoice_number']
        
        # Check balance after invoice
        final_balance = self.get_treasury_balance(account_id)
        balance_increase = final_balance - initial_balance
        
        # Find related transactions
        invoice_transactions = self.find_invoice_transactions(invoice_id)
        
        # Analysis
        expected_increase = amount if payment_method != "آجل" else 0
        balance_correct = abs(balance_increase - expected_increase) < 0.01
        transaction_count_correct = len(invoice_transactions) == (1 if payment_method != "آجل" else 0)
        
        print(f"الفاتورة: {invoice_number}")
        print(f"المبلغ: {amount} ج.م")
        print(f"الرصيد النهائي: {final_balance} ج.م")
        print(f"الزيادة الفعلية: {balance_increase} ج.م")
        print(f"الزيادة المتوقعة: {expected_increase} ج.م")
        print(f"عدد المعاملات: {len(invoice_transactions)}")
        
        # Check for duplication
        if balance_increase > expected_increase * 1.5 and expected_increase > 0:
            self.log_result(f"اختبار {payment_method}", False, 
                           f"تضاعف معاملات! زيادة {balance_increase} بدلاً من {expected_increase}")
            return False
        elif balance_correct and transaction_count_correct:
            self.log_result(f"اختبار {payment_method}", True, "يعمل بشكل صحيح")
            return True
        else:
            self.log_result(f"اختبار {payment_method}", False, 
                           f"مشكلة في الحسابات أو عدد المعاملات")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test for all payment methods"""
        print("🔍 اختبار شامل لمشكلة تضاعف معاملات الخزينة")
        print("=" * 60)
        
        # Payment methods to test
        payment_methods = [
            ("نقدي", "cash", 300.0),
            ("فودافون كاش محمد الصاوي", "vodafone_elsawy", 250.0),
            ("فودافون كاش وائل محمد", "vodafone_wael", 200.0),
            ("انستاباي", "instapay", 350.0),
            ("يد الصاوي", "yad_elsawy", 400.0),
            ("آجل", "deferred", 500.0)  # Special case - should not create immediate treasury transaction
        ]
        
        results = {}
        successful_tests = 0
        
        for payment_method, account_id, amount in payment_methods:
            success = self.test_payment_method(payment_method, account_id, amount)
            results[payment_method] = success
            if success:
                successful_tests += 1
        
        # Summary
        print(f"\n📊 ملخص الاختبار الشامل")
        print("=" * 60)
        print(f"إجمالي طرق الدفع المختبرة: {len(payment_methods)}")
        print(f"الاختبارات الناجحة: {successful_tests}")
        print(f"الاختبارات الفاشلة: {len(payment_methods) - successful_tests}")
        print(f"نسبة النجاح: {(successful_tests/len(payment_methods)*100):.1f}%")
        
        print(f"\n📋 تفاصيل النتائج:")
        for payment_method, success in results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {payment_method}")
        
        if successful_tests == len(payment_methods):
            print(f"\n🎉 جميع الاختبارات نجحت! النظام يعمل بشكل صحيح")
            print("   لا توجد مشكلة تضاعف معاملات في أي من طرق الدفع")
        else:
            print(f"\n⚠️ توجد مشاكل في بعض طرق الدفع")
            failed_methods = [method for method, success in results.items() if not success]
            print(f"   طرق الدفع التي بها مشاكل: {', '.join(failed_methods)}")
        
        return results

def main():
    """Run the comprehensive duplicate transaction test"""
    tester = ComprehensiveDuplicateTest()
    
    try:
        results = tester.run_comprehensive_test()
        return results
        
    except Exception as e:
        print(f"❌ خطأ في تنفيذ الاختبار: {str(e)}")
        return None

if __name__ == "__main__":
    main()