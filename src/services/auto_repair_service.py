import logging
import asyncio
import random
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)

class AutoRepairService:
    """自動修復和反偵察服務"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        
        # 請求間隔配置
        self.min_interval = self.config.get('min_interval', 30)  # 最小間隔30秒
        self.max_interval = self.config.get('max_interval', 300)  # 最大間隔5分鐘
        self.current_interval = self.min_interval
        
        # 錯誤計數和恢復
        self.error_count = 0
        self.max_errors = self.config.get('max_errors', 5)
        self.recovery_time = self.config.get('recovery_time', 3600)  # 1小時後重置錯誤計數
        self.last_error_time = None
        
        # 反偵察配置
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.proxy_list = self.config.get('proxy_list', [])
        self.current_proxy_index = 0
        
        # 請求統計
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'last_request_time': None
        }
        
        logger.info(f"自動修復服務已初始化，啟用狀態: {self.enabled}")
    
    def is_enabled(self) -> bool:
        """檢查服務是否啟用"""
        return self.enabled
    
    def get_random_user_agent(self) -> str:
        """獲取隨機User-Agent"""
        return random.choice(self.user_agents)
    
    def get_next_proxy(self) -> Optional[str]:
        """獲取下一個代理"""
        if not self.proxy_list:
            return None
        
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy
    
    def calculate_delay(self) -> float:
        """計算請求延遲時間"""
        if not self.enabled:
            return 0
        
        # 基於錯誤率調整延遲
        if self.error_count > 0:
            # 有錯誤時增加延遲
            multiplier = min(2 ** self.error_count, 10)  # 指數退避，最大10倍
            base_delay = random.uniform(self.min_interval, self.max_interval)
            delay = base_delay * multiplier
        else:
            # 正常情況下的隨機延遲
            delay = random.uniform(self.min_interval, self.max_interval)
        
        # 添加隨機抖動
        jitter = random.uniform(-0.1, 0.1) * delay
        final_delay = max(delay + jitter, 1.0)  # 最小1秒延遲
        
        logger.debug(f"計算延遲時間: {final_delay:.2f}秒")
        return final_delay
    
    async def apply_delay(self):
        """應用延遲"""
        if not self.enabled:
            return
        
        delay = self.calculate_delay()
        logger.debug(f"等待 {delay:.2f} 秒...")
        await asyncio.sleep(delay)
    
    def prepare_headers(self, additional_headers: Dict[str, str] = None) -> Dict[str, str]:
        """準備請求標頭"""
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def prepare_session_config(self) -> Dict[str, Any]:
        """準備會話配置"""
        config = {
            'timeout': aiohttp.ClientTimeout(total=30, connect=10),
            'connector': aiohttp.TCPConnector(
                limit=10,  # 限制連接池大小
                limit_per_host=3,  # 每個主機最多3個連接
                ttl_dns_cache=300,  # DNS緩存5分鐘
                use_dns_cache=True
            )
        }
        
        # 如果有代理配置
        proxy = self.get_next_proxy()
        if proxy:
            config['connector'] = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=3,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            # 注意：代理配置需要在請求時指定，不是在connector中
        
        return config
    
    def record_request_success(self):
        """記錄請求成功"""
        self.request_stats['total_requests'] += 1
        self.request_stats['successful_requests'] += 1
        self.request_stats['last_request_time'] = datetime.now()
        
        # 成功請求時重置錯誤計數
        if self.error_count > 0:
            self.error_count = max(0, self.error_count - 1)
            logger.debug(f"請求成功，錯誤計數減少至: {self.error_count}")
    
    def record_request_failure(self, error: Exception):
        """記錄請求失敗"""
        self.request_stats['total_requests'] += 1
        self.request_stats['failed_requests'] += 1
        self.request_stats['last_request_time'] = datetime.now()
        
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        logger.warning(f"請求失敗，錯誤計數增加至: {self.error_count}, 錯誤: {error}")
        
        # 如果錯誤過多，暫時禁用
        if self.error_count >= self.max_errors:
            logger.error(f"錯誤次數過多({self.error_count})，建議檢查網絡或API狀態")
    
    def should_skip_request(self) -> bool:
        """判斷是否應該跳過請求"""
        if not self.enabled:
            return False
        
        # 檢查是否在恢復期內
        if self.last_error_time and self.error_count >= self.max_errors:
            time_since_error = datetime.now() - self.last_error_time
            if time_since_error.total_seconds() < self.recovery_time:
                logger.debug("在恢復期內，跳過請求")
                return True
            else:
                # 恢復期結束，重置錯誤計數
                self.error_count = 0
                self.last_error_time = None
                logger.info("恢復期結束，重置錯誤計數")
        
        return False
    
    async def safe_request(self, session: aiohttp.ClientSession, method: str, 
                          url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """安全的HTTP請求"""
        if self.should_skip_request():
            return None
        
        try:
            # 應用延遲
            await self.apply_delay()
            
            # 準備標頭
            headers = self.prepare_headers(kwargs.get('headers'))
            kwargs['headers'] = headers
            
            # 添加代理（如果有）
            proxy = self.get_next_proxy()
            if proxy:
                kwargs['proxy'] = proxy
            
            # 發送請求
            async with session.request(method, url, **kwargs) as response:
                self.record_request_success()
                return response
                
        except Exception as e:
            self.record_request_failure(e)
            raise e
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        success_rate = 0
        if self.request_stats['total_requests'] > 0:
            success_rate = (self.request_stats['successful_requests'] / 
                          self.request_stats['total_requests']) * 100
        
        return {
            'enabled': self.enabled,
            'error_count': self.error_count,
            'max_errors': self.max_errors,
            'current_interval': self.current_interval,
            'request_stats': self.request_stats,
            'success_rate': round(success_rate, 2),
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'proxy_count': len(self.proxy_list),
            'user_agent_count': len(self.user_agents)
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config.update(config)
        self.enabled = self.config.get('enabled', True)
        self.min_interval = self.config.get('min_interval', 30)
        self.max_interval = self.config.get('max_interval', 300)
        self.max_errors = self.config.get('max_errors', 5)
        self.recovery_time = self.config.get('recovery_time', 3600)
        self.proxy_list = self.config.get('proxy_list', [])
        
        logger.info("自動修復服務配置已更新")
    
    def reset_stats(self):
        """重置統計信息"""
        self.error_count = 0
        self.last_error_time = None
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'last_request_time': None
        }
        logger.info("統計信息已重置")

