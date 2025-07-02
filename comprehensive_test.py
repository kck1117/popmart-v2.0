#!/usr/bin/env python3
"""
PopMart監控系統綜合測試腳本
測試所有核心功能是否正常運作
"""

import requests
import json
import time
import sys
from datetime import datetime

class PopMartSystemTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
    
    def log_test(self, test_name, success, message=""):
        """記錄測試結果"""
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_api_connectivity(self):
        """測試API連接性"""
        try:
            response = requests.get(f"{self.base_url}/api/products", timeout=5)
            if response.status_code == 200:
                data = response.json()
                product_count = len(data.get('products', []))
                self.log_test("API連接性", True, f"成功獲取 {product_count} 個產品")
                return True
            else:
                self.log_test("API連接性", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API連接性", False, str(e))
            return False
    
    def test_product_monitoring(self):
        """測試商品監控功能"""
        try:
            # 1. 獲取監控產品列表
            response = requests.get(f"{self.base_url}/api/monitored_products")
            if response.status_code != 200:
                self.log_test("商品監控-獲取列表", False, f"HTTP {response.status_code}")
                return False
            
            initial_products = response.json()
            initial_count = len(initial_products)
            
            # 2. 添加測試產品
            test_product = f"測試產品 {datetime.now().strftime('%H%M%S')}"
            response = requests.post(
                f"{self.base_url}/api/monitored_products",
                headers={'Content-Type': 'application/json'},
                data=json.dumps({'product_name': test_product})
            )
            
            if response.status_code != 200:
                self.log_test("商品監控-添加產品", False, f"HTTP {response.status_code}")
                return False
            
            # 3. 驗證產品已添加
            response = requests.get(f"{self.base_url}/api/monitored_products")
            updated_products = response.json()
            
            if len(updated_products) != initial_count + 1:
                self.log_test("商品監控-驗證添加", False, "產品數量未增加")
                return False
            
            # 4. 移除測試產品
            import urllib.parse
            encoded_product = urllib.parse.quote(test_product)
            response = requests.delete(f"{self.base_url}/api/monitored_products/{encoded_product}")
            
            if response.status_code != 200:
                self.log_test("商品監控-移除產品", False, f"HTTP {response.status_code}")
                return False
            
            # 5. 驗證產品已移除
            response = requests.get(f"{self.base_url}/api/monitored_products")
            final_products = response.json()
            
            if len(final_products) != initial_count:
                self.log_test("商品監控-驗證移除", False, "產品數量未恢復")
                return False
            
            self.log_test("商品監控功能", True, f"成功測試添加/移除監控產品")
            return True
            
        except Exception as e:
            self.log_test("商品監控功能", False, str(e))
            return False
    
    def test_product_update(self):
        """測試產品更新功能"""
        try:
            # 1. 觸發產品更新
            response = requests.post(
                f"{self.base_url}/api/update_products",
                headers={'Content-Type': 'application/json'},
                data=json.dumps({'keywords': ['TEST']})
            )
            
            if response.status_code != 200:
                self.log_test("產品更新-啟動", False, f"HTTP {response.status_code}")
                return False
            
            # 2. 監控更新進度
            max_wait = 30  # 最多等待30秒
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                response = requests.get(f"{self.base_url}/api/update_progress")
                if response.status_code == 200:
                    progress = response.json()
                    
                    if progress['status'] == 'completed':
                        self.log_test("產品更新功能", True, f"更新完成，進度: {progress['percentage']}%")
                        return True
                    elif progress['status'] == 'failed':
                        self.log_test("產品更新功能", False, f"更新失敗: {progress.get('message', '')}")
                        return False
                
                time.sleep(1)
            
            self.log_test("產品更新功能", False, "更新超時")
            return False
            
        except Exception as e:
            self.log_test("產品更新功能", False, str(e))
            return False
    
    def test_notification_config(self):
        """測試通知配置功能"""
        try:
            # 1. 獲取當前配置
            response = requests.get(f"{self.base_url}/api/notification/config")
            if response.status_code != 200:
                self.log_test("通知配置-獲取", False, f"HTTP {response.status_code}")
                return False
            
            original_config = response.json()['config']
            
            # 2. 更新配置
            test_config = {
                'telegram': {
                    'enabled': False,
                    'bot_token': 'test_token_123',
                    'chat_id': 'test_chat_456'
                },
                'discord': {
                    'enabled': False,
                    'webhook_url': 'https://discord.com/api/webhooks/test'
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/notification/config",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(test_config)
            )
            
            if response.status_code != 200:
                self.log_test("通知配置-更新", False, f"HTTP {response.status_code}")
                return False
            
            # 3. 驗證配置已更新
            response = requests.get(f"{self.base_url}/api/notification/config")
            updated_config = response.json()['config']
            
            if updated_config['telegram']['chat_id'] != 'test_chat_456':
                self.log_test("通知配置-驗證", False, "配置未正確更新")
                return False
            
            self.log_test("通知配置功能", True, "成功更新和驗證配置")
            return True
            
        except Exception as e:
            self.log_test("通知配置功能", False, str(e))
            return False
    
    def test_auto_repair_stats(self):
        """測試自動修復統計功能"""
        try:
            # 1. 獲取統計信息
            response = requests.get(f"{self.base_url}/api/auto-repair/stats")
            if response.status_code != 200:
                self.log_test("自動修復-獲取統計", False, f"HTTP {response.status_code}")
                return False
            
            stats = response.json()['stats']
            
            # 2. 驗證統計數據結構
            required_fields = ['enabled', 'error_count', 'success_rate', 'user_agent_count']
            for field in required_fields:
                if field not in stats:
                    self.log_test("自動修復-數據結構", False, f"缺少字段: {field}")
                    return False
            
            # 3. 更新配置
            test_config = {
                'enabled': True,
                'min_interval': 60,
                'max_interval': 600,
                'max_errors': 3
            }
            
            response = requests.post(
                f"{self.base_url}/api/auto-repair/config",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(test_config)
            )
            
            if response.status_code != 200:
                self.log_test("自動修復-更新配置", False, f"HTTP {response.status_code}")
                return False
            
            self.log_test("自動修復功能", True, f"啟用狀態: {stats['enabled']}, User-Agent: {stats['user_agent_count']}")
            return True
            
        except Exception as e:
            self.log_test("自動修復功能", False, str(e))
            return False
    
    def test_data_persistence(self):
        """測試數據持久化"""
        try:
            # 1. 獲取產品數據
            response = requests.get(f"{self.base_url}/api/products?limit=5")
            if response.status_code != 200:
                self.log_test("數據持久化", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            products = data.get('products', [])
            
            if len(products) == 0:
                self.log_test("數據持久化", False, "沒有產品數據")
                return False
            
            # 2. 檢查產品數據完整性
            sample_product = products[0]
            required_fields = ['id', 'name', 'price', 'in_stock']
            
            for field in required_fields:
                if field not in sample_product:
                    self.log_test("數據持久化", False, f"產品數據缺少字段: {field}")
                    return False
            
            self.log_test("數據持久化", True, f"成功驗證 {len(products)} 個產品的數據完整性")
            return True
            
        except Exception as e:
            self.log_test("數據持久化", False, str(e))
            return False
    
    def test_error_handling(self):
        """測試錯誤處理"""
        try:
            # 1. 測試無效的API端點
            response = requests.get(f"{self.base_url}/api/invalid_endpoint")
            if response.status_code == 404:
                self.log_test("錯誤處理-404", True, "正確返回404錯誤")
            else:
                self.log_test("錯誤處理-404", False, f"期望404，實際 {response.status_code}")
                return False
            
            # 2. 測試無效的JSON數據
            response = requests.post(
                f"{self.base_url}/api/monitored_products",
                headers={'Content-Type': 'application/json'},
                data='invalid json'
            )
            
            if response.status_code in [400, 500]:
                self.log_test("錯誤處理-無效JSON", True, f"正確處理無效JSON (HTTP {response.status_code})")
            else:
                self.log_test("錯誤處理-無效JSON", False, f"未正確處理無效JSON")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("錯誤處理", False, str(e))
            return False
    
    def run_all_tests(self):
        """運行所有測試"""
        print("PopMart監控系統綜合測試")
        print("=" * 60)
        print(f"測試開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        tests = [
            ("API連接性測試", self.test_api_connectivity),
            ("商品監控功能測試", self.test_product_monitoring),
            ("產品更新功能測試", self.test_product_update),
            ("通知配置功能測試", self.test_notification_config),
            ("自動修復功能測試", self.test_auto_repair_stats),
            ("數據持久化測試", self.test_data_persistence),
            ("錯誤處理測試", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"測試異常: {e}")
        
        print("\n" + "=" * 60)
        print("測試總結")
        print("=" * 60)
        print(f"總測試數: {total}")
        print(f"通過測試: {passed}")
        print(f"失敗測試: {total - passed}")
        print(f"成功率: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 所有測試通過！系統功能完全正常")
            status = "PASS"
        elif passed >= total * 0.8:
            print("\n✅ 大部分測試通過，系統基本功能正常")
            status = "MOSTLY_PASS"
        else:
            print("\n⚠️ 多項測試失敗，系統存在問題需要修復")
            status = "FAIL"
        
        # 生成測試報告
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': (passed/total)*100,
            'status': status,
            'test_results': self.test_results
        }
        
        with open('/home/ubuntu/popmart_monitor_v2/test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n詳細測試報告已保存至: test_report.json")
        
        return passed == total

def main():
    """主函數"""
    tester = PopMartSystemTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())

