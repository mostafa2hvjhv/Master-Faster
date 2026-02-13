#!/usr/bin/env python3
"""
Treasury Duplicate Transaction Bug Test
======================================

This test specifically investigates the user's reported issue:
1. When creating a new invoice with ANY payment method other than "آجل" (deferred)
2. It gets added to treasury TWICE with different names but same invoice number and same amount  
3. PLUS it also gets added to the deferred account even though it's not deferred

Test Focus:
- Create invoices with different payment methods
- Monitor exactly what treasury transactions are created
- Check for duplicate entries with same invoice reference
- Check if non-deferred invoices are incorrectly processed as deferred
- Examine transaction descriptions and account IDs
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Get backend URL from frontend env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=')[1].strip()
            break

API_BASE = f"{BACKEND_URL}/api"

class TreasuryDuplicateTest:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.created_invoices = []
        self.initial_treasury_count = 0
        self.initial_balances = {}
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def get_treasury_transactions(self):
        """Get all treasury transactions"""
        try:
            async with self.session.get(f"{API_BASE}/treasury/transactions") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"❌ Failed to get treasury transactions: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error getting treasury transactions: {e}")
            return []
            
    async def get_treasury_balances(self):
        """Get treasury account balances"""
        try:
            async with self.session.get(f"{API_BASE}/treasury/balances") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"❌ Failed to get treasury balances: {response.status}")
                    return {}
        except Exception as e:
            print(f"❌ Error getting treasury balances: {e}")
            return {}
            
    async def create_test_customer(self):
        """Create a test customer for invoices"""
        customer_data = {
            "name": "عميل اختبار الخزينة المكررة",
            "phone": "01234567890",
            "address": "عنوان اختبار"
        }
        
        try:
            async with self.session.post(f"{API_BASE}/customers", json=customer_data) as response:
                if response.status == 200:
                    customer = await response.json()
                    print(f"✅ Created test customer: {customer['name']}")
                    return customer
                else:
                    print(f"❌ Failed to create customer: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Error creating customer: {e}")
            return None
            
    async def create_invoice_with_payment_method(self, customer, payment_method, amount=500.0):
        """Create an invoice with specific payment method"""
        invoice_data = {
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "invoice_title": f"فاتورة اختبار {payment_method}",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 10.0,
                    "quantity": 1,
                    "unit_price": amount,
                    "total_price": amount,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": payment_method,
            "discount_type": "amount",
            "discount_value": 0.0,
            "notes": f"اختبار طريقة دفع {payment_method}"
        }
        
        try:
            async with self.session.post(f"{API_BASE}/invoices", json=invoice_data) as response:
                if response.status == 200:
                    invoice = await response.json()
                    self.created_invoices.append(invoice)
                    print(f"✅ Created invoice {invoice['invoice_number']} with payment method: {payment_method}")
                    return invoice
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create invoice with {payment_method}: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error creating invoice with {payment_method}: {e}")
            return None
            
    async def analyze_treasury_transactions_for_invoice(self, invoice):
        """Analyze treasury transactions for a specific invoice"""
        print(f"\n🔍 Analyzing treasury transactions for invoice {invoice['invoice_number']}:")
        
        # Get all treasury transactions
        all_transactions = await self.get_treasury_transactions()
        
        # Find transactions related to this invoice
        invoice_transactions = []
        for transaction in all_transactions:
            reference = transaction.get('reference', '')
            if f"invoice_{invoice['id']}" in reference:
                invoice_transactions.append(transaction)
                
        print(f"   📊 Found {len(invoice_transactions)} treasury transactions for this invoice")
        
        # Analyze each transaction
        for i, transaction in enumerate(invoice_transactions, 1):
            print(f"   Transaction {i}:")
            print(f"     - Account ID: {transaction.get('account_id')}")
            print(f"     - Type: {transaction.get('transaction_type')}")
            print(f"     - Amount: {transaction.get('amount')} ج.م")
            print(f"     - Description: {transaction.get('description')}")
            print(f"     - Reference: {transaction.get('reference')}")
            print(f"     - Date: {transaction.get('date')}")
            
        # Check for duplicates
        if len(invoice_transactions) > 1:
            print(f"   ⚠️  WARNING: Found {len(invoice_transactions)} transactions for one invoice!")
            
            # Check if they have same amount but different descriptions
            amounts = [t.get('amount') for t in invoice_transactions]
            descriptions = [t.get('description') for t in invoice_transactions]
            account_ids = [t.get('account_id') for t in invoice_transactions]
            
            if len(set(amounts)) == 1:  # Same amounts
                print(f"   🚨 DUPLICATE DETECTED: All transactions have same amount ({amounts[0]} ج.م)")
                
            if len(set(descriptions)) > 1:  # Different descriptions
                print(f"   🚨 DIFFERENT DESCRIPTIONS: {descriptions}")
                
            if len(set(account_ids)) > 1:  # Different accounts
                print(f"   🚨 DIFFERENT ACCOUNTS: {account_ids}")
                
        return invoice_transactions
        
    async def check_deferred_account_contamination(self, invoice, payment_method):
        """Check if non-deferred invoice incorrectly affects deferred account"""
        print(f"\n🔍 Checking deferred account contamination for {payment_method} invoice:")
        
        # Get all treasury transactions
        all_transactions = await self.get_treasury_transactions()
        
        # Find deferred account transactions related to this invoice
        deferred_transactions = []
        for transaction in all_transactions:
            if (transaction.get('account_id') == 'deferred' and 
                f"invoice_{invoice['id']}" in transaction.get('reference', '')):
                deferred_transactions.append(transaction)
                
        if deferred_transactions and payment_method != "آجل":
            print(f"   🚨 CONTAMINATION DETECTED: Non-deferred invoice ({payment_method}) has {len(deferred_transactions)} deferred account transactions!")
            for transaction in deferred_transactions:
                print(f"     - Type: {transaction.get('transaction_type')}")
                print(f"     - Amount: {transaction.get('amount')} ج.م")
                print(f"     - Description: {transaction.get('description')}")
        elif not deferred_transactions and payment_method != "آجل":
            print(f"   ✅ CORRECT: No deferred account transactions for {payment_method} invoice")
        else:
            print(f"   ℹ️  Deferred invoice - expected to have deferred transactions")
            
        return deferred_transactions
        
    async def run_comprehensive_test(self):
        """Run comprehensive test for treasury duplicate issue"""
        print("🚀 Starting Treasury Duplicate Transaction Bug Test")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Get initial state
            print("\n📊 Getting initial treasury state...")
            self.initial_balances = await self.get_treasury_balances()
            initial_transactions = await self.get_treasury_transactions()
            self.initial_treasury_count = len(initial_transactions)
            
            print(f"   Initial treasury transactions: {self.initial_treasury_count}")
            print(f"   Initial balances: {self.initial_balances}")
            
            # Create test customer
            print("\n👤 Creating test customer...")
            customer = await self.create_test_customer()
            if not customer:
                print("❌ Failed to create customer. Aborting test.")
                return
                
            # Test different payment methods
            payment_methods_to_test = [
                "نقدي",
                "فودافون كاش محمد الصاوي", 
                "انستاباي"
            ]
            
            print(f"\n💳 Testing {len(payment_methods_to_test)} payment methods...")
            
            for payment_method in payment_methods_to_test:
                print(f"\n" + "="*50)
                print(f"🧪 TESTING PAYMENT METHOD: {payment_method}")
                print(f"="*50)
                
                # Create invoice
                invoice = await self.create_invoice_with_payment_method(customer, payment_method)
                if not invoice:
                    continue
                    
                # Wait a moment for processing
                await asyncio.sleep(1)
                
                # Analyze treasury transactions for this invoice
                invoice_transactions = await self.analyze_treasury_transactions_for_invoice(invoice)
                
                # Check for deferred account contamination
                deferred_transactions = await self.check_deferred_account_contamination(invoice, payment_method)
                
                # Record results
                self.test_results.append({
                    'payment_method': payment_method,
                    'invoice_number': invoice['invoice_number'],
                    'invoice_amount': invoice['total_amount'],
                    'treasury_transactions_count': len(invoice_transactions),
                    'deferred_contamination': len(deferred_transactions) > 0,
                    'duplicate_detected': len(invoice_transactions) > 1
                })
                
            # Final analysis
            await self.generate_final_report()
            
        finally:
            await self.cleanup_session()
            
    async def generate_final_report(self):
        """Generate final test report"""
        print(f"\n" + "="*60)
        print("📋 FINAL TEST REPORT")
        print("="*60)
        
        # Get final state
        final_balances = await self.get_treasury_balances()
        final_transactions = await self.get_treasury_transactions()
        final_treasury_count = len(final_transactions)
        
        print(f"\n📊 Treasury Transaction Summary:")
        print(f"   Initial transactions: {self.initial_treasury_count}")
        print(f"   Final transactions: {final_treasury_count}")
        print(f"   New transactions created: {final_treasury_count - self.initial_treasury_count}")
        print(f"   Expected new transactions: {len(self.created_invoices)} (one per invoice)")
        
        # Check if we have more transactions than expected
        expected_new = len(self.created_invoices)
        actual_new = final_treasury_count - self.initial_treasury_count
        
        if actual_new > expected_new:
            print(f"   🚨 DUPLICATE ISSUE CONFIRMED: {actual_new - expected_new} extra transactions detected!")
        else:
            print(f"   ✅ Transaction count looks correct")
            
        print(f"\n💰 Balance Changes:")
        for account, final_balance in final_balances.items():
            initial_balance = self.initial_balances.get(account, 0)
            change = final_balance - initial_balance
            if change != 0:
                print(f"   {account}: {initial_balance} → {final_balance} (change: {change:+.2f})")
                
        print(f"\n🧪 Test Results Summary:")
        duplicates_found = 0
        contamination_found = 0
        
        for result in self.test_results:
            print(f"\n   Payment Method: {result['payment_method']}")
            print(f"   Invoice: {result['invoice_number']} ({result['invoice_amount']} ج.م)")
            print(f"   Treasury Transactions: {result['treasury_transactions_count']}")
            
            if result['duplicate_detected']:
                print(f"   🚨 DUPLICATE DETECTED")
                duplicates_found += 1
            else:
                print(f"   ✅ No duplicates")
                
            if result['deferred_contamination']:
                print(f"   🚨 DEFERRED CONTAMINATION")
                contamination_found += 1
            else:
                print(f"   ✅ No deferred contamination")
                
        print(f"\n🎯 FINAL VERDICT:")
        if duplicates_found > 0:
            print(f"   🚨 DUPLICATE ISSUE CONFIRMED: {duplicates_found} invoices created duplicate treasury transactions")
        else:
            print(f"   ✅ No duplicate treasury transactions detected")
            
        if contamination_found > 0:
            print(f"   🚨 DEFERRED CONTAMINATION CONFIRMED: {contamination_found} non-deferred invoices affected deferred account")
        else:
            print(f"   ✅ No deferred account contamination detected")
            
        if duplicates_found == 0 and contamination_found == 0:
            print(f"   🎉 USER REPORT COULD NOT BE REPRODUCED - System appears to be working correctly")
        else:
            print(f"   ⚠️  USER REPORT CONFIRMED - Issues found in treasury transaction handling")

async def main():
    """Main test execution"""
    test = TreasuryDuplicateTest()
    await test.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())