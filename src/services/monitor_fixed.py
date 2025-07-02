import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# 延遲導入，避免循環依賴
# from src.services.notification_service import NotificationService
# from src.services.auto_repair_service import AutoRepairService

from src.services.popmart_api_client import PopmartAPIClient, PopmartProduct
from src.services.specific_monsters_scraper import SpecificMonstersScraper
from src.models.product import Product, PriceHistory, StockHistory, db

logger = logging.getLogger(__name__)

class MonitorService:
    """監控服務"""
    
    def __init__(self, api_client: PopmartAPIClient, notification_config: Dict[str, Any] = None, 
                 auto_repair_config: Dict[str, Any] = None):
        self.api_client = api_client
        self.scraper = SpecificMonstersScraper(api_client)
        
        # 延遲導入和實例化
        from src.services.notification_service import NotificationService
        from src.services.auto_repair_service import AutoRepairService
        self.notification_service = NotificationService(notification_config)
        self.auto_repair_service = AutoRepairService(auto_repair_config)
        
        self.update_progress = {"status": "idle", "percentage": 0, "message": ""}
        self._running = False

    async def update_products(self, keywords: List[str] = None):
        """協調產品數據的更新流程"""
        if self._running:
            logger.warning("更新任務已在進行中，請勿重複觸發")
            return
            
        self._running = True
        self.update_progress = {"status": "running", "percentage": 0, "message": "正在更新產品數據..."}
        logger.info("開始更新產品數據...")
        
        try:
            # 1. 獲取新品
            self.update_progress["message"] = "正在獲取新品..."
            new_arrivals = await self.api_client.get_new_arrivals(limit=50)
            if new_arrivals:
                await self._process_products(new_arrivals, "新品")
            self.update_progress["percentage"] = 25

            # 2. 獲取限量商品
            self.update_progress["message"] = "正在獲取限量商品..."
            limited_products = await self.api_client.get_limited_products(limit=50)
            if limited_products:
                await self._process_products(limited_products, "限量商品")
            self.update_progress["percentage"] = 50

            # 3. 處理特定監控產品 (通過 scraper)
            self.update_progress["message"] = "正在獲取特定監控產品..."
            specific_products = await self.scraper.get_all_products()
            if specific_products:
                await self._process_products(specific_products, "特定監控產品")
            self.update_progress["percentage"] = 75

            # 4. 如果有關鍵字，進行搜索並處理
            if keywords and len(keywords) > 0:
                self.update_progress["message"] = "正在搜索關鍵字產品..."
                for i, keyword in enumerate(keywords):
                    search_results = await self.api_client.search_products(keyword, limit=20)
                    if search_results:
                        await self._process_products(search_results, f"搜索結果: {keyword}")
                    self.update_progress["percentage"] = 75 + (i + 1) / len(keywords) * 20

            self.update_progress = {"status": "completed", "percentage": 100, "message": "產品數據更新完成。"}
            logger.info("產品數據更新完成。")

        except Exception as e:
            logger.error(f"產品數據更新失敗: {e}", exc_info=True)
            self.update_progress = {"status": "failed", "percentage": 0, "message": f"產品數據更新失敗: {str(e)}"}
        finally:
            self._running = False

    async def _process_products(self, products: List[PopmartProduct], source: str):
        """處理獲取的產品列表，包括保存和變化檢測"""
        if not products:
            logger.warning(f"沒有產品需要處理: {source}")
            return
            
        logger.info(f"開始處理 {len(products)} 個產品 (來源: {source})")
        
        for product in products:
            try:
                # 獲取資料庫中現有的產品數據，用於變化檢測
                existing_product = Product.query.get(product.id)
                
                # 保存或更新產品基本信息
                if existing_product:
                    # 更新現有產品
                    self._update_product_from_api(existing_product, product)
                    db.session.commit()
                    logger.debug(f"更新產品: {product.name}")
                else:
                    # 創建新產品
                    new_product = self._create_product_from_api(product)
                    db.session.add(new_product)
                    db.session.commit()
                    logger.info(f"新增產品: {product.name}")
                    existing_product = new_product
                
                # 檢測並保存價格歷史，並發送通知
                if existing_product and (
                    not existing_product.price or 
                    abs(existing_product.price - product.price) > 0.01
                ):
                    old_price = existing_product.price or 0
                    price_history = PriceHistory(
                        product_id=product.id,
                        price=product.price,
                        discount_price=product.discount_price
                    )
                    db.session.add(price_history)
                    db.session.commit()
                    logger.info(f"價格變化: {product.name} 從 {old_price} 變為 {product.price}")
                    
                    # 發送價格變動通知
                    try:
                        product_data = self._prepare_notification_data(product)
                        await self.notification_service.send_price_change_notification(
                            product_data, old_price, product.price
                        )
                    except Exception as e:
                        logger.error(f"發送價格變動通知失敗: {e}")

                # 檢測並保存庫存歷史，並發送通知
                if existing_product and (
                    existing_product.in_stock != product.in_stock or 
                    existing_product.stock_quantity != product.stock_quantity
                ):
                    old_in_stock = existing_product.in_stock
                    stock_history = StockHistory(
                        product_id=product.id,
                        in_stock=product.in_stock,
                        stock_quantity=product.stock_quantity
                    )
                    db.session.add(stock_history)
                    db.session.commit()
                    logger.info(f"庫存變化: {product.name} 從 {old_in_stock}/{existing_product.stock_quantity} 變為 {product.in_stock}/{product.stock_quantity}")
                    
                    # 發送庫存變動通知
                    try:
                        product_data = self._prepare_notification_data(product)
                        if not old_in_stock and product.in_stock:
                            # 從無貨變為有貨
                            await self.notification_service.send_stock_available_notification(product_data)
                        elif old_in_stock and not product.in_stock:
                            # 從有貨變為無貨
                            await self.notification_service.send_stock_out_notification(product_data)
                    except Exception as e:
                        logger.error(f"發送庫存變動通知失敗: {e}")

                # 針對新品和限量商品進行特殊處理並發送通知
                if product.is_new and (not existing_product or not existing_product.is_new):
                    logger.info(f"發現新上架商品: {product.name}")
                    try:
                        product_data = self._prepare_notification_data(product)
                        await self.notification_service.send_new_product_notification(product_data)
                    except Exception as e:
                        logger.error(f"發送新品通知失敗: {e}")
                        
                if product.is_limited and (not existing_product or not existing_product.is_limited):
                    logger.info(f"發現限量商品: {product.name}")
                    try:
                        product_data = self._prepare_notification_data(product)
                        await self.notification_service.send_limited_product_notification(product_data)
                    except Exception as e:
                        logger.error(f"發送限量商品通知失敗: {e}")

            except Exception as e:
                logger.error(f"處理產品 {product.name} 時出錯: {e}", exc_info=True)
                # 繼續處理下一個產品，不中斷整個流程
                continue

    def _create_product_from_api(self, api_product: PopmartProduct) -> Product:
        """從API產品創建數據庫產品對象"""
        now = datetime.now().isoformat()
        return Product(
            id=api_product.id,
            name=api_product.name,
            description=api_product.description,
            price=api_product.price,
            currency=api_product.currency,
            original_price=api_product.original_price,
            discount_price=api_product.discount_price,
            image_url=api_product.image_url,
            image_urls=json.dumps(api_product.image_urls) if api_product.image_urls else None,
            video_url=api_product.video_url,
            product_url=api_product.product_url,
            category_id=api_product.category_id,
            category_name=api_product.category_name,
            brand_id=api_product.brand_id,
            brand_name=api_product.brand_name,
            series=api_product.series,
            in_stock=api_product.in_stock,
            stock_quantity=api_product.stock_quantity,
            max_purchase_quantity=api_product.max_purchase_quantity,
            is_new=api_product.is_new,
            is_limited=api_product.is_limited,
            is_pre_order=api_product.is_pre_order,
            is_blind_box=api_product.is_blind_box,
            release_date=api_product.release_date,
            pre_order_start=api_product.pre_order_start,
            pre_order_end=api_product.pre_order_end,
            dimensions=json.dumps(api_product.dimensions) if api_product.dimensions else None,
            weight=api_product.weight,
            material=api_product.material,
            tags=json.dumps(api_product.tags) if api_product.tags else None,
            sku=api_product.sku,
            barcode=api_product.barcode,
            view_count=api_product.view_count,
            like_count=api_product.like_count,
            review_count=api_product.review_count,
            average_rating=api_product.average_rating,
            created_at=now,
            updated_at=now,
            last_checked=now
        )

    def _update_product_from_api(self, db_product: Product, api_product: PopmartProduct):
        """從API產品更新數據庫產品對象"""
        db_product.name = api_product.name
        db_product.description = api_product.description
        db_product.price = api_product.price
        db_product.currency = api_product.currency
        db_product.original_price = api_product.original_price
        db_product.discount_price = api_product.discount_price
        db_product.image_url = api_product.image_url
        db_product.image_urls = json.dumps(api_product.image_urls) if api_product.image_urls else None
        db_product.video_url = api_product.video_url
        db_product.product_url = api_product.product_url
        db_product.category_id = api_product.category_id
        db_product.category_name = api_product.category_name
        db_product.brand_id = api_product.brand_id
        db_product.brand_name = api_product.brand_name
        db_product.series = api_product.series
        db_product.in_stock = api_product.in_stock
        db_product.stock_quantity = api_product.stock_quantity
        db_product.max_purchase_quantity = api_product.max_purchase_quantity
        db_product.is_new = api_product.is_new
        db_product.is_limited = api_product.is_limited
        db_product.is_pre_order = api_product.is_pre_order
        db_product.is_blind_box = api_product.is_blind_box
        db_product.release_date = api_product.release_date
        db_product.pre_order_start = api_product.pre_order_start
        db_product.pre_order_end = api_product.pre_order_end
        db_product.dimensions = json.dumps(api_product.dimensions) if api_product.dimensions else None
        db_product.weight = api_product.weight
        db_product.material = api_product.material
        db_product.tags = json.dumps(api_product.tags) if api_product.tags else None
        db_product.sku = api_product.sku
        db_product.barcode = api_product.barcode
        db_product.view_count = api_product.view_count
        db_product.like_count = api_product.like_count
        db_product.review_count = api_product.review_count
        db_product.average_rating = api_product.average_rating
        db_product.updated_at = datetime.now().isoformat()
        db_product.last_checked = datetime.now().isoformat()

    def get_update_progress(self) -> Dict[str, Any]:
        """獲取更新進度"""
        return self.update_progress
        
    def is_updating(self) -> bool:
        """檢查是否正在更新"""
        return self._running
        
    async def add_product_to_monitor(self, product_name: str) -> bool:
        """添加產品到監控列表"""
        if not product_name or not product_name.strip():
            logger.warning("產品名稱不能為空")
            return False
            
        return await self.scraper.add_product_to_monitor(product_name)
        
    def remove_product_from_monitor(self, product_name: str) -> bool:
        """從監控列表中移除產品"""
        if not product_name or not product_name.strip():
            logger.warning("產品名稱不能為空")
            return False
            
        return self.scraper.remove_product_from_monitor(product_name)
        
    def get_monitored_products(self) -> List[str]:
        """獲取當前監控的產品列表"""
        return self.scraper.get_monitored_products()


    def _prepare_notification_data(self, product: PopmartProduct) -> Dict[str, Any]:
        """準備通知數據"""
        return {
            'product_name': product.name,
            'price': product.price,
            'currency': product.currency,
            'stock_quantity': product.stock_quantity or 0,
            'product_url': product.product_url or '',
            'brand_name': product.brand_name or '',
            'series': product.series or '',
            'is_new': product.is_new,
            'is_limited': product.is_limited
        }
    
    async def start_services(self):
        """啟動相關服務"""
        try:
            await self.notification_service.start_session()
            logger.info("通知服務已啟動")
        except Exception as e:
            logger.error(f"啟動通知服務失敗: {e}")
    
    async def stop_services(self):
        """停止相關服務"""
        try:
            await self.notification_service.close_session()
            logger.info("通知服務已停止")
        except Exception as e:
            logger.error(f"停止通知服務失敗: {e}")
    
    def get_notification_config(self) -> Dict[str, Any]:
        """獲取通知配置"""
        return self.notification_service.get_config()
    
    def update_notification_config(self, config: Dict[str, Any]):
        """更新通知配置"""
        self.notification_service.update_config(config)
    
    def get_auto_repair_stats(self) -> Dict[str, Any]:
        """獲取自動修復統計"""
        return self.auto_repair_service.get_stats()
    
    def update_auto_repair_config(self, config: Dict[str, Any]):
        """更新自動修復配置"""
        self.auto_repair_service.update_config(config)



