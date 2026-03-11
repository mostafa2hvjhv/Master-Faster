from fastapi import APIRouter, HTTPException
from database import db, logger
from models import (
    Invoice, InvoiceCreate, InvoiceItem, InvoiceStatus, Payment, PaymentCreate,
    TreasuryTransaction, SupplierTransaction, WorkOrder,
    InvoiceOperationsPassword, EditInvoiceDisplayRequest
)
from typing import List
from datetime import datetime, date, timezone
import uuid

router = APIRouter()


# Invoice endpoints
@router.post("/invoices", response_model=Invoice)
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
                            logger.info(f"✅ تم خصم {material_consumption} مم من الخامة {raw_material.get('unit_code', 'غير محدد')} لإنتاج {seals_to_produce} سيل - المتبقي: {remaining_height} مم")
                        else:
                            logger.info(f"❌ خطأ: لا يوجد ارتفاع كافٍ في الخامة {raw_material.get('unit_code', 'غير محدد')} - مطلوب: {material_consumption} مم، متوفر: {current_height} مم")
                    else:
                        logger.info(f"❌ خطأ: لم يتم العثور على الخامة {material_info.get('unit_code', 'غير محدد')}")
                
                material_deducted = True
                logger.info(f"🎉 تم خصم المواد من {len(item.selected_materials)} خامة مختلفة")
                
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
                                logger.info(f"⚠️ تم خصم {material_consumption} مم من الخامة {raw_material.get('unit_code', 'غير محدد')} لإنتاج {actual_seals_to_produce} سيل من أصل {total_seals_requested} سيل - المتبقي: {remaining_height} مم")
                                logger.info(f"📌 ملاحظة: يحتاج المستخدم لاختيار خامة أخرى لإنتاج الـ {total_seals_requested - actual_seals_to_produce} سيل المتبقية")
                            else:
                                logger.info(f"✅ تم خصم {material_consumption} مم من الخامة {raw_material.get('unit_code', 'غير محدد')} لإنتاج جميع الـ {total_seals_requested} سيل - المتبقي: {remaining_height} مم")
                        else:
                            if max_possible_seals <= 0:
                                logger.info(f"❌ خطأ: الخامة {raw_material.get('unit_code', 'غير محدد')} لا تكفي لإنتاج أي سيل - الارتفاع: {material_height} مم، المطلوب: {seal_consumption_per_piece} مم للسيل الواحد")
                            else:
                                logger.info(f"❌ خطأ: لا يوجد ارتفاع كافٍ في الخامة {raw_material.get('unit_code', 'غير محدد')} - مطلوب: {material_consumption} مم، متوفر: {material_height} مم")
                    else:
                        logger.info(f"❌ خطأ: لم يتم العثور على الخامة المحددة - {material_details.get('material_type')} {material_details.get('inner_diameter')}×{material_details.get('outer_diameter')} كود: {material_details.get('unit_code', 'غير محدد')}")
            
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
                        logger.info(f"⚠️ تم خصم {material_consumption} مم من ارتفاع الخامة {item.material_used} (بحث بكود الوحدة فقط - أقل دقة)")
                    else:
                        logger.info(f"❌ تحذير: لا يوجد ارتفاع كافٍ في الخامة {item.material_used} - مطلوب: {material_consumption} مم، متوفر: {current_height} مم")
                else:
                    logger.info(f"❌ تحذير: الخامة {item.material_used} غير موجودة في المواد الخام")
    
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
                
                logger.info(f"🔍 Debug - Item data: {item}")
                logger.info(f"🔍 Debug - Selected materials: {item.get('selected_materials')}")
                
                if item.get("selected_materials"):
                    logger.info(f"✅ Found selected_materials: {len(item.get('selected_materials'))} materials")
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
                    logger.info(f"✅ Multi-material unit_code_display: {unit_code_display}")
                    
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
        logger.info(f"Error adding invoice to daily work order: {str(e)}")
    
    return invoice_obj

@router.get("/invoices-summary")
async def get_invoices_summary(company_id: str = "elsawy", limit: int = 100, skip: int = 0):
    """Get invoices summary without items details - OPTIMIZED for list view"""
    try:
        # Only return essential fields for list view
        projection = {
            "_id": 0,
            "id": 1,
            "invoice_number": 1,
            "customer_name": 1,
            "invoice_title": 1,
            "supervisor_name": 1,
            "total_amount": 1,
            "paid_amount": 1,
            "remaining_amount": 1,
            "payment_method": 1,
            "status": 1,
            "status_description": 1,
            "payment_method_used": 1,
            "date": 1,
            "discount": 1
        }
        
        invoices = await db.invoices.find(
            {"company_id": company_id}, 
            projection
        ).sort("date", -1).skip(skip).limit(limit).to_list(limit)
        
        # Get total count for pagination
        total_count = await db.invoices.count_documents({"company_id": company_id})
        
        return {
            "invoices": invoices,
            "total": total_count,
            "limit": limit,
            "skip": skip
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoices", response_model=List[Invoice])
async def get_invoices(company_id: str = "elsawy"):
    invoices = await db.invoices.find({"company_id": company_id}).sort("date", -1).to_list(1000)
    return [Invoice(**invoice) for invoice in invoices]

@router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
    return Invoice(**invoice)

@router.delete("/invoices/clear-all")
async def clear_all_invoices(company_id: str = "elsawy"):
    result = await db.invoices.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} فاتورة", "deleted_count": result.deleted_count}

