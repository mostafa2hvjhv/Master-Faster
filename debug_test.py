#!/usr/bin/env python3
"""
Debug test for specific issues found in the new features testing
"""

import requests
import json

BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

def test_payment_method_conversion_to_deferred():
    """Test converting payment method to deferred (آجل)"""
    print("🔍 Testing payment method conversion to deferred...")
    
    # Create a test invoice
    invoice_data = {
        "customer_name": "عميل اختبار تحويل آجل",
        "items": [
            {
                "seal_type": "RSL",
                "material_type": "NBR",
                "inner_diameter": 20.0,
                "outer_diameter": 30.0,
                "height": 8.0,
                "quantity": 2,
                "unit_price": 10.0,
                "total_price": 20.0,
                "product_type": "manufactured"
            }
        ],
        "payment_method": "نقدي"
    }
    
    response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data)
    if response.status_code == 200:
        invoice = response.json()
        invoice_id = invoice['id']
        print(f"✅ Created invoice: {invoice['invoice_number']}")
        
        # Try to convert to deferred
        response = requests.put(
            f"{BACKEND_URL}/invoices/{invoice_id}/change-payment-method",
            params={'new_payment_method': 'آجل'}
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
        else:
            print(f"Success: {response.json()}")
            
        # Clean up
        requests.delete(f"{BACKEND_URL}/invoices/{invoice_id}")
    else:
        print(f"Failed to create invoice: {response.status_code}")

def test_treasury_balances():
    """Test treasury balances API"""
    print("\n🔍 Testing treasury balances...")
    
    response = requests.get(f"{BACKEND_URL}/treasury/balances")
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        balances = response.json()
        print("Current balances:")
        for account, balance in balances.items():
            print(f"  {account}: {balance}")
    else:
        print(f"Error: {response.text}")

def test_invoice_cancellation_deletion():
    """Test if invoice is actually deleted after cancellation"""
    print("\n🔍 Testing invoice deletion after cancellation...")
    
    # Create a test invoice
    invoice_data = {
        "customer_name": "عميل اختبار حذف الفاتورة",
        "items": [
            {
                "seal_type": "RSL",
                "material_type": "NBR", 
                "inner_diameter": 20.0,
                "outer_diameter": 30.0,
                "height": 8.0,
                "quantity": 1,
                "unit_price": 10.0,
                "total_price": 10.0,
                "product_type": "manufactured"
            }
        ],
        "payment_method": "نقدي"
    }
    
    response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data)
    if response.status_code == 200:
        invoice = response.json()
        invoice_id = invoice['id']
        invoice_number = invoice['invoice_number']
        print(f"✅ Created invoice: {invoice_number}")
        
        # Check if invoice exists
        response = requests.get(f"{BACKEND_URL}/invoices/{invoice_id}")
        print(f"Invoice exists before cancellation: {response.status_code == 200}")
        
        # Cancel the invoice
        response = requests.delete(f"{BACKEND_URL}/invoices/{invoice_id}/cancel")
        print(f"Cancellation response: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Cancellation result: {response.json()}")
            
            # Check if invoice still exists
            response = requests.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            print(f"Invoice exists after cancellation: {response.status_code == 200}")
            print(f"Response status after cancellation: {response.status_code}")
            
            if response.status_code == 200:
                print("⚠️ Invoice still exists - this might be the issue")
                # Clean up manually
                requests.delete(f"{BACKEND_URL}/invoices/{invoice_id}")
        else:
            print(f"Cancellation failed: {response.text}")
    else:
        print(f"Failed to create invoice: {response.status_code}")

if __name__ == "__main__":
    test_payment_method_conversion_to_deferred()
    test_treasury_balances()
    test_invoice_cancellation_deletion()