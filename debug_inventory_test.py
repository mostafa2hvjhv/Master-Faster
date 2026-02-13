#!/usr/bin/env python3
"""
Debug test for inventory issues
"""

import requests
import json
import time

BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def test_inventory_creation():
    print("Testing inventory creation with unique specs...")
    
    # Use unique specs to avoid duplicate error
    inventory_data = {
        "material_type": "BUR",
        "inner_diameter": 28.5,
        "outer_diameter": 38.5,
        "available_pieces": 15,
        "min_stock_level": 3,
        "notes": "Debug test unique item"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/inventory", headers=HEADERS, json=inventory_data, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            item = response.json()
            item_id = item.get('id')
            print(f"✅ Created inventory item: {item_id}")
            
            # Test raw material creation
            print("\nTesting raw material creation...")
            raw_material_data = {
                "material_type": "BUR",
                "inner_diameter": 28.5,
                "outer_diameter": 38.5,
                "height": 10.0,
                "pieces_count": 3,
                "unit_code": "BUR-28.5-38.5-DEBUG",
                "cost_per_mm": 0.7
            }
            
            response = requests.post(f"{BASE_URL}/raw-materials", headers=HEADERS, json=raw_material_data, timeout=15)
            print(f"Raw Material Status: {response.status_code}")
            print(f"Raw Material Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Raw material created successfully")
                
                # Check inventory deduction
                time.sleep(2)
                response = requests.get(f"{BASE_URL}/inventory/{item_id}", headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    updated_item = response.json()
                    remaining = updated_item.get('available_pieces', 0)
                    print(f"Remaining pieces after deduction: {remaining} (expected: 12)")
                    
                    if remaining == 12:
                        print("✅ Inventory deduction working correctly")
                    else:
                        print("❌ Inventory deduction not working")
            
            # Test deletion
            print(f"\nTesting deletion of item {item_id}...")
            response = requests.delete(f"{BASE_URL}/inventory/{item_id}", headers=HEADERS, timeout=10)
            print(f"Delete Status: {response.status_code}")
            print(f"Delete Response: {response.text}")
            
            # Verify deletion
            time.sleep(1)
            response = requests.get(f"{BASE_URL}/inventory/{item_id}", headers=HEADERS, timeout=10)
            print(f"Verification Status: {response.status_code}")
            if response.status_code == 404:
                print("✅ Item deleted successfully")
            else:
                print("❌ Item not deleted from database")
                print(f"Response: {response.text}")
        
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_inventory_creation()