#!/usr/bin/env python3
"""
Detailed Invoice Duplication Analysis
تحليل مفصل لمشكلة تكرار الفواتير

This script provides a detailed analysis of the invoice duplication issue
"""

import requests
import json
import sys
from datetime import datetime
from collections import defaultdict, Counter

# Backend URL from frontend/.env
BACKEND_URL = "https://retail-treasury.preview.emergentagent.com/api"

def analyze_invoice_duplicates():
    """Analyze invoice duplicates in detail"""
    print("🔍 DETAILED INVOICE DUPLICATION ANALYSIS")
    print("=" * 60)
    
    # Get all invoices
    response = requests.get(f"{BACKEND_URL}/invoices")
    if response.status_code != 200:
        print(f"❌ Failed to get invoices: {response.status_code}")
        return
    
    invoices = response.json()
    print(f"📊 Total invoices in database: {len(invoices)}")
    
    # Analyze by customer name and title
    print("\n🔍 ANALYZING DUPLICATES BY CUSTOMER NAME AND TITLE:")
    customer_title_groups = defaultdict(list)
    
    for invoice in invoices:
        key = f"{invoice.get('customer_name', '')}-{invoice.get('invoice_title', '')}"
        customer_title_groups[key].append(invoice)
    
    duplicates_found = False
    for key, group in customer_title_groups.items():
        if len(group) > 1:
            duplicates_found = True
            print(f"\n🚨 DUPLICATE GROUP: {key}")
            print(f"   Count: {len(group)} invoices")
            
            for invoice in group:
                print(f"   - Invoice {invoice['invoice_number']} (ID: {invoice['id']})")
                print(f"     Date: {invoice['date']}")
                print(f"     Amount: {invoice['total_amount']}")
                print(f"     Payment Method: {invoice['payment_method']}")
                print(f"     Status: {invoice['status']}")
                
                # Check if items are identical
                items = invoice.get('items', [])
                print(f"     Items: {len(items)} items")
                for i, item in enumerate(items):
                    print(f"       Item {i+1}: {item.get('seal_type', 'N/A')} - {item.get('material_type', 'N/A')} - Qty: {item.get('quantity', 0)} - Price: {item.get('total_price', 0)}")
    
    if not duplicates_found:
        print("✅ No duplicates found by customer name and title")
    
    # Analyze by invoice content (items)
    print("\n🔍 ANALYZING DUPLICATES BY INVOICE CONTENT:")
    content_groups = defaultdict(list)
    
    for invoice in invoices:
        # Create a content signature based on items
        items = invoice.get('items', [])
        content_signature = []
        for item in items:
            sig = f"{item.get('seal_type', '')}-{item.get('material_type', '')}-{item.get('inner_diameter', 0)}-{item.get('outer_diameter', 0)}-{item.get('height', 0)}-{item.get('quantity', 0)}-{item.get('unit_price', 0)}"
            content_signature.append(sig)
        
        content_key = "|".join(sorted(content_signature))
        content_groups[content_key].append(invoice)
    
    content_duplicates_found = False
    for content_key, group in content_groups.items():
        if len(group) > 1:
            content_duplicates_found = True
            print(f"\n🚨 CONTENT DUPLICATE GROUP:")
            print(f"   Content signature: {content_key}")
            print(f"   Count: {len(group)} invoices")
            
            for invoice in group:
                print(f"   - Invoice {invoice['invoice_number']} (ID: {invoice['id']})")
                print(f"     Customer: {invoice['customer_name']}")
                print(f"     Date: {invoice['date']}")
                print(f"     Amount: {invoice['total_amount']}")
    
    if not content_duplicates_found:
        print("✅ No duplicates found by invoice content")
    
    # Analyze invoice numbers
    print("\n🔍 ANALYZING INVOICE NUMBERS:")
    invoice_numbers = [inv['invoice_number'] for inv in invoices]
    number_counts = Counter(invoice_numbers)
    
    duplicate_numbers = {num: count for num, count in number_counts.items() if count > 1}
    if duplicate_numbers:
        print("🚨 DUPLICATE INVOICE NUMBERS FOUND:")
        for num, count in duplicate_numbers.items():
            print(f"   - {num}: appears {count} times")
    else:
        print("✅ All invoice numbers are unique")
    
    # Analyze creation timestamps
    print("\n🔍 ANALYZING CREATION TIMESTAMPS:")
    timestamp_groups = defaultdict(list)
    
    for invoice in invoices:
        # Group by minute to catch rapid duplications
        date_str = invoice['date'][:16]  # YYYY-MM-DDTHH:MM
        timestamp_groups[date_str].append(invoice)
    
    rapid_creation_found = False
    for timestamp, group in timestamp_groups.items():
        if len(group) > 1:
            rapid_creation_found = True
            print(f"\n⚡ RAPID CREATION DETECTED at {timestamp}:")
            print(f"   Count: {len(group)} invoices created within same minute")
            
            for invoice in group:
                print(f"   - Invoice {invoice['invoice_number']} at {invoice['date']}")
                print(f"     Customer: {invoice['customer_name']}")
                print(f"     Amount: {invoice['total_amount']}")
    
    if not rapid_creation_found:
        print("✅ No rapid creation patterns detected")

