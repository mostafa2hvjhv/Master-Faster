from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import FileResponse
from database import db, logger, BACKUP_TEMP_DIR, GDRIVE_ENABLED, drive_service
from models import (
    DeletedInvoicesPassword, InvoiceOperationsPassword,
    PasswordVerify, PasswordChange
)
from datetime import datetime, timezone
from pathlib import Path
import uuid
import json
import tempfile
import base64
import os

try:
    from google_drive_service import GoogleDriveService
except ImportError:
    GoogleDriveService = None

router = APIRouter()

async def perform_backup(backup_id: str, username: str, upload_to_drive: bool, company_id: str = "elsawy"):
    """Perform backup in background - filtered by company_id"""
    try:
        backup_time = datetime.now(timezone.utc).isoformat()
        
        # Collections to backup (filtered by company_id)
        company_collections = [
            'customers', 'suppliers', 'invoices', 'payments', 'expenses',
            'raw_materials', 'finished_products', 'inventory_items',
            'local_products', 'supplier_transactions', 'treasury_transactions',
            'work_orders', 'deleted_invoices',
            'company_settings', 'main_treasury_transactions', 'main_treasury_passwords',
            'material_pricing', 'pricing_rules'
        ]
        
        backup_data = {
            'backup_id': backup_id,
            'created_at': backup_time,
            'created_by': username or 'system',
            'company_id': company_id,
            'collections': {},
            'drive_file_id': None,
            'drive_link': None,
            'status': 'in_progress'
        }
        
        # Save initial status
        await db.backups.insert_one(backup_data)
        
        # Backup each collection - filtered by company_id
        total_documents = 0
        collections_data = {}
        
        for collection_name in company_collections:
            try:
                collection = db[collection_name]
                # Filter by company_id to only backup this company's data
                query = {"company_id": company_id}
                # company_settings uses _type+company_id
                if collection_name == 'company_settings':
                    query = {"company_id": company_id}
                elif collection_name == 'main_treasury_passwords':
                    query = {"company_id": company_id}
                documents = await collection.find(query).to_list(length=None)
                # Remove MongoDB _id for JSON serialization
                clean_documents = []
                for doc in documents:
                    doc_copy = dict(doc)
                    if '_id' in doc_copy:
                        del doc_copy['_id']
                    clean_documents.append(doc_copy)
                
                collections_data[collection_name] = clean_documents
                total_documents += len(clean_documents)
                logger.info(f"Backed up {collection_name}: {len(clean_documents)} documents (company: {company_id})")
            except Exception as e:
                logger.error(f"Failed to backup {collection_name}: {str(e)}")
                collections_data[collection_name] = []
        
        # Update backup in database with collections data
        await db.backups.update_one(
            {'backup_id': backup_id},
            {'$set': {
                'collections': collections_data,
                'total_documents': total_documents,
                'status': 'completed'
            }}
        )
        
        backup_data['collections'] = collections_data
        backup_data['total_documents'] = total_documents
        
        # Upload to Google Drive if enabled
        if GDRIVE_ENABLED and upload_to_drive and drive_service:
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'backup_{timestamp}.json'
                temp_file = BACKUP_TEMP_DIR / filename
                
                backup_json = backup_data.copy()
                if '_id' in backup_json:
                    del backup_json['_id']
                
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_json, f, ensure_ascii=False, indent=2, default=str)
                
                # Try to upload to Google Drive
                try:
                    drive_result = drive_service.upload_file(
                        file_path=str(temp_file),
                        file_name=filename,
                        mime_type='application/json'
                    )
                    
                    await db.backups.update_one(
                        {'backup_id': backup_id},
                        {'$set': {
                            'drive_file_id': drive_result['id'],
                            'drive_link': drive_result.get('webViewLink'),
                            'status': 'completed_with_drive'
                        }}
                    )
                    
                    logger.info(f"Backup uploaded to Google Drive: {filename}")
                    
                except Exception as drive_error:
                    # Drive upload failed, but backup is complete locally
                    error_msg = str(drive_error)
                    if '403' in error_msg or 'storage quota' in error_msg.lower():
                        error_msg = "يرجى مشاركة مجلد 'ماستر سيل' مع Service Account"
                    
                    await db.backups.update_one(
                        {'backup_id': backup_id},
                        {'$set': {'status': 'completed_no_drive', 'drive_error': error_msg}}
                    )
                    logger.warning(f"Backup completed locally only: {error_msg}")
                
                # Cleanup temp file
                if temp_file.exists():
                    os.remove(temp_file)
                
            except Exception as e:
                logger.error(f"Failed to process Drive upload: {str(e)}")
                await db.backups.update_one(
                    {'backup_id': backup_id},
                    {'$set': {'status': 'completed_no_drive', 'drive_error': str(e)}}
                )
        
        logger.info(f"Backup completed: {backup_id} ({total_documents} documents)")
        
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        await db.backups.update_one(
            {'backup_id': backup_id},
            {'$set': {'status': 'failed', 'error': str(e)}}
        )

