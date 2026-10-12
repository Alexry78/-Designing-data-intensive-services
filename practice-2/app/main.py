from datetime import datetime
import socket

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product

app = FastAPI(title="Highload Shop API", version="0.3.0")


@app.get("/")
async def root():
    return {
        "service": "highload-shop",
        "instance": socket.gethostname(),
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "instance": socket.gethostname()}


@app.get("/products")
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).order_by(Product.id).limit(50))
    products = result.scalars().all()
    return {
        "instance": socket.gethostname(),
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "stock": p.stock,
                "category": p.category,
            }
            for p in products
        ],
        "total": len(products),
    }


@app.get("/products/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "instance": socket.gethostname(),
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "stock": product.stock,
    }


@app.get("/db-stats")
async def db_stats(db: AsyncSession = Depends(get_db)):
    """Диагностический эндпоинт — сколько строк в каждой таблице."""
    from app.models import User, Order, OrderItem
    users = await db.scalar(select(func.count(User.id)))
    products = await db.scalar(select(func.count(Product.id)))
    orders = await db.scalar(select(func.count(Order.id)))
    items = await db.scalar(select(func.count(OrderItem.id)))
    return {
        "users": users,
        "products": products,
        "orders": orders,
        "order_items": items,
    }