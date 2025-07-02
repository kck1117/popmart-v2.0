#!/usr/bin/env python3
"""
通知功能測試腳本
"""

import requests
import json
import sys

def test_notification_config():
    """測試通知配置API"""
    print("=== 測試通知配置 ===")
    
    # 獲取當前配置
    response = requests.get('http://localhost:5000/api/notification/config')
    if response.status_code == 200:
        config = response.json()
        print("✓ 獲取通知配置成功")
        print(f"  Telegram啟用: {config['config']['telegram']['enabled']}")
        print(f"  Discord啟用: {config['config']['discord']['enabled']}")
    else:
        print("✗ 獲取通知配置失敗")
        return False
    
    # 更新配置（測試用）
    test_config = {
        'telegram': {
            'enabled': False,  # 測試環境不啟用
            'bot_token': 'test_token',
            'chat_id': 'test_chat_id'
        },
        'discord': {
            'enabled': False,  # 測試環境不啟用
            'webhook_url': 'https://discord.com/api/webhooks/test'
        }
    }
    
    response = requests.post(
        'http://localhost:5000/api/notification/config',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(test_config)
    )
    
    if response.status_code == 200:
        print("✓ 更新通知配置成功")
    else:
        print("✗ 更新通知配置失敗")
        return False
    
    return True

def test_notification_types():
    """測試各種通知類型"""
    print("\n=== 測試通知類型 ===")
    
    notification_types = [
        'stock_available',
        'stock_out', 
        'price_change',
        'new_product',
        'limited_product'
    ]
    
    for notification_type in notification_types:
        print(f"測試 {notification_type} 通知...")
        
        response = requests.post(
            'http://localhost:5000/api/notification/test',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'type': notification_type})
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 'success':
                print(f"  ✓ {notification_type} 通知測試成功")
            else:
                print(f"  ✗ {notification_type} 通知測試失敗: {result.get('message', '')}")
        else:
            print(f"  ✗ {notification_type} 通知測試請求失敗")

def test_auto_repair():
    """測試自動修復功能"""
    print("\n=== 測試自動修復功能 ===")
    
    # 獲取統計信息
    response = requests.get('http://localhost:5000/api/auto-repair/stats')
    if response.status_code == 200:
        stats = response.json()
        print("✓ 獲取自動修復統計成功")
        print(f"  啟用狀態: {stats['stats']['enabled']}")
        print(f"  錯誤計數: {stats['stats']['error_count']}")
        print(f"  成功率: {stats['stats']['success_rate']}%")
        print(f"  User-Agent數量: {stats['stats']['user_agent_count']}")
    else:
        print("✗ 獲取自動修復統計失敗")
        return False
    
    # 更新配置
    test_config = {
        'enabled': True,
        'min_interval': 45,
        'max_interval': 450,
        'max_errors': 3
    }
    
    response = requests.post(
        'http://localhost:5000/api/auto-repair/config',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(test_config)
    )
    
    if response.status_code == 200:
        print("✓ 更新自動修復配置成功")
    else:
        print("✗ 更新自動修復配置失敗")
        return False
    
    return True

def test_product_monitoring():
    """測試商品監控功能"""
    print("\n=== 測試商品監控功能 ===")
    
    # 獲取監控產品列表
    response = requests.get('http://localhost:5000/api/monitored_products')
    if response.status_code == 200:
        products = response.json()
        print(f"✓ 獲取監控產品列表成功，共 {len(products)} 個產品")
        for product in products[:3]:  # 只顯示前3個
            print(f"  - {product}")
    else:
        print("✗ 獲取監控產品列表失敗")
        return False
    
    # 添加測試產品
    test_product = "測試產品 MOLLY 海洋系列"
    response = requests.post(
        'http://localhost:5000/api/monitored_products',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'product_name': test_product})
    )
    
    if response.status_code == 200:
        print(f"✓ 添加監控產品成功: {test_product}")
    else:
        print(f"✗ 添加監控產品失敗: {test_product}")
    
    # 移除測試產品
    import urllib.parse
    encoded_product = urllib.parse.quote(test_product)
    response = requests.delete(f'http://localhost:5000/api/monitored_products/{encoded_product}')
    
    if response.status_code == 200:
        print(f"✓ 移除監控產品成功: {test_product}")
    else:
        print(f"✗ 移除監控產品失敗: {test_product}")
    
    return True

def test_product_update():
    """測試產品更新功能"""
    print("\n=== 測試產品更新功能 ===")
    
    # 觸發產品更新
    response = requests.post(
        'http://localhost:5000/api/update_products',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'keywords': ['SKULLPANDA']})
    )
    
    if response.status_code == 200:
        print("✓ 產品更新任務啟動成功")
    else:
        print("✗ 產品更新任務啟動失敗")
        return False
    
    # 檢查更新進度
    import time
    for i in range(10):  # 最多等待10秒
        response = requests.get('http://localhost:5000/api/update_progress')
        if response.status_code == 200:
            progress = response.json()
            print(f"  進度: {progress['percentage']}% - {progress['message']}")
            
            if progress['status'] == 'completed':
                print("✓ 產品更新完成")
                break
            elif progress['status'] == 'failed':
                print("✗ 產品更新失敗")
                return False
        
        time.sleep(1)
    
    return True

def main():
    """主測試函數"""
    print("PopMart監控系統功能測試")
    print("=" * 50)
    
    tests = [
        test_notification_config,
        test_notification_types,
        test_auto_repair,
        test_product_monitoring,
        test_product_update
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ 測試失敗: {e}")
    
    print("\n" + "=" * 50)
    print(f"測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！系統功能正常")
        return 0
    else:
        print("⚠️  部分測試失敗，請檢查系統配置")
        return 1

if __name__ == '__main__':
    sys.exit(main())