# Backup and Restore APIs
@router.post("/backup/create")
async def create_backup(background_tasks: BackgroundTasks, username: str = None, company_id: str = "elsawy"):
    """Create a manual backup of company-specific database collections (background task)"""
    try:
        backup_id = str(uuid.uuid4())
        
        # Start backup in background (local only) - filtered by company_id
        background_tasks.add_task(perform_backup, backup_id, username, False, company_id)
        
        return {
            'message': 'بدأت عملية النسخ الاحتياطي المحلي',
            'backup_id': backup_id,
            'status': 'in_progress',
            'note': 'سيتم إشعارك عند اكتمال النسخ الاحتياطي'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في إنشاء النسخة الاحتياطية: {str(e)}")

@router.get("/backup/status/{backup_id}")
async def get_backup_status(backup_id: str):
    """Get status of a specific backup"""
    try:
        backup = await db.backups.find_one({'backup_id': backup_id})
        if not backup:
            raise HTTPException(status_code=404, detail="النسخة الاحتياطية غير موجودة")
        
        return {
            'backup_id': backup.get('backup_id'),
            'status': backup.get('status', 'unknown'),
            'created_at': backup.get('created_at'),
            'total_documents': backup.get('total_documents', 0),
            'drive_link': backup.get('drive_link'),
            'error': backup.get('error')
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"خطأ في جلب حالة النسخة الاحتياطية: {str(e)}")

@router.get("/backup/download/{backup_id}")
async def download_backup(backup_id: str):
    """Download a backup as JSON file"""
    try:
        backup = await db.backups.find_one({'backup_id': backup_id})
        if not backup:
            raise HTTPException(status_code=404, detail="النسخة الاحتياطية غير موجودة")
        
        # Remove MongoDB _id
        if '_id' in backup:
            del backup['_id']
        
        # Create JSON file
        timestamp = datetime.fromisoformat(backup['created_at']).strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.json'
        temp_file = BACKUP_TEMP_DIR / filename
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(backup, f, ensure_ascii=False, indent=2, default=str)
        
        return FileResponse(
            path=str(temp_file),
            filename=filename,
            media_type='application/json',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"خطأ في تنزيل النسخة الاحتياطية: {str(e)}")

@router.post("/backup/upload")
async def upload_backup(file: UploadFile = File(...)):
    """Upload and import a backup JSON file"""
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="يجب أن يكون الملف بصيغة JSON")
        
        # Read and parse JSON
        content = await file.read()
        try:
            backup_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="ملف JSON غير صالح")
        
        # Validate backup structure
        required_fields = ['backup_id', 'created_at', 'collections']
        for field in required_fields:
            if field not in backup_data:
                raise HTTPException(status_code=400, detail=f"ملف النسخة الاحتياطية غير صالح - حقل مفقود: {field}")
        
        # Check if backup already exists
        existing = await db.backups.find_one({'backup_id': backup_data['backup_id']})
        if existing:
            raise HTTPException(status_code=409, detail="هذه النسخة الاحتياطية موجودة بالفعل")
        
        # Add upload metadata
        backup_data['uploaded_at'] = datetime.now(timezone.utc).isoformat()
        backup_data['uploaded_from_file'] = True
        
        # Insert into database
        await db.backups.insert_one(backup_data)
        
        return {
            'message': 'تم رفع النسخة الاحتياطية بنجاح',
            'backup_id': backup_data['backup_id'],
            'created_at': backup_data['created_at'],
            'total_documents': backup_data.get('total_documents', 0)
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"خطأ في رفع النسخة الاحتياطية: {str(e)}")

