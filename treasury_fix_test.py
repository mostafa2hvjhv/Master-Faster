#!/usr/bin/env python3
"""
Quick test to verify the treasury double transaction bug fix
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

async def test_fix():
    async with aiohttp.ClientSession() as session:
        # Get initial balance
        async with session.get(f"{BACKEND_URL}/treasury/balances") as response:
            initial_balances = await response.json()
            initial_cash = initial_balances.get("cash", 0)
            print(f"Initial cash balance: {initial_cash} ج.م")
        
        # Create test customer
        customer_data = {
            "name": "عميل اختبار الإصلاح",
            "phone": "01111111111"
        }
        async with session.post(f"{BACKEND_URL}/customers", json=customer_data) as response:
            customer = await response.json()
            print(f"Created customer: {customer['name']}")
        
        # Create cash invoice
        invoice_data = {
            "customer_name": "عميل اختبار الإصلاح",
            "items": [{
                "seal_type": "RSL",
                "material_type": "NBR",
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "height": 7.0,
                "quantity": 1,
                "unit_price": 300.0,
                "total_price": 300.0,
                "product_type": "manufactured"
            }],
            "payment_method": "نقدي",
            "discount_type": "amount",
            "discount_value": 0.0
        }
        
        async with session.post(f"{BACKEND_URL}/invoices", json=invoice_data) as response:
            invoice = await response.json()
            print(f"Created invoice: {invoice['invoice_number']} - 300 ج.م")
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Check final balance
        async with session.get(f"{BACKEND_URL}/treasury/balances") as response:
            final_balances = await response.json()
            final_cash = final_balances.get("cash", 0)
            increase = final_cash - initial_cash
            
            print(f"Final cash balance: {final_cash} ج.م")
            print(f"Cash increase: {increase} ج.م (Expected: 300 ج.م)")
            
            if abs(increase - 300.0) < 0.01:
                print("✅ FIX SUCCESSFUL - No double transaction!")
            else:
                print("❌ FIX FAILED - Double transaction still exists")
        
        # Cleanup
        await session.delete(f"{BACKEND_URL}/invoices/{invoice['id']}")
        await session.delete(f"{BACKEND_URL}/customers/{customer['id']}")
        print("✅ Cleaned up test data")

if __name__ == "__main__":
    asyncio.run(test_fix())