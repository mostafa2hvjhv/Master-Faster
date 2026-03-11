from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

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

# DB Models
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
    inner_diameter: float
    outer_diameter: float
    height: float
    pieces_count: int
    unit_code: str
    cost_per_mm: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MaterialPricing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    price_per_mm: float
    manufacturing_cost_client1: float
    manufacturing_cost_client2: float
    manufacturing_cost_client3: float
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
    seal_type: Optional[SealType] = None
    material_type: Optional[MaterialType] = None
    inner_diameter: Optional[float] = None
    outer_diameter: Optional[float] = None
    height: Optional[float] = None
    quantity: int
    unit_price: float
    total_price: float
    product_type: Optional[str] = "manufactured"
    product_name: Optional[str] = None
    supplier: Optional[str] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    local_product_details: Optional[Dict[str, Any]] = None
    material_used: Optional[str] = None
    material_details: Optional[Dict[str, Any]] = None
    selected_materials: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None

class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str
    customer_id: Optional[str] = None
    customer_name: str
    invoice_title: Optional[str] = None
    supervisor_name: Optional[str] = None
    items: List[InvoiceItem]
    subtotal: Optional[float] = None
    discount: Optional[float] = 0.0
    discount_type: Optional[str] = "amount"
    discount_value: Optional[float] = 0.0
    total_after_discount: Optional[float] = None
    total_amount: float
    display_amount: Optional[float] = None
    display_description: Optional[str] = None
    display_reference: Optional[str] = None
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
    supervisor_name: Optional[str] = None
    is_daily: bool = False
    work_date: Optional[str] = None
    invoices: List[Dict[str, Any]] = Field(default_factory=list)
    total_amount: float = 0.0
    total_items: int = 0
    status: str = "جديد"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    invoice_id: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)

class TreasuryTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str
    transaction_type: str
    amount: float
    description: str
    reference: Optional[str] = None
    related_transaction_id: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Supplier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    total_purchases: Optional[float] = 0.0
    total_paid: Optional[float] = 0.0
    balance: Optional[float] = 0.0
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
    transaction_type: str
    amount: float
    description: str
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    payment_method: Optional[str] = None
    reference_invoice_id: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class InventoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    available_pieces: int
    min_stock_level: Optional[int] = 2
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class InventoryTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inventory_item_id: str
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    transaction_type: str
    pieces_change: int
    remaining_pieces: int
    reason: str
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MainTreasuryPassword(BaseModel):
    id: str = Field(default_factory=lambda: "main_treasury_password")
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MainTreasuryTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_type: str
    amount: float
    description: str
    reference: Optional[str] = None
    balance_after: float
    performed_by: str
    date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DeletedInvoicesPassword(BaseModel):
    id: str = Field(default_factory=lambda: "deleted_invoices_password")
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InvoiceOperationsPassword(BaseModel):
    id: str = Field(default_factory=lambda: "invoice_operations_password")
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Request/Create Models
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
    unit_code: Optional[str] = None
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
    invoice_title: Optional[str] = None
    supervisor_name: Optional[str] = None
    items: List[InvoiceItem]
    payment_method: PaymentMethod
    discount_type: Optional[str] = "amount"
    discount_value: Optional[float] = 0.0
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

class TreasuryTransactionCreate(BaseModel):
    account_id: str
    transaction_type: str
    amount: float
    description: str
    reference: Optional[str] = None

class MainTreasuryTransactionCreate(BaseModel):
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
    available_pieces: int
    min_stock_level: Optional[int] = 2
    notes: Optional[str] = None

class InventoryTransactionCreate(BaseModel):
    inventory_item_id: Optional[str] = None
    material_type: MaterialType
    inner_diameter: float
    outer_diameter: float
    transaction_type: str
    pieces_change: int
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

class PasswordVerify(BaseModel):
    password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class EditTransactionRequest(BaseModel):
    description: Optional[str] = None
    reference: Optional[str] = None

class EditInvoiceDisplayRequest(BaseModel):
    display_amount: Optional[float] = None
    display_description: Optional[str] = None
    display_reference: Optional[str] = None

# Company mapping
COMPANY_MAP = {
    "Elsawy": "elsawy",
    "master": "elsawy",
    "Root": "elsawy",
    "Faster": "faster",
}
