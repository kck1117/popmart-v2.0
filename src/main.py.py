import os
import sys
import logging
import asyncio
from flask import Flask, send_from_directory, g
from flask_cors import CORS

# DON\'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.product import db
from src.services.popmart_api_client import PopmartAPIClient
# 延遲導入 MonitorService, NotificationService, AutoRepairService, Scheduler
# 避免循環導入問題

# 配置日誌
logging.basicConfig(level=logging.INFO, format=\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\')
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), \'static\'))
    
    # 啟用CORS
    CORS(app)
    
    # 配置密鑰
    app.config[\'SECRET_KEY\'] = \'popmart_monitor_secret_key\'

    # 配置數據庫
    app.config[\'SQLALCHEMY_DATABASE_URI\'] = f\"sqlite:///{os.path.join(os.path.dirname(__file__), \'database\', \'popmart_data.db\')}\"
    app.config[\'SQLALCHEMY_TRACK_MODIFICATIONS\'] = False
    db.init_app(app)
    
    # 創建數據庫表
    with app.app_context():
        db.create_all()
        logger.info(\"數據庫表已創建或已存在。\")

    # 初始化 PopmartAPIClient
    api_client = PopmartAPIClient(region=\"hk\")
    
    # 通知服務配置
    notification_config = {
        \'telegram\': {
            \'enabled\': False,  # 預設關閉，需要用戶配置
            \'bot_token\': \'\',
            \'chat_id\': \'\'
        },
        \'discord\': {
            \'enabled\': False,  # 預設關閉，需要用戶配置
            \'webhook_url\': \'\'
        }
    }
    
    # 自動修復服務配置
    auto_repair_config = {
        \'enabled\': True,
        \'min_interval\': 30,
        \'max_interval\': 300,
        \'max_errors\': 5,
        \'recovery_time\': 3600,
        \'proxy_list\': []
    }
    
    # 啟動API客戶端會話
    @app.before_request
    def ensure_api_client_session():
        if not hasattr(g, \'api_client_session_started\'):
            # 在第一個請求前啟動會話
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(api_client.start_session())
                g.api_client_session_started = True
                logger.info(\"API客戶端會話已啟動\")
            except Exception as e:
                logger.error(f\"啟動API客戶端會話失敗: {e}\")
            finally:
                loop.close()
    
    # 延遲導入 MonitorService 和 Scheduler
    from src.services.monitor import MonitorService
    from src.services.scheduler import Scheduler

    # 初始化 MonitorService 和 Scheduler
    monitor_service = MonitorService(api_client, notification_config, auto_repair_config)
    scheduler = Scheduler(monitor_service)

    # 將服務實例注入到 Flask app
    app.api_client = api_client
    app.monitor_service = monitor_service
    app.scheduler = scheduler

    # 註冊藍圖 (將藍圖註冊放在靜態文件服務之前)
    from src.routes.monitor import monitor_bp
    from src.routes.notification import notification_bp
    app.register_blueprint(monitor_bp, url_prefix=\'/api\')
    app.register_blueprint(notification_bp, url_prefix=\'/api\')

    @app.route(\'/\', defaults={\'path\': \'\'}) # 將此路由放在藍圖註冊之後
    @app.route(\'/<path:path>\')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return \"Static folder not configured\", 404

        if path != \"\" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, \'index.html\')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, \'index.html\')
            else:
                return \"index.html not found\", 404
    
    # 在應用關閉時清理資源
    @app.teardown_appcontext
    def cleanup_resources(exception=None):
        # 這裡不能使用異步函數，因為teardown_appcontext不支持異步
        # 我們將在應用關閉時處理資源清理
        pass
    
    return app
    app = create_app()

if __name__ == \'__main__\':
    
    # 註冊關閉處理程序
    import atexit
    
    @atexit.register
    def cleanup_on_exit():
        # 在應用退出時清理資源
        if hasattr(app, \'scheduler\') and app.scheduler.is_running():
            app.scheduler.stop()
            logger.info(\"排程器已停止\")
        
        # 關閉API客戶端會話
        if hasattr(app, \'api_client\'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(app.api_client.close_session())
                logger.info(\"API客戶端會話已關閉\")
            except Exception as e:
                logger.error(f\"關閉API客戶端會話失敗: {e}\")
            finally:
                loop.close()
    
    app.run(host=\'0.0.0.0\', port=5000, debug=True)


