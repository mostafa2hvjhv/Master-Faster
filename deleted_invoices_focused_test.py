#!/usr/bin/env python3
"""
Focused test for deleted invoices API to investigate the issue
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def test_deleted_invoices_api():
    print("🔍 Testing Deleted Invoices API in detail...")
    
    # Test 1: Create a test invoice first
    print("\n1. Creating test invoice...")
    invoice_data = {
        "customer_name": "عميل اختبار حذف مفصل",
        "invoice_title": "فاتورة اختبار حذف مفصل",
        "items": [
            {
                "seal_type": "RSL",
                "material_type": "NBR",
                "inner_diameter": 20.0,
                "outer_diameter": 30.0,
                "height": 6.0,
                "quantity": 2,
                "unit_price": 8.0,
                "total_price": 16.0,
                "product_type": "manufactured"
            }
        ],
        "payment_method": "نقدي"
    }
    
    response = requests.post(f"{BASE_URL}/invoices", headers=HEADERS, json=invoice_data)
    if response.status_code == 200:
        invoice = response.json()
        invoice_id = invoice.get("id")
        print(f"✅ Created invoice: {invoice.get('invoice_number')} (ID: {invoice_id})")
    else:
        print(f"❌ Failed to create invoice: {response.status_code}")
        return
    
    # Test 2: Cancel the invoice (move to deleted_invoices)
    print("\n2. Cancelling invoice...")
    response = requests.delete(f"{BASE_URL}/invoices/{invoice_id}/cancel", params={"username": "detailed_test"})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Cancelled invoice: {result.get('message')}")
    else:
        print(f"❌ Failed to cancel invoice: {response.status_code}")
        if response.text:
            print(f"Error: {response.text}")
        return
    
    # Test 3: Get deleted invoices (this is where the issue might be)
    print("\n3. Getting deleted invoices...")
    try:
        response = requests.get(f"{BASE_URL}/deleted-invoices", headers=HEADERS, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            deleted_invoices = response.json()
            print(f"✅ Retrieved {len(deleted_invoices)} deleted invoices")
            
            if deleted_invoices:
                # Check the structure of the first deleted invoice
                first_invoice = deleted_invoices[0]
                print(f"First deleted invoice keys: {list(first_invoice.keys())}")
                
                # Check for problematic fields
                problematic_fields = []
                for key, value in first_invoice.items():
                    if str(type(value)) == "<class 'bson.objectid.ObjectId'>":
                        problematic_fields.append(key)
                
                if problematic_fields:
                    print(f"⚠️ Found ObjectId fields: {problematic_fields}")
                else:
                    print("✅ No ObjectId serialization issues found")
            else:
                print("ℹ️ No deleted invoices found")
                
        elif response.status_code == 500:
            print(f"❌ Server error: {response.text}")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    # Test 4: Try to restore the invoice
    print("\n4. Restoring deleted invoice...")
    response = requests.post(f"{BASE_URL}/deleted-invoices/{invoice_id}/restore", params={"username": "detailed_test"})
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Restored invoice: {result.get('message')}")
    else:
        print(f"❌ Failed to restore invoice: {response.status_code}")
        if response.text:
            print(f"Error: {response.text}")
    
    # Test 5: Clean up - cancel again and permanently delete
    print("\n5. Final cleanup...")
    # Cancel again
    requests.delete(f"{BASE_URL}/invoices/{invoice_id}/cancel", params={"username": "cleanup"})
    # Permanently delete
    response = requests.delete(f"{BASE_URL}/deleted-invoices/{invoice_id}")
    if response.status_code == 200:
        print("✅ Cleanup completed")
    else:
        print(f"⚠️ Cleanup issue: {response.status_code}")

if __name__ == "__main__":
    test_deleted_invoices_api()