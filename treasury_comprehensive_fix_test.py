#!/usr/bin/env python3
"""
Comprehensive test to verify the treasury fix works for all payment methods
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

async def test_all_payment_methods():
    async with aiohttp.ClientSession() as session:
        print("🔍 COMPREHENSIVE TREASURY FIX VERIFICATION")
        print("=" * 60)
        
        # Test payment methods
        payment_methods = [
            ("نقدي", "cash", 200.0),
            ("فودافون كاش محمد الصاوي", "vodafone_elsawy", 150.0),
            ("فودافون كاش وائل محمد", "vodafone_wael", 180.0),
            ("انستاباي", "instapay", 220.0),
            ("يد الصاوي", "yad_elsawy", 160.0),
            ("آجل", "deferred", 250.0)
        ]
        
        # Create test customer
        customer_data = {
            "name": "عميل اختبار شامل للإصلاح",
            "phone": "01222222222"
        }
        async with session.post(f"{BACKEND_URL}/customers", json=customer_data) as response:
            customer = await response.json()
            print(f"✅ Created customer: {customer['name']}")
        
        created_invoices = []
        all_tests_passed = True
        
        for payment_method, account_key, amount in payment_methods:
            print(f"\n🔸 Testing: {payment_method}")
            
            # Get initial balance
            async with session.get(f"{BACKEND_URL}/treasury/balances") as response:
                initial_balances = await response.json()
                initial_balance = initial_balances.get(account_key, 0)
            
            # Create invoice
            invoice_data = {
                "customer_name": "عميل اختبار شامل للإصلاح",
                "items": [{
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 7.0,
                    "quantity": 1,
                    "unit_price": amount,
                    "total_price": amount,
                    "product_type": "manufactured"
                }],
                "payment_method": payment_method,
                "discount_type": "amount",
                "discount_value": 0.0
            }
            
            async with session.post(f"{BACKEND_URL}/invoices", json=invoice_data) as response:
                invoice = await response.json()
                created_invoices.append(invoice['id'])
            
            # Wait for processing
            await asyncio.sleep(0.5)
            
            # Check final balance
            async with session.get(f"{BACKEND_URL}/treasury/balances") as response:
                final_balances = await response.json()
                final_balance = final_balances.get(account_key, 0)
                increase = final_balance - initial_balance
            
            # Verify
            is_correct = abs(increase - amount) < 0.01
            status = "✅" if is_correct else "❌"
            print(f"   {status} Balance increase: {increase} ج.م (Expected: {amount} ج.م)")
            
            if not is_correct:
                all_tests_passed = False
        
        # Test deferred payment
        print(f"\n🔸 Testing deferred payment settlement")
        
        # Find a deferred invoice
        deferred_invoice_id = None
        for invoice_id in created_invoices[-1:]:  # Get the last one (deferred)
            async with session.get(f"{BACKEND_URL}/invoices/{invoice_id}") as response:
                invoice = await response.json()
                if invoice.get('payment_method') == 'آجل':
                    deferred_invoice_id = invoice_id
                    break
        
        if deferred_invoice_id:
            # Get initial balances
            async with session.get(f"{BACKEND_URL}/treasury/balances") as response:
                initial_balances = await response.json()
                initial_cash = initial_balances.get("cash", 0)
                initial_deferred = initial_balances.get("deferred", 0)
            
            # Make payment
            payment_data = {
                "invoice_id": deferred_invoice_id,
                "amount": 100.0,
                "payment_method": "نقدي"
            }
            
            async with session.post(f"{BACKEND_URL}/payments", json=payment_data) as response:
                payment = await response.json()
            
            await asyncio.sleep(0.5)
            
            # Check balances
            async with session.get(f"{BACKEND_URL}/treasury/balances") as response:
                final_balances = await response.json()
                final_cash = final_balances.get("cash", 0)
                final_deferred = final_balances.get("deferred", 0)
            
            cash_increase = final_cash - initial_cash
            deferred_decrease = initial_deferred - final_deferred
            
            cash_correct = abs(cash_increase - 100.0) < 0.01
            deferred_correct = abs(deferred_decrease - 100.0) < 0.01
            
            cash_status = "✅" if cash_correct else "❌"
            deferred_status = "✅" if deferred_correct else "❌"
            
            print(f"   {cash_status} Cash increase: {cash_increase} ج.م (Expected: 100.0 ج.م)")
            print(f"   {deferred_status} Deferred decrease: {deferred_decrease} ج.م (Expected: 100.0 ج.م)")
            
            if not (cash_correct and deferred_correct):
                all_tests_passed = False
        
        # Summary
        print(f"\n" + "=" * 60)
        if all_tests_passed:
            print("✅ ALL TESTS PASSED - Treasury fix is working correctly!")
        else:
            print("❌ SOME TESTS FAILED - Treasury fix needs more work")
        
        # Cleanup
        for invoice_id in created_invoices:
            await session.delete(f"{BACKEND_URL}/invoices/{invoice_id}")
        await session.delete(f"{BACKEND_URL}/customers/{customer['id']}")
        print("✅ Cleaned up test data")

if __name__ == "__main__":
    asyncio.run(test_all_payment_methods())