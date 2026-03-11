from fastapi import APIRouter, HTTPException
from database import db, logger
from models import (
    Expense, ExpenseCreate, WorkOrder, TreasuryTransaction, TreasuryTransactionCreate,
    TransferRequest, Supplier, SupplierCreate, LocalProduct, LocalProductCreate,
    SupplierTransaction, SupplierTransactionCreate,
    MainTreasuryTransaction, MainTreasuryTransactionCreate,
    MainTreasuryPassword, PasswordVerify, PasswordChange,
    EditTransactionRequest
)
from typing import List
from datetime import datetime, date, timezone
import uuid

router = APIRouter()


# Expense endpoints
@router.post("/expenses", response_model=Expense)
async def create_expense(expense: ExpenseCreate, company_id: str = "elsawy"):
    expense_obj = Expense(**expense.dict())
    obj = expense_obj.dict()
    obj["company_id"] = company_id
    await db.expenses.insert_one(obj)
    return expense_obj

@router.get("/expenses", response_model=List[Expense])
async def get_expenses(company_id: str = "elsawy"):
    expenses = await db.expenses.find({"company_id": company_id}).sort("date", -1).to_list(1000)
    return [Expense(**expense) for expense in expenses]

@router.delete("/expenses/clear-all")
async def clear_all_expenses(company_id: str = "elsawy"):
    result = await db.expenses.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} مصروف", "deleted_count": result.deleted_count}

@router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    result = await db.expenses.delete_one({"id": expense_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="المصروف غير موجود")
    return {"message": "تم حذف المصروف بنجاح"}

# Revenue reports
@router.get("/reports/revenue")
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
@router.post("/work-orders", response_model=WorkOrder)
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

@router.post("/work-orders/multiple")
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

@router.get("/work-orders/daily/{work_date}")
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

@router.put("/work-orders/daily/{work_order_id}/add-invoice")
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

@router.get("/work-orders")
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

@router.delete("/work-orders/clear-all")
async def clear_all_work_orders(company_id: str = "elsawy"):
    result = await db.work_orders.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} أمر شغل", "deleted_count": result.deleted_count}

