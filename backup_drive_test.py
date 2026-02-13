#!/usr/bin/env python3
"""
اختبار رفع النسخ الاحتياطية إلى Google Drive
Testing Google Drive Upload for Backups
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"
TIMEOUT_LIMIT = 2  # seconds

def test_backup_with_drive():
    """اختبار إنشاء نسخة احتياطية مع رفع إلى Google Drive"""
    try:
        print("🔄 اختبار إنشاء نسخة احتياطية مع رفع إلى Google Drive...")
        
        # Create backup with Google Drive upload
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/backup/create",
            params={"username": "drive_test", "upload_to_drive": True},
            timeout=TIMEOUT_LIMIT
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            backup_id = data.get('backup_id')
            
            print(f"✅ تم إنشاء النسخة الاحتياطية: {backup_id} ({response_time:.2f}s)")
            print(f"   الحالة الأولية: {data.get('status')}")
            
            # Monitor status for Google Drive upload
            print("\n🔍 مراقبة حالة الرفع إلى Google Drive...")
            
            for i in range(30):  # Monitor for up to 60 seconds
                time.sleep(2)
                
                status_response = requests.get(f"{BASE_URL}/backup/status/{backup_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    total_docs = status_data.get('total_documents', 0)
                    drive_link = status_data.get('drive_link')
                    
                    print(f"   الفحص {i+1}: {status} - {total_docs} مستند")
                    
                    if status == 'completed_with_drive':
                        print(f"✅ تم رفع النسخة الاحتياطية إلى Google Drive بنجاح!")
                        print(f"   رابط Google Drive: {drive_link}")
                        return True
                    elif status == 'completed_no_drive':
                        print(f"⚠️ تم إكمال النسخة الاحتياطية لكن بدون رفع إلى Google Drive")
                        print(f"   السبب المحتمل: Google Drive غير مُعد أو حدث خطأ في الرفع")
                        return False
                    elif status == 'failed':
                        error = status_data.get('error', 'خطأ غير محدد')
                        print(f"❌ فشلت النسخة الاحتياطية: {error}")
                        return False
            
            print(f"⏰ انتهت مهلة المراقبة - النسخة الاحتياطية لا تزال قيد التقدم")
            return False
            
        else:
            print(f"❌ فشل في إنشاء النسخة الاحتياطية: HTTP {response.status_code}")
            print(f"   الاستجابة: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {str(e)}")
        return False

def test_backup_without_drive():
    """اختبار إنشاء نسخة احتياطية بدون رفع إلى Google Drive"""
    try:
        print("\n🔄 اختبار إنشاء نسخة احتياطية بدون رفع إلى Google Drive...")
        
        # Create backup without Google Drive upload
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/backup/create",
            params={"username": "no_drive_test", "upload_to_drive": False},
            timeout=TIMEOUT_LIMIT
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            backup_id = data.get('backup_id')
            
            print(f"✅ تم إنشاء النسخة الاحتياطية: {backup_id} ({response_time:.2f}s)")
            print(f"   الحالة الأولية: {data.get('status')}")
            
            # Monitor status briefly
            print("\n🔍 مراقبة حالة النسخة الاحتياطية...")
            
            for i in range(10):  # Monitor for up to 20 seconds
                time.sleep(2)
                
                status_response = requests.get(f"{BASE_URL}/backup/status/{backup_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    total_docs = status_data.get('total_documents', 0)
                    
                    print(f"   الفحص {i+1}: {status} - {total_docs} مستند")
                    
                    if status in ['completed', 'completed_no_drive']:
                        print(f"✅ تم إكمال النسخة الاحتياطية بدون رفع إلى Google Drive")
                        return True
                    elif status == 'failed':
                        error = status_data.get('error', 'خطأ غير محدد')
                        print(f"❌ فشلت النسخة الاحتياطية: {error}")
                        return False
            
            print(f"⏰ انتهت مهلة المراقبة - النسخة الاحتياطية لا تزال قيد التقدم")
            return False
            
        else:
            print(f"❌ فشل في إنشاء النسخة الاحتياطية: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 اختبار رفع النسخ الاحتياطية إلى Google Drive")
    print("=" * 60)
    
    # Test with Google Drive
    drive_result = test_backup_with_drive()
    
    # Test without Google Drive
    no_drive_result = test_backup_without_drive()
    
    print("\n" + "=" * 60)
    print("📊 ملخص النتائج")
    print("=" * 60)
    print(f"النسخ الاحتياطي مع Google Drive: {'✅ نجح' if drive_result else '❌ فشل'}")
    print(f"النسخ الاحتياطي بدون Google Drive: {'✅ نجح' if no_drive_result else '❌ فشل'}")
    
    if drive_result and no_drive_result:
        print("\n🎉 جميع اختبارات النسخ الاحتياطي نجحت!")
    elif no_drive_result:
        print("\n⚠️ النسخ الاحتياطي المحلي يعمل، لكن Google Drive قد يحتاج إعداد")
    else:
        print("\n❌ هناك مشاكل في نظام النسخ الاحتياطي")