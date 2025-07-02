import logging
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class NotificationService:
    """通知服務 - 支援 Telegram 和 Discord"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.telegram_config = self.config.get('telegram', {})
        self.discord_config = self.config.get('discord', {})
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 通知模板
        self.templates = {
            'stock_available': {
                'title': '🎉 商品補貨通知',
                'template': '商品 **{product_name}** 現已有貨！\n\n💰 價格：{price} {currency}\n📦 庫存：{stock_quantity}\n🔗 連結：{product_url}'
            },
            'stock_out': {
                'title': '❌ 商品缺貨通知',
                'template': '商品 **{product_name}** 已售罄\n\n💰 價格：{price} {currency}\n🔗 連結：{product_url}'
            },
            'price_change': {
                'title': '💰 價格變動通知',
                'template': '商品 **{product_name}** 價格變動\n\n舊價格：{old_price} {currency}\n新價格：{new_price} {currency}\n變動：{change_amount} {currency} ({change_percentage}%)\n🔗 連結：{product_url}'
            },
            'new_product': {
                'title': '🆕 新品上架通知',
                'template': '新品 **{product_name}** 已上架！\n\n💰 價格：{price} {currency}\n📦 庫存：{stock_quantity}\n🔗 連結：{product_url}'
            },
            'limited_product': {
                'title': '⭐ 限量商品通知',
                'template': '限量商品 **{product_name}** 現已發售！\n\n💰 價格：{price} {currency}\n📦 庫存：{stock_quantity}\n🔗 連結：{product_url}'
            }
        }
    
    async def start_session(self):
        """啟動HTTP會話"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            logger.info("通知服務HTTP會話已啟動")
    
    async def close_session(self):
        """關閉HTTP會話"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("通知服務HTTP會話已關閉")
    
    async def send_notification(self, notification_type: str, product_data: Dict[str, Any], 
                             additional_data: Dict[str, Any] = None):
        """發送通知"""
        try:
            if notification_type not in self.templates:
                logger.error(f"未知的通知類型: {notification_type}")
                return False
            
            # 準備通知內容
            template_data = self.templates[notification_type]
            title = template_data['title']
            
            # 合併數據
            format_data = {**product_data}
            if additional_data:
                format_data.update(additional_data)
            
            # 格式化消息
            message = template_data['template'].format(**format_data)
            
            # 發送到各個平台
            results = []
            
            if self.telegram_config.get('enabled', False):
                result = await self._send_telegram_message(title, message)
                results.append(('telegram', result))
            
            if self.discord_config.get('enabled', False):
                result = await self._send_discord_message(title, message)
                results.append(('discord', result))
            
            # 記錄結果
            success_count = sum(1 for _, result in results if result)
            total_count = len(results)
            
            if success_count > 0:
                logger.info(f"通知發送成功 {success_count}/{total_count}: {notification_type}")
                return True
            else:
                logger.warning(f"所有通知發送失敗: {notification_type}")
                return False
                
        except Exception as e:
            logger.error(f"發送通知時發生錯誤: {e}", exc_info=True)
            return False
    
    async def _send_telegram_message(self, title: str, message: str) -> bool:
        """發送Telegram消息"""
        try:
            bot_token = self.telegram_config.get('bot_token')
            chat_id = self.telegram_config.get('chat_id')
            
            if not bot_token or not chat_id:
                logger.warning("Telegram配置不完整，跳過發送")
                return False
            
            if not self.session:
                await self.start_session()
            
            # 組合完整消息
            full_message = f"*{title}*\n\n{message}"
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': full_message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info("Telegram消息發送成功")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Telegram消息發送失敗: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"發送Telegram消息時發生錯誤: {e}", exc_info=True)
            return False
    
    async def _send_discord_message(self, title: str, message: str) -> bool:
        """發送Discord消息"""
        try:
            webhook_url = self.discord_config.get('webhook_url')
            
            if not webhook_url:
                logger.warning("Discord配置不完整，跳過發送")
                return False
            
            if not self.session:
                await self.start_session()
            
            # Discord embed格式
            embed = {
                "title": title,
                "description": message,
                "color": 0x00ff00,  # 綠色
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "PopMart監控系統"
                }
            }
            
            data = {
                "embeds": [embed]
            }
            
            async with self.session.post(webhook_url, json=data) as response:
                if response.status == 204:  # Discord webhook成功返回204
                    logger.info("Discord消息發送成功")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Discord消息發送失敗: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"發送Discord消息時發生錯誤: {e}", exc_info=True)
            return False
    
    async def send_stock_available_notification(self, product_data: Dict[str, Any]):
        """發送補貨通知"""
        return await self.send_notification('stock_available', product_data)
    
    async def send_stock_out_notification(self, product_data: Dict[str, Any]):
        """發送缺貨通知"""
        return await self.send_notification('stock_out', product_data)
    
    async def send_price_change_notification(self, product_data: Dict[str, Any], 
                                           old_price: float, new_price: float):
        """發送價格變動通知"""
        change_amount = new_price - old_price
        change_percentage = round((change_amount / old_price) * 100, 2)
        
        additional_data = {
            'old_price': old_price,
            'new_price': new_price,
            'change_amount': change_amount,
            'change_percentage': change_percentage
        }
        
        return await self.send_notification('price_change', product_data, additional_data)
    
    async def send_new_product_notification(self, product_data: Dict[str, Any]):
        """發送新品上架通知"""
        return await self.send_notification('new_product', product_data)
    
    async def send_limited_product_notification(self, product_data: Dict[str, Any]):
        """發送限量商品通知"""
        return await self.send_notification('limited_product', product_data)
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config = config
        self.telegram_config = self.config.get('telegram', {})
        self.discord_config = self.config.get('discord', {})
        logger.info("通知服務配置已更新")
    
    def get_config(self) -> Dict[str, Any]:
        """獲取當前配置"""
        return {
            'telegram': {
                'enabled': self.telegram_config.get('enabled', False),
                'bot_token': '***' if self.telegram_config.get('bot_token') else None,
                'chat_id': self.telegram_config.get('chat_id')
            },
            'discord': {
                'enabled': self.discord_config.get('enabled', False),
                'webhook_url': '***' if self.discord_config.get('webhook_url') else None
            }
        }

