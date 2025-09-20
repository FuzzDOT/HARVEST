"""
Marketplace API Endpoints
Handles agricultural marketplace operations including product listings, orders, and transactions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.schemas.marketplace_schema import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    OrderCreate,
    OrderResponse
)
from app.models.marketplace import Product, Order
from app.services.translate_service import TranslateService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.post("/marketplace/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new product listing in the marketplace.
    """
    try:
        db_product = Product(
            seller_id=product.seller_id,
            name=product.name,
            description=product.description,
            category=product.category,
            price=product.price,
            quantity=product.quantity,
            unit=product.unit,
            location=product.location,
            harvest_date=product.harvest_date,
            expiry_date=product.expiry_date,
            organic_certified=product.organic_certified,
            quality_grade=product.quality_grade,
            is_active=True
        )
        
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        logger.info(f"Product created: {product.name} by seller {product.seller_id}")
        
        return ProductResponse.from_orm(db_product)
        
    except Exception as e:
        logger.error(f"Failed to create product: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create product listing"
        )


@router.get("/marketplace/products", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    organic_only: bool = False,
    available_only: bool = True,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get products from the marketplace with filtering options.
    """
    try:
        query = db.query(Product)
        
        if available_only:
            query = query.filter(Product.is_active == True, Product.quantity > 0)
        
        if category:
            query = query.filter(Product.category == category)
        
        if location:
            query = query.filter(Product.location.ilike(f"%{location}%"))
        
        if min_price:
            query = query.filter(Product.price >= min_price)
        
        if max_price:
            query = query.filter(Product.price <= max_price)
        
        if organic_only:
            query = query.filter(Product.organic_certified == True)
        
        products = query.offset(offset).limit(limit).all()
        
        return [ProductResponse.from_orm(product) for product in products]
        
    except Exception as e:
        logger.error(f"Failed to get products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve products"
        )


@router.get("/marketplace/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    language: Optional[str] = Query(default=None, description="Language code for translation"),
    db: Session = Depends(get_db)
):
    """
    Get a specific product by ID with optional translation.
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product_response = ProductResponse.from_orm(product)
        
        # Translate if language is specified
        if language and language != "en":
            translate_service = TranslateService()
            product_response.name = await translate_service.translate(
                product_response.name, target_language=language
            )
            product_response.description = await translate_service.translate(
                product_response.description, target_language=language
            )
        
        return product_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve product"
        )


@router.put("/marketplace/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a product listing.
    """
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()
        
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update fields
        for field, value in product_update.dict(exclude_unset=True).items():
            setattr(db_product, field, value)
        
        db_product.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_product)
        
        logger.info(f"Product {product_id} updated")
        
        return ProductResponse.from_orm(db_product)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update product"
        )


@router.delete("/marketplace/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a product listing.
    """
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()
        
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        db.delete(db_product)
        db.commit()
        
        logger.info(f"Product {product_id} deleted")
        
        return {"message": "Product deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete product"
        )


@router.post("/marketplace/orders", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new order for a product.
    """
    try:
        # Check product availability
        product = db.query(Product).filter(Product.id == order.product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if product.quantity < order.quantity:
            raise HTTPException(status_code=400, detail="Insufficient quantity available")
        
        # Calculate total
        total_amount = product.price * order.quantity
        
        # Create order
        db_order = Order(
            buyer_id=order.buyer_id,
            product_id=order.product_id,
            seller_id=product.seller_id,
            quantity=order.quantity,
            unit_price=product.price,
            total_amount=total_amount,
            delivery_address=order.delivery_address,
            notes=order.notes,
            status="pending"
        )
        
        # Update product quantity
        product.quantity -= order.quantity
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        logger.info(f"Order created: {db_order.id} for product {order.product_id}")
        
        return OrderResponse.from_orm(db_order)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create order: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create order"
        )


@router.get("/marketplace/orders/{user_id}")
async def get_user_orders(
    user_id: int,
    role: str = Query(..., regex="^(buyer|seller)$"),
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get orders for a user (as buyer or seller).
    """
    try:
        if role == "buyer":
            query = db.query(Order).filter(Order.buyer_id == user_id)
        else:  # seller
            query = db.query(Order).filter(Order.seller_id == user_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        orders = query.offset(offset).limit(limit).all()
        
        return [OrderResponse.from_orm(order) for order in orders]
        
    except Exception as e:
        logger.error(f"Failed to get orders for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve orders"
        )


@router.put("/marketplace/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str = Query(..., regex="^(pending|confirmed|shipped|delivered|cancelled)$"),
    db: Session = Depends(get_db)
):
    """
    Update order status.
    """
    try:
        db_order = db.query(Order).filter(Order.id == order_id).first()
        
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        db_order.status = status
        db_order.updated_at = datetime.utcnow()
        
        if status == "delivered":
            db_order.delivered_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Order {order_id} status updated to {status}")
        
        return {"message": f"Order status updated to {status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update order status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update order status"
        )


@router.get("/marketplace/categories")
async def get_product_categories(db: Session = Depends(get_db)):
    """
    Get all available product categories.
    """
    try:
        categories = db.query(Product.category).distinct().all()
        return [cat[0] for cat in categories if cat[0]]
        
    except Exception as e:
        logger.error(f"Failed to get categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve categories"
        )


@router.post("/marketplace/products/{product_id}/images")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an image for a product.
    """
    try:
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Save file logic would go here
        # For now, just return success message
        
        return {"message": "Image uploaded successfully", "filename": file.filename}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload image"
        )