def analyze_treasury_transactions():
    """Analyze treasury transactions for duplicates"""
    print("\n" + "=" * 60)
    print("💰 TREASURY TRANSACTIONS ANALYSIS")
    print("=" * 60)
    
    response = requests.get(f"{BACKEND_URL}/treasury/transactions")
    if response.status_code != 200:
        print(f"❌ Failed to get treasury transactions: {response.status_code}")
        return
    
    transactions = response.json()
    print(f"📊 Total treasury transactions: {len(transactions)}")
    
    # Filter invoice-related transactions
    invoice_transactions = [t for t in transactions if t.get('reference', '').startswith('invoice_')]
    print(f"📊 Invoice-related transactions: {len(invoice_transactions)}")
    
    # Group by reference
    by_reference = defaultdict(list)
    for t in invoice_transactions:
        by_reference[t['reference']].append(t)
    
    # Check for duplicates
    duplicates_found = False
    for ref, trans_list in by_reference.items():
        if len(trans_list) > 1:
            # Check if they are truly duplicates (same amount, same account, same type)
            unique_transactions = defaultdict(list)
            for trans in trans_list:
                key = f"{trans.get('account_id')}-{trans.get('amount')}-{trans.get('transaction_type')}"
                unique_transactions[key].append(trans)
            
            for key, duplicate_trans in unique_transactions.items():
                if len(duplicate_trans) > 1:
                    duplicates_found = True
                    print(f"\n🚨 DUPLICATE TREASURY TRANSACTIONS:")
                    print(f"   Reference: {ref}")
                    print(f"   Transaction signature: {key}")
                    print(f"   Count: {len(duplicate_trans)}")
                    
                    for trans in duplicate_trans:
                        print(f"   - Transaction ID: {trans['id']}")
                        print(f"     Date: {trans['date']}")
                        print(f"     Description: {trans['description']}")
    
    if not duplicates_found:
        print("✅ No duplicate treasury transactions found")

def analyze_work_orders():
    """Analyze work orders for duplicate invoice entries"""
    print("\n" + "=" * 60)
    print("📋 WORK ORDERS ANALYSIS")
    print("=" * 60)
    
    response = requests.get(f"{BACKEND_URL}/work-orders")
    if response.status_code != 200:
        print(f"❌ Failed to get work orders: {response.status_code}")
        return
    
    work_orders = response.json()
    print(f"📊 Total work orders: {len(work_orders)}")
    
    duplicates_found = False
    for wo in work_orders:
        invoices = wo.get('invoices', [])
        if len(invoices) > 0:
            invoice_ids = [inv.get('id') for inv in invoices if inv.get('id')]
            unique_ids = set(invoice_ids)
            
            if len(invoice_ids) != len(unique_ids):
                duplicates_found = True
                print(f"\n🚨 DUPLICATE INVOICE ENTRIES IN WORK ORDER:")
                print(f"   Work Order: {wo.get('title', 'N/A')} (ID: {wo['id']})")
                print(f"   Total invoice entries: {len(invoice_ids)}")
                print(f"   Unique invoices: {len(unique_ids)}")
                
                # Show which invoices are duplicated
                id_counts = Counter(invoice_ids)
                for inv_id, count in id_counts.items():
                    if count > 1:
                        print(f"   - Invoice {inv_id}: appears {count} times")
    
    if not duplicates_found:
        print("✅ No duplicate invoice entries in work orders found")

