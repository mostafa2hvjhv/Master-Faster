#!/usr/bin/env python3
"""
Treasury Reset Edge Cases Test
==============================

Additional edge case testing for the Treasury Reset functionality
to ensure complete robustness and security.

Author: Testing Agent
Date: 2025-01-27
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://retail-treasury.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TreasuryResetEdgeCaseTester:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """Make HTTP request to API"""
        url = f"{API_BASE}{endpoint}"
        
        try:
            if method.upper() == "POST":
                headers = {"Content-Type": "application/json"}
                async with self.session.post(url, json=data, params=params, headers=headers) as response:
                    return {
                        "status": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text()
                    }
            elif method.upper() == "GET":
                async with self.session.get(url, params=params) as response:
                    return {
                        "status": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text()
                    }
        except Exception as e:
            return {"status": 500, "data": {"error": str(e)}}

    async def test_case_sensitivity(self):
        """Test case sensitivity of username"""
        print("🔍 Testing case sensitivity...")
        
        test_cases = ["elsawy", "ELSAWY", "ElSawy", "eLsAwY"]
        
        for username in test_cases:
            result = await self.make_request("POST", "/treasury/reset", params={"username": username})
            
            if result["status"] == 403:
                print(f"✅ '{username}' correctly denied (case sensitive)")
            else:
                print(f"❌ '{username}' should be denied but got status {result['status']}")

    async def test_whitespace_handling(self):
        """Test username with whitespace"""
        print("\n🔍 Testing whitespace handling...")
        
        test_cases = [" Elsawy", "Elsawy ", " Elsawy ", "\tElsawy", "Elsawy\n"]
        
        for username in test_cases:
            result = await self.make_request("POST", "/treasury/reset", params={"username": username})
            
            if result["status"] == 403:
                print(f"✅ '{repr(username)}' correctly denied (whitespace)")
            else:
                print(f"❌ '{repr(username)}' should be denied but got status {result['status']}")

    async def test_special_characters(self):
        """Test username with special characters"""
        print("\n🔍 Testing special characters...")
        
        test_cases = ["Elsawy;", "Elsawy'", "Elsawy\"", "Elsawy<script>", "Elsawy--", "Elsawy/*"]
        
        for username in test_cases:
            result = await self.make_request("POST", "/treasury/reset", params={"username": username})
            
            if result["status"] == 403:
                print(f"✅ '{username}' correctly denied (special chars)")
            else:
                print(f"❌ '{username}' should be denied but got status {result['status']}")

    async def test_multiple_resets(self):
        """Test multiple consecutive resets"""
        print("\n🔍 Testing multiple consecutive resets...")
        
        # First reset
        result1 = await self.make_request("POST", "/treasury/reset", params={"username": "Elsawy"})
        if result1["status"] == 200:
            deleted_count1 = result1["data"].get("deleted_treasury_transactions", 0)
            print(f"✅ First reset: deleted {deleted_count1} transactions")
        else:
            print(f"❌ First reset failed: {result1['status']}")
            return
        
        # Second reset (should delete 0 since already empty)
        result2 = await self.make_request("POST", "/treasury/reset", params={"username": "Elsawy"})
        if result2["status"] == 200:
            deleted_count2 = result2["data"].get("deleted_treasury_transactions", 0)
            if deleted_count2 == 0:
                print(f"✅ Second reset: correctly deleted {deleted_count2} transactions (empty)")
            else:
                print(f"❌ Second reset: unexpected deletion count {deleted_count2}")
        else:
            print(f"❌ Second reset failed: {result2['status']}")

    async def test_concurrent_requests(self):
        """Test concurrent reset requests"""
        print("\n🔍 Testing concurrent requests...")
        
        # Create some test data first
        test_transaction = {
            "account_id": "cash",
            "transaction_type": "income",
            "amount": 50.0,
            "description": "Concurrent test transaction",
            "reference": "CONCURRENT-TEST"
        }
        
        await self.make_request("POST", "/treasury/transactions", test_transaction)
        
        # Send multiple concurrent requests
        tasks = []
        for i in range(3):
            task = self.make_request("POST", "/treasury/reset", params={"username": "Elsawy"})
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r["status"] == 200)
        
        if success_count >= 1:
            print(f"✅ Concurrent requests handled: {success_count} succeeded")
            
            # Check final state
            final_result = await self.make_request("GET", "/treasury/transactions")
            if final_result["status"] == 200 and len(final_result["data"]) == 0:
                print("✅ Final state: all transactions deleted")
            else:
                print(f"❌ Final state: {len(final_result['data'])} transactions remain")
        else:
            print("❌ No concurrent requests succeeded")

    async def test_empty_database_reset(self):
        """Test reset when database is already empty"""
        print("\n🔍 Testing reset on empty database...")
        
        # Ensure database is empty first
        await self.make_request("POST", "/treasury/reset", params={"username": "Elsawy"})
        
        # Now test reset on empty database
        result = await self.make_request("POST", "/treasury/reset", params={"username": "Elsawy"})
        
        if result["status"] == 200:
            deleted_count = result["data"].get("deleted_treasury_transactions", -1)
            if deleted_count == 0:
                print(f"✅ Empty database reset: correctly deleted {deleted_count} transactions")
            else:
                print(f"❌ Empty database reset: unexpected count {deleted_count}")
        else:
            print(f"❌ Empty database reset failed: {result['status']}")

    async def run_edge_case_tests(self):
        """Run all edge case tests"""
        print("🧪 Starting Treasury Reset Edge Case Tests")
        print("=" * 50)
        
        await self.test_case_sensitivity()
        await self.test_whitespace_handling()
        await self.test_special_characters()
        await self.test_multiple_resets()
        await self.test_concurrent_requests()
        await self.test_empty_database_reset()
        
        print("\n" + "=" * 50)
        print("🏁 Edge case testing completed")

async def main():
    """Main test execution function"""
    async with TreasuryResetEdgeCaseTester() as tester:
        await tester.run_edge_case_tests()

if __name__ == "__main__":
    asyncio.run(main())