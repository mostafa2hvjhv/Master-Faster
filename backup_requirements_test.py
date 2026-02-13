#!/usr/bin/env python3
"""
اختبار متطلبات النسخ الاحتياطي المحددة في المراجعة العربية
Testing Specific Backup Requirements from Arabic Review
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"

class BackupRequirementsTest:
    def __init__(self):
        self.results = []
        
    def log_test(self, name, success, details, response_time=None):
        """تسجيل نتيجة الاختبار"""
        result = {
            "test": name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status = "✅" if success else "❌"
        time_info = f" ({response_time:.3f}s)" if response_time else ""
        print(f"{status} {name}{time_info}")
        print(f"   {details}")
        print()
        
    def test_requirement_1_immediate_response(self):
        """
        المتطلب 1: POST /api/backup/create
        - يجب أن يرجع فوراً مع backup_id و status: in_progress
        - التحقق من أن العملية لا تستغرق أكثر من ثانية واحدة للرد
        """
        print("🔍 اختبار المتطلب 1: الاستجابة الفورية لإنشاء النسخة الاحتياطية")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/backup/create",
                params={"username": "requirement_test_1", "upload_to_drive": True},
                timeout=2
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check backup_id exists
                backup_id = data.get('backup_id')
                if not backup_id:
                    self.log_test(
                        "المتطلب 1أ: وجود backup_id",
                        False,
                        "backup_id مفقود في الاستجابة",
                        response_time
                    )
                    return None
                
                # Check status is in_progress
                status = data.get('status')
                if status != 'in_progress':
                    self.log_test(
                        "المتطلب 1ب: الحالة الأولية in_progress",
                        False,
                        f"الحالة المتوقعة: in_progress، الفعلية: {status}",
                        response_time
                    )
                else:
                    self.log_test(
                        "المتطلب 1ب: الحالة الأولية in_progress",
                        True,
                        f"الحالة صحيحة: {status}",
                        response_time
                    )
                
                # Check response time < 1 second
                if response_time > 1.0:
                    self.log_test(
                        "المتطلب 1ج: الاستجابة خلال ثانية واحدة",
                        False,
                        f"الاستجابة بطيئة: {response_time:.3f}s (يجب أن تكون ≤ 1s)",
                        response_time
                    )
                else:
                    self.log_test(
                        "المتطلب 1ج: الاستجابة خلال ثانية واحدة",
                        True,
                        f"استجابة سريعة: {response_time:.3f}s",
                        response_time
                    )
                
                self.log_test(
                    "المتطلب 1: إنشاء النسخة الاحتياطية",
                    True,
                    f"تم إنشاء النسخة الاحتياطية بنجاح - ID: {backup_id}",
                    response_time
                )
                
                return backup_id
            else:
                self.log_test(
                    "المتطلب 1: إنشاء النسخة الاحتياطية",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return None
                
        except Exception as e:
            self.log_test(
                "المتطلب 1: إنشاء النسخة الاحتياطية",
                False,
                f"خطأ: {str(e)}"
            )
            return None
    
    def test_requirement_2_status_monitoring(self, backup_id):
        """
        المتطلب 2: GET /api/backup/status/{backup_id}
        - يجب أن يظهر الحالة: in_progress → completed أو completed_with_drive
        - متابعة الحالة كل ثانيتين
        """
        if not backup_id:
            self.log_test(
                "المتطلب 2: مراقبة حالة النسخة الاحتياطية",
                False,
                "لا يوجد backup_id للاختبار"
            )
            return False
            
        print("🔍 اختبار المتطلب 2: مراقبة حالة النسخة الاحتياطية")
        
        try:
            status_progression = []
            max_checks = 15  # 30 seconds maximum
            
            for i in range(max_checks):
                start_time = time.time()
                
                response = requests.get(
                    f"{BASE_URL}/backup/status/{backup_id}",
                    timeout=2
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    total_docs = data.get('total_documents', 0)
                    
                    status_progression.append({
                        'check': i + 1,
                        'status': status,
                        'total_documents': total_docs,
                        'response_time': response_time
                    })
                    
                    print(f"   الفحص {i+1}: {status} - {total_docs} مستند ({response_time:.3f}s)")
                    
                    # Check if completed
                    if status in ['completed', 'completed_with_drive', 'completed_no_drive']:
                        self.log_test(
                            "المتطلب 2أ: تطور الحالة إلى مكتملة",
                            True,
                            f"تم إكمال النسخة الاحتياطية - الحالة النهائية: {status}",
                            response_time
                        )
                        
                        # Check total_documents
                        if total_docs > 0:
                            self.log_test(
                                "المتطلب 2ب: وجود total_documents",
                                True,
                                f"تم العثور على {total_docs} مستند في النسخة الاحتياطية"
                            )
                        else:
                            self.log_test(
                                "المتطلب 2ب: وجود total_documents",
                                False,
                                "total_documents = 0 أو مفقود"
                            )
                        
                        return True
                    
                    elif status == 'failed':
                        error = data.get('error', 'خطأ غير محدد')
                        self.log_test(
                            "المتطلب 2: مراقبة حالة النسخة الاحتياطية",
                            False,
                            f"فشلت النسخة الاحتياطية - الخطأ: {error}"
                        )
                        return False
                    
                    # Wait 2 seconds before next check (as required)
                    if i < max_checks - 1:
                        time.sleep(2)
                
                else:
                    self.log_test(
                        "المتطلب 2: مراقبة حالة النسخة الاحتياطية",
                        False,
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return False
            
            # If we reach here, backup didn't complete in time
            self.log_test(
                "المتطلب 2: مراقبة حالة النسخة الاحتياطية",
                False,
                f"النسخة الاحتياطية لم تكتمل خلال {max_checks * 2} ثانية"
            )
            return False
            
        except Exception as e:
            self.log_test(
                "المتطلب 2: مراقبة حالة النسخة الاحتياطية",
                False,
                f"خطأ: {str(e)}"
            )
            return False
    
    def test_requirement_3_backup_list(self):
        """
        المتطلب 3: GET /api/backup/list
        - يجب أن تظهر status لكل نسخة
        - التحقق من وجود total_documents
        """
        print("🔍 اختبار المتطلب 3: قائمة النسخ الاحتياطية")
        
        try:
            start_time = time.time()
            
            response = requests.get(
                f"{BASE_URL}/backup/list",
                timeout=2
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_test(
                        "المتطلب 3: قائمة النسخ الاحتياطية",
                        False,
                        f"نوع البيانات خاطئ - متوقع: list، فعلي: {type(data)}"
                    )
                    return False
                
                backup_count = len(data)
                
                # Check each backup has status
                backups_with_status = 0
                backups_with_total_docs = 0
                
                for backup in data:
                    if 'status' in backup:
                        backups_with_status += 1
                    if 'total_documents' in backup and backup['total_documents'] > 0:
                        backups_with_total_docs += 1
                
                # Test status field
                if backups_with_status == backup_count:
                    self.log_test(
                        "المتطلب 3أ: وجود status لكل نسخة",
                        True,
                        f"جميع النسخ الـ {backup_count} تحتوي على حقل status"
                    )
                else:
                    self.log_test(
                        "المتطلب 3أ: وجود status لكل نسخة",
                        False,
                        f"{backups_with_status} من {backup_count} نسخة تحتوي على status"
                    )
                
                # Test total_documents field
                if backups_with_total_docs > 0:
                    self.log_test(
                        "المتطلب 3ب: وجود total_documents",
                        True,
                        f"{backups_with_total_docs} من {backup_count} نسخة تحتوي على total_documents"
                    )
                else:
                    self.log_test(
                        "المتطلب 3ب: وجود total_documents",
                        False,
                        "لا توجد نسخ احتياطية تحتوي على total_documents"
                    )
                
                self.log_test(
                    "المتطلب 3: قائمة النسخ الاحتياطية",
                    True,
                    f"تم جلب {backup_count} نسخة احتياطية بنجاح",
                    response_time
                )
                
                return True
            else:
                self.log_test(
                    "المتطلب 3: قائمة النسخ الاحتياطية",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test(
                "المتطلب 3: قائمة النسخ الاحتياطية",
                False,
                f"خطأ: {str(e)}"
            )
            return False
    
    def test_requirement_4_no_timeout(self):
        """
        المتطلب 4: تأكيد عدم حدوث timeout
        - التأكد من أن الـ API يرد خلال 2 ثانية أو أقل
        - النسخة الاحتياطية تعمل في الخلفية
        """
        print("🔍 اختبار المتطلب 4: عدم حدوث timeout")
        
        try:
            # Test multiple API calls to ensure consistent performance
            api_calls = [
                ("POST /api/backup/create", "backup/create", {"username": "timeout_test", "upload_to_drive": False}),
                ("GET /api/backup/list", "backup/list", None),
            ]
            
            all_within_limit = True
            response_times = []
            
            for api_name, endpoint, params in api_calls:
                start_time = time.time()
                
                if endpoint == "backup/create":
                    response = requests.post(f"{BASE_URL}/{endpoint}", params=params, timeout=2)
                else:
                    response = requests.get(f"{BASE_URL}/{endpoint}", timeout=2)
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response_time > 2.0:
                    all_within_limit = False
                    self.log_test(
                        f"المتطلب 4: {api_name} - عدم تجاوز 2 ثانية",
                        False,
                        f"تجاوز الحد المسموح: {response_time:.3f}s",
                        response_time
                    )
                else:
                    self.log_test(
                        f"المتطلب 4: {api_name} - عدم تجاوز 2 ثانية",
                        True,
                        f"ضمن الحد المسموح: {response_time:.3f}s",
                        response_time
                    )
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            if all_within_limit:
                self.log_test(
                    "المتطلب 4: عدم حدوث timeout",
                    True,
                    f"جميع APIs تستجيب خلال 2 ثانية - متوسط: {avg_response_time:.3f}s، أقصى: {max_response_time:.3f}s"
                )
            else:
                self.log_test(
                    "المتطلب 4: عدم حدوث timeout",
                    False,
                    f"بعض APIs تجاوزت 2 ثانية - متوسط: {avg_response_time:.3f}s، أقصى: {max_response_time:.3f}s"
                )
            
            return all_within_limit
            
        except Exception as e:
            self.log_test(
                "المتطلب 4: عدم حدوث timeout",
                False,
                f"خطأ: {str(e)}"
            )
            return False
    
    def run_all_requirements(self):
        """تشغيل جميع متطلبات الاختبار"""
        print("🚀 اختبار متطلبات النسخ الاحتياطي المحددة في المراجعة العربية")
        print("=" * 70)
        
        # Requirement 1: Immediate response
        backup_id = self.test_requirement_1_immediate_response()
        
        # Requirement 2: Status monitoring
        if backup_id:
            self.test_requirement_2_status_monitoring(backup_id)
        
        # Requirement 3: Backup list
        self.test_requirement_3_backup_list()
        
        # Requirement 4: No timeout
        self.test_requirement_4_no_timeout()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """طباعة ملخص النتائج"""
        print("\n" + "=" * 70)
        print("📊 ملخص نتائج اختبار متطلبات النسخ الاحتياطي")
        print("=" * 70)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"إجمالي الاختبارات: {total_tests}")
        print(f"نجح: {passed_tests} ✅")
        print(f"فشل: {failed_tests} ❌")
        print(f"معدل النجاح: {success_rate:.1f}%")
        
        # Group results by requirement
        requirements = {
            "المتطلب 1": [r for r in self.results if "المتطلب 1" in r['test']],
            "المتطلب 2": [r for r in self.results if "المتطلب 2" in r['test']],
            "المتطلب 3": [r for r in self.results if "المتطلب 3" in r['test']],
            "المتطلب 4": [r for r in self.results if "المتطلب 4" in r['test']],
        }
        
        print(f"\n📋 تفصيل النتائج حسب المتطلبات:")
        for req_name, req_results in requirements.items():
            if req_results:
                req_passed = sum(1 for r in req_results if r['success'])
                req_total = len(req_results)
                req_rate = (req_passed / req_total * 100) if req_total > 0 else 0
                status = "✅" if req_passed == req_total else "❌"
                print(f"   {status} {req_name}: {req_passed}/{req_total} ({req_rate:.0f}%)")
        
        if failed_tests > 0:
            print(f"\n❌ الاختبارات الفاشلة:")
            for result in self.results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        # Performance summary
        response_times = [r['response_time'] for r in self.results if r['response_time'] is not None]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\n⏱️ أداء الاستجابة:")
            print(f"   متوسط وقت الاستجابة: {avg_time:.3f}s")
            print(f"   أقصى وقت استجابة: {max_time:.3f}s")

if __name__ == "__main__":
    tester = BackupRequirementsTest()
    tester.run_all_requirements()