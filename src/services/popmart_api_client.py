import aiohttp
import asyncio
import random
import logging
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PopmartProduct:
    """Popmart商品數據結構"""
    id: str
    name: str
    price: float
    currency: str = "HKD"
    original_price: Optional[float] = None
    discount_price: Optional[float] = None
    image_url: str = ""
    image_urls: List[str] = None
    video_url: Optional[str] = None
    product_url: str = ""
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    brand_id: Optional[str] = None
    brand_name: Optional[str] = None
    series: Optional[str] = None
    in_stock: bool = True
    stock_quantity: Optional[int] = None
    max_purchase_quantity: Optional[int] = None
    is_new: bool = False
    is_limited: bool = False
    is_pre_order: bool = False
    is_blind_box: bool = False
    release_date: Optional[str] = None
    pre_order_start: Optional[str] = None
    pre_order_end: Optional[str] = None
    dimensions: Optional[Dict[str, float]] = None
    weight: Optional[float] = None
    material: Optional[str] = None
    tags: List[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    review_count: int = 0
    average_rating: float = 0.0
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_checked: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.image_urls is None:
            self.image_urls = []
        if self.dimensions is None:
            self.dimensions = {}
        if not self.last_checked:
            self.last_checked = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self):
        """將dataclass轉換為字典"""
        return asdict(self)


