from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from database import db, logger
from models import (
    RawMaterial, RawMaterialCreate, FinishedProduct, FinishedProductCreate,
    MaterialPricing, CompatibilityCheck, InventoryItem, InventoryItemCreate,
    InventoryTransaction, InventoryTransactionCreate, MaterialType, SealType
)
from typing import List
from datetime import datetime, timezone
import uuid
import pandas as pd
import io

router = APIRouter()


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

@router.post("/raw-materials", response_model=RawMaterial)
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

@router.get("/raw-materials", response_model=List[RawMaterial])
async def get_raw_materials(company_id: str = "elsawy"):
    """Get all raw materials sorted by material type priority then size"""
    # Define material type priority order: BUR-NBR-BT-BOOM-VT
    material_priority = {'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5}
    
    # Get all materials first, exclude _id
    materials = await db.raw_materials.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    
    # Sort by material type priority, then by diameter
    sorted_materials = sorted(materials, key=lambda x: (
        material_priority.get(x.get('material_type', ''), 6),  # Material priority
        x.get('inner_diameter', 0),  # Then inner diameter
        x.get('outer_diameter', 0)   # Then outer diameter
    ))
    
    return sorted_materials

@router.put("/raw-materials/{material_id}")
async def update_raw_material(material_id: str, material: RawMaterialCreate):
    result = await db.raw_materials.update_one(
        {"id": material_id},
        {"$set": material.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="المادة غير موجودة")
    return {"message": "تم تحديث المادة بنجاح"}

@router.delete("/raw-materials/clear-all")
async def clear_all_raw_materials(company_id: str = "elsawy"):
    result = await db.raw_materials.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} مادة خام", "deleted_count": result.deleted_count}

@router.delete("/raw-materials/{material_id}")
async def delete_raw_material(material_id: str):
    result = await db.raw_materials.delete_one({"id": material_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="المادة غير موجودة")
    return {"message": "تم حذف المادة بنجاح"}

# Finished products endpoints
@router.post("/finished-products", response_model=FinishedProduct)
async def create_finished_product(product: FinishedProductCreate, company_id: str = "elsawy"):
    product_dict = product.dict()
    product_obj = FinishedProduct(**product_dict)
    obj = product_obj.dict()
    obj["company_id"] = company_id
    await db.finished_products.insert_one(obj)
    return product_obj

@router.get("/finished-products", response_model=List[FinishedProduct])
async def get_finished_products(company_id: str = "elsawy"):
    products = await db.finished_products.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    return products

@router.delete("/finished-products/clear-all")
async def clear_all_finished_products(company_id: str = "elsawy"):
    result = await db.finished_products.delete_many({"company_id": company_id})
    return {"message": f"تم حذف {result.deleted_count} منتج جاهز", "deleted_count": result.deleted_count}

@router.delete("/finished-products/{product_id}")
async def delete_finished_product(product_id: str):
    result = await db.finished_products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    return {"message": "تم حذف المنتج بنجاح"}

@router.put("/finished-products/{product_id}")
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
@router.post("/compatibility-check")
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
@router.get("/inventory", response_model=List[InventoryItem])
async def get_inventory(company_id: str = "elsawy"):
    """Get all inventory items sorted by material type priority then size"""
    try:
        # Define material type priority order: BUR-NBR-BT-BOOM-VT
        material_priority = {'BUR': 1, 'NBR': 2, 'BT': 3, 'BOOM': 4, 'VT': 5}
        
        # Get all items first, exclude _id
        items = await db.inventory_items.find({"company_id": company_id}, {"_id": 0}).to_list(None)
        
        # Sort by material type priority, then by diameter
        sorted_items = sorted(items, key=lambda x: (
            material_priority.get(x.get('material_type', ''), 6),  # Material priority
            x.get('inner_diameter', 0),  # Then inner diameter
            x.get('outer_diameter', 0)   # Then outer diameter
        ))
        
        return sorted_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/low-stock")
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
            },
            {
                "$project": {
                    "_id": 0
                }
            }
        ]
        items = await db.inventory_items.aggregate(pipeline).to_list(None)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/{item_id}", response_model=InventoryItem)
async def get_inventory_item(item_id: str):
    """Get specific inventory item"""
    try:
        item = await db.inventory_items.find_one({"id": item_id})
        if not item:
            raise HTTPException(status_code=404, detail="العنصر غير موجود في الجرد")
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory", response_model=InventoryItem)
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

@router.put("/inventory/{item_id}")
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