@router.post("/backup/restore-from-file")
async def restore_from_uploaded_file(file: UploadFile = File(...), username: str = None, company_id: str = "elsawy"):
    """Restore database directly from uploaded backup file - company isolated"""
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="يجب أن يكون الملف بصيغة JSON")
        
        # Read and parse JSON
        content = await file.read()
        try:
            backup_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="ملف JSON غير صالح")
        
        # Validate backup structure
        if 'collections' not in backup_data:
            raise HTTPException(status_code=400, detail="ملف النسخة الاحتياطية غير صالح")
        
        # Restore collections - only delete/replace this company's data
        restored_collections = []
        total_restored = 0
        
        for collection_name, documents in backup_data['collections'].items():
            if not documents:
                continue
            
            try:
                collection = db[collection_name]
                
                # Only delete THIS company's data (not all companies)
                await collection.delete_many({"company_id": company_id})
                
                # Insert backup data - ensure company_id is set
                if documents:
                    for doc in documents:
                        doc['company_id'] = company_id
                        if '_id' in doc:
                            del doc['_id']
                    await collection.insert_many(documents)
                
                restored_collections.append(collection_name)
                total_restored += len(documents)
                
            except Exception as e:
                logger.error(f"Failed to restore {collection_name}: {str(e)}")
        
        return {
            'message': 'تم استرجاع البيانات من الملف بنجاح',
            'collections_restored': len(restored_collections),
            'total_documents': total_restored,
            'restored_by': username or 'unknown'
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"خطأ في استرجاع البيانات: {str(e)}")

@router.get("/backup/list")
async def list_backups(company_id: str = "elsawy"):
    """Get list of backups for this company"""
    try:
        # Show backups for this company + old backups without company_id
        query = {"$or": [{"company_id": company_id}, {"company_id": {"$exists": False}}]}
        backups = await db.backups.find(query, {
            'backup_id': 1,
            'created_at': 1,
            'created_by': 1,
            'company_id': 1,
            'status': 1,
            'total_documents': 1,
            'drive_file_id': 1,
            'drive_link': 1,
            'is_scheduled': 1,
            '_id': 0
        }).sort('created_at', -1).to_list(length=None)
        
        return backups
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في جلب قائمة النسخ الاحتياطية: {str(e)}")

@router.post("/backup/restore/{backup_id}")
async def restore_backup(backup_id: str, username: str = None, company_id: str = "elsawy"):
    """Restore a backup - company isolated"""
    try:
        # Find the backup
        backup = await db.backups.find_one({'backup_id': backup_id})
        if not backup:
            raise HTTPException(status_code=404, detail="النسخة الاحتياطية غير موجودة")
        
        if 'collections' not in backup:
            raise HTTPException(status_code=400, detail="النسخة الاحتياطية تالفة")
        
        restored_collections = []
        total_restored = 0
        
        # Restore each collection - only delete/replace this company's data
        for collection_name, documents in backup['collections'].items():
            if not documents:
                continue
                
            try:
                collection = db[collection_name]
                
                # Only delete THIS company's data (not all companies)
                await collection.delete_many({"company_id": company_id})
                
                # Insert backup data - ensure company_id is set
                if documents:
                    for doc in documents:
                        doc['company_id'] = company_id
                        if '_id' in doc:
                            del doc['_id']
                    await collection.insert_many(documents)
                
                restored_collections.append(collection_name)
                total_restored += len(documents)
                
            except Exception as e:
                logger.info(f"تحذير: فشل استرجاع {collection_name}: {str(e)}")
        
        return {
            'message': 'تم استرجاع النسخة الاحتياطية بنجاح',
            'backup_id': backup_id,
            'restored_at': datetime.now(timezone.utc).isoformat(),
            'restored_by': username or 'system',
            'collections_restored': len(restored_collections),
            'total_documents': total_restored
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"خطأ في استرجاع النسخة الاحتياطية: {str(e)}")

