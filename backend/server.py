from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from database import db, client, logger, BACKUP_TEMP_DIR, GDRIVE_ENABLED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
import uuid
import asyncio
import logging
import json
import os

# Import route modules
from routes_auth import router as auth_router
from routes_customers import router as customers_router
from routes_products import router as products_router
from routes_invoices import router as invoices_router
from routes_finance import router as finance_router
from routes_settings import router as settings_router

# Create the main app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://master-faster.vercel.app",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all route modules with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(customers_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(invoices_router, prefix="/api")
app.include_router(finance_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

# Setup Backup Scheduler
scheduler = BackgroundScheduler()

async def scheduled_backup():
    """Scheduled automatic backup - creates separate backup per company"""
    try:
        logger.info("Starting scheduled automatic backup...")
        
        # Backup each company separately
        for cid in ["elsawy", "faster"]:
            backup_id = str(uuid.uuid4())
            backup_time = datetime.now(timezone.utc).isoformat()
            
            collections = [
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
                'created_by': 'system_scheduled',
                'company_id': cid,
                'collections': {},
                'drive_file_id': None,
                'drive_link': None,
                'is_scheduled': True
            }
            
            total_documents = 0
            for collection_name in collections:
                try:
                    collection = db[collection_name]
                    documents = await collection.find({"company_id": cid}).to_list(length=None)
                    for doc in documents:
                        if '_id' in doc:
                            del doc['_id']
                    backup_data['collections'][collection_name] = documents
                    total_documents += len(documents)
                except Exception as e:
                    logger.warning(f"Failed to backup {collection_name} for {cid}: {str(e)}")
                    backup_data['collections'][collection_name] = []
        
            # Save to database
            backup_data['total_documents'] = total_documents
            backup_data['status'] = 'completed'
            await db.backups.insert_one(backup_data)
            
            # Upload to Google Drive
            if GDRIVE_ENABLED and drive_service:
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f'scheduled_backup_{cid}_{timestamp}.json'
                    temp_file = BACKUP_TEMP_DIR / filename
                    
                    backup_json = backup_data.copy()
                    if '_id' in backup_json:
                        del backup_json['_id']
                    
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(backup_json, f, ensure_ascii=False, indent=2, default=str)
                    
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
                                'drive_link': drive_result.get('webViewLink')
                            }}
                        )
                        
                        logger.info(f"Scheduled backup for {cid} completed and uploaded to Google Drive: {filename}")
                        
                    except Exception as drive_error:
                        logger.warning(f"Scheduled backup for {cid} completed locally only: {str(drive_error)}")
                    
                    # Cleanup
                    if temp_file.exists():
                        os.remove(temp_file)
                        
                except Exception as e:
                    logger.error(f"Failed to process scheduled backup Drive upload for {cid}: {str(e)}")
            else:
                logger.info(f"Scheduled backup for {cid} completed (local only): {total_documents} documents")
        
    except Exception as e:
        logger.error(f"Scheduled backup failed: {str(e)}")

