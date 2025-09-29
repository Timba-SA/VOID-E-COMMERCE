# En backend/schemas/metrics_schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class KPIMetrics(BaseModel):
    total_revenue: float
    average_ticket: float
    total_orders: int
    total_users: int
    total_expenses: float
    total_products_sold: int # <-- ¡LÍNEA NUEVA!

class ProductMetrics(BaseModel):
    most_sold_product: Optional[str] = None
    product_with_most_stock: Optional[str] = None
    category_with_most_products: Optional[str] = None

class SalesDataPoint(BaseModel):
    fecha: date
    total: float

class SalesOverTimeChart(BaseModel):
    data: List[SalesDataPoint]

class ExpensesByCategoryDataPoint(BaseModel):
    categoria: str
    monto: float

class ExpensesByCategoryChart(BaseModel):
    data: List[ExpensesByCategoryDataPoint]