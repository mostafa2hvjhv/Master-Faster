from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date, timezone
from enum import Enum
import pandas as pd
import io
import json
import tempfile
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
try:
    from google_drive_service import GoogleDriveService
except ImportError:
    GoogleDriveService = None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create temp directory for backups
BACKUP_TEMP_DIR = ROOT_DIR / 'backup_temp'
BACKUP_TEMP_DIR.mkdir(exist_ok=True)

# Google Drive is disabled - using local backups only
GDRIVE_ENABLED = False
drive_service = None
logger.info("Google Drive integration disabled - using local backups only")

# Create the main app without a prefix
app = FastAPI()
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://master-faster.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class SealType(str, Enum):
    RSL = "RSL"
    RS = "RS"
    RSS = "RSS"
    RSE = "RSE"
    B17 = "B17"
    B3 = "B3"
    B14 = "B14"
    B1 = "B1"
    R15 = "R15"
    R17 = "R17"
    W1 = "W1"
    W4 = "W4"
    W5 = "W5"
    W11 = "W11"
    WBT = "WBT"
    XR = "XR"
    CH = "CH"
    VR = "VR"

class MaterialType(str, Enum):
    NBR = "NBR"
    BUR = "BUR"
    BT = "BT"
    VT = "VT"
    BOOM = "BOOM"

class PaymentMethod(str, Enum):
    CASH = "نقدي"
    DEFERRED = "آجل"
    VODAFONE_SAWY = "فودافون 010"
    VODAFONE_WAEL = "كاش 0100"
    INSTAPAY = "انستاباي"
    YAD_ELSAWY = "يد الصاوي"

class ExpenseCategory(str, Enum):
    MATERIALS = "خامات"
    SALARIES = "رواتب"
    ELECTRICITY = "كهرباء"
    MAINTENANCE = "صيانة"
    OTHER = "أخرى"

class InvoiceStatus(str, Enum):
    PAID = "مدفوعة"
    UNPAID = "غير مدفوعة"
    PARTIAL = "مدفوعة جزئياً"
    PENDING = "انتظار"
    COMPLETED = "تم التنفيذ"
    MANUFACTURED = "تم التصنيع"

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password: str
    role: UserRole
    permissions: Optional[List[str]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RawMaterial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    material_type: MaterialType
    inner_diameter: float  # القطر الداخلي
    outer_diameter: float  # القطر الخارجي
    height: float  # الارتفاع بالملي
    pieces_count: int  # عدد القطع
    unit_code: str  # كود الوحدة
    cost_per_mm: float  # تكلفة الملي الواحد
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MaterialPricing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    material_type: MaterialType
    inner_diameter: float  # القطر الداخلي
    outer_diameter: float  # القطر الخارجي
    price_per_mm: float  # سعر الملي الواحد
    manufacturing_cost_client1: float  # تكلفة التصنيع - عميل 1
    manufacturing_cost_client2: float  # تكلفة التصنيع - عميل 2  
    manufacturing_cost_client3: float  # تكلفة التصنيع - عميل 3
    notes: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FinishedProduct(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    seal_type: SealType
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    height: float
    quantity: int
    unit_price: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class InvoiceItem(BaseModel):
    # Fields for manufactured products
    seal_type: Optional[SealType] = None
    material_type: Optional[MaterialType] = None
    inner_diameter: Optional[float] = None
    outer_diameter: Optional[float] = None
    height: Optional[float] = None
    # Common fields
    quantity: int
    unit_price: float
    total_price: float
    # Product type
    product_type: Optional[str] = "manufactured"  # "manufactured" or "local"
    # Fields for local products
    product_name: Optional[str] = None
    supplier: Optional[str] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    local_product_details: Optional[Dict[str, Any]] = None
    # Fields for manufactured products
    material_used: Optional[str] = None  # كود الوحدة للخامة المستخدمة
    material_details: Optional[Dict[str, Any]] = None  # تفاصيل الخامة المختارة
    selected_materials: Optional[List[Dict[str, Any]]] = None  # الخامات المتعددة المختارة
    notes: Optional[str] = None  # ملاحظات على المنتج

class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    customer_id: Optional[str] = None
    customer_name: str
    invoice_title: Optional[str] = None  # عنوان الفاتورة
    supervisor_name: Optional[str] = None  # اسم المشرف
    items: List[InvoiceItem]
    subtotal: Optional[float] = None  # المجموع الفرعي قبل الخصم
    discount: Optional[float] = 0.0  # مبلغ الخصم
    discount_type: Optional[str] = "amount"  # نوع الخصم: amount أو percentage
    discount_value: Optional[float] = 0.0  # القيمة المدخلة للخصم
    total_after_discount: Optional[float] = None  # الإجمالي بعد الخصم
    total_amount: float  # الإجمالي النهائي (same as total_after_discount for compatibility)
    display_amount: Optional[float] = None  # المبلغ المعروض في السجل (للتعديل بدون تأثير على الرصيد)
    display_description: Optional[str] = None  # الوصف المعروض في السجل
    display_reference: Optional[str] = None  # المرجع المعروض في السجل
    paid_amount: float = 0.0
    remaining_amount: float
    payment_method: PaymentMethod
    status: InvoiceStatus
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    
    class Config:
        use_enum_values = True

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str
    amount: float
    payment_method: PaymentMethod
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    
    class Config:
        use_enum_values = True

class Expense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    amount: float
    category: ExpenseCategory
    date: datetime = Field(default_factory=datetime.utcnow)

class WorkOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    description: Optional[str] = None
    supervisor_name: Optional[str] = None  # اسم المشرف على التصنيع
    is_daily: bool = False  # هل هو أمر شغل يومي تلقائي
    work_date: Optional[str] = None  # تاريخ العمل للأوامر اليومية (stored as string)
    invoices: List[Dict[str, Any]] = Field(default_factory=list)  # الفواتير المرتبطة
    total_amount: float = 0.0
    total_items: int = 0
    status: str = "جديد"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # For backward compatibility
    invoice_id: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)

# Request Models
class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None

class RawMaterialCreate(BaseModel):
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    height: float
    pieces_count: int
    unit_code: Optional[str] = None  # سيتم توليده تلقائياً
    cost_per_mm: float

class FinishedProductCreate(BaseModel):
    seal_type: SealType
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    height: float
    quantity: int
    unit_price: float

class InvoiceCreate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: str
    invoice_title: Optional[str] = None  # عنوان الفاتورة
    supervisor_name: Optional[str] = None  # اسم المشرف
    items: List[InvoiceItem]
    payment_method: PaymentMethod
    discount_type: Optional[str] = "amount"  # نوع الخصم: amount أو percentage
    discount_value: Optional[float] = 0.0  # القيمة المدخلة للخصم
    notes: Optional[str] = None
    
    class Config:
        use_enum_values = True

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float
    payment_method: PaymentMethod
    notes: Optional[str] = None
    
    class Config:
        use_enum_values = True

class TreasuryTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str  # نوع الحساب (cash, vodafone_elsawy, etc.)
    transaction_type: str  # income, expense, transfer_in, transfer_out
    amount: float
    description: str
    reference: Optional[str] = None
    related_transaction_id: Optional[str] = None  # للتحويلات
    date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Supplier and Local Product Models
class Supplier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    total_purchases: Optional[float] = 0.0  # إجمالي المشتريات
    total_paid: Optional[float] = 0.0  # إجمالي المدفوع
    balance: Optional[float] = 0.0  # الرصيد المستحق
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LocalProduct(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    supplier_id: str
    supplier_name: str
    purchase_price: float
    selling_price: float
    current_stock: Optional[int] = 0
    total_purchased: Optional[int] = 0
    total_sold: Optional[int] = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SupplierTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier_id: str
    supplier_name: str
    transaction_type: str  # "purchase" or "payment"
    amount: float
    description: str
    product_name: Optional[str] = None  # للمشتريات
    quantity: Optional[int] = None  # للمشتريات
    unit_price: Optional[float] = None  # للمشتريات
    payment_method: Optional[str] = None  # للدفعات
    reference_invoice_id: Optional[str] = None  # مرجع الفاتورة إذا كان من بيع منتج محلي
    date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Inventory Management Models
class InventoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    available_pieces: int  # تغيير من available_height إلى available_pieces
    min_stock_level: Optional[int] = 2  # الحد الأدنى 2 قطعة
    # إزالة max_stock_level و unit_code
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class InventoryTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inventory_item_id: str
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    transaction_type: str  # "in" (إضافة) أو "out" (استهلاك)
    pieces_change: int  # التغيير في عدد القطع (موجب للإضافة، سالب للاستهلاك)
    remaining_pieces: int  # عدد القطع المتبقية بعد المعاملة
    reason: str  # سبب المعاملة
    reference_id: Optional[str] = None  # مرجع المعاملة (فاتورة، طلب خام، إلخ)
    notes: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TreasuryTransactionCreate(BaseModel):
    account_id: str
    transaction_type: str
    amount: float
    description: str
    reference: Optional[str] = None

class SupplierCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None

class LocalProductCreate(BaseModel):
    name: str
    supplier_id: str
    purchase_price: float
    selling_price: float
    current_stock: Optional[int] = 0

class SupplierTransactionCreate(BaseModel):
    supplier_id: str
    transaction_type: str
    amount: float
    description: str
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    payment_method: Optional[str] = None

class InventoryItemCreate(BaseModel):
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    available_pieces: int  # تغيير من available_height إلى available_pieces
    min_stock_level: Optional[int] = 2  # الحد الأدنى 2 قطعة
    notes: Optional[str] = None

class InventoryTransactionCreate(BaseModel):
    inventory_item_id: Optional[str] = None  # يمكن أن يكون فارغ للإضافة التلقائية
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    transaction_type: str
    pieces_change: int  # التغيير في عدد القطع
    reason: str
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    related_transaction_id: Optional[str] = None

class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float
    notes: Optional[str] = None

class ExpenseCreate(BaseModel):
    description: str
    amount: float
    category: ExpenseCategory

class CompatibilityCheck(BaseModel):
    seal_type: SealType
    inner_diameter: float
    outer_diameter: float
    height: float
    material_type: Optional[MaterialType] = None

# Main Treasury Models
class MainTreasuryPassword(BaseModel):
    id: str = Field(default_factory=lambda: "main_treasury_password")
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MainTreasuryTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_type: str  # "deposit" (إيداع), "withdrawal" (صرف), "transfer_from_yad" (ترحيل من يد الصاوي)
    amount: float
    description: str  # السبب/الوصف
    reference: Optional[str] = None
    balance_after: float  # الرصيد بعد العملية
    performed_by: str  # اسم المستخدم الذي نفذ العملية
    date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MainTreasuryTransactionCreate(BaseModel):
    transaction_type: str
    amount: float
    description: str
    reference: Optional[str] = None

class PasswordVerify(BaseModel):
    password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# Deleted Invoices Password Models
class DeletedInvoicesPassword(BaseModel):
    id: str = Field(default_factory=lambda: "deleted_invoices_password")
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Invoice Operations Password Model
class InvoiceOperationsPassword(BaseModel):
    id: str = Field(default_factory=lambda: "invoice_operations_password")
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Company mapping - each user belongs to a company
COMPANY_MAP = {
    "Elsawy": "elsawy",
    "master": "elsawy",
    "Root": "elsawy",
    "Faster": "faster",
}

# Auth endpoints
@api_router.post("/auth/login")
async def login(username: str, password: str):
    # Check predefined users
    predefined_users = {
        "Elsawy": {"password": "100100", "role": "admin"},
        "master": {"password": "146200", "role": "master"},
        "Root": {"password": "master", "role": "user"},
        "Faster": {"password": "100200", "role": "admin"},
    }
    
    if username in predefined_users and predefined_users[username]["password"] == password:
        company_id = COMPANY_MAP.get(username, "elsawy")
        return {
            "success": True,
            "user": {
                "username": username,
                "role": predefined_users[username]["role"],
                "company_id": company_id
            }
        }
    
    # Check database users
    user = await db.users.find_one({"username": username, "password": password})
    if user:
        company_id = user.get("company_id", "elsawy")
        return {
            "success": True,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "company_id": company_id
            }
        }
    
    raise HTTPException(status_code=401, detail="خطأ في اسم المستخدم أو كلمة المرور")

# Migration endpoint - assign company_id to existing data
@api_router.post("/migrate-company-id")
async def migrate_company_id():
    """Add company_id='elsawy' to all existing documents that don't have one"""
    collections = [
        'customers', 'suppliers', 'invoices', 'payments', 'expenses',
        'raw_materials', 'finished_products', 'inventory', 'inventory_transactions',
        'local_products', 'supplier_transactions', 'treasury_transactions',
        'work_orders', 'users', 'deleted_invoices', 'company_settings'
    ]
    
    total_updated = 0
    for col_name in collections:
        result = await db[col_name].update_many(
            {"company_id": {"$exists": False}},
            {"$set": {"company_id": "elsawy"}}
        )
        total_updated += result.modified_count
    
    return {"message": f"تم ترحيل {total_updated} سجل بنجاح", "total_updated": total_updated}


# User management endpoints
@api_router.post("/users", response_model=User)
async def create_user(user: User):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="اسم المستخدم موجود بالفعل")
    
    await db.users.insert_one(user.dict())
    return user

@api_router.get("/users", response_model=List[User])
async def get_users():
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return User(**user)

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user: User):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": user.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return {"message": "تم تحديث المستخدم بنجاح"}

@api_router.delete("/users/clear-all")
async def clear_all_users():
    # Don't delete default users, only custom ones
    result = await db.users.delete_many({"username": {"$nin": ["Elsawy", "Root"]}})
    return {"message": f"تم حذف {result.deleted_count} مستخدم", "deleted_count": result.deleted_count}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return {"message": "تم حذف المستخدم بنجاح"}

# Dashboard endpoints
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(company_id: str = "elsawy"):
    # Get totals from database
    cf = {"company_id": company_id}
    invoices = list(await db.invoices.find(cf).to_list(1000))
    expenses = list(await db.expenses.find(cf).to_list(1000))
    customers = list(await db.customers.find(cf).to_list(1000))
    
    total_sales = sum(invoice.get("total_amount", 0) for invoice in invoices)
    total_expenses = sum(expense.get("amount", 0) for expense in expenses)
    total_unpaid = sum(invoice.get("remaining_amount", 0) for invoice in invoices if invoice.get("remaining_amount", 0) > 0)
    
    return {
        "total_sales": total_sales,
        "total_expenses": total_expenses,
        "net_profit": total_sales - total_expenses,
        "total_unpaid": total_unpaid,
        "invoice_count": len(invoices),
        "customer_count": len(customers)
    }

# Customer endpoints
@api_router.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate, company_id: str = "elsawy"):
    # Check if customer already exists (by name or phone) within same company
    existing_by_name = await db.customers.find_one({"name": customer.name, "company_id": company_id})
    if existing_by_name:
        raise HTTPException(
            status_code=409, 
            detail=f"عميل بنفس الاسم موجود بالفعل: {customer.name}"
        )
    
    # Check by phone if provided
    if customer.phone:
        existing_by_phone = await db.customers.find_one({"phone": customer.phone, "company_id": company_id})
        if existing_by_phone:
            raise HTTPException(
                status_code=409, 
                detail=f"عميل بنفس رقم الهاتف موجود بالفعل: {customer.phone}"
            )
    
    customer_dict = customer.dict()
    customer_obj = Customer(**customer_dict)
    obj = customer_obj.dict()
    obj["company_id"] = company_id
    await db.customers.insert_one(obj)
    return customer_obj

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(company_id: str = "elsawy"):
    customers = await db.customers.find({"company_id": company_id}).to_list(1000)
    return [Customer(**customer) for customer in customers]

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return Customer(**customer)

@api_router.delete("/customers/clear-all")
async def clear_all_customers(company_id: str = "elsawy"):
    result = await db.customers.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} عميل", "deleted_count": result.deleted_count}

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    result = await db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return {"message": "تم حذف العميل بنجاح"}

