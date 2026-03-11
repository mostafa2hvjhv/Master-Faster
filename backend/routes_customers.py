from fastapi import APIRouter, HTTPException, Request
from database import db, logger
from models import Customer, CustomerCreate
from datetime import datetime, timezone
import uuid

router = APIRouter()

# Customer endpoints
@router.post("/customers", response_model=Customer)
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

@router.get("/customers", response_model=List[Customer])
async def get_customers(company_id: str = "elsawy"):
    customers = await db.customers.find({"company_id": company_id}).to_list(1000)
    return [Customer(**customer) for customer in customers]

@router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return Customer(**customer)

@router.delete("/customers/clear-all")
async def clear_all_customers(company_id: str = "elsawy"):
    result = await db.customers.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} عميل", "deleted_count": result.deleted_count}

@router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, company_id: str = "elsawy"):
    result = await db.customers.delete_one({"id": customer_id, "company_id": company_id})
    if result.deleted_count == 0:
        result = await db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return {"message": "تم حذف العميل بنجاح"}

@router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, request: Request, company_id: str = "elsawy"):
    """Update customer info (name, phone, address) - supports merging customers"""
    try:
        body = await request.json()
        customer = await db.customers.find_one({"id": customer_id, "company_id": company_id})
        if not customer:
            customer = await db.customers.find_one({"id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="العميل غير موجود")
        
        update_data = {}
        old_name = customer.get("name")
        
        if "name" in body and body["name"]:
            new_name = body["name"]
            # Check if another customer with this name exists
            existing = await db.customers.find_one({"name": new_name, "company_id": company_id, "id": {"$ne": customer_id}})
            
            if existing:
                # MERGE: Transfer all invoices and payments to existing customer, then delete current
                # Update invoices to use existing customer's name
                await db.invoices.update_many(
                    {"customer_name": old_name, "company_id": company_id},
                    {"$set": {"customer_name": new_name, "customer_id": existing["id"]}}
                )
                # Update payments
                await db.payments.update_many(
                    {"customer_name": old_name, "company_id": company_id},
                    {"$set": {"customer_name": new_name}}
                )
                # Delete the current customer (merged into existing)
                await db.customers.delete_one({"id": customer_id})
                
                return {
                    "message": f"تم دمج العميل '{old_name}' مع العميل '{new_name}' ✅",
                    "merged": True,
                    "target_customer_id": existing["id"]
                }
            else:
                update_data["name"] = new_name
        
        if "phone" in body:
            update_data["phone"] = body["phone"]
        if "address" in body:
            update_data["address"] = body["address"]
        
        if update_data:
            await db.customers.update_one({"id": customer_id}, {"$set": update_data})
            
            # If name changed, update name in all related invoices
            if "name" in update_data and update_data["name"] != old_name:
                await db.invoices.update_many(
                    {"customer_name": old_name, "company_id": company_id},
                    {"$set": {"customer_name": update_data["name"]}}
                )
                await db.payments.update_many(
                    {"customer_name": old_name, "company_id": company_id},
                    {"$set": {"customer_name": update_data["name"]}}
                )
        
        updated = await db.customers.find_one({"id": customer_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers-balances")
async def get_all_customers_balances(company_id: str = "elsawy"):
    """Get all customers with their debt balances in one query - OPTIMIZED"""
    try:
        # Use aggregation to calculate balances for all customers at once
        pipeline = [
            {"$match": {"company_id": company_id, "remaining_amount": {"$gt": 0}}},
            {"$group": {
                "_id": "$customer_name",
                "total_debt": {"$sum": "$remaining_amount"},
                "unpaid_invoices_count": {"$sum": 1}
            }}
        ]
        
        results = await db.invoices.aggregate(pipeline).to_list(None)
        
        # Convert to dictionary keyed by customer name
        balances = {}
        for r in results:
            balances[r["_id"]] = {
                "total_debt": r["total_debt"],
                "unpaid_invoices_count": r["unpaid_invoices_count"]
            }
        
        return balances
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers/{customer_id}/deferred-invoices")
async def get_customer_deferred_invoices(customer_id: str, company_id: str = "elsawy"):
    """Get deferred invoices for a specific customer - OPTIMIZED"""
    try:
        customer = await db.customers.find_one({"id": customer_id, "company_id": company_id}, {"_id": 0})
        if not customer:
            customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
        if not customer:
            raise HTTPException(status_code=404, detail="العميل غير موجود")
        
        # Get only deferred invoices with remaining amount
        invoices = await db.invoices.find({
            "customer_name": customer["name"],
            "company_id": company_id,
            "payment_method": "آجل",
            "remaining_amount": {"$gt": 0}
        }, {"_id": 0}).sort("date", 1).to_list(None)
        
        return invoices
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers/{customer_id}/balance")
async def get_customer_balance(customer_id: str, company_id: str = "elsawy"):
    """Get customer debt balance from unpaid invoices"""
    try:
        customer = await db.customers.find_one({"id": customer_id, "company_id": company_id})
        if not customer:
            customer = await db.customers.find_one({"id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="العميل غير موجود")
        
        # Find all invoices for this customer with remaining amounts
        invoices = await db.invoices.find({
            "customer_name": customer["name"],
            "company_id": company_id
        }).to_list(None)
        
        total_debt = 0
        unpaid_invoices = []
        for inv in invoices:
            remaining = inv.get("remaining_amount", 0)
            if remaining > 0:
                total_debt += remaining
                unpaid_invoices.append({
                    "invoice_number": inv.get("invoice_number"),
                    "date": inv.get("date"),
                    "total_amount": inv.get("total_amount", 0),
                    "paid_amount": inv.get("paid_amount", 0),
                    "remaining_amount": remaining
                })
        
        return {
            "customer_name": customer["name"],
            "total_debt": total_debt,
            "total_invoices": len(invoices),
            "unpaid_invoices_count": len(unpaid_invoices),
            "unpaid_invoices": unpaid_invoices
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Customer Statement API (كشف الحساب)
@router.get("/customer-statement/{customer_id}")
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
        invoice_query = {"$or": [{"customer_id": customer_id}, {"customer_name": customer.get("name")}]}
        if date_filter:
            invoice_query["date"] = date_filter
        
        invoices = await db.invoices.find(invoice_query).sort("date", 1).to_list(length=None)
        
        # Get all payments for this customer's invoices
        invoice_ids = [inv.get("id") for inv in invoices]
        payments = []
        if invoice_ids:
            payment_query = {"invoice_id": {"$in": invoice_ids}}
            if date_filter:
                payment_query["date"] = date_filter
            payments = await db.payments.find(payment_query).sort("date", 1).to_list(length=None)
        
        # Get supplier transactions if customer is also a supplier
        supplier_transactions = []
        if supplier:
            supplier_query = {"supplier_id": supplier.get("id")}
            if date_filter:
                supplier_query["date"] = date_filter
            supplier_transactions = await db.supplier_transactions.find(supplier_query).sort("date", 1).to_list(length=None)
        
        # Build transactions list
        transactions = []
        running_balance = 0
        
        # Add invoices (دائن - Credit)
        for invoice in invoices:
            transaction_date = invoice.get("date", invoice.get("created_at", ""))
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
            transaction_date = payment.get("date", payment.get("payment_date", ""))
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
            transaction_date = trans.get("date", trans.get("transaction_date", ""))
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
@router.post("/customers/{customer_id}/settle-account")
async def settle_customer_account(
    customer_id: str,
    amount_paid: float,
    payment_method: str,
    username: str = None,
    company_id: str = "elsawy"
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
            "remaining_amount": {"$gt": 0},
            "company_id": company_id
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
                    "remaining_amount": new_remaining_amount,
                    "status": "مدفوعة" if new_remaining_amount == 0 else "مدفوعة جزئياً",
                    "payment_method_used": payment_method if new_remaining_amount == 0 else None,
                    "status_description": f"تم السداد بواسطة {payment_method}" if new_remaining_amount == 0 else "دفع جزئي"
                }}
            )
            
            # Create payment record
            payment_id = str(uuid.uuid4())
            payment_record = {
                "id": payment_id,
                "invoice_id": invoice["id"],
                "invoice_number": invoice.get("invoice_number"),
                "customer_name": customer["name"],
                "amount": payment_for_this_invoice,
                "payment_method": payment_method,
                "date": datetime.now(timezone.utc).isoformat(),
                "settled_by": username or "unknown",
                "company_id": company_id
            }
            await db.payments.insert_one(payment_record)
            payment_records.append(payment_record)
            
            # Create treasury transaction for this payment (income to payment account)
            account_id = payment_method_mapping.get(payment_method, "cash")
            treasury_transaction = TreasuryTransaction(
                account_id=account_id,
                transaction_type="income",
                amount=payment_for_this_invoice,
                description=f"تصفية حساب - فاتورة {invoice.get('invoice_number')} - {customer['name']}",
                reference=f"settlement_{payment_id}"
            )
            treasury_dict = treasury_transaction.dict()
            treasury_dict["company_id"] = company_id
            await db.treasury_transactions.insert_one(treasury_dict)
            
            # Also create a deduction from deferred account (matching create_payment behavior)
            deferred_transaction = TreasuryTransaction(
                account_id="deferred",
                transaction_type="expense",
                amount=payment_for_this_invoice,
                description=f"تسديد آجل - تصفية حساب فاتورة {invoice.get('invoice_number')} - {customer['name']}",
                reference=f"settlement_{payment_id}_deferred"
            )
            deferred_dict = deferred_transaction.dict()
            deferred_dict["company_id"] = company_id
            await db.treasury_transactions.insert_one(deferred_dict)
            
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

@router.post("/customers/{customer_id}/reconcile-with-supplier")
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
