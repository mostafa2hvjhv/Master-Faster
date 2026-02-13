#!/usr/bin/env python3
"""
اختبار مخصص لحالة النسخة الاحتياطية
Dedicated test for backup status monitoring
"""

import requests
import time

BASE_URL = "https://retail-treasury.preview.emergentagent.com/api"

def test_backup_status():
    """اختبار حالة النسخة الاحتياطية مع timeout أطول"""
    
    # First create a backup
    print("🔄 إنشاء نسخة احتياطية جديدة...")
    try:
        response = requests.post(
            f"{BASE_URL}/backup/create",
            params={"username": "status_test", "upload_to_drive": False},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            backup_id = data.get('backup_id')
            print(f"✅ تم إنشاء النسخة الاحتياطية: {backup_id}")
            print(f"   الحالة الأولية: {data.get('status')}")
            
            # Now monitor status with longer timeout
            print("\n🔍 مراقبة حالة النسخة الاحتياطية...")
            
            for i in range(10):
                try:
                    start_time = time.time()
                    
                    status_response = requests.get(
                        f"{BASE_URL}/backup/status/{backup_id}",
                        timeout=10  # Longer timeout
                    )
                    
                    response_time = time.time() - start_time
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        total_docs = status_data.get('total_documents', 0)
                        
                        print(f"   الفحص {i+1}: {status} - {total_docs} مستند ({response_time:.3f}s)")
                        
                        if status in ['completed', 'completed_no_drive', 'completed_with_drive']:
                            print(f"✅ تم إكمال النسخة الاحتياطية بنجاح!")
                            print(f"   الحالة النهائية: {status}")
                            print(f"   إجمالي المستندات: {total_docs}")
                            return True
                        elif status == 'failed':
                            error = status_data.get('error', 'خطأ غير محدد')
                            print(f"❌ فشلت النسخة الاحتياطية: {error}")
                            return False
                    else:
                        print(f"❌ خطأ في جلب الحالة: HTTP {status_response.status_code}")
                        return False
                        
                except requests.exceptions.Timeout:
                    print(f"⏰ انتهت مهلة الانتظار في الفحص {i+1}")
                    continue
                except Exception as e:
                    print(f"❌ خطأ في الفحص {i+1}: {str(e)}")
                    continue
                
                # Wait before next check
                if i < 9:
                    time.sleep(2)
            
            print("⏰ انتهت مهلة المراقبة")
            return False
            
        else:
            print(f"❌ فشل في إنشاء النسخة الاحتياطية: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {str(e)}")
        return False

def test_existing_backup_status():
    """اختبار حالة نسخة احتياطية موجودة"""
    
    print("\n🔍 اختبار حالة النسخ الاحتياطية الموجودة...")
    
    try:
        # Get list of backups first
        response = requests.get(f"{BASE_URL}/backup/list", timeout=5)
        
        if response.status_code == 200:
            backups = response.json()
            
            if backups:
                # Test status of first backup
                backup = backups[0]
                backup_id = backup.get('backup_id')
                
                print(f"🔍 اختبار حالة النسخة الاحتياطية: {backup_id}")
                
                status_response = requests.get(
                    f"{BASE_URL}/backup/status/{backup_id}",
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"✅ تم جلب حالة النسخة الاحتياطية بنجاح:")
                    print(f"   الحالة: {status_data.get('status')}")
                    print(f"   المستندات: {status_data.get('total_documents', 0)}")
                    print(f"   تاريخ الإنشاء: {status_data.get('created_at')}")
                    
                    if status_data.get('drive_link'):
                        print(f"   رابط Google Drive: {status_data.get('drive_link')}")
                    
                    return True
                else:
                    print(f"❌ فشل في جلب الحالة: HTTP {status_response.status_code}")
                    return False
            else:
                print("⚠️ لا توجد نسخ احتياطية للاختبار")
                return False
        else:
            print(f"❌ فشل في جلب قائمة النسخ الاحتياطية: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 اختبار مخصص لحالة النسخة الاحتياطية")
    print("=" * 50)
    
    # Test 1: Create new backup and monitor
    result1 = test_backup_status()
    
    # Test 2: Check existing backup status
    result2 = test_existing_backup_status()
    
    print("\n" + "=" * 50)
    print("📊 ملخص النتائج")
    print("=" * 50)
    print(f"إنشاء ومراقبة نسخة جديدة: {'✅ نجح' if result1 else '❌ فشل'}")
    print(f"اختبار حالة نسخة موجودة: {'✅ نجح' if result2 else '❌ فشل'}")
    
    if result1 and result2:
        print("\n🎉 جميع اختبارات حالة النسخة الاحتياطية نجحت!")
    elif result2:
        print("\n⚠️ API حالة النسخة الاحتياطية يعمل، لكن قد تكون هناك مشكلة في المراقبة المباشرة")
    else:
        print("\n❌ هناك مشاكل في API حالة النسخة الاحتياطية")