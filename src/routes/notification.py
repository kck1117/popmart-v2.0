from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/notification/config', methods=['GET'])
def get_notification_config():
    """獲取通知配置"""
    try:
        monitor_service = current_app.monitor_service
        config = monitor_service.get_notification_config()
        return jsonify({
            'status': 'success',
            'config': config
        })
    except Exception as e:
        logger.error(f"獲取通知配置失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'獲取通知配置失敗: {str(e)}'
        }), 500

@notification_bp.route('/notification/config', methods=['POST'])
def update_notification_config():
    """更新通知配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': '請提供配置數據'
            }), 400
        
        monitor_service = current_app.monitor_service
        monitor_service.update_notification_config(data)
        
        return jsonify({
            'status': 'success',
            'message': '通知配置已更新'
        })
    except Exception as e:
        logger.error(f"更新通知配置失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'更新通知配置失敗: {str(e)}'
        }), 500

@notification_bp.route('/notification/test', methods=['POST'])
def test_notification():
    """測試通知功能"""
    import asyncio
    
    try:
        data = request.get_json()
        notification_type = data.get('type', 'stock_available')
        
        # 測試數據
        test_product_data = {
            'product_name': '測試商品 MOLLY 太空系列 #01',
            'price': 299.0,
            'currency': 'HKD',
            'stock_quantity': 10,
            'product_url': 'https://www.popmart.com/hk/products/test',
            'brand_name': 'MOLLY',
            'series': '太空系列',
            'is_new': True,
            'is_limited': False
        }
        
        monitor_service = current_app.monitor_service
        
        # 創建事件循環來運行異步函數
        async def run_notification():
            if notification_type == 'stock_available':
                return await monitor_service.notification_service.send_stock_available_notification(test_product_data)
            elif notification_type == 'stock_out':
                return await monitor_service.notification_service.send_stock_out_notification(test_product_data)
            elif notification_type == 'price_change':
                return await monitor_service.notification_service.send_price_change_notification(
                    test_product_data, 350.0, 299.0
                )
            elif notification_type == 'new_product':
                return await monitor_service.notification_service.send_new_product_notification(test_product_data)
            elif notification_type == 'limited_product':
                test_product_data['is_limited'] = True
                return await monitor_service.notification_service.send_limited_product_notification(test_product_data)
            else:
                return False
        
        if notification_type not in ['stock_available', 'stock_out', 'price_change', 'new_product', 'limited_product']:
            return jsonify({
                'status': 'error',
                'message': f'不支援的通知類型: {notification_type}'
            }), 400
        
        # 運行異步函數
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_notification())
        except Exception as e:
            logger.error(f"運行通知測試時發生錯誤: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': f'通知測試執行失敗: {str(e)}'
            }), 500
        finally:
            try:
                loop.close()
            except:
                pass
        
        if result:
            return jsonify({
                'status': 'success',
                'message': f'測試通知 ({notification_type}) 發送成功'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'測試通知 ({notification_type}) 發送失敗'
            }), 500
            
    except Exception as e:
        logger.error(f"測試通知失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'測試通知失敗: {str(e)}'
        }), 500

@notification_bp.route('/auto-repair/stats', methods=['GET'])
def get_auto_repair_stats():
    """獲取自動修復統計"""
    try:
        monitor_service = current_app.monitor_service
        stats = monitor_service.get_auto_repair_stats()
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        logger.error(f"獲取自動修復統計失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'獲取自動修復統計失敗: {str(e)}'
        }), 500

@notification_bp.route('/auto-repair/config', methods=['POST'])
def update_auto_repair_config():
    """更新自動修復配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': '請提供配置數據'
            }), 400
        
        monitor_service = current_app.monitor_service
        monitor_service.update_auto_repair_config(data)
        
        return jsonify({
            'status': 'success',
            'message': '自動修復配置已更新'
        })
    except Exception as e:
        logger.error(f"更新自動修復配置失敗: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'更新自動修復配置失敗: {str(e)}'
        }), 500

