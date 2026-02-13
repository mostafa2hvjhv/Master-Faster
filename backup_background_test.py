#!/usr/bin/env python3
"""
اختبار النسخ الاحتياطي المحدث (Background Tasks)
Testing Updated Backup System with Background Tasks

الميزات الجديدة المراد اختبارها:
1. إنشاء نسخة احتياطية (Background Task) - POST /api/backup/create
2. التحقق من حالة النسخة الاحتياطية - GET /api/backup/status/{backup_id}
3. قائمة النسخ الاحتياطية - GET /api/backup/list
4. تأكيد عدم حدوث timeout
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"
TIMEOUT_LIMIT = 2  # seconds - API should respond within 2 seconds

class BackupBackgroundTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_results = []
        self.backup_ids = []
        
    def log_result(self, test_name, success, details, response_time=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ نجح" if success else "❌ فشل"
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}{time_info}")
        print(f"   التفاصيل: {details}")
        print()
        
    def test_backup_create_immediate_response(self):
        """Test 1: إنشاء نسخة احتياطية - يجب أن يرجع فوراً"""
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/backup/create",
                params={"username": "testing_agent", "upload_to_drive": True},
                timeout=TIMEOUT_LIMIT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['backup_id', 'status', 'message']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "إنشاء نسخة احتياطية - الحقول المطلوبة",
                        False,
                        f"حقول مفقودة: {missing_fields}",
                        response_time
                    )
                    return None
                
                # Check status is in_progress
                if data.get('status') != 'in_progress':
                    self.log_result(
                        "إنشاء نسخة احتياطية - الحالة الأولية",
                        False,
                        f"الحالة المتوقعة: in_progress، الحالة الفعلية: {data.get('status')}",
                        response_time
                    )
                    return None
                
                # Check response time
                if response_time > 1.0:  # Should respond within 1 second
                    self.log_result(
                        "إنشاء نسخة احتياطية - سرعة الاستجابة",
                        False,
                        f"الاستجابة بطيئة: {response_time:.2f}s (يجب أن تكون أقل من 1s)",
                        response_time
                    )
                else:
                    self.log_result(
                        "إنشاء نسخة احتياطية - سرعة الاستجابة",
                        True,
                        f"استجابة سريعة: {response_time:.2f}s",
                        response_time
                    )
                
                backup_id = data.get('backup_id')
                self.backup_ids.append(backup_id)
                
                self.log_result(
                    "إنشاء نسخة احتياطية - الاستجابة الفورية",
                    True,
                    f"تم إنشاء النسخة الاحتياطية بنجاح - ID: {backup_id}، الحالة: {data.get('status')}",
                    response_time
                )
                
                return backup_id
            else:
                self.log_result(
                    "إنشاء نسخة احتياطية - خطأ HTTP",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return None
                
        except requests.exceptions.Timeout:
            self.log_result(
                "إنشاء نسخة احتياطية - Timeout",
                False,
                f"انتهت مهلة الانتظار ({TIMEOUT_LIMIT}s) - النظام لا يستجيب بسرعة كافية"
            )
            return None
        except Exception as e:
            self.log_result(
                "إنشاء نسخة احتياطية - خطأ",
                False,
                f"خطأ غير متوقع: {str(e)}"
            )
            return None
    
    def test_backup_status_monitoring(self, backup_id):
        """Test 2: مراقبة حالة النسخة الاحتياطية"""
        if not backup_id:
            self.log_result(
                "مراقبة حالة النسخة الاحتياطية",
                False,
                "لا يوجد backup_id للاختبار"
            )
            return
        
        try:
            max_checks = 20  # Maximum 40 seconds of monitoring
            check_interval = 2  # Check every 2 seconds
            
            for i in range(max_checks):
                start_time = time.time()
                
                response = requests.get(
                    f"{self.base_url}/backup/status/{backup_id}",
                    timeout=TIMEOUT_LIMIT
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    total_docs = data.get('total_documents', 0)
                    
                    print(f"   الفحص {i+1}: الحالة = {status}, المستندات = {total_docs}, الوقت = {response_time:.2f}s")
                    
                    # Check response time
                    if response_time > TIMEOUT_LIMIT:
                        self.log_result(
                            "مراقبة حالة النسخة الاحتياطية - سرعة الاستجابة",
                            False,
                            f"استجابة بطيئة في الفحص {i+1}: {response_time:.2f}s",
                            response_time
                        )
                    
                    # Check if completed (any completion status)
                    if status in ['completed', 'completed_with_drive', 'completed_no_drive']:
                        self.log_result(
                            "مراقبة حالة النسخة الاحتياطية - الإكمال",
                            True,
                            f"تم إكمال النسخة الاحتياطية بنجاح - الحالة: {status}, المستندات: {total_docs}",
                            response_time
                        )
                        
                        # Test Google Drive status if available
                        if status == 'completed_with_drive' and data.get('drive_link'):
                            self.log_result(
                                "رفع Google Drive",
                                True,
                                f"تم رفع النسخة الاحتياطية إلى Google Drive - الرابط: {data.get('drive_link')}"
                            )
                        elif status == 'completed_no_drive':
                            self.log_result(
                                "النسخة الاحتياطية المحلية",
                                True,
                                "تم إكمال النسخة الاحتياطية محلياً بدون رفع إلى Google Drive"
                            )
                        
                        return True
                    
                    elif status == 'failed':
                        error_msg = data.get('error', 'خطأ غير محدد')
                        self.log_result(
                            "مراقبة حالة النسخة الاحتياطية - فشل",
                            False,
                            f"فشلت النسخة الاحتياطية - الخطأ: {error_msg}"
                        )
                        return False
                    
                    # Continue monitoring if still in progress
                    if i < max_checks - 1:  # Don't sleep on last iteration
                        time.sleep(check_interval)
                
                else:
                    self.log_result(
                        "مراقبة حالة النسخة الاحتياطية - خطأ HTTP",
                        False,
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
            
            # If we reach here, backup is still in progress after max time
            self.log_result(
                "مراقبة حالة النسخة الاحتياطية - انتهاء الوقت",
                False,
                f"النسخة الاحتياطية لم تكتمل خلال {max_checks * check_interval} ثانية"
            )
            return False
            
        except Exception as e:
            self.log_result(
                "مراقبة حالة النسخة الاحتياطية - خطأ",
                False,
                f"خطأ في المراقبة: {str(e)}"
            )
            return False
    
    def test_backup_list(self):
        """Test 3: قائمة النسخ الاحتياطية"""
        try:
            start_time = time.time()
            
            response = requests.get(
                f"{self.base_url}/backup/list",
                timeout=TIMEOUT_LIMIT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_result(
                        "قائمة النسخ الاحتياطية - نوع البيانات",
                        False,
                        f"متوقع: قائمة، فعلي: {type(data)}"
                    )
                    return False
                
                backup_count = len(data)
                
                # Check if our created backups are in the list
                found_backups = 0
                total_documents_found = False
                
                for backup in data:
                    if backup.get('backup_id') in self.backup_ids:
                        found_backups += 1
                    
                    # Check for required fields
                    required_fields = ['backup_id', 'status', 'created_at']
                    if all(field in backup for field in required_fields):
                        if 'total_documents' in backup and backup['total_documents'] > 0:
                            total_documents_found = True
                
                self.log_result(
                    "قائمة النسخ الاحتياطية - المحتوى",
                    True,
                    f"تم جلب {backup_count} نسخة احتياطية، تم العثور على {found_backups} من النسخ المنشأة",
                    response_time
                )
                
                if total_documents_found:
                    self.log_result(
                        "قائمة النسخ الاحتياطية - total_documents",
                        True,
                        "تم العثور على حقل total_documents في النسخ الاحتياطية"
                    )
                else:
                    self.log_result(
                        "قائمة النسخ الاحتياطية - total_documents",
                        False,
                        "لم يتم العثور على حقل total_documents أو كانت القيمة صفر"
                    )
                
                return True
            else:
                self.log_result(
                    "قائمة النسخ الاحتياطية - خطأ HTTP",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "قائمة النسخ الاحتياطية - خطأ",
                False,
                f"خطأ في جلب القائمة: {str(e)}"
            )
            return False
    
    def test_multiple_concurrent_backups(self):
        """Test 4: إنشاء عدة نسخ احتياطية متزامنة"""
        try:
            concurrent_backups = []
            
            # Create 3 backups quickly
            for i in range(3):
                start_time = time.time()
                
                response = requests.post(
                    f"{self.base_url}/backup/create",
                    params={"username": f"test_concurrent_{i}", "upload_to_drive": False},
                    timeout=TIMEOUT_LIMIT
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    backup_id = data.get('backup_id')
                    concurrent_backups.append(backup_id)
                    self.backup_ids.append(backup_id)
                    
                    print(f"   نسخة احتياطية {i+1}: {backup_id} ({response_time:.2f}s)")
                else:
                    self.log_result(
                        "النسخ الاحتياطية المتزامنة",
                        False,
                        f"فشل في إنشاء النسخة {i+1}: HTTP {response.status_code}"
                    )
                    return False
            
            self.log_result(
                "النسخ الاحتياطية المتزامنة - الإنشاء",
                True,
                f"تم إنشاء {len(concurrent_backups)} نسخة احتياطية متزامنة بنجاح"
            )
            
            return True
            
        except Exception as e:
            self.log_result(
                "النسخ الاحتياطية المتزامنة - خطأ",
                False,
                f"خطأ في الاختبار المتزامن: {str(e)}"
            )
            return False
    
    def test_backup_without_drive_upload(self):
        """Test 5: نسخة احتياطية بدون رفع إلى Google Drive"""
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/backup/create",
                params={"username": "testing_no_drive", "upload_to_drive": False},
                timeout=TIMEOUT_LIMIT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                backup_id = data.get('backup_id')
                self.backup_ids.append(backup_id)
                
                self.log_result(
                    "نسخة احتياطية بدون Google Drive",
                    True,
                    f"تم إنشاء نسخة احتياطية بدون رفع إلى Drive - ID: {backup_id}",
                    response_time
                )
                
                # Monitor this backup briefly
                time.sleep(5)  # Wait 5 seconds
                
                status_response = requests.get(f"{self.base_url}/backup/status/{backup_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    
                    if status == 'completed':
                        self.log_result(
                            "نسخة احتياطية بدون Google Drive - الحالة",
                            True,
                            f"النسخة الاحتياطية مكتملة بدون رفع إلى Drive - الحالة: {status}"
                        )
                    else:
                        self.log_result(
                            "نسخة احتياطية بدون Google Drive - الحالة",
                            True,
                            f"النسخة الاحتياطية قيد التقدم - الحالة: {status}"
                        )
                
                return backup_id
            else:
                self.log_result(
                    "نسخة احتياطية بدون Google Drive - خطأ",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return None
                
        except Exception as e:
            self.log_result(
                "نسخة احتياطية بدون Google Drive - خطأ",
                False,
                f"خطأ: {str(e)}"
            )
            return None
    
    def run_all_tests(self):
        """تشغيل جميع الاختبارات"""
        print("🚀 بدء اختبار النسخ الاحتياطي المحدث (Background Tasks)")
        print("=" * 60)
        
        # Test 1: Create backup with immediate response
        backup_id = self.test_backup_create_immediate_response()
        
        # Test 2: Monitor backup status
        if backup_id:
            self.test_backup_status_monitoring(backup_id)
        
        # Test 3: List backups
        self.test_backup_list()
        
        # Test 4: Multiple concurrent backups
        self.test_multiple_concurrent_backups()
        
        # Test 5: Backup without Google Drive
        self.test_backup_without_drive_upload()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """طباعة ملخص النتائج"""
        print("\n" + "=" * 60)
        print("📊 ملخص نتائج اختبار النسخ الاحتياطي")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"إجمالي الاختبارات: {total_tests}")
        print(f"نجح: {passed_tests} ✅")
        print(f"فشل: {failed_tests} ❌")
        print(f"معدل النجاح: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ الاختبارات الفاشلة:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        print(f"\n📝 تم إنشاء {len(self.backup_ids)} نسخة احتياطية أثناء الاختبار")
        
        # Performance analysis
        response_times = [r['response_time'] for r in self.test_results if r['response_time'] is not None]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            print(f"\n⏱️ تحليل الأداء:")
            print(f"   متوسط وقت الاستجابة: {avg_response_time:.2f}s")
            print(f"   أقصى وقت استجابة: {max_response_time:.2f}s")
            
            if max_response_time <= 2.0:
                print(f"   ✅ جميع الاستجابات ضمن الحد المطلوب (≤2s)")
            else:
                print(f"   ❌ بعض الاستجابات تجاوزت الحد المطلوب (>2s)")

if __name__ == "__main__":
    tester = BackupBackgroundTester()
    tester.run_all_tests()