@router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str):
    result = await db.invoices.delete_one({"id": invoice_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")
    return {"message": "تم حذف الفاتورة بنجاح"}

@router.put("/invoices/{invoice_id}/status")
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

@router.put("/invoices/{invoice_id}")
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
            # Also update total_amount if items changed
            discount_amount = existing_invoice.get('discount', 0)
            total_after_discount = subtotal - discount_amount
            invoice_update['total_after_discount'] = total_after_discount
            invoice_update['total_amount'] = total_after_discount
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
        
        # CRITICAL: Update remaining_amount when total changes
        # remaining_amount = total_amount - paid_amount
        if 'total_amount' in invoice_update:
            paid_amount = existing_invoice.get('paid_amount', 0)
            new_total = invoice_update['total_amount']
            new_remaining = max(0, new_total - paid_amount)
            invoice_update['remaining_amount'] = new_remaining
            
            # Update status based on remaining amount
            if new_remaining == 0:
                invoice_update['status'] = 'مدفوعة'
            elif paid_amount > 0:
                invoice_update['status'] = 'مدفوعة جزئياً'
            else:
                invoice_update['status'] = 'غير مدفوعة'
        
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
@router.get("/invoices/{invoice_id}/history")
async def get_invoice_edit_history(invoice_id: str):
    """Get edit history for an invoice"""
    history = await db.invoice_edit_history.find(
        {"invoice_id": invoice_id}
    ).sort("edited_at", -1).to_list(length=None)
    
    for entry in history:
        if '_id' in entry:
            del entry['_id']
    
    return history

@router.post("/invoices/{invoice_id}/revert/{history_id}")
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
@router.post("/payments", response_model=Payment)
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

@router.get("/payments", response_model=List[Payment])
async def get_payments(company_id: str = "elsawy"):
    payments = await db.payments.find({"company_id": company_id}).sort("date", -1).to_list(1000)
    return [Payment(**payment) for payment in payments]

@router.delete("/payments/clear-all")
async def clear_all_payments(company_id: str = "elsawy"):
    result = await db.payments.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} دفعة", "deleted_count": result.deleted_count}

@router.delete("/payments/{payment_id}")
async def delete_payment(payment_id: str):
    result = await db.payments.delete_one({"id": payment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="الدفعة غير موجودة")
    return {"message": "تم حذف الدفعة بنجاح"}
@router.put("/invoices/{invoice_id}/change-payment-method")
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
@router.delete("/invoices/{invoice_id}/cancel")
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
                            
                            logger.info(f"✅ تم استرداد {material_to_restore} مم للخامة {raw_material.get('unit_code')}")
                
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
                        
                        logger.info(f"✅ تم استرداد {material_to_restore} مم للخامة {raw_material.get('unit_code')}")
        
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
@router.get("/deleted-invoices")
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

@router.post("/deleted-invoices/{invoice_id}/restore")
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

@router.delete("/deleted-invoices/{invoice_id}")
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

@router.delete("/deleted-invoices/clear-all/confirm")
async def clear_all_deleted_invoices(company_id: str = "elsawy"):
    """Clear all deleted invoices"""
    try:
        result = await db.deleted_invoices.delete_many({"company_id": company_id})
        return {"message": f"تم حذف {result.deleted_count} فاتورة نهائياً", "deleted_count": result.deleted_count}
    except Exception as e:
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

@router.post("/invoices/bulk-delete-by-date")
async def bulk_delete_invoices_by_date(date: str, password: str, username: str, company_id: str = "elsawy"):
    """Delete all invoices of a specific date - filtered by company_id"""
    try:
        # Security checks
        if username not in ["Elsawy", "Faster"]:
            raise HTTPException(status_code=403, detail="غير مصرح لك بتنفيذ هذه العملية")
        
        if password != "200200":
            raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")
        
        # Parse date (expecting format: YYYY-MM-DD)
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except:
            raise HTTPException(status_code=400, detail="صيغة التاريخ غير صحيحة. استخدم: YYYY-MM-DD")
        
        # Find all invoices for this date - filtered by company_id
        all_invoices = await db.invoices.find({"company_id": company_id}).to_list(length=None)
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

@router.post("/invoices/bulk-delete-last")
async def bulk_delete_last_invoices(count: int, password: str, username: str, company_id: str = "elsawy"):
    """Delete last N invoices - filtered by company_id"""
    try:
        # Security checks
        if username not in ["Elsawy", "Faster"]:
            raise HTTPException(status_code=403, detail="غير مصرح لك بتنفيذ هذه العملية")
        
        if password != "200200":
            raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")
        
        if count < 1 or count > 10:
            raise HTTPException(status_code=400, detail="يمكن حذف من 1 إلى 10 فواتير فقط")
        
        # Get last N invoices - filtered by company_id
        all_invoices = await db.invoices.find({"company_id": company_id}).sort("date", -1).limit(count).to_list(length=count)
        
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
@router.put("/invoices/{invoice_id}/edit-display")
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
