import asyncio
import logging
from typing import List, Dict, Optional
from src.services.popmart_api_client import PopmartAPIClient, PopmartProduct

logger = logging.getLogger(__name__)

class SpecificMonstersScraper:
    """特定產品爬蟲服務"""
    
    def __init__(self, api_client: PopmartAPIClient):
        self.api_client = api_client
        # 預設監控的產品名稱列表
        self.default_product_names = [
            "SKULLPANDA 溫度系列",
            "MOLLY 幻想大亨系列",
            "DIMOO 迷失在太空系列",
            "LABUBU 太空旅行系列",
            "PUCKY 森林精靈系列",
            "HIRONO 夢幻星球系列"
        ]
        self.product_name_to_id_map: Dict[str, str] = {}

    async def _build_name_to_id_map(self):
        """建立產品名稱到 ID 的映射"""
        logger.info("正在建立產品名稱到 ID 的映射...")
        
        # 為了效率，分批獲取產品
        all_products = []
        
        # 獲取第一批產品（最新的）
        products_batch1 = await self.api_client.get_products(page=1, limit=100, sort="newest")
        if products_batch1:
            all_products.extend(products_batch1)
        
        # 獲取第二批產品（熱門的）
        products_batch2 = await self.api_client.get_products(page=1, limit=100, sort="popular")
        if products_batch2:
            all_products.extend(products_batch2)
        
        # 如果有特定關鍵字，也可以搜索
        for keyword in ["SKULLPANDA", "MOLLY", "DIMOO", "LABUBU", "PUCKY", "HIRONO"]:
            search_results = await self.api_client.search_products(keyword, limit=20)
            if search_results:
                all_products.extend(search_results)
        
        # 建立映射
        for product in all_products:
            self.product_name_to_id_map[product.name] = product.id
            
        logger.info(f"已建立 {len(self.product_name_to_id_map)} 個產品名稱到 ID 的映射。")
        
        # 檢查是否所有預設產品都有對應的ID
        missing_products = [name for name in self.default_product_names if name not in self.product_name_to_id_map]
        if missing_products:
            logger.warning(f"以下產品未找到對應的ID: {missing_products}")
            
            # 嘗試模糊匹配
            for missing_name in missing_products:
                for product_name, product_id in self.product_name_to_id_map.items():
                    # 如果產品名稱包含缺失名稱的關鍵部分，則視為匹配
                    if any(part in product_name for part in missing_name.split()):
                        logger.info(f"為 '{missing_name}' 找到模糊匹配: '{product_name}' (ID: {product_id})")
                        self.product_name_to_id_map[missing_name] = product_id
                        break

    async def get_all_products(self) -> List[PopmartProduct]:
        """獲取所有預設監控產品的詳細資訊"""
        if not self.product_name_to_id_map:  # 如果映射為空，則先建立映射
            await self._build_name_to_id_map()

        products_data: List[PopmartProduct] = []
        for name in self.default_product_names:
            product_id = self.product_name_to_id_map.get(name)
            if product_id:
                logger.info(f"正在獲取產品詳情: {name} (ID: {product_id})")
                product_detail = await self.api_client.get_product_details(product_id)
                if product_detail:
                    products_data.append(product_detail)
                    logger.info(f"成功獲取產品詳情: {name}")
                else:
                    logger.warning(f"無法獲取產品詳情: {name} (ID: {product_id})，可能已下架或ID失效。")
            else:
                logger.warning(f"無法找到產品ID: {name}，請檢查產品名稱是否正確或 API 是否有更新。")
                
                # 嘗試直接搜索產品名稱
                search_term = name.split()[0]  # 使用名稱的第一個詞作為搜索詞
                logger.info(f"嘗試搜索產品: {search_term}")
                search_results = await self.api_client.search_products(search_term, limit=5)
                
                if search_results:
                    # 找到最匹配的結果
                    best_match = None
                    for result in search_results:
                        if name.split()[0].lower() in result.name.lower():
                            best_match = result
                            break
                    
                    if best_match:
                        logger.info(f"通過搜索找到產品: {best_match.name} (ID: {best_match.id})")
                        products_data.append(best_match)
                        # 更新映射以便將來使用
                        self.product_name_to_id_map[name] = best_match.id
                    else:
                        logger.warning(f"搜索未找到匹配的產品: {name}")
                else:
                    logger.warning(f"搜索未返回任何結果: {search_term}")
                
        return products_data
        
    async def add_product_to_monitor(self, product_name: str) -> bool:
        """添加產品到監控列表"""
        # 檢查產品是否已在監控列表中（精確匹配）
        if product_name in self.default_product_names:
            logger.info(f"產品 '{product_name}' 已在監控列表中")
            return True
            
        # 檢查產品是否已在監控列表中（模糊匹配）
        for existing_name in self.default_product_names:
            if product_name in existing_name or existing_name in product_name:
                logger.info(f"產品 '{product_name}' 與現有產品 '{existing_name}' 相似，已在監控列表中")
                return True
            
        # 嘗試搜索產品
        search_results = await self.api_client.search_products(product_name, limit=5)
        
        if not search_results:
            logger.warning(f"找不到產品: {product_name}")
            # 在模擬模式下，即使找不到產品也添加到監控列表
            if hasattr(self.api_client, 'mock_data') and self.api_client.mock_data:
                self.default_product_names.append(product_name)
                logger.info(f"已添加產品到監控列表 (模擬模式): {product_name}")
                return True
            return False
            
        # 找到最匹配的結果
        best_match = None
        for result in search_results:
            # 檢查產品名稱是否包含搜索詞（不區分大小寫）
            if product_name.lower() in result.name.lower() or result.name.lower() in product_name.lower():
                best_match = result
                break
                
        if not best_match:
            # 如果沒有找到精確匹配，使用第一個結果
            best_match = search_results[0]
            
        if best_match:
            self.default_product_names.append(best_match.name)
            self.product_name_to_id_map[best_match.name] = best_match.id
            logger.info(f"已添加產品到監控列表: {best_match.name} (ID: {best_match.id})")
            return True
        else:
            logger.warning(f"找不到匹配的產品: {product_name}")
            return False
            
    def remove_product_from_monitor(self, product_name: str) -> bool:
        """從監控列表中移除產品"""
        # 精確匹配
        if product_name in self.default_product_names:
            self.default_product_names.remove(product_name)
            if product_name in self.product_name_to_id_map:
                del self.product_name_to_id_map[product_name]
            logger.info(f"已從監控列表中移除產品: {product_name}")
            return True
            
        # 模糊匹配
        for existing_name in list(self.default_product_names):  # 使用列表複製以避免在迭代時修改
            if product_name in existing_name or existing_name in product_name:
                self.default_product_names.remove(existing_name)
                if existing_name in self.product_name_to_id_map:
                    del self.product_name_to_id_map[existing_name]
                logger.info(f"已從監控列表中移除產品: {existing_name} (通過模糊匹配 '{product_name}')")
                return True
                
        logger.warning(f"產品不在監控列表中: {product_name}")
        return False
            
    def get_monitored_products(self) -> List[str]:
        """獲取當前監控的產品列表"""
        return self.default_product_names

