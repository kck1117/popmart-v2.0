from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Product(db.Model):
    """產品數據模型"""
    __tablename__ = 'products'

    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='HKD')
    original_price = db.Column(db.Float)
    discount_price = db.Column(db.Float)
    image_url = db.Column(db.String(512))
    image_urls = db.Column(db.Text)  # JSON string
    video_url = db.Column(db.String(512))
    product_url = db.Column(db.String(512))
    category_id = db.Column(db.String(255))
    category_name = db.Column(db.String(255))
    brand_id = db.Column(db.String(255))
    brand_name = db.Column(db.String(255))
    series = db.Column(db.String(255))
    in_stock = db.Column(db.Boolean, default=False)
    stock_quantity = db.Column(db.Integer)
    max_purchase_quantity = db.Column(db.Integer)
    is_new = db.Column(db.Boolean, default=False)
    is_limited = db.Column(db.Boolean, default=False)
    is_pre_order = db.Column(db.Boolean, default=False)
    is_blind_box = db.Column(db.Boolean, default=False)
    release_date = db.Column(db.String(50))
    pre_order_start = db.Column(db.String(50))
    pre_order_end = db.Column(db.String(50))
    dimensions = db.Column(db.Text)  # JSON string
    weight = db.Column(db.Float)
    material = db.Column(db.String(255))
    tags = db.Column(db.Text)  # JSON string
    sku = db.Column(db.String(255))
    barcode = db.Column(db.String(255))
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    review_count = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.String(50), default=lambda: datetime.now().isoformat())
    updated_at = db.Column(db.String(50))
    last_checked = db.Column(db.String(50))

    def __repr__(self):
        return f'<Product {self.name}>'

    def to_dict(self):
        """將模型轉換為字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'currency': self.currency,
            'original_price': self.original_price,
            'discount_price': self.discount_price,
            'image_url': self.image_url,
            'image_urls': json.loads(self.image_urls) if self.image_urls else [],
            'video_url': self.video_url,
            'product_url': self.product_url,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'brand_id': self.brand_id,
            'brand_name': self.brand_name,
            'series': self.series,
            'in_stock': self.in_stock,
            'stock_quantity': self.stock_quantity,
            'max_purchase_quantity': self.max_purchase_quantity,
            'is_new': self.is_new,
            'is_limited': self.is_limited,
            'is_pre_order': self.is_pre_order,
            'is_blind_box': self.is_blind_box,
            'release_date': self.release_date,
            'pre_order_start': self.pre_order_start,
            'pre_order_end': self.pre_order_end,
            'dimensions': json.loads(self.dimensions) if self.dimensions else {},
            'weight': self.weight,
            'material': self.material,
            'tags': json.loads(self.tags) if self.tags else [],
            'sku': self.sku,
            'barcode': self.barcode,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'review_count': self.review_count,
            'average_rating': self.average_rating,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_checked': self.last_checked
        }
        return data


class PriceHistory(db.Model):
    """價格歷史數據模型"""
    __tablename__ = 'price_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(255), db.ForeignKey('products.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float)
    timestamp = db.Column(db.String(50), default=lambda: datetime.now().isoformat())

    def __repr__(self):
        return f'<PriceHistory {self.product_id} {self.price}>'

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'price': self.price,
            'discount_price': self.discount_price,
            'timestamp': self.timestamp
        }


class StockHistory(db.Model):
    """庫存歷史數據模型"""
    __tablename__ = 'stock_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(255), db.ForeignKey('products.id'), nullable=False)
    in_stock = db.Column(db.Boolean, nullable=False)
    stock_quantity = db.Column(db.Integer)
    timestamp = db.Column(db.String(50), default=lambda: datetime.now().isoformat())

    def __repr__(self):
        return f'<StockHistory {self.product_id} {self.in_stock}>'

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'in_stock': self.in_stock,
            'stock_quantity': self.stock_quantity,
            'timestamp': self.timestamp
        }

