#!/usr/bin/env python3
"""
Focused test for the exact scenario mentioned in the review request.
Testing: NBR 20×30mm inventory with 1000 pieces → Create invoice with NBR seal 20×30×6mm, quantity 10
Expected: Should deduct (6+2)×10 = 80 pieces from inventory
"""

import requests
import json
import sys

BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

def test_exact_scenario():
    print("🎯 TESTING EXACT SCENARIO FROM REVIEW REQUEST")
    print("=" * 60)
    print("Scenario: Create NBR 20×30mm inventory with 1000 pieces")
    print("Create invoice via Sales page workflow (not direct API):")
    print("- Add manufactured product: NBR seal 20×30×6mm, quantity 10")
    print("- Do NOT use compatibility check (test basic material deduction)")
    print("Expected: Should deduct (6+2)×10 = 80 pieces from inventory")
    print("=" * 60)
    
    # Step 1: Clear and setup fresh inventory
    print("\n1. Setting up fresh NBR 20×30mm inventory...")
    try:
        # Clear existing inventory
        requests.delete(f"{BACKEND_URL}/inventory/clear-all")
        
        # Create NBR 20×30mm inventory with exactly 1000 pieces
        inventory_data = {
            "material_type": "NBR",
            "inner_diameter": 20.0,
            "outer_diameter": 30.0,
            "available_pieces": 1000,
            "min_stock_level": 10,
            "notes": "Test inventory for exact scenario"
        }
        
        response = requests.post(f"{BACKEND_URL}/inventory", json=inventory_data)
        if response.status_code == 200:
            inventory_item = response.json()
            print(f"✅ Created NBR 20×30mm inventory with 1000 pieces")
            print(f"   Inventory ID: {inventory_item['id']}")
        else:
            print(f"❌ Failed to create inventory: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception creating inventory: {e}")
        return False
    
    # Step 2: Verify initial count
    print("\n2. Verifying initial inventory count...")
    try:
        response = requests.get(f"{BACKEND_URL}/inventory")
        if response.status_code == 200:
            inventory_items = response.json()
            nbr_items = [item for item in inventory_items 
                        if item.get("material_type") == "NBR" 
                        and item.get("inner_diameter") == 20.0 
                        and item.get("outer_diameter") == 30.0]
            
            if nbr_items:
                initial_count = nbr_items[0].get("available_pieces", 0)
                print(f"✅ Initial inventory count: {initial_count} pieces")
                if initial_count != 1000:
                    print(f"❌ Expected 1000 pieces, got {initial_count}")
                    return False
            else:
                print("❌ NBR 20×30mm inventory item not found")
                return False
        else:
            print(f"❌ Failed to get inventory: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception getting inventory: {e}")
        return False
    
    # Step 3: Create customer
    print("\n3. Creating test customer...")
    try:
        customer_data = {
            "name": "عميل اختبار السيناريو المحدد",
            "phone": "01111111111",
            "address": "عنوان اختبار"
        }
        
        response = requests.post(f"{BACKEND_URL}/customers", json=customer_data)
        if response.status_code == 200:
            customer = response.json()
            customer_id = customer["id"]
            print(f"✅ Created customer: {customer['name']}")
        else:
            print(f"❌ Failed to create customer: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception creating customer: {e}")
        return False
    
    # Step 4: Create invoice with NBR seal 20×30×6mm, quantity 10
    print("\n4. Creating invoice with NBR seal 20×30×6mm × 10...")
    print("   This simulates the Sales page workflow without compatibility check")
    
    try:
        # This is the exact invoice structure that would be sent from the frontend
        invoice_data = {
            "customer_id": customer_id,
            "customer_name": "عميل اختبار السيناريو المحدد",
            "invoice_title": "فاتورة اختبار السيناريو المحدد",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR",
                    "inner_diameter": 20.0,
                    "outer_diameter": 30.0,
                    "height": 6.0,
                    "quantity": 10,
                    "unit_price": 15.0,
                    "total_price": 150.0,
                    "product_type": "manufactured",
                    # This is the key: material_details for all manufactured products
                    "material_details": {
                        "material_type": "NBR",
                        "inner_diameter": 20.0,
                        "outer_diameter": 30.0,
                        "is_finished_product": False
                    }
                }
            ],
            "payment_method": "نقدي",
            "discount_type": "amount",
            "discount_value": 0.0,
            "notes": "اختبار السيناريو المحدد - خصم المخزون"
        }
        
        print("   Sending invoice creation request...")
        response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data)
        
        if response.status_code == 200:
            invoice = response.json()
            print(f"✅ Invoice created successfully: {invoice['invoice_number']}")
            print(f"   Invoice ID: {invoice['id']}")
            
            # Print material details to verify they were sent
            for item in invoice['items']:
                if item.get('material_details'):
                    print(f"   Material details sent: {item['material_details']}")
                else:
                    print("   ⚠️  No material_details found in invoice item")
        else:
            print(f"❌ Failed to create invoice: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception creating invoice: {e}")
        return False
    
    # Step 5: Verify inventory deduction
    print("\n5. Verifying inventory deduction...")
    print("   Expected calculation: (6mm height + 2mm waste) × 10 quantity = 80 pieces deducted")
    print("   Expected final count: 1000 - 80 = 920 pieces")
    
    try:
        response = requests.get(f"{BACKEND_URL}/inventory")
        if response.status_code == 200:
            inventory_items = response.json()
            nbr_items = [item for item in inventory_items 
                        if item.get("material_type") == "NBR" 
                        and item.get("inner_diameter") == 20.0 
                        and item.get("outer_diameter") == 30.0]
            
            if nbr_items:
                final_count = nbr_items[0].get("available_pieces", 0)
                deducted_amount = 1000 - final_count
                expected_deduction = (6 + 2) * 10  # 80 pieces
                
                print(f"   Final inventory count: {final_count} pieces")
                print(f"   Actual deduction: {deducted_amount} pieces")
                print(f"   Expected deduction: {expected_deduction} pieces")
                
                if deducted_amount == expected_deduction:
                    print("✅ INVENTORY DEDUCTION IS WORKING CORRECTLY!")
                    print(f"   ✅ Correctly deducted {deducted_amount} pieces")
                    success = True
                else:
                    print("❌ INVENTORY DEDUCTION IS NOT WORKING!")
                    print(f"   ❌ Expected {expected_deduction} pieces, but deducted {deducted_amount}")
                    success = False
            else:
                print("❌ NBR 20×30mm inventory item not found after invoice")
                success = False
        else:
            print(f"❌ Failed to get inventory after invoice: {response.status_code}")
            success = False
    except Exception as e:
        print(f"❌ Exception verifying inventory: {e}")
        success = False
    
    # Step 6: Check inventory transactions
    print("\n6. Checking inventory transactions...")
    try:
        response = requests.get(f"{BACKEND_URL}/inventory-transactions")
        if response.status_code == 200:
            transactions = response.json()
            
            # Look for recent outbound transactions for NBR 20×30
            relevant_transactions = [t for t in transactions 
                                   if t.get("material_type") == "NBR" 
                                   and t.get("inner_diameter") == 20.0 
                                   and t.get("outer_diameter") == 30.0
                                   and t.get("transaction_type") == "out"]
            
            if relevant_transactions:
                latest_transaction = relevant_transactions[0]
                pieces_change = abs(latest_transaction.get("pieces_change", 0))
                reason = latest_transaction.get("reason", "")
                
                print(f"✅ Found inventory transaction:")
                print(f"   Pieces deducted: {pieces_change}")
                print(f"   Reason: {reason}")
                print(f"   Transaction type: {latest_transaction.get('transaction_type')}")
                
                if pieces_change == 80:
                    print("✅ Transaction amount is correct (80 pieces)")
                else:
                    print(f"❌ Transaction amount is incorrect (expected 80, got {pieces_change})")
            else:
                print("❌ No inventory transactions found for NBR 20×30mm")
                print("   This indicates the deduction logic is not creating transactions")
        else:
            print(f"❌ Failed to get inventory transactions: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception checking transactions: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULT")
    print("=" * 60)
    
    if success:
        print("✅ SUCCESS: Inventory deduction is working correctly!")
        print("   The user's reported issue appears to be resolved.")
        print("   Material heights are being properly deducted from inventory.")
        return True
    else:
        print("❌ FAILURE: Inventory deduction is not working!")
        print("   The user's reported issue is confirmed.")
        print("   Material heights are NOT being deducted from inventory.")
        return False

if __name__ == "__main__":
    success = test_exact_scenario()
    sys.exit(0 if success else 1)