@router.delete("/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: str):
    result = await db.work_orders.delete_one({"id": work_order_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="أمر الشغل غير موجود")
    return {"message": "تم حذف أمر الشغل بنجاح"}

@router.put("/work-orders/{work_order_id}/add-invoice")
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
@router.get("/treasury/transactions")
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

@router.post("/treasury/transactions")
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

@router.post("/treasury/transfer")
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

@router.get("/treasury/balances")
async def get_account_balances(company_id: str = "elsawy"):
    """Get current balances for all accounts - OPTIMIZED with aggregation"""
    try:
        # Initialize balances
        account_balances = {
            'cash': 0,
            'vodafone_elsawy': 0,
            'vodafone_wael': 0,
            'deferred': 0,
            'instapay': 0,
            'yad_elsawy': 0,
            'main_treasury': 0
        }
        
        # 1. Calculate deferred balance from invoices (sum of total_amount for آجل invoices - original logic)
        deferred_pipeline = [
            {"$match": {"company_id": company_id, "payment_method": "آجل"}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]
        deferred_result = await db.invoices.aggregate(deferred_pipeline).to_list(1)
        if deferred_result:
            account_balances['deferred'] = deferred_result[0].get('total', 0)
        
        # 2. Calculate expenses total
        expenses_pipeline = [
            {"$match": {"company_id": company_id}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        expenses_result = await db.expenses.aggregate(expenses_pipeline).to_list(1)
        if expenses_result:
            account_balances['cash'] -= expenses_result[0].get('total', 0)
        
        # 3. Calculate treasury transactions balances
        transactions_pipeline = [
            {"$match": {"company_id": company_id}},
            {"$group": {
                "_id": {
                    "account_id": "$account_id",
                    "transaction_type": "$transaction_type"
                },
                "total": {"$sum": "$amount"}
            }}
        ]
        transactions_result = await db.treasury_transactions.aggregate(transactions_pipeline).to_list(None)
        
        for item in transactions_result:
            account_id = item['_id']['account_id']
            transaction_type = item['_id']['transaction_type']
            amount = item['total']
            
            if account_id in account_balances:
                if transaction_type in ['income', 'transfer_in']:
                    account_balances[account_id] += amount
                elif transaction_type in ['expense', 'transfer_out']:
                    account_balances[account_id] -= amount
        
        return account_balances
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Daily Sales Report API
@router.get("/daily-sales-report")
async def get_daily_sales_report(report_date: str = None, company_id: str = "elsawy"):
    """
    كشف مبيعات يومي
    - مبيعات اليوم: إجمالي كل فواتير اليوم بما فيها الآجل
    - نقدي: فواتير نقدية + آجل محصل نقدي في نفس اليوم
    - فودافون: فواتير فودافون + آجل محصل فودافون في نفس اليوم
    - انستاباي: فواتير انستا + آجل محصل انستا في نفس اليوم
    - آجل: فواتير آجل لم يتم دفعها في نفس اليوم
    - تحصيل من الآجل: تحصيل فواتير آجل قديمة فقط
    - صافي الدخل اليومي: نقدي + فودافون + انستا + تحصيل من الآجل
    """
    try:
        from datetime import datetime, timedelta
        
        if report_date:
            try:
                target_date = datetime.strptime(report_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="تنسيق التاريخ غير صحيح. استخدم YYYY-MM-DD")
        else:
            target_date = datetime.now()
        
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Fetch data
        invoices = await db.invoices.find({
            "date": {"$gte": start_of_day, "$lte": end_of_day},
            "company_id": company_id
        }, {"_id": 0}).to_list(1000)
        
        payments = await db.payments.find({
            "date": {"$gte": start_of_day, "$lte": end_of_day},
            "company_id": company_id
        }, {"_id": 0}).to_list(1000)
        
        expenses = await db.expenses.find({
            "date": {"$gte": start_of_day, "$lte": end_of_day},
            "company_id": company_id
        }, {"_id": 0}).to_list(1000)
        
        treasury_transactions = await db.treasury_transactions.find({
            "date": {"$gte": start_of_day, "$lte": end_of_day},
            "company_id": company_id
        }, {"_id": 0}).to_list(1000)
        
        # === Sales calculation ===
        total_sales = 0
        cash_sales = 0
        vodafone_sales = 0
        instapay_sales = 0
        deferred_sales = 0
        today_deferred_invoice_ids = set()
        
        for invoice in invoices:
            inv_total = invoice.get("total_after_discount") or invoice.get("total_amount", 0)
            method = invoice.get("payment_method", "")
            remaining = invoice.get("remaining_amount", 0)
            inv_id = invoice.get("id", "")
            
            total_sales += inv_total
            
            if method == "آجل":
                today_deferred_invoice_ids.add(inv_id)
                if remaining == 0:
                    # Fully paid same day - classify by payment method used
                    inv_payments = [p for p in payments if p.get("invoice_id") == inv_id]
                    if inv_payments:
                        for p in inv_payments:
                            pm = p.get("payment_method", "نقدي")
                            pa = p.get("amount", 0)
                            if pm in ["فودافون", "vodafone"]:
                                vodafone_sales += pa
                            elif pm in ["انستاباي", "instapay", "انستا"]:
                                instapay_sales += pa
                            else:
                                cash_sales += pa
                    else:
                        cash_sales += inv_total
                elif remaining < inv_total:
                    # Partially paid same day
                    inv_payments = [p for p in payments if p.get("invoice_id") == inv_id]
                    if inv_payments:
                        for p in inv_payments:
                            pm = p.get("payment_method", "نقدي")
                            pa = p.get("amount", 0)
                            if pm in ["فودافون", "vodafone"]:
                                vodafone_sales += pa
                            elif pm in ["انستاباي", "instapay", "انستا"]:
                                instapay_sales += pa
                            else:
                                cash_sales += pa
                    else:
                        cash_sales += (inv_total - remaining)
                    deferred_sales += remaining
                else:
                    deferred_sales += inv_total
            elif method in ["فودافون", "vodafone"]:
                vodafone_sales += inv_total
            elif method in ["انستاباي", "instapay", "انستا"]:
                instapay_sales += inv_total
            else:
                cash_sales += inv_total
        
        # === Deferred collections (OLD invoices paid today only) ===
        deferred_collections = 0
        deferred_collections_cash = 0
        deferred_collections_vodafone = 0
        deferred_collections_instapay = 0
        
        for payment in payments:
            inv_id = payment.get("invoice_id")
            pa = payment.get("amount", 0)
            pm = payment.get("payment_method", "نقدي")
            
            # Skip today's invoices (already counted)
            if inv_id in today_deferred_invoice_ids:
                continue
            
            invoice = await db.invoices.find_one({"id": inv_id}, {"_id": 0})
            if invoice and invoice.get("payment_method") == "آجل":
                inv_date = invoice.get("date")
                is_old = True
                if isinstance(inv_date, datetime):
                    is_old = inv_date.replace(hour=0, minute=0, second=0, microsecond=0) < start_of_day
                
                if is_old:
                    deferred_collections += pa
                    if pm in ["فودافون", "vodafone"]:
                        deferred_collections_vodafone += pa
                    elif pm in ["انستاباي", "instapay", "انستا"]:
                        deferred_collections_instapay += pa
                    else:
                        deferred_collections_cash += pa
        
        # === Expenses ===
        total_expenses = sum(e.get("amount", 0) for e in expenses)
        
        # === Net daily income = all collected today ===
        net_daily_income = cash_sales + vodafone_sales + instapay_sales + deferred_collections
        
        # === Treasury account changes ===
        daily_account_changes = {"cash": 0, "vodafone_elsawy": 0, "vodafone_wael": 0, "instapay": 0, "yad_elsawy": 0}
        account_labels = {"cash": "نقدي", "vodafone_elsawy": "فودافون 010", "vodafone_wael": "كاش 0100", "instapay": "انستاباي", "yad_elsawy": "يد الصاوي"}
        
        for t in treasury_transactions:
            aid = t.get("account_id", "")
            amt = t.get("amount", 0)
            tt = t.get("transaction_type", "")
            if aid in daily_account_changes:
                if tt in ["income", "transfer_in"]:
                    daily_account_changes[aid] += amt
                elif tt in ["expense", "transfer_out"]:
                    daily_account_changes[aid] -= amt
        
        formatted_account_changes = [
            {"account_id": k, "label": account_labels.get(k, k), "daily_change": v}
            for k, v in daily_account_changes.items()
        ]
        
        return {
            "report_date": target_date.strftime("%Y-%m-%d"),
            "report_date_formatted": target_date.strftime("%d/%m/%Y"),
            "summary": {
                "total_sales": total_sales,
                "cash_sales": cash_sales,
                "vodafone_sales": vodafone_sales,
                "instapay_sales": instapay_sales,
                "deferred_sales": deferred_sales,
                "deferred_collections": deferred_collections,
                "deferred_collections_cash": deferred_collections_cash,
                "deferred_collections_vodafone": deferred_collections_vodafone,
                "deferred_collections_instapay": deferred_collections_instapay,
                "total_expenses": total_expenses,
                "net_daily_income": net_daily_income
            },
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




@router.get("/suppliers", response_model=List[Supplier])
async def get_suppliers(company_id: str = "elsawy"):
    """Get all suppliers"""
    try:
        suppliers = await db.suppliers.find({"company_id": company_id}).to_list(None)
        return suppliers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suppliers", response_model=Supplier)
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

@router.put("/suppliers/{supplier_id}")
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

@router.delete("/suppliers/{supplier_id}")
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
@router.get("/local-products", response_model=List[LocalProduct])
async def get_local_products(company_id: str = "elsawy"):
    """Get all local products"""
    try:
        products = await db.local_products.find({"company_id": company_id}).to_list(None)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/local-products/supplier/{supplier_id}", response_model=List[LocalProduct])
async def get_products_by_supplier(supplier_id: str):
    """Get products by supplier"""
    try:
        products = await db.local_products.find({"supplier_id": supplier_id}).to_list(None)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/local-products", response_model=LocalProduct)
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

@router.put("/local-products/{product_id}")
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

@router.delete("/local-products/{product_id}")
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
@router.get("/supplier-transactions", response_model=List[SupplierTransaction])
async def get_supplier_transactions(company_id: str = "elsawy"):
    """Get all supplier transactions"""
    try:
        transactions = await db.supplier_transactions.find({"company_id": company_id}).sort("date", -1).to_list(None)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supplier-transactions/{supplier_id}", response_model=List[SupplierTransaction])
async def get_supplier_transactions_by_id(supplier_id: str):
    """Get transactions for a specific supplier"""
    try:
        transactions = await db.supplier_transactions.find({"supplier_id": supplier_id}).sort("date", -1).to_list(None)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/supplier-transactions", response_model=SupplierTransaction)
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

@router.post("/supplier-payment")
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
@router.post("/treasury/reset")
async def reset_treasury(username: str, company_id: str = "elsawy"):
    """Reset all treasury data - Only for Elsawy user"""
    try:
        # Security check - only Elsawy can perform this operation
        if username not in ["Elsawy", "Faster"]:
            raise HTTPException(status_code=403, detail="غير مصرح لك بتنفيذ هذه العملية")
        
        # Get count of records before deletion for logging
        treasury_count = await db.treasury_transactions.count_documents({"company_id": company_id})
        
        # Delete only this company's treasury transactions
        treasury_result = await db.treasury_transactions.delete_many({"company_id": company_id})
        
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

@router.post("/main-treasury/verify-password")
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

@router.post("/main-treasury/change-password")
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

@router.get("/main-treasury/balance")
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

@router.get("/main-treasury/transactions")
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

@router.post("/main-treasury/deposit")
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

@router.post("/main-treasury/withdrawal")
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

@router.post("/main-treasury/transfer-from-yad")
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
@router.delete("/treasury/transactions/{transaction_id}")
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

@router.put("/treasury/transactions/{transaction_id}/edit-record")
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
@router.delete("/suppliers/transactions/{transaction_id}")
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

