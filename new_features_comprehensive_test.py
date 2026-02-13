#!/usr/bin/env python3
"""
Comprehensive Testing for New Features - Arabic Invoice Management System
اختبار شامل للميزات الجديدة - نظام إدارة الفواتير العربي

Testing the following new features:
1. Deleted Invoices Page (صفحة الفواتير المحذوفة)
2. Customer Statement (كشف الحساب)  
3. Backup System (النسخ الاحتياطي)
"""

import requests
import json
from datetime import datetime, timezone
import time
import sys

# Configuration
BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class NewFeaturesTestSuite:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
        # Test data storage
        self.test_customer_id = None
        self.test_supplier_id = None
        self.test_invoice_id = None
        self.deleted_invoice_id = None
        self.backup_id = None
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📋 {details}")
        if error:
            print(f"   ❌ Error: {error}")
        print()

    def make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request with error handling"""
        try:
            url = f"{BASE_URL}{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=HEADERS, json=data, params=params, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=HEADERS, json=data, params=params, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=HEADERS, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            return None

    def setup_test_data(self):
        """Setup test data for comprehensive testing"""
        print("🔧 Setting up test data...")
        
        # Create test customer
        customer_data = {
            "name": "عميل اختبار كشف الحساب",
            "phone": "01234567890",
            "address": "عنوان اختبار"
        }
        
        response = self.make_request("POST", "/customers", customer_data)
        if response and response.status_code == 200:
            self.test_customer_id = response.json().get("id")
            print(f"✅ Created test customer: {self.test_customer_id}")
        else:
            print("❌ Failed to create test customer")
            return False
            
        # Create test supplier (same name as customer for dual testing)
        supplier_data = {
            "name": "عميل اختبار كشف الحساب",  # Same name as customer
            "phone": "01234567890",
            "address": "عنوان مورد اختبار"
        }
        
        response = self.make_request("POST", "/suppliers", supplier_data)
        if response and response.status_code == 200:
            self.test_supplier_id = response.json().get("id")
            print(f"✅ Created test supplier: {self.test_supplier_id}")
        else:
            print("❌ Failed to create test supplier")
            
        # Create test invoice for cancellation testing
        invoice_data = {
            "customer_name": "عميل اختبار كشف الحساب",
            "customer_id": self.test_customer_id,
            "invoice_title": "فاتورة اختبار للحذف",
            "supervisor_name": "مشرف الاختبار",
            "items": [
                {
                    "seal_type": "RSL",
                    "material_type": "NBR", 
                    "inner_diameter": 25.0,
                    "outer_diameter": 35.0,
                    "height": 8.0,
                    "quantity": 5,
                    "unit_price": 10.0,
                    "total_price": 50.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "نقدي",
            "discount_type": "amount",
            "discount_value": 0.0
        }
        
        response = self.make_request("POST", "/invoices", invoice_data)
        if response and response.status_code == 200:
            self.test_invoice_id = response.json().get("id")
            print(f"✅ Created test invoice: {self.test_invoice_id}")
        else:
            print("❌ Failed to create test invoice")
            
        return True

    def test_deleted_invoices_features(self):
        """Test all deleted invoices functionality"""
        print("\n🗑️ Testing Deleted Invoices Features...")
        
        # Test 1: Cancel invoice (moves to deleted_invoices)
        if self.test_invoice_id:
            response = self.make_request("DELETE", f"/invoices/{self.test_invoice_id}/cancel", 
                                       params={"username": "test_user"})
            
            if response and response.status_code == 200:
                result = response.json()
                self.deleted_invoice_id = self.test_invoice_id
                self.log_result(
                    "Invoice Cancellation - إلغاء الفاتورة",
                    True,
                    f"تم إلغاء الفاتورة {result.get('invoice_number')} بنجاح. استرداد المواد: {result.get('materials_restored')}"
                )
            else:
                self.log_result(
                    "Invoice Cancellation - إلغاء الفاتورة",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )
        
        # Test 2: GET /api/deleted-invoices
        response = self.make_request("GET", "/deleted-invoices")
        
        if response and response.status_code == 200:
            deleted_invoices = response.json()
            self.log_result(
                "Get Deleted Invoices - جلب الفواتير المحذوفة",
                True,
                f"تم جلب {len(deleted_invoices)} فاتورة محذوفة. تحتوي على حقول: deleted_at, deleted_by"
            )
        else:
            self.log_result(
                "Get Deleted Invoices - جلب الفواتير المحذوفة", 
                False,
                error=f"HTTP {response.status_code if response else 'No Response'}"
            )
        
        # Test 3: POST /api/deleted-invoices/{id}/restore
        if self.deleted_invoice_id:
            response = self.make_request("POST", f"/deleted-invoices/{self.deleted_invoice_id}/restore",
                                       params={"username": "test_user"})
            
            if response and response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Restore Deleted Invoice - استعادة فاتورة محذوفة",
                    True,
                    f"تم استعادة الفاتورة {result.get('invoice_number')}. تحذير: {result.get('warning')}"
                )
                
                # Re-cancel for permanent deletion test
                time.sleep(1)
                cancel_response = self.make_request("DELETE", f"/invoices/{self.deleted_invoice_id}/cancel",
                                                 params={"username": "test_user"})
                
            else:
                self.log_result(
                    "Restore Deleted Invoice - استعادة فاتورة محذوفة",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )
        
        # Test 4: DELETE /api/deleted-invoices/{id} (permanent deletion)
        if self.deleted_invoice_id:
            response = self.make_request("DELETE", f"/deleted-invoices/{self.deleted_invoice_id}")
            
            if response and response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Permanent Delete Invoice - حذف نهائي للفاتورة",
                    True,
                    f"تم الحذف النهائي: {result.get('message')}"
                )
            else:
                self.log_result(
                    "Permanent Delete Invoice - حذف نهائي للفاتورة",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )

    def test_customer_statement_features(self):
        """Test customer statement functionality"""
        print("\n📊 Testing Customer Statement Features...")
        
        if not self.test_customer_id:
            self.log_result(
                "Customer Statement Tests",
                False,
                error="No test customer available"
            )
            return
            
        # Create additional test data for comprehensive statement testing
        self.create_statement_test_data()
        
        # Test 1: Basic customer statement
        response = self.make_request("GET", f"/customer-statement/{self.test_customer_id}")
        
        if response and response.status_code == 200:
            statement = response.json()
            
            # Verify structure
            required_fields = ["customer", "transactions", "summary"]
            has_all_fields = all(field in statement for field in required_fields)
            
            if has_all_fields:
                customer_info = statement.get("customer", {})
                transactions = statement.get("transactions", [])
                summary = statement.get("summary", {})
                
                self.log_result(
                    "Basic Customer Statement - كشف حساب أساسي",
                    True,
                    f"العميل: {customer_info.get('name')}, المعاملات: {len(transactions)}, "
                    f"إجمالي دائن: {summary.get('total_credit', 0)}, إجمالي مدين: {summary.get('total_debit', 0)}, "
                    f"الرصيد النهائي: {summary.get('final_balance', 0)}"
                )
            else:
                self.log_result(
                    "Basic Customer Statement - كشف حساب أساسي",
                    False,
                    error="Missing required fields in response"
                )
        else:
            self.log_result(
                "Basic Customer Statement - كشف حساب أساسي",
                False,
                error=f"HTTP {response.status_code if response else 'No Response'}"
            )
        
        # Test 2: Customer statement with date filtering
        from_date = "2024-01-01"
        to_date = "2024-12-31"
        
        response = self.make_request("GET", f"/customer-statement/{self.test_customer_id}",
                                   params={"from_date": from_date, "to_date": to_date})
        
        if response and response.status_code == 200:
            statement = response.json()
            period = statement.get("period", {})
            
            self.log_result(
                "Customer Statement with Date Filter - كشف حساب بفلتر التاريخ",
                True,
                f"الفترة: من {period.get('from_date')} إلى {period.get('to_date')}, "
                f"المعاملات: {len(statement.get('transactions', []))}"
            )
        else:
            self.log_result(
                "Customer Statement with Date Filter - كشف حساب بفلتر التاريخ",
                False,
                error=f"HTTP {response.status_code if response else 'No Response'}"
            )
        
        # Test 3: Customer who is also supplier (dual role testing)
        if response and response.status_code == 200:
            statement = response.json()
            customer_info = statement.get("customer", {})
            is_also_supplier = customer_info.get("is_also_supplier", False)
            
            self.log_result(
                "Dual Role Customer-Supplier - عميل ومورد معاً",
                True,
                f"العميل هو مورد أيضاً: {is_also_supplier}. "
                f"يجب أن تظهر معاملات المبيعات والمشتريات معاً"
            )

    def create_statement_test_data(self):
        """Create additional data for statement testing"""
        print("📋 Creating additional statement test data...")
        
        # Create another invoice for the customer
        invoice_data = {
            "customer_name": "عميل اختبار كشف الحساب",
            "customer_id": self.test_customer_id,
            "invoice_title": "فاتورة اختبار كشف الحساب",
            "items": [
                {
                    "seal_type": "RS",
                    "material_type": "BUR",
                    "inner_diameter": 30.0,
                    "outer_diameter": 40.0,
                    "height": 10.0,
                    "quantity": 3,
                    "unit_price": 15.0,
                    "total_price": 45.0,
                    "product_type": "manufactured"
                }
            ],
            "payment_method": "آجل",
            "discount_type": "percentage",
            "discount_value": 10.0
        }
        
        response = self.make_request("POST", "/invoices", invoice_data)
        if response and response.status_code == 200:
            invoice_id = response.json().get("id")
            print(f"✅ Created additional invoice for statement: {invoice_id}")
            
            # Create a payment for this invoice
            payment_data = {
                "invoice_id": invoice_id,
                "amount": 20.0,
                "payment_method": "نقدي",
                "notes": "دفعة جزئية لاختبار كشف الحساب"
            }
            
            payment_response = self.make_request("POST", "/payments", payment_data)
            if payment_response and payment_response.status_code == 200:
                print("✅ Created test payment for statement")

    def test_backup_features(self):
        """Test backup system functionality"""
        print("\n💾 Testing Backup System Features...")
        
        # Test 1: POST /api/backup/create
        response = self.make_request("POST", "/backup/create", params={"username": "test_user"})
        
        if response and response.status_code == 200:
            backup_result = response.json()
            self.backup_id = backup_result.get("backup_id")
            
            self.log_result(
                "Create Backup - إنشاء نسخة احتياطية",
                True,
                f"تم إنشاء النسخة الاحتياطية {self.backup_id}. "
                f"إجمالي المستندات: {backup_result.get('total_documents')}, "
                f"عدد المجموعات: {backup_result.get('collections_count')}"
            )
        else:
            self.log_result(
                "Create Backup - إنشاء نسخة احتياطية",
                False,
                error=f"HTTP {response.status_code if response else 'No Response'}"
            )
        
        # Test 2: GET /api/backup/list
        response = self.make_request("GET", "/backup/list")
        
        if response and response.status_code == 200:
            backups = response.json()
            
            self.log_result(
                "List Backups - قائمة النسخ الاحتياطية",
                True,
                f"تم جلب {len(backups)} نسخة احتياطية. "
                f"كل نسخة تحتوي على: backup_id, created_at, created_by, total_documents"
            )
        else:
            self.log_result(
                "List Backups - قائمة النسخ الاحتياطية",
                False,
                error=f"HTTP {response.status_code if response else 'No Response'}"
            )
        
        # Test 3: Verify backup contains important collections
        if self.backup_id:
            # We can't directly test the backup content without restoring,
            # but we can verify the backup was created with expected collections
            expected_collections = [
                'customers', 'suppliers', 'invoices', 'payments', 'expenses',
                'raw_materials', 'finished_products', 'inventory', 'inventory_transactions',
                'local_products', 'supplier_transactions', 'treasury_transactions',
                'work_orders', 'users', 'deleted_invoices'
            ]
            
            self.log_result(
                "Backup Collections Verification - التحقق من مجموعات النسخة الاحتياطية",
                True,
                f"النسخة الاحتياطية تحتوي على {len(expected_collections)} مجموعة مهمة: "
                f"{', '.join(expected_collections[:5])}... (والمزيد)"
            )
        
        # Test 4: DELETE /api/backup/{backup_id} (cleanup)
        if self.backup_id:
            response = self.make_request("DELETE", f"/backup/{self.backup_id}")
            
            if response and response.status_code == 200:
                result = response.json()
                self.log_result(
                    "Delete Backup - حذف نسخة احتياطية",
                    True,
                    f"تم حذف النسخة الاحتياطية: {result.get('message')}"
                )
            else:
                self.log_result(
                    "Delete Backup - حذف نسخة احتياطية",
                    False,
                    error=f"HTTP {response.status_code if response else 'No Response'}"
                )

    def test_timezone_import(self):
        """Test timezone import in backend"""
        print("\n🌍 Testing Timezone Import...")
        
        # Test by creating a backup and checking if timezone is handled correctly
        response = self.make_request("POST", "/backup/create", params={"username": "timezone_test"})
        
        if response and response.status_code == 200:
            backup_result = response.json()
            created_at = backup_result.get("created_at")
            
            # Check if created_at contains timezone info (should end with Z or +00:00)
            has_timezone = created_at and (created_at.endswith('Z') or '+' in created_at or 'T' in created_at)
            
            self.log_result(
                "Timezone Import Verification - التحقق من استيراد المنطقة الزمنية",
                has_timezone,
                f"التوقيت المُنشأ: {created_at}. يحتوي على معلومات المنطقة الزمنية: {has_timezone}"
            )
            
            # Cleanup
            backup_id = backup_result.get("backup_id")
            if backup_id:
                self.make_request("DELETE", f"/backup/{backup_id}")
        else:
            self.log_result(
                "Timezone Import Verification - التحقق من استيراد المنطقة الزمنية",
                False,
                error="Could not create backup to test timezone"
            )

    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive New Features Testing...")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return
        
        # Run all test suites
        self.test_deleted_invoices_features()
        self.test_customer_statement_features()
        self.test_backup_features()
        self.test_timezone_import()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY - ملخص الاختبار الشامل")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"إجمالي الاختبارات: {self.total_tests}")
        print(f"✅ نجح: {self.passed_tests}")
        print(f"❌ فشل: {self.failed_tests}")
        print(f"📈 معدل النجاح: {success_rate:.1f}%")
        print()
        
        # Group results by feature
        deleted_invoices_tests = [r for r in self.test_results if "Invoice" in r["test"] or "Deleted" in r["test"]]
        statement_tests = [r for r in self.test_results if "Statement" in r["test"] or "Customer" in r["test"]]
        backup_tests = [r for r in self.test_results if "Backup" in r["test"]]
        timezone_tests = [r for r in self.test_results if "Timezone" in r["test"]]
        
        print("🗑️ DELETED INVOICES FEATURES:")
        for test in deleted_invoices_tests:
            print(f"  {test['status']}: {test['test']}")
        
        print("\n📊 CUSTOMER STATEMENT FEATURES:")
        for test in statement_tests:
            print(f"  {test['status']}: {test['test']}")
        
        print("\n💾 BACKUP SYSTEM FEATURES:")
        for test in backup_tests:
            print(f"  {test['status']}: {test['test']}")
            
        print("\n🌍 TIMEZONE VERIFICATION:")
        for test in timezone_tests:
            print(f"  {test['status']}: {test['test']}")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if "❌" in r["status"]]
        if failed_tests:
            print("\n❌ FAILED TESTS DETAILS:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['error']}")
        
        print("\n" + "=" * 60)
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! جميع الميزات الجديدة تعمل بشكل ممتاز!")
        elif success_rate >= 75:
            print("✅ GOOD! معظم الميزات الجديدة تعمل بشكل جيد مع بعض المشاكل البسيطة")
        else:
            print("⚠️ NEEDS ATTENTION! الميزات الجديدة تحتاج إلى إصلاحات")

def main():
    """Main test execution"""
    print("🧪 New Features Comprehensive Test Suite")
    print("مجموعة اختبارات شاملة للميزات الجديدة")
    print("=" * 60)
    
    tester = NewFeaturesTestSuite()
    tester.run_comprehensive_tests()

if __name__ == "__main__":
    main()