@router.delete("/backup/{backup_id}")
async def delete_backup(backup_id: str):
    """Delete a backup"""
    try:
        # Get backup to check if it has Drive file
        backup = await db.backups.find_one({'backup_id': backup_id})
        
        # Delete from Drive if exists
        if backup and backup.get('drive_file_id') and GDRIVE_ENABLED:
            try:
                drive_service.delete_file(backup['drive_file_id'])
                logger.info(f"Deleted backup from Google Drive: {backup['drive_file_id']}")
            except Exception as e:
                logger.warning(f"Could not delete from Drive: {str(e)}")
        
        # Delete from database
        result = await db.backups.delete_one({'backup_id': backup_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="النسخة الاحتياطية غير موجودة")
        return {'message': 'تم حذف النسخة الاحتياطية بنجاح'}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"خطأ في حذف النسخة الاحتياطية: {str(e)}")

# Google Drive APIs
@router.get("/backup/drive/list")
async def list_drive_backups():
    """List all backups in Google Drive"""
    try:
        if not GDRIVE_ENABLED:
            raise HTTPException(status_code=503, detail="Google Drive غير مفعّل")
        
        files = drive_service.list_files()
        
        return {
            'status': 'success',
            'count': len(files),
            'files': files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في جلب ملفات Google Drive: {str(e)}")

@router.post("/backup/{backup_id}/upload-to-drive")
async def upload_backup_to_drive(backup_id: str):
    """Upload an existing backup to Google Drive"""
    try:
        if not GDRIVE_ENABLED:
            raise HTTPException(status_code=503, detail="Google Drive غير مفعّل")
        
        # Get backup from database
        backup = await db.backups.find_one({'backup_id': backup_id})
        if not backup:
            raise HTTPException(status_code=404, detail="النسخة الاحتياطية غير موجودة")
        
        # Check if already uploaded
        if backup.get('drive_file_id'):
            return {
                'message': 'النسخة الاحتياطية موجودة بالفعل على Google Drive',
                'drive_link': backup.get('drive_link')
            }
        
        # Create JSON file
        timestamp = datetime.fromisoformat(backup['created_at']).strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.json'
        temp_file = BACKUP_TEMP_DIR / filename
        
        # Remove _id for JSON serialization
        backup_json = backup.copy()
        if '_id' in backup_json:
            del backup_json['_id']
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(backup_json, f, ensure_ascii=False, indent=2, default=str)
        
        # Upload to Drive
        drive_result = drive_service.upload_file(
            file_path=str(temp_file),
            file_name=filename,
            mime_type='application/json'
        )
        
        # Update backup record
        await db.backups.update_one(
            {'backup_id': backup_id},
            {'$set': {
                'drive_file_id': drive_result['id'],
                'drive_link': drive_result.get('webViewLink')
            }}
        )
        
        # Cleanup
        os.remove(temp_file)
        
        return {
            'message': 'تم رفع النسخة الاحتياطية إلى Google Drive بنجاح',
            'drive_file_id': drive_result['id'],
            'drive_link': drive_result.get('webViewLink')
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"خطأ في رفع النسخة الاحتياطية: {str(e)}")

@router.get("/backup/drive/download/{file_id}")
async def download_from_drive(file_id: str):
    """Download a backup file from Google Drive"""
    try:
        if not GDRIVE_ENABLED:
            raise HTTPException(status_code=503, detail="Google Drive غير مفعّل")
        
        # Get file metadata
        metadata = drive_service.get_file_metadata(file_id)
        filename = metadata.get('name', 'backup.json')
        
        # Download to temp location
        temp_file = BACKUP_TEMP_DIR / filename
        drive_service.download_file(file_id, str(temp_file))
        
        return FileResponse(
            path=str(temp_file),
            filename=filename,
            media_type='application/json'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في تنزيل الملف: {str(e)}")

@router.post("/backup/drive/restore/{file_id}")
async def restore_from_drive(file_id: str, company_id: str = "elsawy"):
    """Restore backup from Google Drive file - company isolated"""
    try:
        if not GDRIVE_ENABLED:
            raise HTTPException(status_code=503, detail="Google Drive غير مفعّل")
        
        # Get file metadata
        metadata = drive_service.get_file_metadata(file_id)
        filename = metadata.get('name', 'backup.json')
        
        # Download file
        temp_file = BACKUP_TEMP_DIR / filename
        drive_service.download_file(file_id, str(temp_file))
        
        # Load JSON
        with open(temp_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Restore collections
        restored_collections = []
        total_restored = 0
        
        if 'collections' in backup_data:
            for collection_name, documents in backup_data['collections'].items():
                if not documents:
                    continue
                
                try:
                    collection = db[collection_name]
                    
                    # Only delete THIS company's data (not all companies)
                    await collection.delete_many({"company_id": company_id})
                    
                    # Insert backup data - ensure company_id is set
                    if documents:
                        for doc in documents:
                            doc['company_id'] = company_id
                            if '_id' in doc:
                                del doc['_id']
                        await collection.insert_many(documents)
                    
                    restored_collections.append(collection_name)
                    total_restored += len(documents)
                    
                except Exception as e:
                    logger.error(f"Failed to restore {collection_name}: {str(e)}")
        
        # Cleanup
        os.remove(temp_file)
        
        return {
            'message': 'تم استرجاع النسخة الاحتياطية من Google Drive بنجاح',
            'file_id': file_id,
            'collections_restored': len(restored_collections),
            'total_documents': total_restored
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"خطأ في استرجاع النسخة الاحتياطية: {str(e)}")

@router.get("/backup/drive/status")
async def get_drive_status():
    """Get Google Drive integration status"""
    try:
        if not GDRIVE_ENABLED:
            return {
                'enabled': False,
                'message': 'Google Drive غير مفعّل'
            }
        
        # Get folder info
        return {
            'enabled': True,
            'folder_name': 'ماستر سيل',
            'folder_id': drive_service.folder_id,
            'message': 'Google Drive متصل ويعمل بشكل صحيح'
        }
        
    except Exception as e:
        return {
            'enabled': False,
            'error': str(e),
            'message': 'خطأ في الاتصال بـ Google Drive'
        }

# ==================== Company Settings ====================

DEFAULT_SETTINGS = {
    "company_name": "ماستر سيل",
    "company_name_full": "شركة ماستر سيل",
    "company_subtitle": "تصنيع جميع أنواع الأويل سيل",
    "company_details_1": "جميع الأقطار حتى ٥٠٠مل",
    "company_details_2": "هيدروليك - نيوماتيك",
    "company_address": "الحرفيين - السلام - أمام السوبر جيت",
    "company_phone": "٠١٠٢٠٦٣٠٦٧٧",
    "company_mobile": "٠١٠٢٠٦٣٠٦٧٧ - ٠١٠٦٢٣٩٠٨٧٠",
    "company_landline": "٠١٠٢٠٦٣٠٦٧٧",
    "company_name_full_en": "",
    "company_subtitle_en": "",
    "company_details_1_en": "",
    "company_details_2_en": "",
    "company_address_en": "",
    "company_mobile_en": "",
    "company_landline_en": "",
    "logo_url": "https://customer-assets.emergentagent.com/job_oilseal-mgmt/artifacts/42i3e7yn_WhatsApp%20Image%202025-07-31%20at%2015.14.10_e8c55120.jpg",
    "system_subtitle": "نظام إدارة متكامل",
    "currency": "ج.م",
    "invoice_language": "ar"
}

@router.get("/settings")
async def get_settings(company_id: str = "elsawy"):
    """Get company settings"""
    settings = await db.company_settings.find_one({"_type": "company", "company_id": company_id})
    if settings:
        if '_id' in settings:
            del settings['_id']
        # Merge with defaults for any missing keys
        merged = {**DEFAULT_SETTINGS, **settings}
        return merged
    return DEFAULT_SETTINGS

@router.put("/settings")
async def update_settings(request: Request, company_id: str = "elsawy"):
    """Update company settings"""
    settings = await request.json()
    settings.pop("company_id", None)  # Remove from body if present
    settings["_type"] = "company"
    settings["company_id"] = company_id
    settings["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.company_settings.update_one(
        {"_type": "company", "company_id": company_id},
        {"$set": settings},
        upsert=True
    )
    
    # Return the saved settings
    saved = await db.company_settings.find_one({"_type": "company", "company_id": company_id})
    if saved and '_id' in saved:
        del saved['_id']
    
    return saved or settings

@router.post("/settings/logo")
async def upload_logo(file: UploadFile = File(...), company_id: str = "elsawy"):
    """Upload company logo"""
    import base64
    
    # Read file contents
    contents = await file.read()
    
    # Validate file size (max 5MB)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="حجم الملف كبير جداً (الحد الأقصى 5 ميجابايت)")
    
    # Determine MIME type
    content_type = file.content_type or 'image/png'
    
    # Convert to base64 data URI
    b64 = base64.b64encode(contents).decode('utf-8')
    data_uri = f"data:{content_type};base64,{b64}"
    
    # Save to settings
    await db.company_settings.update_one(
        {"_type": "company", "company_id": company_id},
        {"$set": {"logo_url": data_uri, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"logo_url": data_uri, "message": "تم رفع اللوجو بنجاح"}
@router.post("/deleted-invoices/verify-password")
async def verify_deleted_invoices_password(password_data: PasswordVerify):
    """Verify password for deleted invoices access"""
    try:
        # Get stored password
        password_doc = await db.deleted_invoices_passwords.find_one({"id": "deleted_invoices_password"})
        
        # If no password set yet, create default one
        if not password_doc:
            default_password = DeletedInvoicesPassword(password="200200")  # Default password
            await db.deleted_invoices_passwords.insert_one(default_password.dict())
            password_doc = default_password.dict()
        
        # Verify password
        if password_data.password == password_doc.get("password"):
            return {"success": True, "message": "تم التحقق من كلمة المرور بنجاح"}
        else:
            return {"success": False, "message": "كلمة المرور غير صحيحة"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deleted-invoices/change-password")
async def change_deleted_invoices_password(password_change: PasswordChange):
    """Change deleted invoices password"""
    try:
        # Get stored password
        password_doc = await db.deleted_invoices_passwords.find_one({"id": "deleted_invoices_password"})
        
        if not password_doc:
            raise HTTPException(status_code=404, detail="كلمة المرور غير موجودة")
        
        # Verify old password
        if password_change.old_password != password_doc.get("password"):
            raise HTTPException(status_code=401, detail="كلمة المرور القديمة غير صحيحة")
        
        # Update password
        result = await db.deleted_invoices_passwords.update_one(
            {"id": "deleted_invoices_password"},
            {"$set": {
                "password": password_change.new_password,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "تم تغيير كلمة المرور بنجاح"}
        else:
            raise HTTPException(status_code=400, detail="فشل تغيير كلمة المرور")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# End of Deleted Invoices Password Protection APIs
# ============================================================================

# ============================================================================
# Invoice Operations Password Protection APIs (Cancel/Edit/Change Payment)
# ============================================================================

@router.post("/invoice-operations/verify-password")
async def verify_invoice_operations_password(password_data: PasswordVerify):
    """Verify password for invoice operations (cancel/edit/change payment)"""
    try:
        # Get stored password
        password_doc = await db.invoice_operations_passwords.find_one({"id": "invoice_operations_password"})
        
        # If no password set yet, create default one
        if not password_doc:
            default_password = InvoiceOperationsPassword(password="1462")  # Default password
            await db.invoice_operations_passwords.insert_one(default_password.dict())
            password_doc = default_password.dict()
        
        # Verify password
        if password_data.password == password_doc.get("password"):
            return {"success": True, "message": "تم التحقق من كلمة المرور بنجاح"}
        else:
            return {"success": False, "message": "كلمة المرور غير صحيحة"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invoice-operations/change-password")
async def change_invoice_operations_password(password_change: PasswordChange):
    """Change invoice operations password"""
    try:
        # Get stored password
        password_doc = await db.invoice_operations_passwords.find_one({"id": "invoice_operations_password"})
        
        if not password_doc:
            raise HTTPException(status_code=404, detail="كلمة المرور غير موجودة")
        
        # Verify old password
        if password_change.old_password != password_doc.get("password"):
            raise HTTPException(status_code=401, detail="كلمة المرور القديمة غير صحيحة")
        
        # Update password
        result = await db.invoice_operations_passwords.update_one(
            {"id": "invoice_operations_password"},
            {"$set": {
                "password": password_change.new_password,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "تم تغيير كلمة المرور بنجاح"}
        else:
            raise HTTPException(status_code=400, detail="فشل تغيير كلمة المرور")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