@router.delete("/inventory/{item_id}")
async def delete_inventory_item(item_id: str):
    """Delete inventory item"""
    try:
        result = await db.inventory_items.delete_one({"id": item_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="العنصر غير موجود في الجرد")
        return {"message": "تم حذف عنصر الجرد بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory-transactions", response_model=List[InventoryTransaction])
async def get_inventory_transactions():
    """Get all inventory transactions"""
    try:
        transactions = await db.inventory_transactions.find({}, {"_id": 0}).sort("date", -1).to_list(None)
        
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

@router.get("/inventory-transactions/{item_id}", response_model=List[InventoryTransaction])
async def get_inventory_transactions_by_item(item_id: str):
    """Get transactions for a specific inventory item"""
    try:
        transactions = await db.inventory_transactions.find(
            {"inventory_item_id": item_id}, {"_id": 0}
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
@router.get("/material-pricing")
async def get_material_pricing():
    """Get all material pricing"""
    try:
        pricings = await db.material_pricing.find({}).sort("created_at", -1).to_list(None)
        for p in pricings:
            p.pop("_id", None)
        return pricings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/material-pricing", response_model=MaterialPricing)
async def create_material_pricing(pricing: MaterialPricing):
    """Create new material pricing"""
    try:
        pricing_dict = pricing.dict()
        await db.material_pricing.insert_one(pricing_dict)
        return pricing
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/material-pricing/{pricing_id}")
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

@router.delete("/material-pricing/{pricing_id}")
async def delete_material_pricing(pricing_id: str):
    """Delete material pricing"""
    try:
        result = await db.material_pricing.delete_one({"id": pricing_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="التسعيرة غير موجودة")
        return {"message": "تم حذف التسعيرة بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/excel/export/material-pricing")
async def export_material_pricing_excel(company_id: str = "elsawy"):
    """Export material pricing to Excel file"""
    try:
        items = await db.material_pricing.find({"$or": [{"company_id": company_id}, {"company_id": {"$exists": False}}]}).to_list(None)
        
        if not items:
            raise HTTPException(status_code=404, detail="لا توجد تسعيرات للتصدير")
        
        df_data = []
        for item in items:
            df_data.append({
                'material_type': item.get('material_type', ''),
                'inner_diameter': item.get('inner_diameter', 0),
                'outer_diameter': item.get('outer_diameter', 0),
                'price_per_mm': item.get('price_per_mm', 0),
                'manufacturing_cost_client1': item.get('manufacturing_cost_client1', 0),
                'manufacturing_cost_client2': item.get('manufacturing_cost_client2', 0),
                'manufacturing_cost_client3': item.get('manufacturing_cost_client3', 0),
                'notes': item.get('notes', '')
            })
        
        df = pd.DataFrame(df_data)
        
        # Create Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Material Pricing')
        output.seek(0)
        
        current_date = datetime.now().strftime('%Y%m%d')
        filename = f"material_pricing_export_{current_date}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في تصدير الملف: {str(e)}")

@router.post("/excel/import/material-pricing")
async def import_material_pricing_excel(file: UploadFile = File(...), company_id: str = "elsawy"):
    """Import material pricing from Excel file"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="يجب أن يكون الملف بصيغة Excel (.xlsx أو .xls)")
        
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # Validate required columns
        required_columns = ['material_type', 'inner_diameter', 'outer_diameter', 'price_per_mm']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"أعمدة مفقودة: {', '.join(missing_columns)}")
        
        imported_count = 0
        updated_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Skip non-data rows (e.g. Arabic description headers)
                try:
                    float(row['inner_diameter'])
                except (ValueError, TypeError):
                    continue
                # Check if pricing already exists (same material_type + inner + outer)
                existing = await db.material_pricing.find_one({
                    "material_type": str(row['material_type']),
                    "inner_diameter": float(row['inner_diameter']),
                    "outer_diameter": float(row['outer_diameter']),
                    "company_id": company_id
                })
                
                if existing:
                    # Update existing pricing
                    await db.material_pricing.update_one(
                        {"id": existing["id"]},
                        {"$set": {
                            "price_per_mm": float(row['price_per_mm']),
                            "manufacturing_cost_client1": float(row.get('manufacturing_cost_client1', 0)),
                            "manufacturing_cost_client2": float(row.get('manufacturing_cost_client2', 0)),
                            "manufacturing_cost_client3": float(row.get('manufacturing_cost_client3', 0)),
                            "notes": str(row.get('notes', '')),
                            "updated_at": datetime.utcnow()
                        }}
                    )
                    updated_count += 1
                else:
                    # Create new pricing
                    pricing = MaterialPricing(
                        material_type=str(row['material_type']),
                        inner_diameter=float(row['inner_diameter']),
                        outer_diameter=float(row['outer_diameter']),
                        price_per_mm=float(row['price_per_mm']),
                        manufacturing_cost_client1=float(row.get('manufacturing_cost_client1', 0)),
                        manufacturing_cost_client2=float(row.get('manufacturing_cost_client2', 0)),
                        manufacturing_cost_client3=float(row.get('manufacturing_cost_client3', 0)),
                        notes=str(row.get('notes', ''))
                    )
                    pricing_dict = pricing.dict()
                    pricing_dict["company_id"] = company_id
                    await db.material_pricing.insert_one(pricing_dict)
                    imported_count += 1
                
            except Exception as e:
                errors.append(f"صف {index + 2}: {str(e)}")
        
        return {
            "message": f"تم استيراد {imported_count} تسعيرة جديدة وتحديث {updated_count} تسعيرة",
            "imported_count": imported_count,
            "updated_count": updated_count,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في استيراد الملف: {str(e)}")

@router.post("/calculate-price")
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

@router.post("/inventory-transactions", response_model=InventoryTransaction)
async def create_inventory_transaction_api(transaction: InventoryTransactionCreate):
    """Create inventory transaction via API"""
    try:
        result = await create_inventory_transaction(transaction)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory/check-availability")
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
@router.post("/excel/import/inventory")
async def import_inventory_excel(file: UploadFile = File(...), company_id: str = "elsawy"):
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
                    "outer_diameter": float(row['outer_diameter']),
                    "company_id": company_id
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
                    obj = inventory_item.dict()
                    obj["company_id"] = company_id
                    await db.inventory_items.insert_one(obj)
                
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

@router.get("/excel/export/inventory")
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

@router.post("/excel/import/raw-materials")
async def import_raw_materials_excel(file: UploadFile = File(...), company_id: str = "elsawy"):
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
                obj = raw_material.dict()
                obj["company_id"] = company_id
                await db.raw_materials.insert_one(obj)
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

@router.get("/excel/export/raw-materials")
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