def test_invoice_creation_process():
    """Test the invoice creation process to see if it creates duplicates"""
    print("\n" + "=" * 60)
    print("🧪 TESTING INVOICE CREATION PROCESS")
    print("=" * 60)
    
    # Create a test customer first
    customer_data = {
        "name": "عميل اختبار التكرار المفصل",
        "phone": "01111111111",
        "address": "عنوان اختبار"
    }
    
    response = requests.post(f"{BACKEND_URL}/customers", json=customer_data)
    if response.status_code != 200:
        print(f"❌ Failed to create test customer: {response.status_code}")
        return
    
    customer = response.json()
    print(f"✅ Created test customer: {customer['id']}")
    
    # Get initial counts
    initial_invoice_count = len(requests.get(f"{BACKEND_URL}/invoices").json())
    initial_treasury_count = len(requests.get(f"{BACKEND_URL}/treasury/transactions").json())
    
    print(f"📊 Initial counts - Invoices: {initial_invoice_count}, Treasury: {initial_treasury_count}")
    
    # Create a test invoice
    invoice_data = {
        "customer_id": customer['id'],
        "customer_name": "عميل اختبار التكرار المفصل",
        "invoice_title": "فاتورة اختبار التكرار المفصل",
        "supervisor_name": "مشرف الاختبار",
        "items": [
            {
                "seal_type": "RSL",
                "material_type": "NBR",
                "inner_diameter": 25.0,
                "outer_diameter": 35.0,
                "height": 10.0,
                "quantity": 1,
                "unit_price": 100.0,
                "total_price": 100.0,
                "product_type": "manufactured"
            }
        ],
        "payment_method": "نقدي",
        "discount_type": "amount",
        "discount_value": 0.0,
        "notes": "فاتورة اختبار التكرار المفصل"
    }
    
    print("🔄 Creating test invoice...")
    response = requests.post(f"{BACKEND_URL}/invoices", json=invoice_data)
    
    if response.status_code != 200:
        print(f"❌ Failed to create test invoice: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    created_invoice = response.json()
    print(f"✅ Created test invoice: {created_invoice['invoice_number']} (ID: {created_invoice['id']})")
    
    # Wait a moment and check final counts
    import time
    time.sleep(1)
    
    final_invoice_count = len(requests.get(f"{BACKEND_URL}/invoices").json())
    final_treasury_count = len(requests.get(f"{BACKEND_URL}/treasury/transactions").json())
    
    print(f"📊 Final counts - Invoices: {final_invoice_count}, Treasury: {final_treasury_count}")
    
    invoice_increase = final_invoice_count - initial_invoice_count
    treasury_increase = final_treasury_count - initial_treasury_count
    
    print(f"📈 Changes - Invoices: +{invoice_increase}, Treasury: +{treasury_increase}")
    
    if invoice_increase == 1:
        print("✅ Invoice creation: Normal (1 invoice created)")
    else:
        print(f"🚨 Invoice creation: ABNORMAL ({invoice_increase} invoices created, expected 1)")
    
    if treasury_increase == 1:
        print("✅ Treasury transaction: Normal (1 transaction created)")
    else:
        print(f"🚨 Treasury transaction: ABNORMAL ({treasury_increase} transactions created, expected 1)")
    
    # Cleanup
    print("🧹 Cleaning up test data...")
    requests.delete(f"{BACKEND_URL}/invoices/{created_invoice['id']}")
    requests.delete(f"{BACKEND_URL}/customers/{customer['id']}")
    print("✅ Cleanup completed")

if __name__ == "__main__":
    analyze_invoice_duplicates()
    analyze_treasury_transactions()
    analyze_work_orders()
    test_invoice_creation_process()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY OF FINDINGS")
    print("=" * 60)
    print("Based on the analysis above:")
    print("1. Check if duplicate invoices exist in the database")
    print("2. Check if treasury transactions are duplicated")
    print("3. Check if work order entries are duplicated")
    print("4. Test if the invoice creation process itself creates duplicates")
    print("=" * 60)