import asyncio
import threading
import logging
from typing import List, Optional
from src.services.monitor import MonitorService

logger = logging.getLogger(__name__)

class Scheduler:
    """排程器服務"""
    
    def __init__(self, monitor_service: MonitorService):
        self.monitor_service = monitor_service
        self._loop = None
        self._thread = None
        self._running = False
        self._interval = 300  # 默認5分鐘
        self._keywords = []

    def start(self, interval: int = 300, keywords: List[str] = None):
        """啟動排程器，定期執行更新任務"""
        if self._running:
            logger.warning("排程器已在運行中。")
            return False

        self._running = True
        self._interval = interval
        self._keywords = keywords or []
        
        # 創建新的事件循環
        self._loop = asyncio.new_event_loop()
        
        # 在獨立線程中運行事件循環
        self._thread = threading.Thread(target=self._run_loop)
        self._thread.daemon = True  # 設置為守護線程，主程序退出時自動終止
        self._thread.start()
        
        logger.info(f"排程器已啟動，每 {interval} 秒執行一次更新任務。")
        return True

    def stop(self):
        """停止排程器"""
        if not self._running:
            logger.warning("排程器未在運行中。")
            return False

        self._running = False
        
        # 安全地停止事件循環
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
            
        # 等待線程結束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)  # 最多等待5秒
            
        logger.info("排程器已停止。")
        return True

    def _run_loop(self):
        """在獨立線程中運行異步事件循環"""
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._schedule_updates())
        except Exception as e:
            logger.error(f"排程器事件循環出錯: {e}", exc_info=True)
        finally:
            # 確保事件循環被關閉
            if not self._loop.is_closed():
                self._loop.close()

    async def _schedule_updates(self):
        """異步調度更新任務"""
        while self._running:
            try:
                if not self.monitor_service.is_updating():
                    logger.info("排程器觸發產品數據更新...")
                    await self.monitor_service.update_products(self._keywords)
                else:
                    logger.info("上一次更新任務尚未完成，跳過本次更新。")
            except Exception as e:
                logger.error(f"排程器執行更新任務時發生錯誤: {e}", exc_info=True)
            finally:
                # 等待指定的間隔時間
                for _ in range(self._interval):
                    if not self._running:
                        break
                    await asyncio.sleep(1)  # 每秒檢查一次是否應該停止

    def is_running(self) -> bool:
        """檢查排程器是否正在運行"""
        return self._running
        
    def get_status(self) -> dict:
        """獲取排程器狀態"""
        return {
            "running": self._running,
            "interval": self._interval,
            "keywords": self._keywords
        }
        
    def update_settings(self, interval: Optional[int] = None, keywords: Optional[List[str]] = None) -> bool:
        """更新排程器設置"""
        if interval is not None:
            self._interval = interval
        
        if keywords is not None:
            self._keywords = keywords
            
        logger.info(f"排程器設置已更新: 間隔={self._interval}秒, 關鍵字={self._keywords}")
        return True

