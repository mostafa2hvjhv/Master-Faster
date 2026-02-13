#!/usr/bin/env python3
"""
Detailed Duplicate Investigation
===============================

This script provides detailed analysis of the duplicate transaction patterns found.
"""

import asyncio
import aiohttp
import json
from collections import defaultdict, Counter
from datetime import datetime

# Get backend URL from frontend env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=')[1].strip()
            break

API_BASE = f"{BACKEND_URL}/api"

class DetailedInvestigator:
    def __init__(self):
        self.session = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def get_all_data(self):
        """Get all relevant data"""
        try:
            # Get treasury transactions
            async with self.session.get(f"{API_BASE}/treasury/transactions") as response:
                transactions = await response.json() if response.status == 200 else []
                
            # Get invoices
            async with self.session.get(f"{API_BASE}/invoices") as response:
                invoices = await response.json() if response.status == 200 else []
                
            return transactions, invoices
            
        except Exception as e:
            print(f"❌ Error getting data: {e}")
            return [], []
            
    def analyze_duplicate_patterns(self, transactions, invoices):
        """Analyze the patterns in duplicate transactions"""
        print("🔍 DETAILED DUPLICATE PATTERN ANALYSIS")
        print("=" * 60)
        
        # Create invoice lookup
        invoice_lookup = {}
        for invoice in invoices:
            invoice_lookup[invoice['invoice_number']] = invoice
            
        # Group transactions by invoice number mentioned in description
        invoice_transactions = defaultdict(list)
        
        for transaction in transactions:
            description = transaction.get('description', '')
            if 'فاتورة' in description and 'INV-' in description:
                # Extract invoice number
                parts = description.split()
                for part in parts:
                    if part.startswith('INV-'):
                        invoice_num = part
                        invoice_transactions[invoice_num].append(transaction)
                        break
                        
        # Analyze each invoice with multiple transactions
        duplicate_cases = []
        for invoice_num, trans_list in invoice_transactions.items():
            if len(trans_list) > 1:
                # Group by amount to find exact duplicates
                amount_groups = defaultdict(list)
                for trans in trans_list:
                    amount = trans.get('amount', 0)
                    amount_groups[amount].append(trans)
                    
                for amount, same_amount_trans in amount_groups.items():
                    if len(same_amount_trans) > 1:
                        duplicate_cases.append({
                            'invoice_number': invoice_num,
                            'amount': amount,
                            'transactions': same_amount_trans,
                            'count': len(same_amount_trans)
                        })
                        
        # Sort by invoice number for better readability
        duplicate_cases.sort(key=lambda x: x['invoice_number'])
        
        print(f"Found {len(duplicate_cases)} duplicate transaction cases:")
        print()
        
        # Analyze patterns
        patterns = {
            'invoice_creation_and_payment': 0,
            'multiple_invoice_creations': 0,
            'different_accounts_same_amount': 0,
            'same_account_same_amount': 0
        }
        
        for case in duplicate_cases:
            invoice_num = case['invoice_number']
            amount = case['amount']
            transactions = case['transactions']
            
            print(f"📋 INVOICE {invoice_num} - Amount: {amount} ج.م ({case['count']} transactions)")
            
            # Get the actual invoice data
            invoice_data = invoice_lookup.get(invoice_num)
            if invoice_data:
                print(f"   Invoice Payment Method: {invoice_data.get('payment_method', 'Unknown')}")
                print(f"   Invoice Total: {invoice_data.get('total_amount', 'Unknown')} ج.م")
                print(f"   Invoice Date: {invoice_data.get('date', 'Unknown')}")
            
            # Analyze transaction types and accounts
            accounts = []
            types = []
            descriptions = []
            dates = []
            
            for i, trans in enumerate(transactions, 1):
                account = trans.get('account_id', 'Unknown')
                trans_type = trans.get('transaction_type', 'Unknown')
                desc = trans.get('description', 'Unknown')
                date = trans.get('date', 'Unknown')
                
                accounts.append(account)
                types.append(trans_type)
                descriptions.append(desc)
                dates.append(date)
                
                print(f"   Transaction {i}:")
                print(f"     Account: {account}")
                print(f"     Type: {trans_type}")
                print(f"     Description: {desc}")
                print(f"     Date: {date}")
                
            # Classify the pattern
            unique_accounts = set(accounts)
            unique_types = set(types)
            
            # Check if it's invoice creation + payment
            has_invoice_creation = any('فاتورة' in desc and 'دفع' not in desc for desc in descriptions)
            has_payment = any('دفع فاتورة' in desc for desc in descriptions)
            
            if has_invoice_creation and has_payment:
                patterns['invoice_creation_and_payment'] += 1
                print(f"   🔍 PATTERN: Invoice creation + Payment (EXPECTED)")
            elif len(unique_accounts) == 1 and len(unique_types) == 1:
                patterns['same_account_same_amount'] += 1
                print(f"   🚨 PATTERN: Same account, same type, same amount (DUPLICATE!)")
            elif len(unique_accounts) > 1 and all(t == 'income' for t in types):
                patterns['different_accounts_same_amount'] += 1
                print(f"   🚨 PATTERN: Different accounts, same amount (SUSPICIOUS!)")
            else:
                patterns['multiple_invoice_creations'] += 1
                print(f"   🚨 PATTERN: Multiple invoice creations (DUPLICATE!)")
                
            print()
            
        # Summary of patterns
        print("📊 PATTERN SUMMARY:")
        print("=" * 40)
        total_cases = len(duplicate_cases)
        
        for pattern_name, count in patterns.items():
            percentage = (count / total_cases * 100) if total_cases > 0 else 0
            print(f"{pattern_name.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
            
        # Identify the most problematic cases
        print("\n🚨 MOST PROBLEMATIC CASES:")
        print("=" * 40)
        
        problematic = []
        for case in duplicate_cases:
            transactions = case['transactions']
            accounts = [t.get('account_id') for t in transactions]
            types = [t.get('transaction_type') for t in transactions]
            descriptions = [t.get('description') for t in transactions]
            
            # Same account, same type = clear duplicate
            if len(set(accounts)) == 1 and len(set(types)) == 1:
                # Check if it's not invoice + payment
                has_payment = any('دفع فاتورة' in desc for desc in descriptions)
                has_invoice = any('فاتورة' in desc and 'دفع' not in desc for desc in descriptions)
                
                if not (has_payment and has_invoice):
                    problematic.append(case)
                    
        for case in problematic:
            print(f"   {case['invoice_number']}: {case['count']} identical transactions of {case['amount']} ج.م")
            
        return duplicate_cases, patterns
        
    async def run_investigation(self):
        """Run detailed investigation"""
        print("🕵️ DETAILED DUPLICATE TRANSACTION INVESTIGATION")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Get all data
            print("📊 Loading data...")
            transactions, invoices = await self.get_all_data()
            
            print(f"   Loaded {len(transactions)} treasury transactions")
            print(f"   Loaded {len(invoices)} invoices")
            print()
            
            # Run detailed analysis
            duplicate_cases, patterns = self.analyze_duplicate_patterns(transactions, invoices)
            
            # Final conclusion
            print("🎯 INVESTIGATION CONCLUSION:")
            print("=" * 40)
            
            true_duplicates = patterns.get('same_account_same_amount', 0) + patterns.get('multiple_invoice_creations', 0)
            expected_pairs = patterns.get('invoice_creation_and_payment', 0)
            
            print(f"Total duplicate cases found: {len(duplicate_cases)}")
            print(f"Expected invoice+payment pairs: {expected_pairs}")
            print(f"True duplicate problems: {true_duplicates}")
            print(f"Suspicious different account cases: {patterns.get('different_accounts_same_amount', 0)}")
            
            if true_duplicates > 0:
                print(f"\n🚨 USER REPORT CONFIRMED!")
                print(f"   {true_duplicates} cases of true duplicate transactions found")
                print(f"   These are causing the treasury balance issues reported")
            else:
                print(f"\n✅ Most duplicates appear to be legitimate invoice+payment pairs")
                print(f"   However, some suspicious patterns detected")
                
        finally:
            await self.cleanup_session()

async def main():
    """Main investigation execution"""
    investigator = DetailedInvestigator()
    await investigator.run_investigation()

if __name__ == "__main__":
    asyncio.run(main())