# Customer Statement API (كشف الحساب)
@api_router.get("/customer-statement/{customer_id}")
async def get_customer_statement(
    customer_id: str,
    from_date: str = None,
    to_date: str = None
):
    """Get customer account statement (كشف حساب)"""
    try:
        # Find customer
        customer = await db.customers.find_one({"id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="العميل غير موجود")
        
        # Check if customer is also a supplier
        supplier = await db.suppliers.find_one({"name": customer.get("name")})
        
        # Build date filter
        date_filter = {}
        if from_date:
            date_filter["$gte"] = from_date
        if to_date:
            date_filter["$lte"] = to_date
        
        # Get all invoices for this customer
        invoice_query = {"customer_id": customer_id}
        if date_filter:
            invoice_query["created_at"] = date_filter
        
        invoices = await db.invoices.find(invoice_query).sort("created_at", 1).to_list(length=None)
        
        # Get all payments for this customer's invoices
        invoice_ids = [inv.get("id") for inv in invoices]
        payments = []
        if invoice_ids:
            payment_query = {"invoice_id": {"$in": invoice_ids}}
            if date_filter:
                payment_query["payment_date"] = date_filter
            payments = await db.payments.find(payment_query).sort("payment_date", 1).to_list(length=None)
        
        # Get supplier transactions if customer is also a supplier
        supplier_transactions = []
        if supplier:
            supplier_query = {"supplier_id": supplier.get("id")}
            if date_filter:
                supplier_query["transaction_date"] = date_filter
            supplier_transactions = await db.supplier_transactions.find(supplier_query).sort("transaction_date", 1).to_list(length=None)
        
        # Build transactions list
        transactions = []
        running_balance = 0
        
        # Add invoices (دائن - Credit)
        for invoice in invoices:
            transaction_date = invoice.get("created_at", "")
            amount = invoice.get("total_amount", 0)
            running_balance += amount
            
            transactions.append({
                "date": transaction_date,
                "type": "فاتورة مبيعات",
                "description": f"فاتورة رقم {invoice.get('invoice_number')}",
                "reference": invoice.get("invoice_number"),
                "debit": 0,  # مدين
                "credit": amount,  # دائن
                "balance": running_balance
            })
        
        # Add payments (مدين - Debit)
        for payment in payments:
            transaction_date = payment.get("payment_date", "")
            amount = payment.get("amount", 0)
            running_balance -= amount
            
            # Find invoice number
            invoice_number = "غير محدد"
            for inv in invoices:
                if inv.get("id") == payment.get("invoice_id"):
                    invoice_number = inv.get("invoice_number")
                    break
            
            transactions.append({
                "date": transaction_date,
                "type": "دفعة",
                "description": f"دفعة على فاتورة {invoice_number} - {payment.get('payment_method')}",
                "reference": invoice_number,
                "debit": amount,  # مدين
                "credit": 0,  # دائن
                "balance": running_balance
            })
        
        # Add supplier transactions if exists (purchases from customer as supplier)
        for trans in supplier_transactions:
            transaction_date = trans.get("transaction_date", "")
            trans_type = trans.get("transaction_type", "")
            amount = trans.get("amount", 0)
            
            if trans_type == "purchase":
                # شراء منتج من العميل (كمورد) = مدين (سالب)
                running_balance -= amount
                transactions.append({
                    "date": transaction_date,
                    "type": "مشتريات",
                    "description": f"شراء من {customer.get('name')} - {trans.get('description', '')}",
                    "reference": trans.get("id"),
                    "debit": amount,  # مدين
                    "credit": 0,  # دائن
                    "balance": running_balance
                })
            elif trans_type == "payment":
                # دفع للمورد = مدين (سالب)
                running_balance -= amount
                transactions.append({
                    "date": transaction_date,
                    "type": "دفع للمورد",
                    "description": f"دفع لـ {customer.get('name')} - {trans.get('payment_method')}",
                    "reference": trans.get("id"),
                    "debit": amount,  # مدين
                    "credit": 0,  # دائن
                    "balance": running_balance
                })
        
        # Sort all transactions by date
        transactions.sort(key=lambda x: x.get("date", ""))
        
        # Recalculate running balance
        balance = 0
        for trans in transactions:
            balance += trans.get("credit", 0) - trans.get("debit", 0)
            trans["balance"] = balance
        
        # Calculate totals
        total_credit = sum(t.get("credit", 0) for t in transactions)
        total_debit = sum(t.get("debit", 0) for t in transactions)
        final_balance = total_credit - total_debit
        
        return {
            "customer": {
                "id": customer.get("id"),
                "name": customer.get("name"),
                "phone": customer.get("phone", ""),
                "is_also_supplier": supplier is not None
            },
            "period": {
                "from_date": from_date or "البداية",
                "to_date": to_date or "الآن"
            },
            "transactions": transactions,
            "summary": {
                "total_credit": total_credit,  # إجمالي الدائن
                "total_debit": total_debit,  # إجمالي المدين
                "final_balance": final_balance  # الرصيد النهائي
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Raw materials endpoints
# Material code generation helper
async def generate_unit_code(material_type: str, inner_diameter: float, outer_diameter: float):
    """Generate automatic unit code based on material type and specifications"""
    # Material type to prefix mapping
    type_prefix = {
        "BUR": "B",
        "NBR": "N", 
        "BT": "T",
        "VT": "V",
        "BOOM": "M"
    }
    
    prefix = type_prefix.get(material_type, "X")  # Default to X if type not found
    
    # Find existing materials with same specifications
    existing_materials = await db.raw_materials.find({
        "material_type": material_type,
        "inner_diameter": inner_diameter,
        "outer_diameter": outer_diameter
    }).to_list(None)
    
    # Get the highest sequence number
    max_sequence = 0
    for mat in existing_materials:
        unit_code = mat.get("unit_code", "")
        if unit_code.startswith(f"{prefix}-"):
            try:
                sequence = int(unit_code.split("-")[1])
                max_sequence = max(max_sequence, sequence)
            except (IndexError, ValueError):
                continue
    
    # Generate new code with next sequence number
    new_sequence = max_sequence + 1
    return f"{prefix}-{new_sequence}"

@api_router.post("/raw-materials", response_model=RawMaterial)
async def create_raw_material(material: RawMaterialCreate, company_id: str = "elsawy"):
    """Create raw material with inventory check and automatic unit code"""
    try:
        # Generate automatic unit code
        auto_unit_code = await generate_unit_code(
            material.material_type,
            material.inner_diameter, 
            material.outer_diameter
        )
        
        # Check inventory availability
        inventory_check = await check_inventory_availability(
            material_type=material.material_type,
            inner_diameter=material.inner_diameter,
            outer_diameter=material.outer_diameter,
            required_pieces=material.pieces_count
        )
        
        if not inventory_check["available"]:
            raise HTTPException(
                status_code=400, 
                detail=f"لا يمكن إضافة المادة الخام. {inventory_check['message']}. المطلوب: {material.pieces_count} قطعة، المتاح: {inventory_check['available_pieces']} قطعة"
            )
        
        # Create raw material with auto-generated unit code
        material_dict = material.dict()
        material_dict["unit_code"] = auto_unit_code  # Override with auto-generated code
        material_obj = RawMaterial(**material_dict)
        obj = material_obj.dict()
        obj["company_id"] = company_id
        await db.raw_materials.insert_one(obj)
        
        # Deduct from inventory
        deduction_amount = material.height * material.pieces_count
        inventory_transaction = InventoryTransactionCreate(
            inventory_item_id=inventory_check["inventory_item_id"],
            material_type=material.material_type,
            inner_diameter=material.inner_diameter,
            outer_diameter=material.outer_diameter,
            transaction_type="out",
            pieces_change=-material.pieces_count,
            reason=f"إضافة مادة خام جديدة: {auto_unit_code}",
            reference_id=material_obj.id,
            notes=f"خصم {material.pieces_count} قطعة لإنتاج {material.pieces_count} قطعة بارتفاع {material.height} مم لكل قطعة"
        )
        
        # Create inventory transaction
        await create_inventory_transaction(inventory_transaction)
        
        return material_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/raw-materials", response_model=List[RawMaterial])
async def get_raw_materials(company_id: str = "elsawy"):
    """Get all raw materials sorted by material type priority then size"""
    # Define material type priority order: BUR-NBR-BT-BOOM-VT
    material_priority = {'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5}
    
    # Get all materials first
    materials = await db.raw_materials.find({"company_id": company_id}).to_list(1000)
    
    # Sort by material type priority, then by diameter
    sorted_materials = sorted(materials, key=lambda x: (
        material_priority.get(x.get('material_type', ''), 6),  # Material priority
        x.get('inner_diameter', 0),  # Then inner diameter
        x.get('outer_diameter', 0)   # Then outer diameter
    ))
    
    return [RawMaterial(**material) for material in sorted_materials]

@api_router.put("/raw-materials/{material_id}")
async def update_raw_material(material_id: str, material: RawMaterialCreate):
    result = await db.raw_materials.update_one(
        {"id": material_id},
        {"$set": material.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="المادة غير موجودة")
    return {"message": "تم تحديث المادة بنجاح"}

@api_router.delete("/raw-materials/clear-all")
async def clear_all_raw_materials(company_id: str = "elsawy"):
    result = await db.raw_materials.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} مادة خام", "deleted_count": result.deleted_count}

@api_router.delete("/raw-materials/{material_id}")
async def delete_raw_material(material_id: str):
    result = await db.raw_materials.delete_one({"id": material_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="المادة غير موجودة")
    return {"message": "تم حذف المادة بنجاح"}

# Finished products endpoints
@api_router.post("/finished-products", response_model=FinishedProduct)
async def create_finished_product(product: FinishedProductCreate, company_id: str = "elsawy"):
    product_dict = product.dict()
    product_obj = FinishedProduct(**product_dict)
    obj = product_obj.dict()
    obj["company_id"] = company_id
    await db.finished_products.insert_one(obj)
    return product_obj

@api_router.get("/finished-products", response_model=List[FinishedProduct])
async def get_finished_products(company_id: str = "elsawy"):
    products = await db.finished_products.find({"company_id": company_id}).to_list(1000)
    return [FinishedProduct(**product) for product in products]

@api_router.delete("/finished-products/clear-all")
async def clear_all_finished_products(company_id: str = "elsawy"):
    result = await db.finished_products.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} منتج جاهز", "deleted_count": result.deleted_count}

@api_router.delete("/finished-products/{product_id}")
async def delete_finished_product(product_id: str):
    result = await db.finished_products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    return {"message": "تم حذف المنتج بنجاح"}

@api_router.put("/finished-products/{product_id}")
async def update_finished_product(product_id: str, product_update: FinishedProductCreate):
    updated_data = product_update.dict()
    
    # Check if product exists
    existing_product = await db.finished_products.find_one({"id": product_id})
    if not existing_product:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    
    # Update the product
    result = await db.finished_products.update_one(
        {"id": product_id},
        {"$set": updated_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="لم يتم تحديث أي بيانات")
    
    # Get updated product
    updated_product = await db.finished_products.find_one({"id": product_id})
    if "_id" in updated_product:
        del updated_product["_id"]
    
    return updated_product

# Compatibility check endpoint
@api_router.post("/compatibility-check")
async def check_compatibility(check: CompatibilityCheck):
    # Get raw materials
    raw_materials = await db.raw_materials.find().to_list(1000)
    finished_products = await db.finished_products.find().to_list(1000)
    
    compatible_materials = []
    compatible_products = []
    
    # Define tolerance ranges for better compatibility matching
    # Especially important for converted measurements from inches
    tolerance_percentage = 0.1  # 10% tolerance
    
    inner_tolerance = check.inner_diameter * tolerance_percentage
    outer_tolerance = check.outer_diameter * tolerance_percentage
    height_tolerance = max(5.0, check.height * tolerance_percentage)  # Minimum 5mm or 10%
    
    # Check raw materials
    for material in raw_materials:
        # Remove MongoDB ObjectId if present
        if "_id" in material:
            del material["_id"]
            
        # Material type filter - if specified, only show materials of that type
        if check.material_type and material.get("material_type") != check.material_type:
            continue
            
        # CRITICAL: Filter materials based on usability after consumption
        # Don't show materials if using them would leave < 15mm (unusable waste)
        if material.get("height", 0) <= 15:
            continue
            
        # Calculate required material height for one seal
        required_height_per_seal = check.height + 2
        
        # Check if material can produce at least 1 seal AND remain >= 15mm or become 0
        material_height = material.get("height", 0)
        remaining_after_one_seal = material_height - required_height_per_seal
        
        # Skip material if it would leave unusable waste (1-14mm range)
        if remaining_after_one_seal > 0 and remaining_after_one_seal < 15:
            continue
        
        inner_compatible = material["inner_diameter"] <= (check.inner_diameter + inner_tolerance)
        outer_compatible = material["outer_diameter"] >= (check.outer_diameter - outer_tolerance)
        height_compatible = material_height >= required_height_per_seal
        
        if inner_compatible and outer_compatible and height_compatible:
            
            warning = ""
            compatibility_score = 100
            
            # Calculate compatibility warnings and scoring
            if material["height"] < (check.height + 5):
                warning = "تحذير: الارتفاع قريب من الحد الأدنى"
                compatibility_score -= 10
            
            if material["inner_diameter"] > check.inner_diameter:
                warning += " - القطر الداخلي أكبر قليلاً"
                compatibility_score -= 5
                
            if material["outer_diameter"] < check.outer_diameter:
                warning += " - القطر الخارجي أصغر قليلاً" 
                compatibility_score -= 5
            
            # Add exact match bonus
            if (abs(material["inner_diameter"] - check.inner_diameter) < 1 and
                abs(material["outer_diameter"] - check.outer_diameter) < 1):
                compatibility_score += 10
                if not warning:
                    warning = "مطابقة ممتازة"
            
            compatible_materials.append({
                **material,
                "warning": warning.strip(" -"),
                "compatibility_score": compatibility_score,
                "low_stock": material.get("height", 0) < 20,
                "tolerance_used": {
                    "inner_tolerance": inner_tolerance,
                    "outer_tolerance": outer_tolerance,
                    "height_tolerance": height_tolerance
                }
            })
    
    # Sort by compatibility score (highest first)
    compatible_materials.sort(key=lambda x: x.get("compatibility_score", 0), reverse=True)
    
    # Check finished products (keep exact matching for finished products)
    for product in finished_products:
        # Remove MongoDB ObjectId if present
        if "_id" in product:
            del product["_id"]
            
        # Check seal type and material compatibility with small tolerance
        inner_match = abs(product["inner_diameter"] - check.inner_diameter) <= 1
        outer_match = abs(product["outer_diameter"] - check.outer_diameter) <= 1
        height_match = abs(product["height"] - check.height) <= 1
        
        if (product["seal_type"] == check.seal_type and
            inner_match and outer_match and height_match):
            compatible_products.append(product)
    
    return {
        "compatible_materials": compatible_materials,
        "compatible_products": compatible_products,
        "search_criteria": {
            "inner_diameter": check.inner_diameter,
            "outer_diameter": check.outer_diameter, 
            "height": check.height,
            "tolerances_applied": {
                "inner_tolerance": inner_tolerance,
                "outer_tolerance": outer_tolerance,
                "height_tolerance": height_tolerance
            }
        }
    }

# Invoice endpoints
@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice: InvoiceCreate, supervisor_name: str = "", company_id: str = "elsawy"):
    # Generate invoice number (per company)
    invoice_count = await db.invoices.count_documents({"company_id": company_id})
    invoice_number = f"INV-{invoice_count + 1:06d}"
    
    # Calculate totals with discount
    subtotal = sum(item.total_price for item in invoice.items)
    
    # Handle discount calculation
    discount_amount = 0.0
    if hasattr(invoice, 'discount') and invoice.discount is not None:
        discount_amount = invoice.discount
    elif hasattr(invoice, 'discount_value') and invoice.discount_value is not None:
        # Calculate discount based on type
        if hasattr(invoice, 'discount_type') and invoice.discount_type == 'percentage':
            discount_amount = (subtotal * invoice.discount_value) / 100
        else:
            discount_amount = invoice.discount_value
    
    total_after_discount = subtotal - discount_amount
    remaining_amount = total_after_discount if str(invoice.payment_method) == "آجل" else 0
    status = InvoiceStatus.PENDING  # Always start with PENDING status
    
    invoice_dict = invoice.dict()
    invoice_obj = Invoice(
        invoice_number=invoice_number,
        subtotal=subtotal,
        discount=discount_amount,
        total_after_discount=total_after_discount,
        total_amount=total_after_discount,  # للتوافق مع الكود الموجود
        remaining_amount=remaining_amount,
        status=status,
        **invoice_dict
    )
    
    # Update inventory and handle local products
    for item in invoice.items:
        if hasattr(item, 'product_type') and item.product_type == 'local':
            # Handle local product sale
            if hasattr(item, 'local_product_details') and item.local_product_details:
                # Update local product stock
                await db.local_products.update_one(
                    {"name": item.local_product_details.get("name"), 
                     "supplier": item.local_product_details.get("supplier")},
                    {"$inc": {"total_sold": item.quantity}}
                )
                
                # Create supplier transaction for purchase cost
                supplier_transaction = SupplierTransaction(
                    supplier_id="", # We'll need to find this based on supplier name
                    supplier_name=item.local_product_details.get("supplier", ""),
                    transaction_type="purchase",
                    amount=item.local_product_details.get("purchase_price", 0) * item.quantity,
                    description=f"شراء {item.local_product_details.get('name')} من فاتورة {invoice_number}",
                    product_name=item.local_product_details.get("name", ""),
                    quantity=item.quantity,
                    unit_price=item.local_product_details.get("purchase_price", 0),
                    reference_invoice_id=invoice_obj.id
                )
                
                # Find supplier by name to get ID
                supplier = await db.suppliers.find_one({"name": item.local_product_details.get("supplier", "")})
                if supplier:
                    supplier_transaction.supplier_id = supplier["id"]
                    await db.supplier_transactions.insert_one(supplier_transaction.dict())
                    
                    # Update supplier balance
                    purchase_amount = item.local_product_details.get("purchase_price", 0) * item.quantity
                    await db.suppliers.update_one(
                        {"id": supplier["id"]},
                        {
                            "$inc": {
                                "total_purchases": purchase_amount,
                                "balance": purchase_amount,
                                "current_balance": purchase_amount  # Update both fields
                            }
                        }
                    )
        else:
            # Handle manufactured products - deduct from material height
            material_deducted = False  # Flag to prevent double deduction
            
            # Prioritize multi-material selection over single material selection
            if hasattr(item, 'selected_materials') and item.selected_materials and not material_deducted:
                # Handle multiple materials with specified seal counts
                for material_info in item.selected_materials:
                    raw_material = await db.raw_materials.find_one({
                        "unit_code": material_info.get("unit_code"),
                        "inner_diameter": material_info.get("inner_diameter"),
                        "outer_diameter": material_info.get("outer_diameter")
                    })
                    
                    if raw_material:
                        seal_consumption_per_piece = item.height + 2
                        seals_to_produce = material_info.get("seals_count", 0)
                        material_consumption = seals_to_produce * seal_consumption_per_piece
                        current_height = raw_material.get("height", 0)
                        
                        if current_height >= material_consumption:
                            # Deduct from this material
                            await db.raw_materials.update_one(
                                {"id": raw_material["id"]},
                                {"$inc": {"height": -material_consumption}}
                            )
                            
                            remaining_height = current_height - material_consumption
                            print(f"✅ تم خصم {material_consumption} مم من الخامة {raw_material.get('unit_code', 'غير محدد')} لإنتاج {seals_to_produce} سيل - المتبقي: {remaining_height} مم")
                        else:
                            print(f"❌ خطأ: لا يوجد ارتفاع كافٍ في الخامة {raw_material.get('unit_code', 'غير محدد')} - مطلوب: {material_consumption} مم، متوفر: {current_height} مم")
                    else:
                        print(f"❌ خطأ: لم يتم العثور على الخامة {material_info.get('unit_code', 'غير محدد')}")
                
                material_deducted = True
                print(f"🎉 تم خصم المواد من {len(item.selected_materials)} خامة مختلفة")
                
            # Prioritize material_details (single material) if no multi-material selection
            elif item.material_details and not material_deducted:
                material_details = item.material_details
                if not material_details.get('is_finished_product', False):
                    # Find the specific material selected by user
                    raw_material = None
                    
                    # Search by inner_diameter + outer_diameter + unit_code together for highest accuracy
                    if (material_details.get("inner_diameter") and 
                        material_details.get("outer_diameter") and 
                        material_details.get("unit_code")):
                        raw_material = await db.raw_materials.find_one({
                            "inner_diameter": material_details.get("inner_diameter"),
                            "outer_diameter": material_details.get("outer_diameter"),
                            "unit_code": material_details.get("unit_code")
                        })
                    
                    # If not found by dimensions + unit_code, try by specifications only
                    if not raw_material and material_details.get("material_type"):
                        raw_material = await db.raw_materials.find_one({
                            "material_type": material_details.get("material_type"),
                            "inner_diameter": material_details.get("inner_diameter"),
                            "outer_diameter": material_details.get("outer_diameter")
                        })
                    
                    if raw_material:
                        # Calculate actual seals to be made from this material
                        seal_consumption_per_piece = item.height + 2
                        total_seals_requested = item.quantity
                        material_height = raw_material.get("height", 0)
                        
                        # Calculate maximum seals possible from this material
                        max_possible_seals = int(material_height // seal_consumption_per_piece)
                        
                        # Check if remaining height would be unusable (< 15mm but > 0)
                        remaining_after_max = material_height - (max_possible_seals * seal_consumption_per_piece)
                        if remaining_after_max > 0 and remaining_after_max < 15 and max_possible_seals > 0:
                            max_possible_seals -= 1  # Reduce by 1 to avoid unusable remainder
                        
                        # Determine actual seals to produce (limited by material availability)
                        actual_seals_to_produce = min(total_seals_requested, max_possible_seals)
                        material_consumption = actual_seals_to_produce * seal_consumption_per_piece
                        
                        if actual_seals_to_produce > 0 and material_height >= material_consumption:
                            # Deduct from material height
                            await db.raw_materials.update_one(
                                {"id": raw_material["id"]},
                                {"$inc": {"height": -material_consumption}}
                            )
                            
                            material_deducted = True
                            remaining_height = material_height - material_consumption
                            
                            if actual_seals_to_produce < total_seals_requested:
                                print(f"⚠️ تم خصم {material_consumption} مم من الخامة {raw_material.get('unit_code', 'غير محدد')} لإنتاج {actual_seals_to_produce} سيل من أصل {total_seals_requested} سيل - المتبقي: {remaining_height} مم")
                                print(f"📌 ملاحظة: يحتاج المستخدم لاختيار خامة أخرى لإنتاج الـ {total_seals_requested - actual_seals_to_produce} سيل المتبقية")
                            else:
                                print(f"✅ تم خصم {material_consumption} مم من الخامة {raw_material.get('unit_code', 'غير محدد')} لإنتاج جميع الـ {total_seals_requested} سيل - المتبقي: {remaining_height} مم")
                        else:
                            if max_possible_seals <= 0:
                                print(f"❌ خطأ: الخامة {raw_material.get('unit_code', 'غير محدد')} لا تكفي لإنتاج أي سيل - الارتفاع: {material_height} مم، المطلوب: {seal_consumption_per_piece} مم للسيل الواحد")
                            else:
                                print(f"❌ خطأ: لا يوجد ارتفاع كافٍ في الخامة {raw_material.get('unit_code', 'غير محدد')} - مطلوب: {material_consumption} مم، متوفر: {material_height} مم")
                    else:
                        print(f"❌ خطأ: لم يتم العثور على الخامة المحددة - {material_details.get('material_type')} {material_details.get('inner_diameter')}×{material_details.get('outer_diameter')} كود: {material_details.get('unit_code', 'غير محدد')}")
            
            # Fallback to material_used only if material_details didn't work and no deduction happened
            if item.material_used and not material_deducted:
                # Find the raw material by unit_code only (less accurate fallback)
                raw_material = await db.raw_materials.find_one({"unit_code": item.material_used})
                
                if raw_material:
                    # Calculate required material consumption (seal height + 2mm waste) * quantity
                    material_consumption = (item.height + 2) * item.quantity
                    
                    # Check if there's enough height available
                    current_height = raw_material.get("height", 0)
                    if current_height >= material_consumption:
                        # Deduct from material height
                        await db.raw_materials.update_one(
                            {"unit_code": item.material_used},
                            {"$inc": {"height": -material_consumption}}
                        )
                        
                        material_deducted = True
                        print(f"⚠️ تم خصم {material_consumption} مم من ارتفاع الخامة {item.material_used} (بحث بكود الوحدة فقط - أقل دقة)")
                    else:
                        print(f"❌ تحذير: لا يوجد ارتفاع كافٍ في الخامة {item.material_used} - مطلوب: {material_consumption} مم، متوفر: {current_height} مم")
                else:
                    print(f"❌ تحذير: الخامة {item.material_used} غير موجودة في المواد الخام")
    
    invoice_data = invoice_obj.dict()
    invoice_data["company_id"] = company_id
    await db.invoices.insert_one(invoice_data)
    
    # Add treasury transaction for non-deferred payments
    if str(invoice.payment_method) != "آجل":  # التحقق من النص العربي
        # Map payment methods to treasury account IDs
        payment_method_mapping = {
            "نقدي": "cash",
            "فودافون 010": "vodafone_elsawy", 
            "كاش 0100": "vodafone_wael",
            "انستاباي": "instapay",
            "يد الصاوي": "yad_elsawy"
        }
        
        account_id = payment_method_mapping.get(str(invoice.payment_method), "cash")
        
        # Check if treasury transaction already exists for this invoice
        existing_transaction = await db.treasury_transactions.find_one({
            "reference": f"invoice_{invoice_obj.id}"
        })
        
        if not existing_transaction:
            treasury_transaction = TreasuryTransaction(
                account_id=account_id,
                transaction_type="income",
                amount=total_after_discount,
                description=f"فاتورة {invoice_number} - {invoice.customer_name}",
                reference=f"invoice_{invoice_obj.id}"
            )
            treasury_dict = treasury_transaction.dict()
            treasury_dict["company_id"] = company_id
            await db.treasury_transactions.insert_one(treasury_dict)
    
    # Add to daily work order automatically
    try:
        today = datetime.now().date()
        
        # Get or create daily work order for today
        daily_work_order = await db.work_orders.find_one({
            "is_daily": True,
            "work_date": today.isoformat()
        })
        
        if not daily_work_order:
            # Create new daily work order
            work_order = WorkOrder(
                title=f"أمر شغل يومي - {today.strftime('%d/%m/%Y')}",
                description=f"أمر شغل يومي لجميع فواتير يوم {today.strftime('%d/%m/%Y')}",
                supervisor_name=supervisor_name,
                is_daily=True,
                work_date=today.isoformat(),  # Store as string
                invoices=[],
                total_amount=0.0,
                total_items=0,
                status="جديد"
            )
            
            await db.work_orders.insert_one(work_order.dict())
            daily_work_order = work_order.dict()
        
        # Add invoice to daily work order with enhanced material details
        invoice_for_work_order = invoice_obj.dict()
        if "_id" in invoice_for_work_order:
            del invoice_for_work_order["_id"]
        
        # Enhance items with material usage details for work order display
        enhanced_items = []
        for item in invoice_for_work_order.get("items", []):
            enhanced_item = item.copy()
            
            # Add material consumption details for manufactured products
            if item.get("product_type") == "manufactured":
                seal_consumption = (item.get("height", 0) + 2) * item.get("quantity", 0)
                
                # Build material info string based on selected materials
                material_info = ""
                unit_code_display = ""
                
                print(f"🔍 Debug - Item data: {item}")
                print(f"🔍 Debug - Selected materials: {item.get('selected_materials')}")
                
                if item.get("selected_materials"):
                    print(f"✅ Found selected_materials: {len(item.get('selected_materials'))} materials")
                    # Multi-material case
                    material_parts = []
                    for mat in item.get("selected_materials", []):
                        inner_dia = mat.get("inner_diameter", 0)
                        outer_dia = mat.get("outer_diameter", 0) 
                        unit_code = mat.get("unit_code", "غير محدد")
                        seals_count = mat.get("seals_count", 0)
                        material_parts.append(f"{inner_dia}×{outer_dia} {unit_code} ({seals_count})")
                    
                    unit_code_display = " / ".join(material_parts)
                    material_info = f"مواد متعددة: {len(item.get('selected_materials', []))} خامة"
                    print(f"✅ Multi-material unit_code_display: {unit_code_display}")
                    
                elif item.get("material_details"):
                    # Single material case
                    mat_details = item.get("material_details")
                    inner_dia = mat_details.get("inner_diameter", 0)
                    outer_dia = mat_details.get("outer_diameter", 0)
                    unit_code = mat_details.get("unit_code", "غير محدد")
                    unit_code_display = f"{inner_dia}×{outer_dia} {unit_code} ({item.get('quantity', 0)})"
                    material_info = f"{unit_code} ({item.get('quantity', 0)} سيل)"
                    
                elif item.get("material_used"):
                    # Fallback case
                    unit_code_display = f"{item.get('material_used')} ({item.get('quantity', 0)})"
                    material_info = f"{item.get('material_used')} ({item.get('quantity', 0)} سيل)"
                
                enhanced_item["material_consumption"] = seal_consumption
                enhanced_item["material_info"] = material_info
                enhanced_item["unit_code_display"] = unit_code_display  # This will be used in work order
                enhanced_item["work_order_display"] = f"{item.get('seal_type', '')} {item.get('material_type', '')} {item.get('inner_diameter', 0)}×{item.get('outer_diameter', 0)}×{item.get('height', 0)} - {material_info} - استهلاك: {seal_consumption} مم"
            
            enhanced_items.append(enhanced_item)
        
        invoice_for_work_order["items"] = enhanced_items
            
        current_invoices = daily_work_order.get("invoices", [])
        current_invoices.append(invoice_for_work_order)
        
        new_total_amount = daily_work_order.get("total_amount", 0) + total_after_discount
        new_total_items = daily_work_order.get("total_items", 0) + len(invoice.items)
        
        await db.work_orders.update_one(
            {"id": daily_work_order["id"]},
            {"$set": {
                "invoices": current_invoices,
                "total_amount": new_total_amount,
                "total_items": new_total_items,
                "supervisor_name": supervisor_name  # Update supervisor name if provided
            }}
        )
        
    except Exception as e:
        # Log error but don't fail invoice creation
        print(f"Error adding invoice to daily work order: {str(e)}")
    
    return invoice_obj

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(company_id: str = "elsawy"):
    invoices = await db.invoices.find({"company_id": company_id}).sort("date", -1).to_list(1000)
    return [Invoice(**invoice) for invoice in invoices]

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
    return Invoice(**invoice)

@api_router.delete("/invoices/clear-all")
async def clear_all_invoices():
    result = await db.invoices.delete_many({})
    return {"message": f"تم حذف {result.deleted_count} فاتورة", "deleted_count": result.deleted_count}

@api_router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str):
    result = await db.invoices.delete_one({"id": invoice_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
    return {"message": "تم حذف الفاتورة بنجاح"}

@api_router.put("/invoices/{invoice_id}/status")
async def update_invoice_status(invoice_id: str, request: dict):
    try:
        # Extract status from request body
        if isinstance(request, dict) and 'status' in request:
            status = request['status']
        else:
            # Try parsing as direct string value
            status = request if isinstance(request, str) else str(request)
            
        result = await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"status": status}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
        return {"message": "تم تحديث حالة الفاتورة", "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/invoices/{invoice_id}")
async def update_invoice(invoice_id: str, invoice_update: dict, password: str = None):
    """Update invoice details - requires password"""
    try:
        # Verify password
        if not password:
            raise HTTPException(status_code=400, detail="كلمة المرور مطلوبة")
        
        # Get stored password (create if not exists)
        password_doc = await db.invoice_operations_passwords.find_one({"id": "invoice_operations_password"})
        if not password_doc:
            default_password = InvoiceOperationsPassword(password="1462")
            await db.invoice_operations_passwords.insert_one(default_password.dict())
            password_doc = default_password.dict()
        
        if password != password_doc.get("password"):
            raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")
        # Find existing invoice
        existing_invoice = await db.invoices.find_one({"id": invoice_id})
        if not existing_invoice:
            raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
        
        # Save a snapshot of the invoice before modification for edit history
        history_entry = {
            "id": str(uuid.uuid4()),
            "invoice_id": invoice_id,
            "invoice_snapshot": {k: v for k, v in existing_invoice.items() if k != '_id'},
            "edited_at": datetime.now(timezone.utc).isoformat(),
            "edited_by": invoice_update.get("edited_by", "unknown"),
            "changes_summary": ", ".join(invoice_update.keys())
        }
        await db.invoice_edit_history.insert_one(history_entry)
        
        # Handle items update and calculate subtotal
        if 'items' in invoice_update:
            subtotal = sum(item.get('total_price', 0) for item in invoice_update['items'])
            invoice_update['subtotal'] = subtotal
        else:
            # Get current subtotal from existing invoice
            subtotal = existing_invoice.get('subtotal', 0)
            
        # Handle discount calculation (independent of items update)
        discount_amount = 0.0
        if 'discount_type' in invoice_update and 'discount_value' in invoice_update:
            discount_value = float(invoice_update.get('discount_value', 0))
            if invoice_update['discount_type'] == 'percentage':
                discount_amount = (subtotal * discount_value) / 100
            else:
                discount_amount = discount_value
            
            # Update discount and totals
            total_after_discount = subtotal - discount_amount
            invoice_update.update({
                'discount': discount_amount,
                'total_after_discount': total_after_discount,
                'total_amount': total_after_discount
            })
        elif 'discount' in invoice_update:
            discount_amount = float(invoice_update.get('discount', 0))
            total_after_discount = subtotal - discount_amount
            invoice_update.update({
                'total_after_discount': total_after_discount,
                'total_amount': total_after_discount
            })
        
        # Update the invoice
        result = await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": invoice_update}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
        
        return {"message": "تم تحديث الفاتورة بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Invoice Edit History endpoints
@api_router.get("/invoices/{invoice_id}/history")
async def get_invoice_edit_history(invoice_id: str):
    """Get edit history for an invoice"""
    history = await db.invoice_edit_history.find(
        {"invoice_id": invoice_id}
    ).sort("edited_at", -1).to_list(length=None)
    
    for entry in history:
        if '_id' in entry:
            del entry['_id']
    
    return history

@api_router.post("/invoices/{invoice_id}/revert/{history_id}")
async def revert_invoice_edit(invoice_id: str, history_id: str):
    """Revert an invoice to a previous state from edit history"""
    # Find the history entry
    history_entry = await db.invoice_edit_history.find_one({"id": history_id, "invoice_id": invoice_id})
    if not history_entry:
        raise HTTPException(status_code=404, detail="سجل التعديل غير موجود")
    
    # Get current invoice state before reverting (save it to history too)
    current_invoice = await db.invoices.find_one({"id": invoice_id})
    if not current_invoice:
        raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
    
    revert_history = {
        "id": str(uuid.uuid4()),
        "invoice_id": invoice_id,
        "invoice_snapshot": {k: v for k, v in current_invoice.items() if k != '_id'},
        "edited_at": datetime.now(timezone.utc).isoformat(),
        "edited_by": "system_revert",
        "changes_summary": f"تراجع إلى نسخة {history_entry['edited_at']}"
    }
    await db.invoice_edit_history.insert_one(revert_history)
    
    # Restore the invoice from the snapshot
    snapshot = history_entry["invoice_snapshot"]
    snapshot_clean = {k: v for k, v in snapshot.items() if k != '_id'}
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": snapshot_clean}
    )
    
    return {"message": "تم التراجع عن التعديل بنجاح"}


# Payment endpoints
@api_router.post("/payments", response_model=Payment)
async def create_payment(payment: PaymentCreate, company_id: str = "elsawy"):
    payment_obj = Payment(**payment.dict())
    
    # Update invoice
    invoice = await db.invoices.find_one({"id": payment.invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
    
    new_paid_amount = invoice["paid_amount"] + payment.amount
    new_remaining = invoice["total_amount"] - new_paid_amount
    
    status = InvoiceStatus.PAID if new_remaining <= 0 else InvoiceStatus.PARTIAL
    
    # Build update data
    update_data = {
        "paid_amount": new_paid_amount,
        "remaining_amount": max(0, new_remaining),
        "status": status,
        "last_payment_date": datetime.now(timezone.utc).isoformat()
    }
    
    # For deferred invoices, include payment method in status description
    payment_method_str = str(payment.payment_method)
    if invoice.get("payment_method") == "آجل" and payment_method_str:
        update_data["payment_method_used"] = payment_method_str
        if new_remaining <= 0:
            update_data["status_description"] = f"تم الدفع عن طريق {payment_method_str}"
        else:
            update_data["status_description"] = f"دفعة جزئية عن طريق {payment_method_str}"
    
    await db.invoices.update_one(
        {"id": payment.invoice_id},
        {"$set": update_data}
    )

    
    # Add treasury transaction for the payment
    payment_method_mapping = {
        "نقدي": "cash",
        "فودافون 010": "vodafone_elsawy", 
        "كاش 0100": "vodafone_wael",
        "انستاباي": "instapay",
        "يد الصاوي": "yad_elsawy"
    }
    
    payment_method_str = str(payment.payment_method)
    account_id = payment_method_mapping.get(payment_method_str, "cash")
    
    # Check if treasury transaction already exists for this payment
    existing_transaction = await db.treasury_transactions.find_one({
        "reference": f"payment_{payment_obj.id}"
    })
    
    if not existing_transaction:
        # Add income transaction to the payment account
        treasury_transaction = TreasuryTransaction(
            account_id=account_id,
            transaction_type="income",
            amount=payment.amount,
            description=f"دفع فاتورة {invoice['invoice_number']} - {invoice['customer_name']}",
            reference=f"payment_{payment_obj.id}"
        )
        treasury_dict = treasury_transaction.dict()
        treasury_dict["company_id"] = company_id
        await db.treasury_transactions.insert_one(treasury_dict)
        
        # For deferred invoices, also create a deduction from deferred account
        if invoice.get("payment_method") == "آجل":
            deferred_transaction = TreasuryTransaction(
                account_id="deferred",
                transaction_type="expense",
                amount=payment.amount,
                description=f"تسديد آجل فاتورة {invoice['invoice_number']} - {invoice['customer_name']}",
                reference=f"payment_{payment_obj.id}_deferred"
            )
            deferred_dict = deferred_transaction.dict()
            deferred_dict["company_id"] = company_id
            await db.treasury_transactions.insert_one(deferred_dict)
    
    payment_data = payment_obj.dict()
    payment_data["company_id"] = company_id
    await db.payments.insert_one(payment_data)
    return payment_obj

@api_router.get("/payments", response_model=List[Payment])
async def get_payments(company_id: str = "elsawy"):
    payments = await db.payments.find({"company_id": company_id}).sort("date", -1).to_list(1000)
    return [Payment(**payment) for payment in payments]

@api_router.delete("/payments/clear-all")
async def clear_all_payments(company_id: str = "elsawy"):
    result = await db.payments.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} دفعة", "deleted_count": result.deleted_count}

@api_router.delete("/payments/{payment_id}")
async def delete_payment(payment_id: str):
    result = await db.payments.delete_one({"id": payment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="الدفعة غير موجودة")
    return {"message": "تم حذف الدفعة بنجاح"}

# Expense endpoints
@api_router.post("/expenses", response_model=Expense)
async def create_expense(expense: ExpenseCreate, company_id: str = "elsawy"):
    expense_obj = Expense(**expense.dict())
    obj = expense_obj.dict()
    obj["company_id"] = company_id
    await db.expenses.insert_one(obj)
    return expense_obj

@api_router.get("/expenses", response_model=List[Expense])
async def get_expenses(company_id: str = "elsawy"):
    expenses = await db.expenses.find({"company_id": company_id}).sort("date", -1).to_list(1000)
    return [Expense(**expense) for expense in expenses]

@api_router.delete("/expenses/clear-all")
async def clear_all_expenses(company_id: str = "elsawy"):
    result = await db.expenses.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} مصروف", "deleted_count": result.deleted_count}

@api_router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    result = await db.expenses.delete_one({"id": expense_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="المصروف غير موجود")
    return {"message": "تم حذف المصروف بنجاح"}

# Revenue reports
@api_router.get("/reports/revenue")
async def get_revenue_report(period: str = "daily", company_id: str = "elsawy"):
    # Implementation for revenue reports based on period
    cf = {"company_id": company_id}
    invoices = list(await db.invoices.find(cf).to_list(1000))
    expenses = list(await db.expenses.find(cf).to_list(1000))
    
    total_revenue = sum(invoice.get("total_amount", 0) for invoice in invoices)
    total_expenses = sum(expense.get("amount", 0) for expense in expenses)
    material_cost = sum(expense.get("amount", 0) for expense in expenses if expense.get("category") == "خامات")
    
    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "material_cost": material_cost,
        "profit": total_revenue - total_expenses,
        "period": period
    }

# Work orders
@api_router.post("/work-orders", response_model=WorkOrder)
async def create_work_order(invoice_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
    
    work_order = WorkOrder(
        invoice_id=invoice_id,
        items=invoice["items"]
    )
    
    await db.work_orders.insert_one(work_order.dict())
    return work_order

@api_router.post("/work-orders/multiple")
async def create_work_order_multiple(work_order_data: dict):
    """Create work order from multiple invoices"""
    try:
        # Create work order with multiple invoices
        work_order = {
            "id": str(uuid.uuid4()),
            "title": work_order_data.get("title", ""),
            "description": work_order_data.get("description", ""),
            "priority": work_order_data.get("priority", "عادي"),
            "invoices": work_order_data.get("invoices", []),
            "total_amount": work_order_data.get("total_amount", 0),
            "total_items": work_order_data.get("total_items", 0),
            "status": "جديد",
            "created_at": datetime.utcnow()
        }
        
        await db.work_orders.insert_one(work_order)
        
        # Remove MongoDB ObjectId for return
        if "_id" in work_order:
            del work_order["_id"]
            
        return work_order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/work-orders/daily/{work_date}")
async def get_or_create_daily_work_order(work_date: str, supervisor_name: str = ""):
    """Get or create daily work order for specified date"""
    try:
        # Parse date from string (YYYY-MM-DD format)
        work_date_obj = datetime.strptime(work_date, "%Y-%m-%d").date()
        
        # Check if daily work order already exists for this date
        existing_order = await db.work_orders.find_one({
            "is_daily": True,
            "work_date": work_date_obj.isoformat()  # Store as string
        })
        
        if existing_order:
            # Clean up MongoDB ObjectId
            if "_id" in existing_order:
                del existing_order["_id"]
            
            # Convert date to string for JSON serialization
            if "work_date" in existing_order and existing_order["work_date"]:
                existing_order["work_date"] = existing_order["work_date"] if isinstance(existing_order["work_date"], str) else existing_order["work_date"].isoformat()
                
            return existing_order
        
        # Create new daily work order
        work_order = WorkOrder(
            title=f"أمر شغل يومي - {work_date_obj.strftime('%d/%m/%Y')}",
            description=f"أمر شغل يومي لجميع فواتير يوم {work_date_obj.strftime('%d/%m/%Y')}",
            supervisor_name=supervisor_name,
            is_daily=True,
            work_date=work_date_obj.isoformat(),  # Store as string
            invoices=[],
            total_amount=0.0,
            total_items=0,
            status="جديد"
        )
        
        await db.work_orders.insert_one(work_order.dict())
        
        # Clean up MongoDB ObjectId for return
        work_order_dict = work_order.dict()
        if "_id" in work_order_dict:
            del work_order_dict["_id"]
        
        # Convert date to string for JSON serialization
        if "work_date" in work_order_dict and work_order_dict["work_date"]:
            work_order_dict["work_date"] = work_order_dict["work_date"].isoformat() if hasattr(work_order_dict["work_date"], 'isoformat') else str(work_order_dict["work_date"])
            
        return work_order_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/work-orders/daily/{work_order_id}/add-invoice")
async def add_invoice_to_daily_work_order(work_order_id: str, invoice_id: str):
    """Add invoice to daily work order"""
    try:
        # Get the work order
        work_order = await db.work_orders.find_one({"id": work_order_id})
        if not work_order:
            raise HTTPException(status_code=404, detail="أمر الشغل غير موجود")
        
        # Get the invoice
        invoice = await db.invoices.find_one({"id": invoice_id})
        if not invoice:
            raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
        
        # Clean up MongoDB ObjectId from invoice
        if "_id" in invoice:
            del invoice["_id"]
        
        # Get current invoices
        current_invoices = work_order.get("invoices", [])
        
        # Check if invoice already exists
        if any(inv.get("id") == invoice_id for inv in current_invoices):
            return {"message": "الفاتورة موجودة بالفعل في أمر الشغل"}
            
        current_invoices.append(invoice)
        
        # Update totals
        new_total_amount = work_order.get("total_amount", 0) + invoice.get("total_amount", 0)
        new_total_items = work_order.get("total_items", 0) + len(invoice.get("items", []))
        
        # Update in database
        result = await db.work_orders.update_one(
            {"id": work_order_id},
            {"$set": {
                "invoices": current_invoices,
                "total_amount": new_total_amount,
                "total_items": new_total_items
            }}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="فشل في تحديث أمر الشغل")
            
        return {"message": "تم إضافة الفاتورة إلى أمر الشغل اليومي بنجاح"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/work-orders")
async def get_work_orders(company_id: str = "elsawy"):
    try:
        orders = await db.work_orders.find({"company_id": company_id}).sort("created_at", -1).to_list(1000)
        
        # Clean up MongoDB ObjectIds and handle date serialization
        for order in orders:
            if "_id" in order:
                del order["_id"]
            # Convert date to string for JSON serialization
            if "work_date" in order and order["work_date"]:
                order["work_date"] = order["work_date"] if isinstance(order["work_date"], str) else order["work_date"].isoformat()
                
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/work-orders/clear-all")
async def clear_all_work_orders(company_id: str = "elsawy"):
    result = await db.work_orders.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} أمر شغل", "deleted_count": result.deleted_count}

@api_router.delete("/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: str):
    result = await db.work_orders.delete_one({"id": work_order_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="أمر الشغل غير موجود")
    return {"message": "تم حذف أمر الشغل بنجاح"}

@api_router.put("/work-orders/{work_order_id}/add-invoice")
async def add_invoice_to_work_order(work_order_id: str, invoice_id: str):
    """Add an invoice to an existing work order"""
    try:
        # Get the work order
        work_order = await db.work_orders.find_one({"id": work_order_id})
        if not work_order:
            raise HTTPException(status_code=404, detail="أمر الشغل غير موجود")
            
        # Get the invoice
        invoice = await db.invoices.find_one({"id": invoice_id})
        if not invoice:
            raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
            
        # Clean invoice data
        if "_id" in invoice:
            del invoice["_id"]
            
        # Update work order with new invoice
        current_invoices = work_order.get("invoices", [])
        
        # Check if invoice already exists in work order
        if any(inv.get("id") == invoice_id for inv in current_invoices):
            raise HTTPException(status_code=400, detail="الفاتورة موجودة بالفعل في أمر الشغل")
            
        current_invoices.append(invoice)
        
        # Update totals
        new_total_amount = work_order.get("total_amount", 0) + invoice.get("total_amount", 0)
        new_total_items = work_order.get("total_items", 0) + len(invoice.get("items", []))
        
        # Update in database
        result = await db.work_orders.update_one(
            {"id": work_order_id},
            {"$set": {
                "invoices": current_invoices,
                "total_amount": new_total_amount,
                "total_items": new_total_items
            }}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="فشل في تحديث أمر الشغل")
            
        return {"message": "تم إضافة الفاتورة إلى أمر الشغل بنجاح"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Treasury Management APIs
@api_router.get("/treasury/transactions")
async def get_treasury_transactions(company_id: str = "elsawy"):
    """Get all treasury transactions"""
    try:
        transactions = await db.treasury_transactions.find({"company_id": company_id}).sort("date", -1).to_list(1000)
        
        # Clean up MongoDB ObjectIds
        for transaction in transactions:
            if "_id" in transaction:
                del transaction["_id"]
                
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/treasury/transactions")
async def create_treasury_transaction(transaction: TreasuryTransactionCreate, company_id: str = "elsawy"):
    """Create a new treasury transaction"""
    try:
        transaction_obj = TreasuryTransaction(**transaction.dict())
        obj = transaction_obj.dict()
        obj["company_id"] = company_id
        await db.treasury_transactions.insert_one(obj)
        
        transaction_dict = transaction_obj.dict()
        if "_id" in transaction_dict:
            del transaction_dict["_id"]
            
        return transaction_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/treasury/transfer")
async def transfer_funds(transfer: TransferRequest, company_id: str = "elsawy"):
    """Transfer funds between accounts"""
    try:
        # Create outgoing transaction
        out_transaction = TreasuryTransaction(
            account_id=transfer.from_account,
            transaction_type="transfer_out",
            amount=transfer.amount,
            description=f"تحويل إلى حساب {transfer.to_account}",
            reference=transfer.notes or "تحويل داخلي"
        )
        
        # Create incoming transaction
        in_transaction = TreasuryTransaction(
            account_id=transfer.to_account,
            transaction_type="transfer_in",
            amount=transfer.amount,
            description=f"تحويل من حساب {transfer.from_account}",
            reference=transfer.notes or "تحويل داخلي",
            related_transaction_id=out_transaction.id
        )
        
        # Link transactions
        out_transaction.related_transaction_id = in_transaction.id
        
        # Save both transactions with company_id
        out_dict = out_transaction.dict()
        out_dict["company_id"] = company_id
        in_dict = in_transaction.dict()
        in_dict["company_id"] = company_id
        await db.treasury_transactions.insert_one(out_dict)
        await db.treasury_transactions.insert_one(in_dict)
        
        return {"message": "تم التحويل بنجاح", "transfer_id": out_transaction.id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/treasury/balances")
async def get_account_balances(company_id: str = "elsawy"):
    """Get current balances for all accounts"""
    try:
        # Get all transactions
        cf = {"company_id": company_id}
        transactions = await db.treasury_transactions.find(cf).to_list(10000)
        
        # Get invoice data for automatic transactions
        invoices = await db.invoices.find(cf).to_list(1000)
        expenses = await db.expenses.find(cf).to_list(1000)
        
        # Calculate balances
        account_balances = {
            'cash': 0,
            'vodafone_elsawy': 0,
            'vodafone_wael': 0,
            'deferred': 0,
            'instapay': 0,
            'yad_elsawy': 0,
            'main_treasury': 0  # الخزنة الرئيسية
        }
        
        # Add invoice amounts (only for deferred invoices that don't have treasury transactions)
        payment_method_map = {
            'نقدي': 'cash',
            'فودافون 010': 'vodafone_elsawy',
            'كاش 0100': 'vodafone_wael',
            'آجل': 'deferred',
            'انستاباي': 'instapay',
            'يد الصاوي': 'yad_elsawy'
        }
        
        # Only add deferred invoices directly (non-deferred invoices are handled by treasury transactions)
        for invoice in invoices:
            if invoice.get('payment_method') == 'آجل':
                account_balances['deferred'] += invoice.get('total_amount', 0)
        
        # Subtract expenses from cash
        for expense in expenses:
            account_balances['cash'] -= expense.get('amount', 0)
        
        # Apply manual transactions
        for transaction in transactions:
            account_id = transaction.get('account_id')
            if account_id in account_balances:
                amount = transaction.get('amount', 0)
                transaction_type = transaction.get('transaction_type')
                
                if transaction_type in ['income', 'transfer_in']:
                    account_balances[account_id] += amount
                elif transaction_type in ['expense', 'transfer_out']:
                    account_balances[account_id] -= amount
        
        return account_balances
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Daily Sales Report API
@api_router.get("/daily-sales-report")
async def get_daily_sales_report(report_date: str = None, company_id: str = "elsawy"):
    """
    Get daily sales report for a specific date
    - report_date: YYYY-MM-DD format (defaults to today)
    
    Returns:
    - cash_sales: مبيعات نقدية (فواتير نقدية + فواتير آجل مدفوعة بالكامل في نفس اليوم)
    - deferred_sales: مبيعات آجل (فواتير آجل لم تدفع في نفس اليوم)
    - deferred_collections: تحصيل من الآجل (مدفوعات على فواتير آجل سابقة)
    - expenses: مصروفات اليوم
    - daily_account_changes: الزيادة اليومية في كل حساب
    """
    try:
        from datetime import datetime, timedelta
        
        # Parse the date or use today
        if report_date:
            try:
                target_date = datetime.strptime(report_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="تنسيق التاريخ غير صحيح. استخدم YYYY-MM-DD")
        else:
            target_date = datetime.now()
        
        # Define date range (start of day to end of day)
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get all invoices for the target date
        invoices = await db.invoices.find({
            "date": {"$gte": start_of_day, "$lte": end_of_day},
            "company_id": company_id
        }, {"_id": 0}).to_list(1000)
        
        # Get all payments for the target date
        payments = await db.payments.find({
            "date": {"$gte": start_of_day, "$lte": end_of_day},
            "company_id": company_id
        }, {"_id": 0}).to_list(1000)
        
        # Get all treasury transactions for the target date
        treasury_transactions = await db.treasury_transactions.find({
            "date": {"$gte": start_of_day, "$lte": end_of_day},
            "company_id": company_id
        }, {"_id": 0}).to_list(1000)
        
        # Get all expenses for the target date
        expenses = await db.expenses.find({
            "date": {"$gte": start_of_day, "$lte": end_of_day},
            "company_id": company_id
        }, {"_id": 0}).to_list(1000)
        
        # Calculate cash sales
        # Cash sales = cash invoices + deferred invoices fully paid on same day
        cash_sales = 0
        deferred_sales = 0
        
        for invoice in invoices:
            invoice_total = invoice.get("total_after_discount") or invoice.get("total_amount", 0)
            payment_method = invoice.get("payment_method", "")
            remaining = invoice.get("remaining_amount", 0)
            
            if payment_method == "آجل":
                # Check if this deferred invoice was fully paid on the same day
                if remaining == 0:
                    # Fully paid deferred invoice = count as cash
                    cash_sales += invoice_total
                else:
                    # Not fully paid = count as deferred
                    deferred_sales += invoice_total
            else:
                # Non-deferred invoice (cash, vodafone, etc.)
                cash_sales += invoice_total
        
        # Calculate deferred collections (payments on previous deferred invoices)
        deferred_collections = 0
        deferred_collections_cash = 0  # تحصيل من الآجل نقدي
        deferred_collections_by_method = {}  # تحصيل مفصل حسب طريقة الدفع
        
        for payment in payments:
            invoice_id = payment.get("invoice_id")
            payment_amount = payment.get("amount", 0)
            payment_method = payment.get("payment_method", "نقدي")
            
            # Find the original invoice
            invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
            
            if invoice:
                invoice_date = invoice.get("date")
                invoice_payment_method = invoice.get("payment_method", "")
                
                # Check if this is a payment on a deferred invoice from a previous day
                if invoice_payment_method == "آجل":
                    # Check if invoice was created before today
                    if isinstance(invoice_date, datetime):
                        invoice_day = invoice_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        if invoice_day < start_of_day:
                            # This is a collection from a previous deferred invoice
                            deferred_collections += payment_amount
                            
                            # Track by payment method
                            if payment_method not in deferred_collections_by_method:
                                deferred_collections_by_method[payment_method] = 0
                            deferred_collections_by_method[payment_method] += payment_amount
                            
                            if payment_method == "نقدي":
                                deferred_collections_cash += payment_amount
        
        # Calculate daily account changes from treasury transactions
        daily_account_changes = {
            "cash": 0,
            "vodafone_elsawy": 0,
            "vodafone_wael": 0,
            "instapay": 0,
            "yad_elsawy": 0
        }
        
        account_labels = {
            "cash": "نقدي",
            "vodafone_elsawy": "فودافون 010",
            "vodafone_wael": "كاش 0100",
            "instapay": "انستاباي",
            "yad_elsawy": "يد الصاوي"
        }
        
        for transaction in treasury_transactions:
            account_id = transaction.get("account_id", "")
            amount = transaction.get("amount", 0)
            transaction_type = transaction.get("transaction_type", "")
            
            if account_id in daily_account_changes:
                if transaction_type in ["income", "transfer_in"]:
                    daily_account_changes[account_id] += amount
                elif transaction_type in ["expense", "transfer_out"]:
                    daily_account_changes[account_id] -= amount
        
        # Calculate total expenses for the day
        total_expenses = sum(expense.get("amount", 0) for expense in expenses)
        
        # Format the response
        formatted_account_changes = []
        for account_id, amount in daily_account_changes.items():
            formatted_account_changes.append({
                "account_id": account_id,
                "label": account_labels.get(account_id, account_id),
                "daily_change": amount
            })
        
        return {
            "report_date": target_date.strftime("%Y-%m-%d"),
            "report_date_formatted": target_date.strftime("%d/%m/%Y"),
            "summary": {
                "cash_sales": cash_sales,
                "deferred_sales": deferred_sales,
                "deferred_collections": deferred_collections,
                "deferred_collections_cash": deferred_collections_cash,
                "total_expenses": total_expenses,
                "net_daily_income": cash_sales + deferred_collections - total_expenses
            },
            "deferred_collections_by_method": deferred_collections_by_method,
            "daily_account_changes": formatted_account_changes,
            "details": {
                "invoices_count": len(invoices),
                "payments_count": len(payments),
                "expenses_count": len(expenses)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating daily sales report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Suppliers endpoints
@api_router.get("/suppliers", response_model=List[Supplier])
async def get_suppliers(company_id: str = "elsawy"):
    """Get all suppliers"""
    try:
        suppliers = await db.suppliers.find({"company_id": company_id}).to_list(None)
        return suppliers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/suppliers", response_model=Supplier)
async def create_supplier(supplier: SupplierCreate, company_id: str = "elsawy"):
    """Create a new supplier"""
    try:
        supplier_obj = Supplier(**supplier.dict())
        obj = supplier_obj.dict()
        obj["company_id"] = company_id
        await db.suppliers.insert_one(obj)
        
        supplier_dict = supplier_obj.dict()
        if "_id" in supplier_dict:
            del supplier_dict["_id"]
        return supplier_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/suppliers/{supplier_id}")
async def update_supplier(supplier_id: str, supplier: SupplierCreate):
    """Update supplier information"""
    try:
        result = await db.suppliers.update_one(
            {"id": supplier_id},
            {"$set": supplier.dict()}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="المورد غير موجود")
        return {"message": "تم تحديث بيانات المورد بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str):
    """Delete a supplier"""
    try:
        result = await db.suppliers.delete_one({"id": supplier_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="المورد غير موجود")
        return {"message": "تم حذف المورد بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Local Products endpoints
@api_router.get("/local-products", response_model=List[LocalProduct])
async def get_local_products(company_id: str = "elsawy"):
    """Get all local products"""
    try:
        products = await db.local_products.find({"company_id": company_id}).to_list(None)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/local-products/supplier/{supplier_id}", response_model=List[LocalProduct])
async def get_products_by_supplier(supplier_id: str):
    """Get products by supplier"""
    try:
        products = await db.local_products.find({"supplier_id": supplier_id}).to_list(None)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/local-products", response_model=LocalProduct)
async def create_local_product(product: LocalProductCreate, company_id: str = "elsawy"):
    """Create a new local product"""
    try:
        # Get supplier name
        supplier = await db.suppliers.find_one({"id": product.supplier_id})
        if not supplier:
            raise HTTPException(status_code=404, detail="المورد غير موجود")
        
        product_obj = LocalProduct(
            **product.dict(),
            supplier_name=supplier["name"]
        )
        obj = product_obj.dict()
        obj["company_id"] = company_id
        await db.local_products.insert_one(obj)
        
        product_dict = product_obj.dict()
        if "_id" in product_dict:
            del product_dict["_id"]
        return product_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/local-products/{product_id}")
async def update_local_product(product_id: str, product: LocalProductCreate):
    """Update local product"""
    try:
        # Get supplier name
        supplier = await db.suppliers.find_one({"id": product.supplier_id})
        if not supplier:
            raise HTTPException(status_code=404, detail="المورد غير موجود")
        
        update_data = product.dict()
        update_data["supplier_name"] = supplier["name"]
        
        result = await db.local_products.update_one(
            {"id": product_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="المنتج غير موجود")
        return {"message": "تم تحديث المنتج بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/local-products/{product_id}")
async def delete_local_product(product_id: str):
    """Delete a local product"""
    try:
        result = await db.local_products.delete_one({"id": product_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="المنتج غير موجود")
        return {"message": "تم حذف المنتج بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Supplier Transactions endpoints
@api_router.get("/supplier-transactions", response_model=List[SupplierTransaction])
async def get_supplier_transactions(company_id: str = "elsawy"):
    """Get all supplier transactions"""
    try:
        transactions = await db.supplier_transactions.find({"company_id": company_id}).sort("date", -1).to_list(None)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/supplier-transactions/{supplier_id}", response_model=List[SupplierTransaction])
async def get_supplier_transactions_by_id(supplier_id: str):
    """Get transactions for a specific supplier"""
    try:
        transactions = await db.supplier_transactions.find({"supplier_id": supplier_id}).sort("date", -1).to_list(None)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/supplier-transactions", response_model=SupplierTransaction)
async def create_supplier_transaction(transaction: SupplierTransactionCreate):
    """Create a supplier transaction (purchase or payment)"""
    try:
        # Get supplier name
        supplier = await db.suppliers.find_one({"id": transaction.supplier_id})
        if not supplier:
            raise HTTPException(status_code=404, detail="المورد غير موجود")
        
        transaction_obj = SupplierTransaction(
            **transaction.dict(),
            supplier_name=supplier["name"]
        )
        await db.supplier_transactions.insert_one(transaction_obj.dict())
        
        # Update supplier balance
        if transaction.transaction_type == "purchase":
            # Increase supplier balance (we owe them)
            await db.suppliers.update_one(
                {"id": transaction.supplier_id},
                {
                    "$inc": {
                        "total_purchases": transaction.amount,
                        "balance": transaction.amount,
                        "current_balance": transaction.amount  # Update both fields
                    }
                }
            )
        elif transaction.transaction_type == "payment":
            # Decrease supplier balance (we paid them)
            await db.suppliers.update_one(
                {"id": transaction.supplier_id},
                {
                    "$inc": {
                        "total_paid": transaction.amount,
                        "balance": -transaction.amount,
                        "current_balance": -transaction.amount  # Update both fields
                    }
                }
            )
        
        transaction_dict = transaction_obj.dict()
        if "_id" in transaction_dict:
            del transaction_dict["_id"]
        return transaction_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/supplier-payment")
async def pay_supplier(supplier_id: str, amount: float, payment_method: str = "cash"):
    """Pay a supplier and deduct from treasury"""
    try:
        # Get supplier
        supplier = await db.suppliers.find_one({"id": supplier_id})
        if not supplier:
            raise HTTPException(status_code=404, detail="المورد غير موجود")
        
        # Create supplier payment transaction
        supplier_transaction = SupplierTransaction(
            supplier_id=supplier_id,
            supplier_name=supplier["name"],
            transaction_type="payment",
            amount=amount,
            description=f"دفع للمورد {supplier['name']}",
            payment_method=payment_method
        )
        await db.supplier_transactions.insert_one(supplier_transaction.dict())
        
        # Update supplier balance
        await db.suppliers.update_one(
            {"id": supplier_id},
            {
                "$inc": {
                    "total_paid": amount,
                    "balance": -amount,
                    "current_balance": -amount  # Update both fields
                }
            }
        )
        
        # Create treasury transaction (expense)
        treasury_transaction = TreasuryTransaction(
            account_id=payment_method,
            transaction_type="expense",
            amount=amount,
            description=f"دفع للمورد {supplier['name']}",
            reference=f"supplier_payment_{supplier_transaction.id}"
        )
        treasury_dict = treasury_transaction.dict()
        treasury_dict["company_id"] = supplier.get("company_id", "elsawy")
        await db.treasury_transactions.insert_one(treasury_dict)
        
        return {"message": "تم دفع المبلغ للمورد بنجاح", "payment_id": supplier_transaction.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Inventory Management endpoints
@api_router.get("/inventory", response_model=List[InventoryItem])
async def get_inventory(company_id: str = "elsawy"):
    """Get all inventory items sorted by material type priority then size"""
    try:
        # Define material type priority order: BUR-NBR-BT-BOOM-VT
        material_priority = {'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5}
        
        # Get all items first
        items = await db.inventory_items.find({"company_id": company_id}).to_list(None)
        
        # Sort by material type priority, then by diameter
        sorted_items = sorted(items, key=lambda x: (
            material_priority.get(x.get('material_type', ''), 6),  # Material priority
            x.get('inner_diameter', 0),  # Then inner diameter
            x.get('outer_diameter', 0)   # Then outer diameter
        ))
        
        return sorted_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/inventory/low-stock")
async def get_low_stock_items():
    """Get items with stock below minimum level"""
    try:
        pipeline = [
            {
                "$match": {
                    "$expr": {
                        "$lt": ["$available_pieces", "$min_stock_level"]
                    }
                }
            }
        ]
        items = await db.inventory_items.aggregate(pipeline).to_list(None)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/inventory/{item_id}", response_model=InventoryItem)
async def get_inventory_item(item_id: str):
    """Get specific inventory item"""
    try:
        item = await db.inventory_items.find_one({"id": item_id})
        if not item:
            raise HTTPException(status_code=404, detail="العنصر غير موجود في الجرد")
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/inventory", response_model=InventoryItem)
async def create_inventory_item(item: InventoryItemCreate, company_id: str = "elsawy"):
    """Create a new inventory item"""
    try:
        # Check if item with same specifications already exists
        existing_item = await db.inventory_items.find_one({
            "material_type": item.material_type,
            "inner_diameter": item.inner_diameter,
            "outer_diameter": item.outer_diameter,
            "company_id": company_id
        })
        
        if existing_item:
            raise HTTPException(
                status_code=400, 
                detail=f"عنصر بنفس المواصفات موجود بالفعل: {item.material_type} - {item.inner_diameter}x{item.outer_diameter}"
            )
        
        inventory_item = InventoryItem(**item.dict())
        obj = inventory_item.dict()
        obj["company_id"] = company_id
        await db.inventory_items.insert_one(obj)
        
        # Create initial transaction
        initial_transaction = InventoryTransaction(
            inventory_item_id=inventory_item.id,
            material_type=item.material_type,
            inner_diameter=item.inner_diameter,
            outer_diameter=item.outer_diameter,
            transaction_type="in",
            pieces_change=item.available_pieces,
            remaining_pieces=item.available_pieces,
            reason="إضافة عنصر جديد للجرد",
            reference_id=inventory_item.id,
            notes=f"إنشاء عنصر جديد: {item.material_type} - {item.inner_diameter}x{item.outer_diameter}"
        )
        await db.inventory_transactions.insert_one(initial_transaction.dict())
        
        item_dict = inventory_item.dict()
        if "_id" in item_dict:
            del item_dict["_id"]
        return item_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/inventory/{item_id}")
async def update_inventory_item(item_id: str, item: InventoryItemCreate):
    """Update inventory item"""
    try:
        result = await db.inventory_items.update_one(
            {"id": item_id},
            {
                "$set": {
                    **item.dict(),
                    "last_updated": datetime.utcnow()
                }
            }
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="العنصر غير موجود في الجرد")
        return {"message": "تم تحديث عنصر الجرد بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/inventory/{item_id}")
async def delete_inventory_item(item_id: str):
    """Delete inventory item"""
    try:
        result = await db.inventory_items.delete_one({"id": item_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="العنصر غير موجود في الجرد")
        return {"message": "تم حذف عنصر الجرد بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/inventory-transactions", response_model=List[InventoryTransaction])
async def get_inventory_transactions():
    """Get all inventory transactions"""
    try:
        transactions = await db.inventory_transactions.find({}).sort("date", -1).to_list(None)
        
        # Clean transactions for response - handle old schema compatibility
        cleaned_transactions = []
        for transaction in transactions:
            # Handle old schema fields (height_change -> pieces_change, remaining_height -> remaining_pieces)
            if "height_change" in transaction and "pieces_change" not in transaction:
                transaction["pieces_change"] = transaction.get("height_change", 0)
            if "remaining_height" in transaction and "remaining_pieces" not in transaction:
                transaction["remaining_pieces"] = transaction.get("remaining_height", 0)
            
            # Ensure required fields exist
            if "pieces_change" not in transaction:
                transaction["pieces_change"] = 0
            if "remaining_pieces" not in transaction:
                transaction["remaining_pieces"] = 0
                
            cleaned_transactions.append(transaction)
            
        return cleaned_transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/inventory-transactions/{item_id}", response_model=List[InventoryTransaction])
async def get_inventory_transactions_by_item(item_id: str):
    """Get transactions for a specific inventory item"""
    try:
        transactions = await db.inventory_transactions.find(
            {"inventory_item_id": item_id}
        ).sort("date", -1).to_list(None)
        
        # Clean transactions for response - handle old schema compatibility
        cleaned_transactions = []
        for transaction in transactions:
            # Handle old schema fields
            if "height_change" in transaction and "pieces_change" not in transaction:
                transaction["pieces_change"] = transaction.get("height_change", 0)
            if "remaining_height" in transaction and "remaining_pieces" not in transaction:
                transaction["remaining_pieces"] = transaction.get("remaining_height", 0)
            
            # Ensure required fields exist
            if "pieces_change" not in transaction:
                transaction["pieces_change"] = 0
            if "remaining_pieces" not in transaction:
                transaction["remaining_pieces"] = 0
                
            cleaned_transactions.append(transaction)
            
        return cleaned_transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Material Pricing APIs
@api_router.get("/material-pricing", response_model=List[MaterialPricing])
async def get_material_pricing():
    """Get all material pricing"""
    try:
        pricings = await db.material_pricing.find({}).sort("created_at", -1).to_list(None)
        return [MaterialPricing(**pricing) for pricing in pricings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/material-pricing", response_model=MaterialPricing)
async def create_material_pricing(pricing: MaterialPricing):
    """Create new material pricing"""
    try:
        pricing_dict = pricing.dict()
        await db.material_pricing.insert_one(pricing_dict)
        return pricing
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/material-pricing/{pricing_id}")
async def update_material_pricing(pricing_id: str, pricing: MaterialPricing):
    """Update material pricing"""
    try:
        pricing_dict = pricing.dict()
        pricing_dict["updated_at"] = datetime.utcnow()
        
        result = await db.material_pricing.update_one(
            {"id": pricing_id},
            {"$set": pricing_dict}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="التسعيرة غير موجودة")
        return {"message": "تم تحديث التسعيرة بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/material-pricing/{pricing_id}")
async def delete_material_pricing(pricing_id: str):
    """Delete material pricing"""
    try:
        result = await db.material_pricing.delete_one({"id": pricing_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="التسعيرة غير موجودة")
        return {"message": "تم حذف التسعيرة بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/calculate-price")
async def calculate_material_price(
    material_type: str,
    inner_diameter: float,
    outer_diameter: float,
    height: float,
    client_type: int  # 1, 2, or 3
):
    """Calculate price based on material pricing"""
    try:
        # Find matching material pricing
        pricing = await db.material_pricing.find_one({
            "material_type": material_type,
            "inner_diameter": inner_diameter,
            "outer_diameter": outer_diameter
        })
        
        if not pricing:
            raise HTTPException(status_code=404, detail="لم يتم العثور على تسعيرة مطابقة لهذه الخامة")
        
        # Calculate price: (price_per_mm * height) + manufacturing_cost
        mm_cost = pricing["price_per_mm"] * height
        
        if client_type == 1:
            manufacturing_cost = pricing["manufacturing_cost_client1"]
        elif client_type == 2:
            manufacturing_cost = pricing["manufacturing_cost_client2"]
        elif client_type == 3:
            manufacturing_cost = pricing["manufacturing_cost_client3"]
        else:
            raise HTTPException(status_code=400, detail="نوع العميل يجب أن يكون 1، 2، أو 3")
        
        total_price = mm_cost + manufacturing_cost
        
        return {
            "material_type": material_type,
            "dimensions": f"{inner_diameter}×{outer_diameter}×{height}",
            "price_per_mm": pricing["price_per_mm"],
            "mm_cost": mm_cost,
            "manufacturing_cost": manufacturing_cost,
            "client_type": client_type,
            "total_price": total_price,
            "pricing_id": pricing["id"]
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Treasury Reset API (Only for Elsawy)
@api_router.post("/treasury/reset")
async def reset_treasury(username: str):
    """Reset all treasury data - Only for Elsawy user"""
    try:
        # Security check - only Elsawy can perform this operation
        if username != "Elsawy":
            raise HTTPException(status_code=403, detail="غير مصرح لك بتنفيذ هذه العملية")
        
        # Get count of records before deletion for logging
        treasury_count = await db.treasury_transactions.count_documents({})
        
        # Delete all treasury transactions
        treasury_result = await db.treasury_transactions.delete_many({})
        
        return {
            "message": "تم مسح جميع بيانات الخزينة بنجاح",
            "deleted_treasury_transactions": treasury_result.deleted_count,
            "reset_by": username,
            "reset_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Change Invoice Payment Method API
@api_router.put("/invoices/{invoice_id}/change-payment-method")
async def change_invoice_payment_method(
    invoice_id: str, 
    new_payment_method: str,
    password: str,
    username: str = None
):
    """Change invoice payment method and update treasury transactions - requires password"""
    try:
        # Verify password (create if not exists)
        password_doc = await db.invoice_operations_passwords.find_one({"id": "invoice_operations_password"})
        if not password_doc:
            default_password = InvoiceOperationsPassword(password="1462")
            await db.invoice_operations_passwords.insert_one(default_password.dict())
            password_doc = default_password.dict()
        
        if password != password_doc.get("password"):
            raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")
        # Find the invoice
        invoice = await db.invoices.find_one({"id": invoice_id})
        if not invoice:
            raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
        
        old_payment_method = invoice.get("payment_method")
        if old_payment_method == new_payment_method:
            return {"message": "طريقة الدفع هي نفسها بالفعل"}
        
        # Map payment methods to treasury account IDs
        payment_method_mapping = {
            "نقدي": "cash",
            "فودافون 010": "vodafone_elsawy", 
            "كاش 0100": "vodafone_wael",
            "انستاباي": "instapay",
            "يد الصاوي": "yad_elsawy",
            "آجل": "deferred"
        }
        
        old_account_id = payment_method_mapping.get(old_payment_method)
        new_account_id = payment_method_mapping.get(new_payment_method)
        
        # Handle special cases for deferred payment method
        if old_payment_method == "آجل":
            old_account_id = "deferred"
        if new_payment_method == "آجل":
            new_account_id = "deferred"
        
        # For deferred payments, we need to handle differently
        if old_payment_method == "آجل" and new_payment_method != "آجل":
            # Converting from deferred to immediate payment - only create positive transaction for new account
            new_account_id = payment_method_mapping.get(new_payment_method)
            if not new_account_id:
                raise HTTPException(status_code=400, detail=f"طريقة الدفع غير مدعومة: {new_payment_method}")
        elif old_payment_method != "آجل" and new_payment_method == "آجل":
            # Converting from immediate payment to deferred - only create negative transaction for old account
            old_account_id = payment_method_mapping.get(old_payment_method)
            if not old_account_id:
                raise HTTPException(status_code=400, detail=f"طريقة الدفع غير مدعومة: {old_payment_method}")
        elif old_payment_method != "آجل" and new_payment_method != "آجل":
            # Converting between immediate payment methods
            if not old_account_id or not new_account_id:
                raise HTTPException(status_code=400, detail="طريقة الدفع غير مدعومة")
        else:
            # Converting from deferred to deferred (shouldn't happen)
            raise HTTPException(status_code=400, detail="لا يمكن التحويل من آجل إلى آجل")
        
        invoice_amount = invoice.get("total_amount", 0)
        
        # Create treasury transactions for the transfer
        transfer_reference = f"تحويل دفع فاتورة {invoice.get('invoice_number')} من {old_payment_method} إلى {new_payment_method}"
        
        # Handle different conversion scenarios
        if old_payment_method == "آجل" and new_payment_method != "آجل":
            # Converting from deferred to immediate payment - only create positive transaction
            new_transaction = TreasuryTransaction(
                account_id=new_account_id,
                transaction_type="income",
                amount=invoice_amount,
                description=f"دفع فاتورة آجلة - {transfer_reference}",
                reference=f"تحويل-{invoice.get('invoice_number')}",
                balance=invoice_amount
            )
            new_dict = new_transaction.dict()
            new_dict["company_id"] = invoice.get("company_id", "elsawy")
            await db.treasury_transactions.insert_one(new_dict)
            
        elif old_payment_method != "آجل" and new_payment_method == "آجل":
            # Converting from immediate payment to deferred - only create negative transaction
            old_transaction = TreasuryTransaction(
                account_id=old_account_id,
                transaction_type="expense",
                amount=invoice_amount,
                description=f"تحويل إلى آجل - {transfer_reference}",
                reference=f"تحويل-{invoice.get('invoice_number')}",
                balance=-invoice_amount
            )
            old_dict = old_transaction.dict()
            old_dict["company_id"] = invoice.get("company_id", "elsawy")
            await db.treasury_transactions.insert_one(old_dict)
            
        else:
            # Converting between immediate payment methods
            # Remove from old account (negative transaction)
            old_transaction = TreasuryTransaction(
                account_id=old_account_id,
                transaction_type="expense",
                amount=invoice_amount,
                description=f"خصم لتحويل طريقة الدفع - {transfer_reference}",
                reference=f"تحويل-{invoice.get('invoice_number')}",
                balance=-invoice_amount
            )
            old_dict2 = old_transaction.dict()
            old_dict2["company_id"] = invoice.get("company_id", "elsawy")
            await db.treasury_transactions.insert_one(old_dict2)
            
            # Add to new account (positive transaction) 
            new_transaction = TreasuryTransaction(
                account_id=new_account_id,
                transaction_type="income",
                amount=invoice_amount,
                description=f"إضافة من تحويل طريقة الدفع - {transfer_reference}",
                reference=f"تحويل-{invoice.get('invoice_number')}",
                balance=invoice_amount
            )
            new_dict2 = new_transaction.dict()
            new_dict2["company_id"] = invoice.get("company_id", "elsawy")
            await db.treasury_transactions.insert_one(new_dict2)
        
        # Update invoice payment method and remaining amount based on conversion type
        update_data = {"payment_method": new_payment_method}
        
        if old_payment_method == "آجل" and new_payment_method != "آجل":
            # Converting from deferred to immediate payment - set remaining_amount to 0
            update_data["remaining_amount"] = 0.0
            update_data["paid_amount"] = invoice_amount
            update_data["status"] = "مدفوعة"
        elif old_payment_method != "آجل" and new_payment_method == "آجل":
            # Converting from immediate payment to deferred - set remaining_amount to total
            update_data["remaining_amount"] = invoice_amount
            update_data["paid_amount"] = 0.0
            update_data["status"] = "غير مدفوعة"
        # For immediate to immediate conversion, keep existing amounts unchanged
        
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": update_data}
        )
        
        return {
            "message": f"تم تحويل طريقة الدفع من {old_payment_method} إلى {new_payment_method}",
            "old_method": old_payment_method,
            "new_method": new_payment_method,
            "amount_transferred": invoice_amount
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Cancel Invoice API
@api_router.delete("/invoices/{invoice_id}/cancel")
async def cancel_invoice(invoice_id: str, password: str, username: str = None):
    """Cancel invoice and restore materials to inventory - requires password"""
    try:
        # Verify password (create if not exists)
        password_doc = await db.invoice_operations_passwords.find_one({"id": "invoice_operations_password"})
        if not password_doc:
            default_password = InvoiceOperationsPassword(password="1462")
            await db.invoice_operations_passwords.insert_one(default_password.dict())
            password_doc = default_password.dict()
        
        if password != password_doc.get("password"):
            raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")
        # Find the invoice
        invoice = await db.invoices.find_one({"id": invoice_id})
        if not invoice:
            raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
        
        # Restore materials to inventory for each item
        for item in invoice.get("items", []):
            if item.get("product_type") == "manufactured":
                # Handle multi-material restoration
                if item.get("selected_materials"):
                    for material_info in item.get("selected_materials", []):
                        raw_material = await db.raw_materials.find_one({
                            "unit_code": material_info.get("unit_code"),
                            "inner_diameter": material_info.get("inner_diameter"),
                            "outer_diameter": material_info.get("outer_diameter")
                        })
                        
                        if raw_material:
                            seals_to_restore = material_info.get("seals_count", 0)
                            material_to_restore = seals_to_restore * (item.get("height", 0) + 2)
                            
                            # Add material back
                            await db.raw_materials.update_one(
                                {"id": raw_material["id"]},
                                {"$inc": {"height": material_to_restore}}
                            )
                            
                            print(f"✅ تم استرداد {material_to_restore} مم للخامة {raw_material.get('unit_code')}")
                
                # Handle single material restoration
                elif item.get("material_details"):
                    material_details = item.get("material_details")
                    raw_material = await db.raw_materials.find_one({
                        "unit_code": material_details.get("unit_code"),
                        "inner_diameter": material_details.get("inner_diameter"),
                        "outer_diameter": material_details.get("outer_diameter")
                    })
                    
                    if raw_material:
                        material_to_restore = item.get("quantity", 0) * (item.get("height", 0) + 2)
                        
                        # Add material back
                        await db.raw_materials.update_one(
                            {"id": raw_material["id"]},
                            {"$inc": {"height": material_to_restore}}
                        )
                        
                        print(f"✅ تم استرداد {material_to_restore} مم للخامة {raw_material.get('unit_code')}")
        
        # Remove treasury transaction if not deferred
        if invoice.get("payment_method") != "آجل":
            payment_method_mapping = {
                "نقدي": "cash",
                "فودافون 010": "vodafone_elsawy",
                "كاش 0100": "vodafone_wael", 
                "انستاباي": "instapay",
                "يد الصاوي": "yad_elsawy"
            }
            
            account_id = payment_method_mapping.get(invoice.get("payment_method"))
            if account_id:
                # Create negative transaction to reverse the income
                reversal_transaction = TreasuryTransaction(
                    account_id=account_id,
                    transaction_type="expense",
                    amount=invoice.get("total_amount", 0),
                    description=f"إلغاء فاتورة {invoice.get('invoice_number')}",
                    reference=f"إلغاء-{invoice.get('invoice_number')}",
                    balance=-invoice.get("total_amount", 0)
                )
                await db.treasury_transactions.insert_one(reversal_transaction.dict())
        
        # Move invoice to deleted_invoices collection instead of deleting
        deleted_invoice = {**invoice}
        deleted_invoice["deleted_at"] = datetime.now(timezone.utc).isoformat()
        deleted_invoice["deleted_by"] = username or "unknown"
        await db.deleted_invoices.insert_one(deleted_invoice)
        
        # Remove invoice from active invoices
        await db.invoices.delete_one({"id": invoice_id})
        
        # Remove from work orders
        await db.work_orders.update_many(
            {"invoices.id": invoice_id},
            {"$pull": {"invoices": {"id": invoice_id}}}
        )
        
        return {
            "message": f"تم إلغاء الفاتورة {invoice.get('invoice_number')} واسترداد المواد",
            "invoice_number": invoice.get("invoice_number"),
            "materials_restored": True,
            "treasury_reversed": invoice.get("payment_method") != "آجل"
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Deleted Invoices APIs
@api_router.get("/deleted-invoices")
async def get_deleted_invoices(company_id: str = "elsawy"):
    """Get all deleted invoices"""
    try:
        invoices = await db.deleted_invoices.find({"company_id": company_id}).sort("deleted_at", -1).to_list(length=None)
        
        # Remove MongoDB ObjectId to prevent serialization issues
        for invoice in invoices:
            if "_id" in invoice:
                del invoice["_id"]
        
        return invoices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/deleted-invoices/{invoice_id}/restore")
async def restore_deleted_invoice(invoice_id: str, username: str = None):
    """Restore a deleted invoice"""
    try:
        # Find the deleted invoice
        deleted_invoice = await db.deleted_invoices.find_one({"id": invoice_id})
        if not deleted_invoice:
            raise HTTPException(status_code=404, detail="الفاتورة المحذوفة غير موجودة")
        
        # Remove deletion metadata
        del deleted_invoice["deleted_at"]
        del deleted_invoice["deleted_by"]
        if "_id" in deleted_invoice:
            del deleted_invoice["_id"]
        
        # Restore to active invoices
        await db.invoices.insert_one(deleted_invoice)
        
        # Remove from deleted invoices
        await db.deleted_invoices.delete_one({"id": invoice_id})
        
        # Note: We don't restore materials or treasury transactions
        # This just undeletes the invoice record
        
        return {
            "message": f"تم استعادة الفاتورة {deleted_invoice.get('invoice_number')}",
            "invoice_number": deleted_invoice.get("invoice_number"),
            "warning": "ملاحظة: المواد والخزينة لن يتم استرجاعها تلقائياً"
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/deleted-invoices/{invoice_id}")
async def permanently_delete_invoice(invoice_id: str):
    """Permanently delete an invoice (cannot be undone)"""
    try:
        result = await db.deleted_invoices.delete_one({"id": invoice_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="الفاتورة المحذوفة غير موجودة")
        return {"message": "تم حذف الفاتورة نهائياً"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# Business logic function for inventory transactions
async def create_inventory_transaction(transaction: InventoryTransactionCreate):
    """Create inventory transaction (in/out) - Business logic"""
    # Find inventory item by specifications if item_id not provided
    if not transaction.inventory_item_id:
        inventory_item = await db.inventory_items.find_one({
            "material_type": transaction.material_type,
            "inner_diameter": transaction.inner_diameter,
            "outer_diameter": transaction.outer_diameter
        })
        
        if not inventory_item:
            raise HTTPException(
                status_code=404, 
                detail=f"لا يوجد عنصر في الجرد بالمواصفات المطلوبة: {transaction.material_type} - {transaction.inner_diameter}x{transaction.outer_diameter}"
            )
        transaction.inventory_item_id = inventory_item["id"]
    else:
        inventory_item = await db.inventory_items.find_one({"id": transaction.inventory_item_id})
        if not inventory_item:
            raise HTTPException(status_code=404, detail="العنصر غير موجود في الجرد")
    
    # Check if there's enough stock for "out" transactions
    if transaction.transaction_type == "out" and abs(transaction.pieces_change) > inventory_item["available_pieces"]:
        raise HTTPException(
            status_code=400, 
            detail=f"المخزون غير كافي. المتاح: {inventory_item['available_pieces']} قطعة، المطلوب: {abs(transaction.pieces_change)} قطعة"
        )
    
    # Calculate new remaining pieces
    new_pieces = inventory_item["available_pieces"] + transaction.pieces_change
    if new_pieces < 0:
        new_pieces = 0
    
    # Create transaction
    transaction_obj = InventoryTransaction(
        **transaction.dict(),
        remaining_pieces=new_pieces
    )
    await db.inventory_transactions.insert_one(transaction_obj.dict())
    
    # Update inventory item
    await db.inventory_items.update_one(
        {"id": transaction.inventory_item_id},
        {
            "$set": {
                "available_pieces": new_pieces,
                "last_updated": datetime.utcnow()
            }
        }
    )
    
    transaction_dict = transaction_obj.dict()
    if "_id" in transaction_dict:
        del transaction_dict["_id"]
    return transaction_dict

@api_router.post("/inventory-transactions", response_model=InventoryTransaction)
async def create_inventory_transaction_api(transaction: InventoryTransactionCreate):
    """Create inventory transaction via API"""
    try:
        result = await create_inventory_transaction(transaction)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/inventory/check-availability")
async def check_inventory_availability(
    material_type: MaterialType, 
    inner_diameter: float, 
    outer_diameter: float, 
    required_pieces: int
):
    """Check if material is available in inventory with required pieces"""
    try:
        inventory_item = await db.inventory_items.find_one({
            "material_type": material_type,
            "inner_diameter": inner_diameter,
            "outer_diameter": outer_diameter
        })
        
        if not inventory_item:
            return {
                "available": False,
                "message": f"المادة الخام غير متوفرة في الجرد: {material_type} - {inner_diameter}x{outer_diameter}",
                "available_pieces": 0,
                "required_pieces": required_pieces
            }
        
        available_pieces = inventory_item.get("available_pieces", 0)
        is_available = available_pieces >= required_pieces
        
        return {
            "available": is_available,
            "message": f"{'المادة متوفرة' if is_available else 'المادة غير متوفرة بالكمية المطلوبة'}",
            "available_pieces": available_pieces,
            "required_pieces": required_pieces,
            "inventory_item_id": inventory_item["id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Excel Import/Export endpoints
@api_router.post("/excel/import/inventory")
async def import_inventory_excel(file: UploadFile = File(...)):
    """Import inventory items from Excel file"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="يجب أن يكون الملف من نوع Excel (.xlsx أو .xls)")
        
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        required_columns = ['material_type', 'inner_diameter', 'outer_diameter', 'available_pieces']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"أعمدة مفقودة: {', '.join(missing_columns)}")
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Check if item already exists
                existing_item = await db.inventory_items.find_one({
                    "material_type": row['material_type'],
                    "inner_diameter": float(row['inner_diameter']),
                    "outer_diameter": float(row['outer_diameter'])
                })
                
                if existing_item:
                    # Update existing item
                    await db.inventory_items.update_one(
                        {"id": existing_item["id"]},
                        {
                            "$set": {
                                "available_pieces": int(row['available_pieces']),
                                "min_stock_level": int(row.get('min_stock_level', 2)),
                                "notes": str(row.get('notes', '')),
                                "last_updated": datetime.utcnow()
                            }
                        }
                    )
                else:
                    # Create new item
                    inventory_item = InventoryItem(
                        material_type=row['material_type'],
                        inner_diameter=float(row['inner_diameter']),
                        outer_diameter=float(row['outer_diameter']),
                        available_pieces=int(row['available_pieces']),
                        min_stock_level=int(row.get('min_stock_level', 2)),
                        notes=str(row.get('notes', ''))
                    )
                    await db.inventory_items.insert_one(inventory_item.dict())
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"صف {index + 2}: {str(e)}")
        
        return {
            "message": f"تم استيراد {imported_count} عنصر بنجاح",
            "imported_count": imported_count,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في استيراد الملف: {str(e)}")

@api_router.get("/excel/export/inventory")
async def export_inventory_excel():
    """Export inventory items to Excel file"""
    try:
        # Get all inventory items
        items = await db.inventory_items.find({}).to_list(None)
        
        if not items:
            raise HTTPException(status_code=404, detail="لا توجد عناصر جرد للتصدير")
        
        # Convert to DataFrame
        df_data = []
        for item in items:
            df_data.append({
                'material_type': item.get('material_type', ''),
                'inner_diameter': item.get('inner_diameter', 0),
                'outer_diameter': item.get('outer_diameter', 0),
                'available_pieces': item.get('available_pieces', 0),
                'min_stock_level': item.get('min_stock_level', 2),
                'notes': item.get('notes', ''),
                'created_at': item.get('created_at', ''),
                'last_updated': item.get('last_updated', '')
            })
        
        df = pd.DataFrame(df_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Inventory', index=False)
            
            # Get the workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Inventory']
            
            # Add some formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Write the column headers with the defined format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        output.seek(0)
        
        # Return as streaming response
        current_date = datetime.now().strftime("%Y-%m-%d")
        filename = f"inventory_export_{current_date}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في تصدير الملف: {str(e)}")

@api_router.post("/excel/import/raw-materials")
async def import_raw_materials_excel(file: UploadFile = File(...)):
    """Import raw materials from Excel file"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="يجب أن يكون الملف من نوع Excel (.xlsx أو .xls)")
        
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        required_columns = ['material_type', 'inner_diameter', 'outer_diameter', 'height', 'pieces_count', 'unit_code', 'cost_per_mm']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"أعمدة مفقودة: {', '.join(missing_columns)}")
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                raw_material = RawMaterial(
                    material_type=row['material_type'],
                    inner_diameter=float(row['inner_diameter']),
                    outer_diameter=float(row['outer_diameter']),
                    height=float(row['height']),
                    pieces_count=int(row['pieces_count']),
                    unit_code=str(row['unit_code']),
                    cost_per_mm=float(row['cost_per_mm'])
                )
                await db.raw_materials.insert_one(raw_material.dict())
                imported_count += 1
                
            except Exception as e:
                errors.append(f"صف {index + 2}: {str(e)}")
        
        return {
            "message": f"تم استيراد {imported_count} مادة خام بنجاح",
            "imported_count": imported_count,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في استيراد الملف: {str(e)}")

@api_router.get("/excel/export/raw-materials")
async def export_raw_materials_excel():
    """Export raw materials to Excel file"""
    try:
        # Get all raw materials
        materials = await db.raw_materials.find({}).to_list(None)
        
        if not materials:
            raise HTTPException(status_code=404, detail="لا توجد مواد خام للتصدير")
        
        # Convert to DataFrame
        df_data = []
        for material in materials:
            df_data.append({
                'material_type': material.get('material_type', ''),
                'inner_diameter': material.get('inner_diameter', 0),
                'outer_diameter': material.get('outer_diameter', 0),
                'height': material.get('height', 0),
                'pieces_count': material.get('pieces_count', 0),
                'unit_code': material.get('unit_code', ''),
                'cost_per_mm': material.get('cost_per_mm', 0),
                'created_at': material.get('created_at', '')
            })
        
        df = pd.DataFrame(df_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Raw Materials', index=False)
            
            # Get the workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Raw Materials']
            
            # Add some formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Write the column headers with the defined format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        output.seek(0)
        
        # Return as streaming response
        current_date = datetime.now().strftime("%Y-%m-%d")
        filename = f"raw_materials_export_{current_date}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في تصدير الملف: {str(e)}")

# Helper function for background backup
async def perform_backup(backup_id: str, username: str, upload_to_drive: bool):
    """Perform backup in background"""
    try:
        backup_time = datetime.now(timezone.utc).isoformat()
        
        # Collections to backup
        collections = [
            'customers', 'suppliers', 'invoices', 'payments', 'expenses',
            'raw_materials', 'finished_products', 'inventory', 'inventory_transactions',
            'local_products', 'supplier_transactions', 'treasury_transactions',
            'work_orders', 'users', 'deleted_invoices',
            'company_settings', 'main_treasury_transactions', 'main_treasury_passwords',
            'material_pricing', 'pricing_rules'
        ]
        
        backup_data = {
            'backup_id': backup_id,
            'created_at': backup_time,
            'created_by': username or 'system',
            'collections': {},
            'drive_file_id': None,
            'drive_link': None,
            'status': 'in_progress'
        }
        
        # Save initial status
        await db.backups.insert_one(backup_data)
        
        # Backup each collection
        total_documents = 0
        collections_data = {}
        
        for collection_name in collections:
            try:
                collection = db[collection_name]
                documents = await collection.find().to_list(length=None)
                # Remove MongoDB _id for JSON serialization
                clean_documents = []
                for doc in documents:
                    doc_copy = dict(doc)
                    if '_id' in doc_copy:
                        del doc_copy['_id']
                    clean_documents.append(doc_copy)
                
                collections_data[collection_name] = clean_documents
                total_documents += len(clean_documents)
                logger.info(f"Backed up {collection_name}: {len(clean_documents)} documents")
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
@api_router.post("/backup/create")
async def create_backup(background_tasks: BackgroundTasks, username: str = None):
    """Create a manual backup of all database collections (background task)"""
    try:
        backup_id = str(uuid.uuid4())
        
        # Start backup in background (local only)
        background_tasks.add_task(perform_backup, backup_id, username, False)
        
        return {
            'message': 'بدأت عملية النسخ الاحتياطي المحلي',
            'backup_id': backup_id,
            'status': 'in_progress',
            'note': 'سيتم إشعارك عند اكتمال النسخ الاحتياطي'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في إنشاء النسخة الاحتياطية: {str(e)}")

@api_router.get("/backup/status/{backup_id}")
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

@api_router.get("/backup/download/{backup_id}")
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

@api_router.post("/backup/upload")
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

@api_router.post("/backup/restore-from-file")
async def restore_from_uploaded_file(file: UploadFile = File(...), username: str = None):
    """Restore database directly from uploaded backup file"""
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
        
        # Restore collections
        restored_collections = []
        total_restored = 0
        
        for collection_name, documents in backup_data['collections'].items():
            if not documents:
                continue
            
            try:
                collection = db[collection_name]
                
                # Clear existing data
                await collection.delete_many({})
                
                # Insert backup data
                if documents:
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

@api_router.get("/backup/list")
async def list_backups():
    """Get list of all backups"""
    try:
        backups = await db.backups.find({}, {
            'backup_id': 1,
            'created_at': 1,
            'created_by': 1,
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

@api_router.post("/backup/restore/{backup_id}")
async def restore_backup(backup_id: str, username: str = None):
    """Restore a backup"""
    try:
        # Find the backup
        backup = await db.backups.find_one({'backup_id': backup_id})
        if not backup:
            raise HTTPException(status_code=404, detail="النسخة الاحتياطية غير موجودة")
        
        if 'collections' not in backup:
            raise HTTPException(status_code=400, detail="النسخة الاحتياطية تالفة")
        
        restored_collections = []
        total_restored = 0
        
        # Restore each collection
        for collection_name, documents in backup['collections'].items():
            if not documents:
                continue
                
            try:
                collection = db[collection_name]
                
                # Clear existing data
                await collection.delete_many({})
                
                # Insert backup data
                if documents:
                    await collection.insert_many(documents)
                
                restored_collections.append(collection_name)
                total_restored += len(documents)
                
            except Exception as e:
                print(f"تحذير: فشل استرجاع {collection_name}: {str(e)}")
        
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

@api_router.delete("/backup/{backup_id}")
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
@api_router.get("/backup/drive/list")
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

@api_router.post("/backup/{backup_id}/upload-to-drive")
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

@api_router.get("/backup/drive/download/{file_id}")
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

@api_router.post("/backup/drive/restore/{file_id}")
async def restore_from_drive(file_id: str):
    """Restore backup from Google Drive file"""
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
                    
                    # Clear existing data
                    await collection.delete_many({})
                    
                    # Insert backup data
                    if documents:
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

@api_router.get("/backup/drive/status")
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
    "logo_url": "https://customer-assets.emergentagent.com/job_oilseal-mgmt/artifacts/42i3e7yn_WhatsApp%20Image%202025-07-31%20at%2015.14.10_e8c55120.jpg",
    "system_subtitle": "نظام إدارة متكامل"
}

@api_router.get("/settings")
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

@api_router.put("/settings")
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

@api_router.post("/settings/logo")
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

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Backup Scheduler
scheduler = BackgroundScheduler()

async def scheduled_backup():
    """Scheduled automatic backup"""
    try:
        logger.info("Starting scheduled automatic backup...")
        
        # Create backup
        backup_id = str(uuid.uuid4())
        backup_time = datetime.now(timezone.utc).isoformat()
        
        collections = [
            'customers', 'suppliers', 'invoices', 'payments', 'expenses',
            'raw_materials', 'finished_products', 'inventory', 'inventory_transactions',
            'local_products', 'supplier_transactions', 'treasury_transactions',
            'work_orders', 'users', 'deleted_invoices',
            'company_settings', 'main_treasury_transactions', 'main_treasury_passwords',
            'material_pricing', 'pricing_rules'
        ]
        
        backup_data = {
            'backup_id': backup_id,
            'created_at': backup_time,
            'created_by': 'system_scheduled',
            'collections': {},
            'drive_file_id': None,
            'drive_link': None,
            'is_scheduled': True
        }
        
        total_documents = 0
        for collection_name in collections:
            try:
                collection = db[collection_name]
                documents = await collection.find().to_list(length=None)
                for doc in documents:
                    if '_id' in doc:
                        del doc['_id']
                backup_data['collections'][collection_name] = documents
                total_documents += len(documents)
            except Exception as e:
                logger.warning(f"Failed to backup {collection_name}: {str(e)}")
                backup_data['collections'][collection_name] = []
        
        # Save to database
        backup_data['total_documents'] = total_documents
        backup_data['status'] = 'completed'
        await db.backups.insert_one(backup_data)
        
        # Upload to Google Drive
        if GDRIVE_ENABLED and drive_service:
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'scheduled_backup_{timestamp}.json'
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
                    
                    logger.info(f"Scheduled backup completed and uploaded to Google Drive: {filename}")
                    
                except Exception as drive_error:
                    logger.warning(f"Scheduled backup completed locally only: {str(drive_error)}")
                
                # Cleanup
                if temp_file.exists():
                    os.remove(temp_file)
                    
            except Exception as e:
                logger.error(f"Failed to process scheduled backup Drive upload: {str(e)}")
        else:
            logger.info(f"Scheduled backup completed (local only): {total_documents} documents")
        
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

@app.on_event("shutdown")
async def shutdown_scheduler():
    """Shutdown scheduler"""
    scheduler.shutdown()
    logger.info("Backup scheduler stopped")

# ============================================================================
# Main Treasury APIs - الخزنة الرئيسية
# ============================================================================

@api_router.post("/main-treasury/verify-password")
async def verify_main_treasury_password(password_data: PasswordVerify, company_id: str = "elsawy"):
    """Verify password for main treasury access"""
    try:
        # Get stored password
        password_doc = await db.main_treasury_passwords.find_one({"id": "main_treasury_password", "company_id": company_id})
        
        # If no password set yet, create default one
        if not password_doc:
            default_password = MainTreasuryPassword(password="100100")  # Default password
            obj = default_password.dict()
            obj["company_id"] = company_id
            await db.main_treasury_passwords.insert_one(obj)
            password_doc = obj
        
        # Verify password
        if password_data.password == password_doc.get("password"):
            return {"success": True, "message": "تم التحقق من كلمة المرور بنجاح"}
        else:
            return {"success": False, "message": "كلمة المرور غير صحيحة"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/main-treasury/change-password")
async def change_main_treasury_password(password_change: PasswordChange, company_id: str = "elsawy"):
    """Change main treasury password"""
    try:
        # Get stored password
        password_doc = await db.main_treasury_passwords.find_one({"id": "main_treasury_password", "company_id": company_id})
        
        if not password_doc:
            raise HTTPException(status_code=404, detail="كلمة المرور غير موجودة")
        
        # Verify old password
        if password_change.old_password != password_doc.get("password"):
            raise HTTPException(status_code=401, detail="كلمة المرور القديمة غير صحيحة")
        
        # Update password
        result = await db.main_treasury_passwords.update_one(
            {"id": "main_treasury_password", "company_id": company_id},
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

@api_router.get("/main-treasury/balance")
async def get_main_treasury_balance(company_id: str = "elsawy"):
    """Get current main treasury balance"""
    try:
        # Get all transactions
        transactions = await db.main_treasury_transactions.find({"company_id": company_id}).to_list(10000)
        
        # Calculate balance
        balance = 0
        for transaction in transactions:
            transaction_type = transaction.get('transaction_type')
            amount = transaction.get('amount', 0)
            
            if transaction_type in ['deposit', 'transfer_from_yad']:
                balance += amount
            elif transaction_type == 'withdrawal':
                balance -= amount
        
        return {
            "balance": balance,
            "transaction_count": len(transactions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/main-treasury/transactions")
async def get_main_treasury_transactions(company_id: str = "elsawy"):
    """Get all main treasury transactions"""
    try:
        transactions = await db.main_treasury_transactions.find({"company_id": company_id}).sort("date", -1).to_list(10000)
        
        # Remove MongoDB _id
        for transaction in transactions:
            if "_id" in transaction:
                del transaction["_id"]
        
        return transactions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/main-treasury/deposit")
async def deposit_to_main_treasury(transaction: MainTreasuryTransactionCreate, username: str, company_id: str = "elsawy"):
    """Manual deposit to main treasury - إيداع يدوي"""
    try:
        # Get current balance
        balance_response = await get_main_treasury_balance(company_id)
        current_balance = balance_response["balance"]
        new_balance = current_balance + transaction.amount
        
        # Create transaction
        transaction_obj = MainTreasuryTransaction(
            transaction_type="deposit",
            amount=transaction.amount,
            description=transaction.description,
            reference=transaction.reference,
            balance_after=new_balance,
            performed_by=username
        )
        
        obj = transaction_obj.dict()
        obj["company_id"] = company_id
        await db.main_treasury_transactions.insert_one(obj)
        
        return {
            "success": True,
            "message": "تم الإيداع بنجاح",
            "transaction_id": transaction_obj.id,
            "new_balance": new_balance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/main-treasury/withdrawal")
async def withdrawal_from_main_treasury(transaction: MainTreasuryTransactionCreate, username: str, company_id: str = "elsawy"):
    """Manual withdrawal from main treasury - صرف يدوي"""
    try:
        # Get current balance
        balance_response = await get_main_treasury_balance(company_id)
        current_balance = balance_response["balance"]
        
        # Check if sufficient balance
        if current_balance < transaction.amount:
            raise HTTPException(
                status_code=400, 
                detail=f"الرصيد غير كافٍ. الرصيد الحالي: {current_balance} ج.م"
            )
        
        new_balance = current_balance - transaction.amount
        
        # Create transaction
        transaction_obj = MainTreasuryTransaction(
            transaction_type="withdrawal",
            amount=transaction.amount,
            description=transaction.description,
            reference=transaction.reference,
            balance_after=new_balance,
            performed_by=username
        )
        
        obj = transaction_obj.dict()
        obj["company_id"] = company_id
        await db.main_treasury_transactions.insert_one(obj)
        
        return {
            "success": True,
            "message": "تم الصرف بنجاح",
            "transaction_id": transaction_obj.id,
            "new_balance": new_balance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/main-treasury/transfer-from-yad")
async def transfer_from_yad_to_main_treasury(amount: float, username: str, company_id: str = "elsawy"):
    """Transfer from yad to main treasury - ترحيل"""
    try:
        # Get current main treasury balance
        balance_response = await get_main_treasury_balance(company_id)
        current_balance = balance_response["balance"]
        new_balance = current_balance + amount
        
        # Create transaction in main treasury
        transaction_obj = MainTreasuryTransaction(
            transaction_type="transfer_from_yad",
            amount=amount,
            description=f"ترحيل من الخزينة",
            reference="تحويل تلقائي عند التصفير",
            balance_after=new_balance,
            performed_by=username
        )
        
        obj = transaction_obj.dict()
        obj["company_id"] = company_id
        await db.main_treasury_transactions.insert_one(obj)
        
        return {
            "success": True,
            "message": "تم الترحيل بنجاح للخزنة الرئيسية",
            "transaction_id": transaction_obj.id,
            "new_balance": new_balance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# End of Main Treasury APIs
# ============================================================================

# ============================================================================
# Deleted Invoices Password Protection APIs
# ============================================================================

@api_router.post("/deleted-invoices/verify-password")
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

@api_router.post("/deleted-invoices/change-password")
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

@api_router.post("/invoice-operations/verify-password")
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

@api_router.post("/invoice-operations/change-password")
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

# ============================================================================
# End of Invoice Operations Password Protection APIs
# ============================================================================

# ============================================================================
# Bulk Invoice Deletion APIs (For Backup Management Page)
# ============================================================================

@api_router.post("/invoices/bulk-delete-by-date")
async def bulk_delete_invoices_by_date(date: str, password: str, username: str):
    """Delete all invoices of a specific date - Elsawy only with password"""
    try:
        # Security checks
        if username != "Elsawy":
            raise HTTPException(status_code=403, detail="غير مصرح لك بتنفيذ هذه العملية")
        
        if password != "200200":
            raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")
        
        # Parse date (expecting format: YYYY-MM-DD)
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except:
            raise HTTPException(status_code=400, detail="صيغة التاريخ غير صحيحة. استخدم: YYYY-MM-DD")
        
        # Find all invoices for this date
        all_invoices = await db.invoices.find().to_list(length=None)
        invoices_to_delete = []
        
        for invoice in all_invoices:
            invoice_date_str = invoice.get("date")
            if invoice_date_str:
                try:
                    invoice_date = datetime.fromisoformat(invoice_date_str).date()
                    if invoice_date == target_date:
                        invoices_to_delete.append(invoice)
                except:
                    pass
        
        if not invoices_to_delete:
            return {
                "message": f"لا توجد فواتير في تاريخ {date}",
                "deleted_count": 0,
                "invoices": []
            }
        
        # Delete each invoice with full reversal
        deleted_invoices = []
        for invoice in invoices_to_delete:
            # Restore materials
            for item in invoice.get("items", []):
                if item.get("product_type") == "manufactured":
                    # Handle multi-material restoration
                    if item.get("selected_materials"):
                        for material_info in item.get("selected_materials", []):
                            raw_material = await db.raw_materials.find_one({
                                "unit_code": material_info.get("unit_code"),
                                "inner_diameter": material_info.get("inner_diameter"),
                                "outer_diameter": material_info.get("outer_diameter")
                            })
                            
                            if raw_material:
                                seals_to_restore = material_info.get("seals_count", 0)
                                material_to_restore = seals_to_restore * (item.get("height", 0) + 2)
                                await db.raw_materials.update_one(
                                    {"id": raw_material["id"]},
                                    {"$inc": {"height": material_to_restore}}
                                )
                    
                    # Handle single material restoration
                    elif item.get("material_details"):
                        material_details = item.get("material_details")
                        raw_material = await db.raw_materials.find_one({
                            "unit_code": material_details.get("unit_code"),
                            "inner_diameter": material_details.get("inner_diameter"),
                            "outer_diameter": material_details.get("outer_diameter")
                        })
                        
                        if raw_material:
                            material_to_restore = item.get("quantity", 0) * (item.get("height", 0) + 2)
                            await db.raw_materials.update_one(
                                {"id": raw_material["id"]},
                                {"$inc": {"height": material_to_restore}}
                            )
            
            # Reverse treasury transaction
            if invoice.get("payment_method") != "آجل":
                payment_method_mapping = {
                    "نقدي": "cash",
                    "فودافون 010": "vodafone_elsawy",
                    "كاش 0100": "vodafone_wael",
                    "انستاباي": "instapay",
                    "يد الصاوي": "yad_elsawy"
                }
                
                account_id = payment_method_mapping.get(invoice.get("payment_method"))
                if account_id:
                    reversal_transaction = TreasuryTransaction(
                        account_id=account_id,
                        transaction_type="expense",
                        amount=invoice.get("total_amount", 0),
                        description=f"حذف جماعي - فاتورة {invoice.get('invoice_number')}",
                        reference=f"bulk-delete-{invoice.get('invoice_number')}",
                        balance=-invoice.get("total_amount", 0)
                    )
                    await db.treasury_transactions.insert_one(reversal_transaction.dict())
            
            # Move to deleted_invoices
            deleted_invoice = {**invoice}
            deleted_invoice["deleted_at"] = datetime.now(timezone.utc).isoformat()
            deleted_invoice["deleted_by"] = username
            deleted_invoice["deletion_reason"] = f"حذف جماعي - تاريخ {date}"
            await db.deleted_invoices.insert_one(deleted_invoice)
            
            # Remove from active invoices
            await db.invoices.delete_one({"id": invoice["id"]})
            
            deleted_invoices.append({
                "invoice_number": invoice.get("invoice_number"),
                "customer_name": invoice.get("customer_name"),
                "total_amount": invoice.get("total_amount")
            })
        
        return {
            "message": f"تم حذف {len(deleted_invoices)} فاتورة من تاريخ {date}",
            "deleted_count": len(deleted_invoices),
            "invoices": deleted_invoices,
            "date": date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/invoices/bulk-delete-last")
async def bulk_delete_last_invoices(count: int, password: str, username: str):
    """Delete last N invoices - Elsawy only with password"""
    try:
        # Security checks
        if username != "Elsawy":
            raise HTTPException(status_code=403, detail="غير مصرح لك بتنفيذ هذه العملية")
        
        if password != "200200":
            raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")
        
        if count < 1 or count > 10:
            raise HTTPException(status_code=400, detail="يمكن حذف من 1 إلى 10 فواتير فقط")
        
        # Get last N invoices (sorted by date descending)
        all_invoices = await db.invoices.find().sort("date", -1).limit(count).to_list(length=count)
        
        if not all_invoices:
            return {
                "message": "لا توجد فواتير للحذف",
                "deleted_count": 0,
                "invoices": []
            }
        
        # Delete each invoice with full reversal
        deleted_invoices = []
        for invoice in all_invoices:
            # Restore materials
            for item in invoice.get("items", []):
                if item.get("product_type") == "manufactured":
                    # Handle multi-material restoration
                    if item.get("selected_materials"):
                        for material_info in item.get("selected_materials", []):
                            raw_material = await db.raw_materials.find_one({
                                "unit_code": material_info.get("unit_code"),
                                "inner_diameter": material_info.get("inner_diameter"),
                                "outer_diameter": material_info.get("outer_diameter")
                            })
                            
                            if raw_material:
                                seals_to_restore = material_info.get("seals_count", 0)
                                material_to_restore = seals_to_restore * (item.get("height", 0) + 2)
                                await db.raw_materials.update_one(
                                    {"id": raw_material["id"]},
                                    {"$inc": {"height": material_to_restore}}
                                )
                    
                    # Handle single material restoration
                    elif item.get("material_details"):
                        material_details = item.get("material_details")
                        raw_material = await db.raw_materials.find_one({
                            "unit_code": material_details.get("unit_code"),
                            "inner_diameter": material_details.get("inner_diameter"),
                            "outer_diameter": material_details.get("outer_diameter")
                        })
                        
                        if raw_material:
                            material_to_restore = item.get("quantity", 0) * (item.get("height", 0) + 2)
                            await db.raw_materials.update_one(
                                {"id": raw_material["id"]},
                                {"$inc": {"height": material_to_restore}}
                            )
            
            # Reverse treasury transaction
            if invoice.get("payment_method") != "آجل":
                payment_method_mapping = {
                    "نقدي": "cash",
                    "فودافون 010": "vodafone_elsawy",
                    "كاش 0100": "vodafone_wael",
                    "انستاباي": "instapay",
                    "يد الصاوي": "yad_elsawy"
                }
                
                account_id = payment_method_mapping.get(invoice.get("payment_method"))
                if account_id:
                    reversal_transaction = TreasuryTransaction(
                        account_id=account_id,
                        transaction_type="expense",
                        amount=invoice.get("total_amount", 0),
                        description=f"حذف آخر فواتير - فاتورة {invoice.get('invoice_number')}",
                        reference=f"bulk-delete-last-{invoice.get('invoice_number')}",
                        balance=-invoice.get("total_amount", 0)
                    )
                    await db.treasury_transactions.insert_one(reversal_transaction.dict())
            
            # Move to deleted_invoices
            deleted_invoice = {**invoice}
            deleted_invoice["deleted_at"] = datetime.now(timezone.utc).isoformat()
            deleted_invoice["deleted_by"] = username
            deleted_invoice["deletion_reason"] = f"حذف آخر {count} فاتورة"
            await db.deleted_invoices.insert_one(deleted_invoice)
            
            # Remove from active invoices
            await db.invoices.delete_one({"id": invoice["id"]})
            
            deleted_invoices.append({
                "invoice_number": invoice.get("invoice_number"),
                "customer_name": invoice.get("customer_name"),
                "total_amount": invoice.get("total_amount"),
                "date": invoice.get("date")
            })
        
        return {
            "message": f"تم حذف آخر {len(deleted_invoices)} فاتورة",
            "deleted_count": len(deleted_invoices),
            "invoices": deleted_invoices
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# End of Bulk Invoice Deletion APIs
# ============================================================================

# ============================================================================
# Customer Account Settlement API
# ============================================================================

@api_router.post("/customers/{customer_id}/settle-account")
async def settle_customer_account(
    customer_id: str,
    amount_paid: float,
    payment_method: str,
    username: str = None
):
    """Settle customer account by distributing payment across deferred invoices from oldest to newest"""
    try:
        # Validate amount
        if amount_paid <= 0:
            raise HTTPException(status_code=400, detail="المبلغ يجب أن يكون أكبر من صفر")
        
        # Get customer
        customer = await db.customers.find_one({"id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="العميل غير موجود")
        
        # Get all deferred invoices for this customer with remaining amount > 0
        deferred_invoices = await db.invoices.find({
            "customer_name": customer["name"],
            "payment_method": "آجل",
            "remaining_amount": {"$gt": 0}
        }).sort("date", 1).to_list(length=None)  # Sort by date ascending (oldest first)
        
        if not deferred_invoices:
            return {
                "success": False,
                "message": f"لا توجد فواتير آجلة مستحقة للعميل {customer['name']}",
                "paid_invoices": [],
                "remaining_amount": amount_paid
            }
        
        # Distribute payment across invoices
        remaining_payment = amount_paid
        paid_invoices = []
        payment_records = []
        
        # Map payment methods to treasury account IDs
        payment_method_mapping = {
            "نقدي": "cash",
            "فودافون 010": "vodafone_elsawy",
            "كاش 0100": "vodafone_wael",
            "انستاباي": "instapay",
            "يد الصاوي": "yad_elsawy"
        }
        
        for invoice in deferred_invoices:
            if remaining_payment <= 0:
                break
            
            invoice_remaining = invoice.get("remaining_amount", 0)
            payment_for_this_invoice = min(remaining_payment, invoice_remaining)
            
            # Update invoice
            new_paid_amount = invoice.get("paid_amount", 0) + payment_for_this_invoice
            new_remaining_amount = invoice.get("total_amount", 0) - new_paid_amount
            
            await db.invoices.update_one(
                {"id": invoice["id"]},
                {"$set": {
                    "paid_amount": new_paid_amount,
                    "remaining_amount": new_remaining_amount
                }}
            )
            
            # Create payment record
            payment_record = {
                "id": str(uuid.uuid4()),
                "invoice_id": invoice["id"],
                "invoice_number": invoice.get("invoice_number"),
                "customer_name": customer["name"],
                "amount": payment_for_this_invoice,
                "payment_method": payment_method,
                "date": datetime.now(timezone.utc).isoformat(),
                "settled_by": username or "unknown"
            }
            await db.payments.insert_one(payment_record)
            payment_records.append(payment_record)
            
            # Create treasury transaction for this payment
            account_id = payment_method_mapping.get(payment_method)
            if account_id:
                treasury_transaction = TreasuryTransaction(
                    account_id=account_id,
                    transaction_type="income",
                    amount=payment_for_this_invoice,
                    description=f"تصفية حساب - فاتورة {invoice.get('invoice_number')} - {customer['name']}",
                    reference=f"settlement-{invoice.get('invoice_number')}",
                    balance=payment_for_this_invoice
                )
                await db.treasury_transactions.insert_one(treasury_transaction.dict())
            
            # Track paid invoice
            paid_invoices.append({
                "invoice_number": invoice.get("invoice_number"),
                "invoice_id": invoice["id"],
                "original_remaining": invoice_remaining,
                "amount_paid": payment_for_this_invoice,
                "new_remaining": new_remaining_amount,
                "status": "مدفوعة بالكامل" if new_remaining_amount == 0 else "دفع جزئي"
            })
            
            remaining_payment -= payment_for_this_invoice
        
        return {
            "success": True,
            "message": f"تم تصفية حساب العميل {customer['name']} بنجاح",
            "customer_name": customer["name"],
            "total_amount_paid": amount_paid,
            "amount_distributed": amount_paid - remaining_payment,
            "remaining_amount": remaining_payment,
            "payment_method": payment_method,
            "paid_invoices": paid_invoices,
            "invoices_count": len(paid_invoices)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# End of Customer Account Settlement API
# ============================================================================

# ============================================================================
# Customer-Supplier Account Reconciliation API
# ============================================================================

@api_router.post("/customers/{customer_id}/reconcile-with-supplier")
async def reconcile_customer_supplier_account(
    customer_id: str,
    username: str = None
):
    """Reconcile customer and supplier accounts (no cash flow - internal settlement)"""
    try:
        # Get customer
        customer = await db.customers.find_one({"id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="العميل غير موجود")
        
        # Check if customer is also a supplier
        supplier = await db.suppliers.find_one({"name": customer["name"]})
        if not supplier:
            raise HTTPException(
                status_code=400, 
                detail=f"العميل {customer['name']} ليس مورداً. لا يمكن إجراء التسوية"
            )
        
        # Get customer's deferred invoices (what they owe us)
        customer_invoices = await db.invoices.find({
            "customer_name": customer["name"],
            "payment_method": "آجل",
            "remaining_amount": {"$gt": 0}
        }).sort("date", 1).to_list(length=None)
        
        customer_total_debt = sum(inv.get("remaining_amount", 0) for inv in customer_invoices)
        
        # Get supplier balance (what we owe them) - support both field names
        supplier_balance = supplier.get("current_balance", supplier.get("balance", 0))
        
        if supplier_balance <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"رصيد المورد {supplier['name']} = {supplier_balance} ج.م. لا يمكن إجراء التسوية"
            )
        
        if customer_total_debt <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"لا توجد فواتير آجلة للعميل {customer['name']}. لا يمكن إجراء التسوية"
            )
        
        # Calculate settlement amount (minimum of both)
        settlement_amount = min(supplier_balance, customer_total_debt)
        
        # Distribute settlement on customer invoices
        remaining_settlement = settlement_amount
        settled_invoices = []
        
        for invoice in customer_invoices:
            if remaining_settlement <= 0:
                break
            
            invoice_remaining = invoice.get("remaining_amount", 0)
            payment_for_this_invoice = min(remaining_settlement, invoice_remaining)
            
            # Update invoice
            new_paid_amount = invoice.get("paid_amount", 0) + payment_for_this_invoice
            new_remaining_amount = invoice.get("total_amount", 0) - new_paid_amount
            
            await db.invoices.update_one(
                {"id": invoice["id"]},
                {"$set": {
                    "paid_amount": new_paid_amount,
                    "remaining_amount": new_remaining_amount,
                    "payment_method": "تسوية حساب" if new_remaining_amount == 0 else "آجل"
                }}
            )
            
            # Create payment record with special note
            payment_record = {
                "id": str(uuid.uuid4()),
                "invoice_id": invoice["id"],
                "invoice_number": invoice.get("invoice_number"),
                "customer_name": customer["name"],
                "amount": payment_for_this_invoice,
                "payment_method": "تسوية مع حساب المورد",
                "date": datetime.now(timezone.utc).isoformat(),
                "settled_by": username or "unknown",
                "note": f"تسوية داخلية - لا تأثير على الخزينة"
            }
            await db.payments.insert_one(payment_record)
            
            # Track settled invoice
            settled_invoices.append({
                "invoice_number": invoice.get("invoice_number"),
                "invoice_id": invoice["id"],
                "original_remaining": invoice_remaining,
                "amount_paid": payment_for_this_invoice,
                "new_remaining": new_remaining_amount,
                "status": "مدفوعة بالكامل" if new_remaining_amount == 0 else "دفع جزئي"
            })
            
            remaining_settlement -= payment_for_this_invoice
        
        # Update supplier balance (reduce by settlement amount)
        new_supplier_balance = supplier_balance - settlement_amount
        await db.suppliers.update_one(
            {"id": supplier["id"]},
            {"$set": {
                "current_balance": new_supplier_balance,
                "balance": new_supplier_balance  # Update both fields for compatibility
            }}
        )
        
        # Create supplier transaction record
        supplier_transaction = {
            "id": str(uuid.uuid4()),
            "supplier_id": supplier["id"],
            "supplier_name": supplier["name"],
            "transaction_type": "payment",
            "amount": settlement_amount,
            "description": f"تسوية حساب مع العميل {customer['name']}",
            "date": datetime.now(timezone.utc).isoformat(),
            "balance_after": new_supplier_balance,
            "performed_by": username or "unknown",
            "note": "تسوية داخلية - لا تأثير على الخزينة"
        }
        await db.supplier_transactions.insert_one(supplier_transaction)
        
        return {
            "success": True,
            "message": f"تمت التسوية بين حساب العميل والمورد {customer['name']} بنجاح",
            "customer_name": customer["name"],
            "supplier_previous_balance": supplier_balance,
            "customer_previous_debt": customer_total_debt,
            "settlement_amount": settlement_amount,
            "supplier_new_balance": new_supplier_balance,
            "customer_remaining_debt": customer_total_debt - settlement_amount,
            "settled_invoices": settled_invoices,
            "invoices_count": len(settled_invoices),
            "note": "⚠️ تسوية داخلية - لا تأثير على الخزينة"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# End of Customer-Supplier Account Reconciliation API
# ============================================================================

# ============================================================================
# Master User - Delete Records APIs (Treasury Transactions, Supplier Transactions)
# ============================================================================

@api_router.delete("/treasury/transactions/{transaction_id}")
async def delete_treasury_transaction(
    transaction_id: str, 
    username: str,
    reverse_transaction: bool = False
):
    """Delete treasury transaction - Master only
    reverse_transaction: if True, reverses the transaction effect on balance
    """
    try:
        # Check if user is master
        if username != "master":
            raise HTTPException(status_code=403, detail="غير مصرح لك بحذف السجلات")
        
        # Find transaction before deleting
        transaction = await db.treasury_transactions.find_one({"id": transaction_id})
        if not transaction:
            raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
        
        # If reverse_transaction is True, create a reversal transaction
        if reverse_transaction:
            reversal_type = "expense" if transaction.get("transaction_type") == "income" else "income"
            reversal_transaction = TreasuryTransaction(
                account_id=transaction.get("account_id"),
                transaction_type=reversal_type,
                amount=transaction.get("amount", 0),
                description=f"عكس معاملة محذوفة - {transaction.get('description')}",
                reference=f"reversal-{transaction_id}",
                balance=-transaction.get("amount", 0) if reversal_type == "expense" else transaction.get("amount", 0)
            )
            await db.treasury_transactions.insert_one(reversal_transaction.dict())
        
        # Delete original transaction
        result = await db.treasury_transactions.delete_one({"id": transaction_id})
        
        if result.deleted_count > 0:
            message = "تم حذف المعاملة بنجاح"
            if reverse_transaction:
                message += " وتم عكس تأثيرها على الحساب"
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Edit treasury transaction record - Master only (without affecting balance)
class EditTransactionRequest(BaseModel):
    description: Optional[str] = None
    reference: Optional[str] = None
    # Note: amount is NOT included because editing it would affect balance calculations

@api_router.put("/treasury/transactions/{transaction_id}/edit-record")
async def edit_treasury_transaction_record(
    transaction_id: str,
    edit_data: EditTransactionRequest,
    username: str
):
    """
    Edit treasury transaction record - Master only
    This only edits the record (description, reference) without affecting the actual balance
    NOTE: Amount cannot be edited as it would affect balance calculations
    """
    try:
        # Check if user is master
        if username != "master":
            raise HTTPException(status_code=403, detail="غير مصرح لك بتعديل السجلات")
        
        # Find transaction
        transaction = await db.treasury_transactions.find_one({"id": transaction_id})
        if not transaction:
            raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
        
        # Prepare update data (only description and reference, NOT amount)
        update_data = {}
        if edit_data.description is not None:
            update_data["description"] = edit_data.description
        if edit_data.reference is not None:
            update_data["reference"] = edit_data.reference
        
        if not update_data:
            raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")
        
        # Update the record
        result = await db.treasury_transactions.update_one(
            {"id": transaction_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "message": "تم تعديل السجل بنجاح (بدون تأثير على الرصيد)",
                "updated_fields": list(update_data.keys()),
                "note": "المبلغ لا يمكن تعديله لأنه يؤثر على حساب الرصيد"
            }
        else:
            return {
                "success": True,
                "message": "لم يتم إجراء أي تغييرات"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Edit invoice display amount - Master only (without affecting balance)
class EditInvoiceDisplayRequest(BaseModel):
    display_amount: Optional[float] = None
    display_description: Optional[str] = None
    display_reference: Optional[str] = None

@api_router.put("/invoices/{invoice_id}/edit-display")
async def edit_invoice_display(
    invoice_id: str,
    edit_data: EditInvoiceDisplayRequest,
    username: str
):
    """
    Edit invoice display values - Master only
    This only edits the display values (shown in treasury) without affecting the actual balance
    The actual total_amount remains unchanged for balance calculations
    """
    try:
        # Check if user is master
        if username != "master":
            raise HTTPException(status_code=403, detail="غير مصرح لك بتعديل السجلات")
        
        # Find invoice
        invoice = await db.invoices.find_one({"id": invoice_id})
        if not invoice:
            raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
        
        # Prepare update data
        update_data = {}
        if edit_data.display_amount is not None:
            update_data["display_amount"] = edit_data.display_amount
        if edit_data.display_description is not None:
            update_data["display_description"] = edit_data.display_description
        if edit_data.display_reference is not None:
            update_data["display_reference"] = edit_data.display_reference
        
        if not update_data:
            raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")
        
        # Update the invoice
        result = await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "message": "تم تعديل السجل بنجاح (بدون تأثير على الرصيد)",
                "updated_fields": list(update_data.keys()),
                "note": "المبلغ الفعلي للفاتورة لم يتغير، فقط القيم المعروضة في السجل"
            }
        else:
            return {
                "success": True,
                "message": "لم يتم إجراء أي تغييرات"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/suppliers/transactions/{transaction_id}")
async def delete_supplier_transaction(
    transaction_id: str, 
    username: str,
    reverse_transaction: bool = False
):
    """Delete supplier transaction - Master only
    reverse_transaction: if True, reverses the transaction and recalculates balance
                         if False, just deletes the record without affecting balance
    """
    try:
        # Check if user is master
        if username != "master":
            raise HTTPException(status_code=403, detail="غير مصرح لك بحذف السجلات")
        
        # Find transaction to get supplier info
        transaction = await db.supplier_transactions.find_one({"id": transaction_id})
        if not transaction:
            raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
        
        supplier_id = transaction.get("supplier_id")
        
        # If reverse_transaction is True, create a reversal transaction
        if reverse_transaction and supplier_id:
            supplier = await db.suppliers.find_one({"id": supplier_id})
            if supplier:
                # Create opposite transaction
                reversal_type = "payment" if transaction.get("transaction_type") == "purchase" else "purchase"
                
                current_balance = supplier.get("current_balance", 0)
                amount = transaction.get("amount", 0)
                
                # Calculate new balance after reversal
                if reversal_type == "payment":
                    new_balance = current_balance - amount
                else:
                    new_balance = current_balance + amount
                
                reversal_transaction = {
                    "id": str(uuid.uuid4()),
                    "supplier_id": supplier_id,
                    "supplier_name": transaction.get("supplier_name"),
                    "transaction_type": reversal_type,
                    "amount": amount,
                    "description": f"عكس معاملة محذوفة - {transaction.get('description')}",
                    "date": datetime.now(timezone.utc).isoformat(),
                    "balance_after": new_balance,
                    "performed_by": username,
                    "note": "عكس معاملة محذوفة"
                }
                
                await db.supplier_transactions.insert_one(reversal_transaction)
                
                # Update supplier balance
                await db.suppliers.update_one(
                    {"id": supplier_id},
                    {"$set": {
                        "current_balance": new_balance,
                        "balance": new_balance  # Update both fields
                    }}
                )
        
        # Delete original transaction
        result = await db.supplier_transactions.delete_one({"id": transaction_id})
        
        if result.deleted_count > 0:
            message = "تم حذف المعاملة بنجاح"
            
            # If not reversing, just recalculate balance from remaining transactions
            if not reverse_transaction and supplier_id:
                supplier = await db.suppliers.find_one({"id": supplier_id})
                if supplier:
                    # Get all remaining transactions
                    transactions = await db.supplier_transactions.find({"supplier_id": supplier_id}).to_list(length=None)
                    
                    # Calculate new balance
                    new_balance = 0
                    for trans in transactions:
                        trans_type = trans.get("transaction_type")
                        amount = trans.get("amount", 0)
                        if trans_type == "purchase":
                            new_balance += amount
                        elif trans_type == "payment":
                            new_balance -= amount
                    
                    # Update supplier balance
                    await db.suppliers.update_one(
                        {"id": supplier_id},
                        {"$set": {
                            "current_balance": new_balance,
                            "balance": new_balance  # Update both fields
                        }}
                    )
                    message += " وتم إعادة حساب رصيد المورد"
            elif reverse_transaction:
                message += " وتم عكس تأثيرها على رصيد المورد"
            
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=404, detail="المعاملة غير موجودة")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# End of Master User - Delete Records APIs
# ============================================================================

# Include the router in the main app (MUST be after all API endpoints are defined)
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