class PopmartAPIClient:
    """Popmart API客戶端"""
    
    def __init__(self, region: str = "hk"):
        self.region = region
        self.base_url = "https://prod-intl-api.popmart.com"
        self.web_base_url = f"https://www.popmart.com/{region}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = asyncio.Semaphore(3)  # 限制並發請求
        
        # 用戶代理池
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0'
        ]
        
        # 模擬數據
        self.mock_data = True
        self.mock_products = self._generate_mock_products()
    
    def _generate_mock_products(self) -> List[PopmartProduct]:
        """生成模擬產品數據"""
        products = []
        series_list = [
            "溫度系列", "幻想大亨系列", "迷失在太空系列", "太空旅行系列", 
            "森林精靈系列", "夢幻星球系列", "太空系列", "海洋系列"
        ]
        brands = ["SKULLPANDA", "MOLLY", "DIMOO", "LABUBU", "PUCKY", "HIRONO"]
        
        for i in range(1, 21):
            brand = random.choice(brands)
            series = random.choice(series_list)
            product_id = f"prod_{i:03d}"
            price = random.uniform(100, 500)
            discount = random.random() < 0.3  # 30% 的產品有折扣
            discount_price = price * 0.8 if discount else None
            in_stock = random.random() < 0.7  # 70% 的產品有庫存
            stock_quantity = random.randint(1, 100) if in_stock else 0
            is_new = random.random() < 0.2  # 20% 的產品是新品
            is_limited = random.random() < 0.15  # 15% 的產品是限量版
            
            product = PopmartProduct(
                id=product_id,
                name=f"{brand} {series} #{i:02d}",
                description=f"{brand} {series} 系列第 {i} 款，限量發售。",
                price=price,
                original_price=price if discount else None,
                discount_price=discount_price,
                image_url=f"https://example.com/images/{product_id}.jpg",
                image_urls=[f"https://example.com/images/{product_id}_{j}.jpg" for j in range(1, 4)],
                product_url=f"https://www.popmart.com/hk/products/{product_id}",
                category_id=f"cat_{random.randint(1, 5):02d}",
                category_name="玩具公仔",
                brand_id=f"brand_{brands.index(brand) + 1:02d}",
                brand_name=brand,
                series=series,
                in_stock=in_stock,
                stock_quantity=stock_quantity,
                max_purchase_quantity=5,
                is_new=is_new,
                is_limited=is_limited,
                is_pre_order=random.random() < 0.1,
                is_blind_box=random.random() < 0.25,
                release_date="2025-06-01",
                dimensions={"height": 10.0, "width": 5.0, "depth": 5.0},
                weight=0.2,
                material="PVC",
                tags=["公仔", brand, series, "收藏品"],
                sku=f"SKU{product_id}",
                barcode=f"BAR{product_id}",
                view_count=random.randint(100, 10000),
                like_count=random.randint(10, 1000),
                review_count=random.randint(0, 100),
                average_rating=random.uniform(3.5, 5.0)
            )
            products.append(product)
        
        return products
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.close_session()
    
    async def start_session(self):
        """啟動HTTP會話"""
        if self.session is not None:
            await self.close_session()
            
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_base_headers()
        )
        logger.info("API客戶端會話已啟動")
    
    async def close_session(self):
        """關閉HTTP會話"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("API客戶端會話已關閉")
    
    def _get_base_headers(self) -> Dict[str, str]:
        """獲取基礎請求頭"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-HK,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Region': self.region,
            'X-Language': 'zh-HK',
            'X-Currency': 'HKD'
        }
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """發送HTTP請求"""
        if self.mock_data:
            # 模擬延遲
            await asyncio.sleep(random.uniform(0.5, 1.5))
            return {"code": 200, "data": {}}
            
        if self.session is None:
            await self.start_session()
            
        async with self.rate_limiter:
            try:
                # 隨機延遲避免檢測
                await asyncio.sleep(random.uniform(1.5, 4.0))
                
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        logger.warning("請求頻率過高，等待後重試")
                        await asyncio.sleep(random.uniform(10, 20))
                        return await self._make_request(method, url, **kwargs)
                    elif response.status == 403:
                        logger.error("請求被禁止，可能觸發了反爬蟲機制")
                        return None
                    elif response.status == 404:
                        logger.error(f"資源不存在: {url}")
                        return None
                    else:
                        logger.error(f"請求失敗，狀態碼: {response.status}, URL: {url}")
                        try:
                            error_text = await response.text()
                            logger.error(f"錯誤響應: {error_text[:200]}...")
                        except:
                            pass
                        return None
                        
            except asyncio.TimeoutError:
                logger.error(f"請求超時: {url}")
                return None
            except Exception as e:
                logger.error(f"請求異常: {e}, URL: {url}")
                return None
    
    async def get_products(self, page: int = 1, limit: int = 20, 
                          category: str = None, sort: str = "newest") -> List[PopmartProduct]:
        """獲取商品列表"""
        if self.mock_data:
            # 模擬延遲
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 根據排序方式處理
            sorted_products = self.mock_products.copy()
            if sort == "newest":
                # 隨機排序模擬最新
                random.shuffle(sorted_products)
            elif sort == "popular":
                # 按照點讚數排序
                sorted_products.sort(key=lambda p: p.like_count, reverse=True)
                
            # 分頁處理
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            result = sorted_products[start_idx:end_idx]
            
            logger.info(f"成功獲取 {len(result)} 個商品")
            return result
        
        params = {
            'page': page,
            'limit': limit,
            'region': self.region,
            'sort': sort
        }
        
        if category:
            params['category'] = category
        
        url = f"{self.base_url}/shop/v1/products"
        response = await self._make_request('GET', url, params=params)
        
        if not response or response.get('code') != 200:
            logger.error("獲取商品列表失敗")
            return []
        
        products = []
        for item in response.get('data', {}).get('products', []):
            try:
                product = self._parse_product_data(item)
                products.append(product)
            except Exception as e:
                logger.warning(f"解析商品數據失敗: {e}")
                continue
        
        logger.info(f"成功獲取 {len(products)} 個商品")
        return products
    
    def _parse_product_data(self, item: Dict[str, Any]) -> PopmartProduct:
        """解析商品數據"""
        return PopmartProduct(
            id=item.get('id', ''),
            name=item.get('name', ''),
            description=item.get('description', ''),
            price=float(item.get('price', 0)),
            currency=item.get('currency', 'HKD'),
            original_price=float(item.get('original_price')) if item.get('original_price') else None,
            discount_price=float(item.get('discount_price')) if item.get('discount_price') else None,
            image_url=item.get('image_url', ''),
            image_urls=item.get('image_urls', []),
            video_url=item.get('video_url'),
            product_url=item.get('product_url', ''),
            category_id=item.get('category_id'),
            category_name=item.get('category', ''),
            brand_id=item.get('brand_id'),
            brand_name=item.get('brand', ''),
            series=item.get('series'),
            in_stock=item.get('in_stock', True),
            stock_quantity=item.get('stock_quantity'),
            max_purchase_quantity=item.get('max_purchase_quantity'),
            is_new=item.get('is_new', False),
            is_limited=item.get('is_limited', False),
            is_pre_order=item.get('is_pre_order', False),
            is_blind_box=item.get('is_blind_box', False),
            release_date=item.get('release_date'),
            pre_order_start=item.get('pre_order_start'),
            pre_order_end=item.get('pre_order_end'),
            dimensions=item.get('dimensions'),
            weight=item.get('weight'),
            material=item.get('material'),
            tags=item.get('tags', []),
            sku=item.get('sku'),
            barcode=item.get('barcode'),
            view_count=item.get('view_count', 0),
            like_count=item.get('like_count', 0),
            review_count=item.get('review_count', 0),
            average_rating=item.get('average_rating', 0.0)
        )
    
    async def get_product_details(self, product_id: str) -> Optional[PopmartProduct]:
        """獲取商品詳情"""
        if self.mock_data:
            # 模擬延遲
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 查找對應ID的產品
            for product in self.mock_products:
                if product.id == product_id:
                    return product
                    
            # 如果找不到，返回一個新的模擬產品
            brand = random.choice(["SKULLPANDA", "MOLLY", "DIMOO", "LABUBU", "PUCKY", "HIRONO"])
            series = random.choice(["溫度系列", "幻想大亨系列", "迷失在太空系列", "太空旅行系列"])
            price = random.uniform(100, 500)
            
            return PopmartProduct(
                id=product_id,
                name=f"{brand} {series} #{product_id}",
                description=f"{brand} {series} 系列產品，限量發售。",
                price=price,
                image_url=f"https://example.com/images/{product_id}.jpg",
                brand_name=brand,
                series=series,
                in_stock=True,
                stock_quantity=random.randint(1, 100)
            )
        
        url = f"{self.base_url}/shop/v1/products/{product_id}"
        response = await self._make_request('GET', url)
        
        if not response or response.get('code') != 200:
            logger.error(f"獲取商品詳情失敗: {product_id}")
            return None
        
        item = response.get('data', {})
        try:
            return self._parse_product_data(item)
        except Exception as e:
            logger.error(f"解析商品詳情失敗: {e}")
            return None
    
    async def search_products(self, keyword: str, page: int = 1, limit: int = 20) -> List[PopmartProduct]:
        """搜索商品"""
        if self.mock_data:
            # 模擬延遲
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 根據關鍵字過濾產品
            filtered_products = [
                p for p in self.mock_products 
                if keyword.lower() in p.name.lower() or 
                   (p.brand_name and keyword.lower() in p.brand_name.lower()) or
                   (p.series and keyword.lower() in p.series.lower())
            ]
            
            # 分頁處理
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            result = filtered_products[start_idx:end_idx]
            
            logger.info(f"搜索 '{keyword}' 找到 {len(result)} 個商品")
            return result
        
        params = {
            'q': keyword,
            'page': page,
            'limit': limit,
            'region': self.region
        }
        
        url = f"{self.base_url}/search/v1/products"
        response = await self._make_request('GET', url, params=params)
        
        if not response or response.get('code') != 200:
            logger.error(f"搜索商品失敗: {keyword}")
            return []
        
        products = []
        for item in response.get('data', {}).get('products', []):
            try:
                product = self._parse_product_data(item)
                products.append(product)
            except Exception as e:
                logger.warning(f"解析搜索結果失敗: {e}")
                continue
        
        logger.info(f"搜索 '{keyword}' 找到 {len(products)} 個商品")
        return products
    
    async def check_inventory(self, product_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """檢查商品庫存"""
        if self.mock_data:
            # 模擬延遲
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            inventory_data = {}
            for product_id in product_ids:
                # 查找對應ID的產品
                product = next((p for p in self.mock_products if p.id == product_id), None)
                
                if product:
                    inventory_data[product_id] = {
                        'in_stock': product.in_stock,
                        'quantity': product.stock_quantity,
                        'last_updated': datetime.now().isoformat()
                    }
                else:
                    # 如果找不到，生成隨機庫存數據
                    in_stock = random.random() < 0.7
                    inventory_data[product_id] = {
                        'in_stock': in_stock,
                        'quantity': random.randint(1, 100) if in_stock else 0,
                        'last_updated': datetime.now().isoformat()
                    }
            
            logger.info(f"成功檢查 {len(inventory_data)} 個商品的庫存")
            return inventory_data
            
        if not product_ids:
            logger.warning("沒有提供產品ID進行庫存檢查")
            return {}
            
        params = {
            'product_ids': ','.join(product_ids),
            'region': self.region
        }
        
        url = f"{self.base_url}/inventory/v1/check"
        response = await self._make_request('GET', url, params=params)
        
        if not response or response.get('code') != 200:
            logger.error("檢查庫存失敗")
            return {}
        
        inventory_data = {}
        for item in response.get('data', {}).get('inventory', []):
            product_id = item.get('product_id')
            if product_id:
                inventory_data[product_id] = {
                    'in_stock': item.get('in_stock', False),
                    'quantity': item.get('quantity', 0),
                    'last_updated': item.get('last_updated', datetime.now().isoformat())
                }
        
        logger.info(f"成功檢查 {len(inventory_data)} 個商品的庫存")
        return inventory_data
    
    async def get_new_arrivals(self, limit: int = 50) -> List[PopmartProduct]:
        """獲取新品"""
        if self.mock_data:
            # 模擬延遲
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 篩選新品
            new_products = [p for p in self.mock_products if p.is_new]
            # 如果新品不足，隨機添加一些
            if len(new_products) < limit:
                additional_products = random.sample([p for p in self.mock_products if not p.is_new], min(limit - len(new_products), len(self.mock_products) - len(new_products)))
                for p in additional_products:
                    p.is_new = True
                new_products.extend(additional_products)
                
            # 隨機排序並限制數量
            random.shuffle(new_products)
            result = new_products[:limit]
            
            logger.info(f"成功獲取 {len(result)} 個新品")
            return result
            
        return await self.get_products(limit=limit, sort="newest")
    
    async def get_limited_products(self, limit: int = 50) -> List[PopmartProduct]:
        """獲取限量商品"""
        if self.mock_data:
            # 模擬延遲
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 篩選限量商品
            limited_products = [p for p in self.mock_products if p.is_limited]
            # 如果限量商品不足，隨機添加一些
            if len(limited_products) < limit:
                additional_products = random.sample([p for p in self.mock_products if not p.is_limited], min(limit - len(limited_products), len(self.mock_products) - len(limited_products)))
                for p in additional_products:
                    p.is_limited = True
                limited_products.extend(additional_products)
                
            # 隨機排序並限制數量
            random.shuffle(limited_products)
            result = limited_products[:limit]
            
            logger.info(f"成功獲取 {len(result)} 個限量商品")
            return result
            
        params = {
            'is_limited': 'true',
            'limit': limit,
            'region': self.region
        }
        
        url = f"{self.base_url}/shop/v1/products"
        response = await self._make_request('GET', url, params=params)
        
        if not response or response.get('code') != 200:
            logger.error("獲取限量商品失敗")
            return []
        
        products = []
        for item in response.get('data', {}).get('products', []):
            try:
                product = self._parse_product_data(item)
                product.is_limited = True  # 確保標記為限量商品
                products.append(product)
            except Exception as e:
                logger.warning(f"解析限量商品數據失敗: {e}")
                continue
        
        logger.info(f"成功獲取 {len(products)} 個限量商品")
        return products

