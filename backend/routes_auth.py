from fastapi import APIRouter, HTTPException
from database import db, logger
from models import User, COMPANY_MAP
from typing import List

router = APIRouter()

# Auth endpoints
@router.post("/auth/login")
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
@router.post("/migrate-company-id")
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
@router.post("/users", response_model=User)
async def create_user(user: User):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="اسم المستخدم موجود بالفعل")
    
    await db.users.insert_one(user.dict())
    return user

@router.get("/users", response_model=List[User])
async def get_users():
    users = await db.users.find().to_list(1000)
    return [User(**user) for user in users]

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return User(**user)

@router.put("/users/{user_id}")
async def update_user(user_id: str, user: User):
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": user.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return {"message": "تم تحديث المستخدم بنجاح"}

@router.delete("/users/clear-all")
async def clear_all_users():
    # Don't delete default users, only custom ones
    result = await db.users.delete_many({"username": {"$nin": ["Elsawy", "Root"]}})
    return {"message": f"تم حذف {result.deleted_count} مستخدم", "deleted_count": result.deleted_count}

@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return {"message": "تم حذف المستخدم بنجاح"}

# Dashboard endpoints
@router.get("/dashboard/stats")
async def get_dashboard_stats(company_id: str = "elsawy"):
    from cache import cache_get, cache_set
    
    cache_key = f"dashboard:{company_id}"
    cached = cache_get(cache_key, ttl=30)
    if cached:
        return cached
    
    cf = {"company_id": company_id}
    
    # Use aggregation instead of fetching all documents
    invoice_stats = await db.invoices.aggregate([
        {"$match": cf},
        {"$group": {
            "_id": None,
            "total_sales": {"$sum": "$total_amount"},
            "total_unpaid": {"$sum": {
                "$cond": [{"$gt": ["$remaining_amount", 0]}, "$remaining_amount", 0]
            }},
            "count": {"$sum": 1}
        }}
    ]).to_list(1)
    
    expense_stats = await db.expenses.aggregate([
        {"$match": cf},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    customer_count = await db.customers.count_documents(cf)
    
    inv = invoice_stats[0] if invoice_stats else {"total_sales": 0, "total_unpaid": 0, "count": 0}
    exp = expense_stats[0] if expense_stats else {"total": 0}
    
    result = {
        "total_sales": inv.get("total_sales", 0),
        "total_expenses": exp.get("total", 0),
        "net_profit": inv.get("total_sales", 0) - exp.get("total", 0),
        "total_unpaid": inv.get("total_unpaid", 0),
        "invoice_count": inv.get("count", 0),
        "customer_count": customer_count
    }
    
    cache_set(cache_key, result)
    return result