def run_scheduled_backup():
    """Wrapper to run async backup in sync context - uses existing event loop"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside a running event loop (uvicorn), schedule as task
            future = asyncio.run_coroutine_threadsafe(scheduled_backup(), loop)
            try:
                future.result(timeout=120)  # Wait up to 2 minutes
            except Exception as e:
                logger.error(f"Scheduled backup task failed: {str(e)}")
        else:
            loop.run_until_complete(scheduled_backup())
    except RuntimeError as e:
        logger.error(f"Scheduled backup runtime error: {str(e)}")
        try:
            asyncio.run(scheduled_backup())
        except Exception as e2:
            logger.error(f"Scheduled backup fallback also failed: {str(e2)}")

# Schedule backup at 7 PM daily
scheduler.add_job(
    run_scheduled_backup,
    trigger=CronTrigger(hour=19, minute=0),  # 7 PM
    id='daily_backup',
    name='Daily Automatic Backup at 7 PM',
    replace_existing=True
)

@app.on_event("startup")
async def startup_scheduler():
    """Start the scheduler on app startup"""
    scheduler.start()
    logger.info("Backup scheduler started - Daily backup at 7 PM")

@app.on_event("startup")
async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Invoices indexes - most frequently queried
        await db.invoices.create_index("company_id")
        await db.invoices.create_index("customer_id")
        await db.invoices.create_index("date")
        await db.invoices.create_index([("company_id", 1), ("date", -1)])
        await db.invoices.create_index([("company_id", 1), ("customer_id", 1)])
        await db.invoices.create_index([("company_id", 1), ("payment_method", 1)])
        await db.invoices.create_index("invoice_number")
        
        # Customers indexes
        await db.customers.create_index("company_id")
        await db.customers.create_index([("company_id", 1), ("name", 1)])
        await db.customers.create_index("id", unique=True)
        
        # Payments indexes
        await db.payments.create_index("company_id")
        await db.payments.create_index("customer_id")
        await db.payments.create_index("date")
        await db.payments.create_index([("company_id", 1), ("date", -1)])
        await db.payments.create_index([("company_id", 1), ("customer_id", 1)])
        
        # Expenses indexes
        await db.expenses.create_index("company_id")
        await db.expenses.create_index("date")
        await db.expenses.create_index([("company_id", 1), ("date", -1)])
        
        # Raw materials indexes
        await db.raw_materials.create_index("company_id")
        await db.raw_materials.create_index("unit_code")
        await db.raw_materials.create_index([("company_id", 1), ("material_type", 1)])
        
        # Inventory items indexes
        await db.inventory_items.create_index("company_id")
        await db.inventory_items.create_index("name")
        await db.inventory_items.create_index([("company_id", 1), ("name", 1)])
        
        # Treasury transactions indexes
        await db.treasury_transactions.create_index("company_id")
        await db.treasury_transactions.create_index("date")
        await db.treasury_transactions.create_index([("company_id", 1), ("date", -1)])
        
        # Main treasury transactions indexes
        await db.main_treasury_transactions.create_index("company_id")
        await db.main_treasury_transactions.create_index([("company_id", 1), ("date", -1)])
        
        # Suppliers indexes
        await db.suppliers.create_index("company_id")
        await db.suppliers.create_index("id", unique=True)
        
        # Supplier transactions indexes
        await db.supplier_transactions.create_index("company_id")
        await db.supplier_transactions.create_index("supplier_id")
        await db.supplier_transactions.create_index([("company_id", 1), ("date", -1)])
        await db.supplier_transactions.create_index([("supplier_id", 1), ("date", -1)])
        
        # Local products indexes
        await db.local_products.create_index("company_id")
        await db.local_products.create_index("supplier_id")
        
        # Work orders indexes
        await db.work_orders.create_index("company_id")
        await db.work_orders.create_index([("company_id", 1), ("created_at", -1)])
        
        # Deleted invoices indexes
        await db.deleted_invoices.create_index("company_id")
        await db.deleted_invoices.create_index([("company_id", 1), ("deleted_at", -1)])
        
        # Material pricing indexes
        await db.material_pricing.create_index("company_id")
        await db.material_pricing.create_index([("material_type", 1), ("inner_diameter", 1), ("outer_diameter", 1)])
        
        # Backups indexes
        await db.backups.create_index("company_id")
        await db.backups.create_index([("company_id", 1), ("created_at", -1)])
        
        # Invoice edit history indexes
        await db.invoice_edit_history.create_index("invoice_id")
        await db.invoice_edit_history.create_index([("invoice_id", 1), ("edited_at", -1)])
        
        logger.info("Database indexes created successfully for improved performance")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

@app.on_event("shutdown")
async def shutdown_scheduler():
    """Shutdown scheduler"""
    scheduler.shutdown()
    logger.info("Backup scheduler stopped")

# Include routes (MUST be after all API endpoints are defined)
# Already included above via router modules

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
