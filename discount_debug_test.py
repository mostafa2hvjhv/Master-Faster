#!/usr/bin/env python3
"""
Debug test for discount calculation issues
"""

import requests
import json

BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

def debug_discount_calculation():
    session = requests.Session()
    
    # Create a test customer
    customer_data = {
        "name": "عميل اختبار خصم",
        "phone": "01111111111"
    }
    
    customer_response = session.post(f"{BACKEND_URL}/customers", json=customer_data)
    if customer_response.status_code != 200:
        print("Failed to create customer")
        return
    
    customer = customer_response.json()
    
    # Create a simple invoice
    invoice_data = {
        "customer_id": customer['id'],
        "customer_name": customer['name'],
        "invoice_title": "فاتورة اختبار خصم",
        "items": [{
            "seal_type": "RSL",
            "material_type": "NBR",
            "inner_diameter": 20.0,
            "outer_diameter": 40.0,
            "height": 10.0,
            "quantity": 5,
            "unit_price": 15.0,
            "total_price": 75.0,
            "product_type": "manufactured"
        }],
        "payment_method": "نقدي",
        "discount_type": "amount",
        "discount_value": 0.0
    }
    
    invoice_response = session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
    if invoice_response.status_code != 200:
        print(f"Failed to create invoice: {invoice_response.text}")
        return
    
    invoice = invoice_response.json()
    print(f"Created invoice: {invoice['invoice_number']}")
    print(f"Initial subtotal: {invoice.get('subtotal', 'N/A')}")
    print(f"Initial discount: {invoice.get('discount', 'N/A')}")
    print(f"Initial total_after_discount: {invoice.get('total_after_discount', 'N/A')}")
    print(f"Initial total_amount: {invoice.get('total_amount', 'N/A')}")
    
    # Update with fixed discount
    update_data = {
        "discount_type": "amount",
        "discount_value": 15.0
    }
    
    update_response = session.put(f"{BACKEND_URL}/invoices/{invoice['id']}", json=update_data)
    if update_response.status_code != 200:
        print(f"Failed to update invoice: {update_response.text}")
        return
    
    # Get updated invoice
    get_response = session.get(f"{BACKEND_URL}/invoices/{invoice['id']}")
    if get_response.status_code != 200:
        print(f"Failed to get updated invoice: {get_response.text}")
        return
    
    updated_invoice = get_response.json()
    print(f"\nAfter discount update:")
    print(f"Subtotal: {updated_invoice.get('subtotal', 'N/A')}")
    print(f"Discount type: {updated_invoice.get('discount_type', 'N/A')}")
    print(f"Discount value: {updated_invoice.get('discount_value', 'N/A')}")
    print(f"Discount: {updated_invoice.get('discount', 'N/A')}")
    print(f"Total after discount: {updated_invoice.get('total_after_discount', 'N/A')}")
    print(f"Total amount: {updated_invoice.get('total_amount', 'N/A')}")
    
    # Test percentage discount
    update_data = {
        "discount_type": "percentage",
        "discount_value": 20.0
    }
    
    update_response = session.put(f"{BACKEND_URL}/invoices/{invoice['id']}", json=update_data)
    if update_response.status_code == 200:
        get_response = session.get(f"{BACKEND_URL}/invoices/{invoice['id']}")
        if get_response.status_code == 200:
            updated_invoice = get_response.json()
            print(f"\nAfter percentage discount update:")
            print(f"Subtotal: {updated_invoice.get('subtotal', 'N/A')}")
            print(f"Discount type: {updated_invoice.get('discount_type', 'N/A')}")
            print(f"Discount value: {updated_invoice.get('discount_value', 'N/A')}")
            print(f"Discount: {updated_invoice.get('discount', 'N/A')}")
            print(f"Expected discount (20% of 75): {75 * 0.20}")
            print(f"Total after discount: {updated_invoice.get('total_after_discount', 'N/A')}")
            print(f"Total amount: {updated_invoice.get('total_amount', 'N/A')}")
    
    # Cleanup
    session.delete(f"{BACKEND_URL}/invoices/{invoice['id']}")
    session.delete(f"{BACKEND_URL}/customers/{customer['id']}")

if __name__ == "__main__":
    debug_discount_calculation()