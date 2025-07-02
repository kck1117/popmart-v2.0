from flask import Blueprint, jsonify, request, current_app
import os
import sys
import logging
import asyncio
from threading import Thread
import urllib.parse

from src.services.monitor import MonitorService
from src.services.popmart_api_client import PopmartAPIClient
from src.models.product import Product, db

monitor_bp = Blueprint('monitor', __name__)
logger = logging.getLogger(__name__)

# 全局變量
api_client = None
monitor_service = None

def init_services():
    """初始化服務"""
    global api_client, monitor_service
    api_client = PopmartAPIClient(region="hk")
    monitor_service = MonitorService(api_client)
    
    # 啟動API客戶端會話
    async def start_session():
        await api_client.start_session()
    
    loop = asyncio.new_event_loop()
    loop.run_until_complete(start_session())
    loop.close()

# 初始化服務
init_services()

@monitor_bp.route('/products', methods=['GET'])
def get_products():
    """獲取產品列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 100)), 100)  # 限制最大返回數量
        offset = (page - 1) * limit
        
        # 查詢產品總數
        total = Product.query.count()
        
        # 查詢分頁數據
        products = Product.query.order_by(Product.updated_at.desc()).offset(offset).limit(limit).all()
        
        # 轉換為字典列表
        products_data = [product.to_dict() for product in products]
        
        return jsonify({
            'products': products_data,
            'total': total,
            'offset': offset,
            'limit': limit
        })
    except Exception as e:
        logger.error(f"獲取產品列表失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'獲取產品列表失敗: {str(e)}'
        }), 500

@monitor_bp.route('/update_products', methods=['POST'])
def update_products():
    """更新產品數據"""
    try:
        data = request.json or {}
        keywords = data.get('keywords', [])
        
        # 檢查是否已經在更新中
        if monitor_service.is_updating():
            return jsonify({
                'status': 'error',
                'message': '產品更新任務已在進行中，請稍後再試。'
            }), 400
        
        # 啟動異步更新任務
        def run_update():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(monitor_service.update_products(keywords))
            loop.close()
        
        update_thread = Thread(target=run_update)
        update_thread.daemon = True
        update_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': '產品更新任務已啟動。'
        })
    except Exception as e:
        logger.error(f"啟動產品更新任務失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'啟動產品更新任務失敗: {str(e)}'
        }), 500

@monitor_bp.route('/update_progress', methods=['GET'])
def get_update_progress():
    """獲取更新進度"""
    try:
        progress = monitor_service.get_update_progress()
        return jsonify(progress)
    except Exception as e:
        logger.error(f"獲取更新進度失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'獲取更新進度失敗: {str(e)}'
        }), 500

@monitor_bp.route('/monitored_products', methods=['GET'])
def get_monitored_products():
    """獲取監控產品列表"""
    try:
        products = monitor_service.get_monitored_products()
        return jsonify(products)
    except Exception as e:
        logger.error(f"獲取監控產品列表失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'獲取監控產品列表失敗: {str(e)}'
        }), 500

@monitor_bp.route('/monitored_products', methods=['POST'])
def add_monitored_product():
    """添加監控產品"""
    try:
        data = request.json or {}
        product_name = data.get('product_name')
        
        if not product_name:
            return jsonify({
                'status': 'error',
                'message': '產品名稱不能為空。'
            }), 400
            
        # 記錄原始產品名稱，用於調試
        logger.info(f"嘗試添加產品，原始名稱: '{product_name}'")
        
        # 啟動異步添加任務
        def run_add():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(monitor_service.add_product_to_monitor(product_name))
            loop.close()
            return result
        
        add_thread = Thread(target=run_add)
        add_thread.daemon = True
        add_thread.start()
        add_thread.join()  # 等待添加完成
        
        # 檢查產品是否已添加到監控列表
        monitored_products = monitor_service.get_monitored_products()
        
        # 檢查完全匹配
        if product_name in monitored_products:
            return jsonify({
                'status': 'success',
                'message': f'產品 \'{product_name}\' 已添加到監控列表。'
            })
            
        # 檢查部分匹配（產品名稱可能被修改或擴展）
        for p in monitored_products:
            if product_name in p or p in product_name:
                return jsonify({
                    'status': 'success',
                    'message': f'產品 \'{p}\' 已添加到監控列表。'
                })
                
        # 如果在模擬模式下，強制添加產品
        if hasattr(api_client, 'mock_data') and api_client.mock_data:
            monitor_service.scraper.default_product_names.append(product_name)
            return jsonify({
                'status': 'success',
                'message': f'產品 \'{product_name}\' 已添加到監控列表（模擬模式）。'
            })
                
        return jsonify({
            'status': 'error',
            'message': f'添加產品 \'{product_name}\' 失敗。'
        }), 400
    except Exception as e:
        logger.error(f"添加監控產品失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'添加監控產品失敗: {str(e)}'
        }), 500

@monitor_bp.route('/monitored_products/<path:product_name>', methods=['DELETE'])
def remove_monitored_product(product_name):
    """移除監控產品"""
    try:
        # URL解碼產品名稱
        decoded_product_name = urllib.parse.unquote(product_name)
        logger.info(f"嘗試移除產品，原始名稱: '{product_name}', 解碼後: '{decoded_product_name}'")
        
        # 嘗試使用解碼後的名稱移除產品
        result = monitor_service.remove_product_from_monitor(decoded_product_name)
        
        if result:
            return jsonify({
                'status': 'success',
                'message': f'產品 \'{decoded_product_name}\' 已從監控列表中移除。'
            })
            
        # 如果直接匹配失敗，嘗試模糊匹配
        monitored_products = monitor_service.get_monitored_products()
        for p in monitored_products:
            if decoded_product_name in p or p in decoded_product_name:
                result = monitor_service.remove_product_from_monitor(p)
                if result:
                    return jsonify({
                        'status': 'success',
                        'message': f'產品 \'{p}\' 已從監控列表中移除。'
                    })
                    
        return jsonify({
            'status': 'error',
            'message': f'產品 \'{decoded_product_name}\' 不在監控列表中。'
        }), 400
    except Exception as e:
        logger.error(f"移除監控產品失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'移除監控產品失敗: {str(e)}'
        }), 500

@monitor_bp.route('/restart', methods=['POST'])
def restart_services():
    """重啟服務"""
    try:
        # 關閉現有服務
        global api_client, monitor_service
        
        async def close_session():
            if api_client:
                await api_client.close_session()
        
        loop = asyncio.new_event_loop()
        loop.run_until_complete(close_session())
        loop.close()
        
        # 重新初始化服務
        init_services()
        
        return jsonify({
            'status': 'success',
            'message': '服務已重啟。'
        })
    except Exception as e:
        logger.error(f"重啟服務失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'重啟服務失敗: {str(e)}'
        }), 500

