#!/usr/bin/env python3
"""
Focused test to verify specific issues found in latest improvements testing
"""

import requests
import json

BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

def test_treasury_integration():
    """Test treasury integration with different payment methods"""
    print("=== Testing Treasury Integration ===")
    
    # Create a customer first
    customer_data = {
        "name": "عميل اختبار الخزينة المركز",
        "phone": "01234567890",
        "address": "القاهرة"
    }
    
    response = requests.post(f"{BACKEND_URL}/customers", json=customer_data, headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        print("Failed to create customer")
        return
    
    customer = response.json()
    
    # Get initial treasury count
    treasury_response = requests.get(f"{BACKEND_URL}/treasury/transactions")
    initial_count = len(treasury_response.json()) if treasury_response.status_code == 200 else 0
    
    # Test 1: Deferred payment should NOT create treasury transaction
    deferred_invoice = {
        "customer_id": customer['id'],
        "customer_name": customer['name'],
        "items": [
            {
                "seal_type": "RSL",
                "material_type": "NBR",
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "height": 8.0,
                "quantity": 1,
                "unit_price": 50.0,
                "total_price": 50.0,
                "product_type": "manufactured"
            }
        ],
        "payment_method": "آجل",
        "discount_type": "amount",
        "discount_value": 0.0
    }
    
    print(f"Initial treasury count: {initial_count}")
    
    response = requests.post(f"{BACKEND_URL}/invoices", json=deferred_invoice, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        print("✅ Deferred invoice created successfully")
        
        # Check treasury count
        treasury_response = requests.get(f"{BACKEND_URL}/treasury/transactions")
        new_count = len(treasury_response.json()) if treasury_response.status_code == 200 else 0
        
        if new_count == initial_count:
            print("✅ CORRECT: No treasury transaction created for deferred payment")
        else:
            print(f"❌ WRONG: Treasury transaction was created for deferred payment (count: {initial_count} -> {new_count})")
            
            # Check what transaction was created
            if treasury_response.status_code == 200:
                transactions = treasury_response.json()
                if transactions:
                    latest = transactions[0]
                    print(f"   Latest transaction: {latest}")
    else:
        print(f"❌ Failed to create deferred invoice: {response.status_code}")
    
    # Test 2: Check payment method enum values
    print("\n=== Payment Method Enum Values ===")
    
    # Let's check what the actual enum values are by looking at the PaymentMethod enum
    cash_invoice = {
        "customer_id": customer['id'],
        "customer_name": customer['name'],
        "items": [
            {
                "seal_type": "RSL",
                "material_type": "NBR",
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "height": 8.0,
                "quantity": 1,
                "unit_price": 30.0,
                "total_price": 30.0,
                "product_type": "manufactured"
            }
        ],
        "payment_method": "نقدي",
        "discount_type": "amount",
        "discount_value": 0.0
    }
    
    pre_cash_response = requests.get(f"{BACKEND_URL}/treasury/transactions")
    pre_cash_count = len(pre_cash_response.json()) if pre_cash_response.status_code == 200 else 0
    
    response = requests.post(f"{BACKEND_URL}/invoices", json=cash_invoice, headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        print("✅ Cash invoice created successfully")
        
        # Check treasury transaction
        treasury_response = requests.get(f"{BACKEND_URL}/treasury/transactions")
        post_cash_count = len(treasury_response.json()) if treasury_response.status_code == 200 else 0
        
        if post_cash_count > pre_cash_count:
            transactions = treasury_response.json()
            latest = transactions[0]
            print(f"✅ Treasury transaction created: account_id={latest.get('account_id')}, amount={latest.get('amount')}")
        else:
            print("❌ No treasury transaction created for cash payment")
    else:
        print(f"❌ Failed to create cash invoice: {response.status_code}")

def test_inventory_system():
    """Test inventory system creation"""
    print("\n=== Testing Inventory System ===")
    
    inventory_data = {
        "material_type": "NBR",
        "inner_diameter": 25.0,
        "outer_diameter": 35.0,
        "available_pieces": 50,
        "min_stock_level": 5,
        "notes": "test inventory"
    }
    
    response = requests.post(f"{BACKEND_URL}/inventory", json=inventory_data, headers={'Content-Type': 'application/json'})
    print(f"Inventory creation response: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
    else:
        print("✅ Inventory item created successfully")

if __name__ == "__main__":
    test_treasury_integration()
    test_inventory_system()