#!/usr/bin/env python3
"""
Treasury Historical Analysis
===========================

This script analyzes existing treasury transactions to find:
1. Duplicate transactions with same invoice reference
2. Transactions with same amount and similar descriptions
3. Non-deferred invoices that have deferred account transactions
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

class TreasuryAnalyzer:
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
                
            # Get balances
            async with self.session.get(f"{API_BASE}/treasury/balances") as response:
                balances = await response.json() if response.status == 200 else {}
                
            return transactions, invoices, balances
            
        except Exception as e:
            print(f"❌ Error getting data: {e}")
            return [], [], {}
            
    def analyze_duplicate_references(self, transactions):
        """Find transactions with duplicate invoice references"""
        print("\n🔍 ANALYZING DUPLICATE INVOICE REFERENCES")
        print("=" * 50)
        
        # Group transactions by reference
        reference_groups = defaultdict(list)
        for transaction in transactions:
            reference = transaction.get('reference', '')
            if reference.startswith('invoice_'):
                reference_groups[reference].append(transaction)
                
        # Find duplicates
        duplicates_found = 0
        for reference, trans_list in reference_groups.items():
            if len(trans_list) > 1:
                duplicates_found += 1
                print(f"\n🚨 DUPLICATE REFERENCE: {reference}")
                print(f"   Found {len(trans_list)} transactions:")
                
                for i, trans in enumerate(trans_list, 1):
                    print(f"   Transaction {i}:")
                    print(f"     - Account: {trans.get('account_id')}")
                    print(f"     - Type: {trans.get('transaction_type')}")
                    print(f"     - Amount: {trans.get('amount')} ج.م")
                    print(f"     - Description: {trans.get('description')}")
                    print(f"     - Date: {trans.get('date')}")
                    
        if duplicates_found == 0:
            print("✅ No duplicate invoice references found")
        else:
            print(f"\n🚨 TOTAL DUPLICATES: {duplicates_found} invoice references have multiple transactions")
            
        return duplicates_found
        
    def analyze_similar_transactions(self, transactions):
        """Find transactions with same amount and similar descriptions"""
        print("\n🔍 ANALYZING SIMILAR TRANSACTIONS")
        print("=" * 50)
        
        # Group by amount and look for similar descriptions
        amount_groups = defaultdict(list)
        for transaction in transactions:
            amount = transaction.get('amount', 0)
            if amount > 0:  # Only positive amounts (income)
                amount_groups[amount].append(transaction)
                
        suspicious_groups = 0
        for amount, trans_list in amount_groups.items():
            if len(trans_list) > 1:
                # Check if descriptions contain same invoice number
                descriptions = [t.get('description', '') for t in trans_list]
                invoice_numbers = []
                
                for desc in descriptions:
                    if 'فاتورة' in desc and 'INV-' in desc:
                        # Extract invoice number
                        parts = desc.split()
                        for part in parts:
                            if part.startswith('INV-'):
                                invoice_numbers.append(part)
                                break
                                
                # Check for same invoice number with same amount
                invoice_counter = Counter(invoice_numbers)
                for inv_num, count in invoice_counter.items():
                    if count > 1:
                        suspicious_groups += 1
                        print(f"\n🚨 SUSPICIOUS: Invoice {inv_num} has {count} transactions with amount {amount} ج.م")
                        
                        # Show the suspicious transactions
                        for trans in trans_list:
                            if inv_num in trans.get('description', ''):
                                print(f"   - Account: {trans.get('account_id')}")
                                print(f"   - Type: {trans.get('transaction_type')}")
                                print(f"   - Description: {trans.get('description')}")
                                print(f"   - Date: {trans.get('date')}")
                                
        if suspicious_groups == 0:
            print("✅ No suspicious similar transactions found")
        else:
            print(f"\n🚨 TOTAL SUSPICIOUS: {suspicious_groups} invoice numbers have multiple transactions with same amount")
            
        return suspicious_groups
        
    def analyze_deferred_contamination(self, transactions, invoices):
        """Check for non-deferred invoices affecting deferred account"""
        print("\n🔍 ANALYZING DEFERRED ACCOUNT CONTAMINATION")
        print("=" * 50)
        
        # Create invoice lookup
        invoice_lookup = {}
        for invoice in invoices:
            invoice_lookup[invoice['id']] = invoice
            
        # Find deferred account transactions
        deferred_transactions = [t for t in transactions if t.get('account_id') == 'deferred']
        
        contamination_cases = 0
        for trans in deferred_transactions:
            reference = trans.get('reference', '')
            if reference.startswith('invoice_'):
                # Extract invoice ID
                invoice_id = reference.replace('invoice_', '').split('_')[0]
                
                # Find the invoice
                invoice = invoice_lookup.get(invoice_id)
                if invoice:
                    payment_method = invoice.get('payment_method', '')
                    if payment_method != 'آجل':
                        contamination_cases += 1
                        print(f"\n🚨 CONTAMINATION: Non-deferred invoice affects deferred account")
                        print(f"   Invoice: {invoice.get('invoice_number')} ({payment_method})")
                        print(f"   Transaction Type: {trans.get('transaction_type')}")
                        print(f"   Amount: {trans.get('amount')} ج.م")
                        print(f"   Description: {trans.get('description')}")
                        
        if contamination_cases == 0:
            print("✅ No deferred account contamination found")
        else:
            print(f"\n🚨 TOTAL CONTAMINATION: {contamination_cases} non-deferred invoices affected deferred account")
            
        return contamination_cases
        
    def analyze_balance_discrepancies(self, transactions, invoices, balances):
        """Analyze if balances match expected values"""
        print("\n🔍 ANALYZING BALANCE DISCREPANCIES")
        print("=" * 50)
        
        # Calculate expected balances from transactions
        calculated_balances = {
            'cash': 0,
            'vodafone_elsawy': 0,
            'vodafone_wael': 0,
            'deferred': 0,
            'instapay': 0,
            'yad_elsawy': 0
        }
        
        # Add up all transactions
        for trans in transactions:
            account_id = trans.get('account_id')
            if account_id in calculated_balances:
                amount = trans.get('amount', 0)
                trans_type = trans.get('transaction_type')
                
                if trans_type in ['income', 'transfer_in']:
                    calculated_balances[account_id] += amount
                elif trans_type in ['expense', 'transfer_out']:
                    calculated_balances[account_id] -= amount
                    
        # Add deferred invoices directly
        for invoice in invoices:
            if invoice.get('payment_method') == 'آجل':
                calculated_balances['deferred'] += invoice.get('total_amount', 0)
                
        # Subtract expenses from cash (simplified)
        # Note: This is a simplified calculation, actual system may be more complex
        
        print("Balance Comparison:")
        discrepancies = 0
        for account in calculated_balances:
            calculated = calculated_balances[account]
            actual = balances.get(account, 0)
            difference = actual - calculated
            
            print(f"   {account}:")
            print(f"     Calculated: {calculated:.2f} ج.م")
            print(f"     Actual: {actual:.2f} ج.م")
            
            if abs(difference) > 0.01:  # Allow for small rounding differences
                print(f"     🚨 DISCREPANCY: {difference:+.2f} ج.م")
                discrepancies += 1
            else:
                print(f"     ✅ Match")
                
        return discrepancies
        
    async def run_analysis(self):
        """Run complete treasury analysis"""
        print("🔍 TREASURY HISTORICAL ANALYSIS")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Get all data
            print("📊 Loading data...")
            transactions, invoices, balances = await self.get_all_data()
            
            print(f"   Loaded {len(transactions)} treasury transactions")
            print(f"   Loaded {len(invoices)} invoices")
            print(f"   Loaded balances for {len(balances)} accounts")
            
            # Run analyses
            duplicate_refs = self.analyze_duplicate_references(transactions)
            similar_trans = self.analyze_similar_transactions(transactions)
            contamination = self.analyze_deferred_contamination(transactions, invoices)
            discrepancies = self.analyze_balance_discrepancies(transactions, invoices, balances)
            
            # Final summary
            print("\n" + "=" * 60)
            print("📋 ANALYSIS SUMMARY")
            print("=" * 60)
            
            total_issues = duplicate_refs + similar_trans + contamination + discrepancies
            
            print(f"🔍 Issues Found:")
            print(f"   Duplicate References: {duplicate_refs}")
            print(f"   Similar Transactions: {similar_trans}")
            print(f"   Deferred Contamination: {contamination}")
            print(f"   Balance Discrepancies: {discrepancies}")
            print(f"   TOTAL ISSUES: {total_issues}")
            
            if total_issues == 0:
                print(f"\n🎉 TREASURY SYSTEM APPEARS HEALTHY")
                print(f"   No historical issues detected")
            else:
                print(f"\n⚠️  TREASURY ISSUES DETECTED")
                print(f"   {total_issues} issues found in historical data")
                print(f"   User's report may be based on historical problems")
                
        finally:
            await self.cleanup_session()

async def main():
    """Main analysis execution"""
    analyzer = TreasuryAnalyzer()
    await analyzer.run_analysis()

if __name__ == "__main__":
    asyncio.run(main())