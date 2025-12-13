"""
============================================
conftest.py - Pytest 測試設定
============================================

【這個檔案的作用】
定義 pytest 的共用設定和 fixtures。
Fixtures 是測試中可重複使用的「預設資料」或「測試環境」。

【什麼是 Fixture？】
Fixture 就像是測試的「準備工作」。
例如：每次測試前都需要一個乾淨的資料庫、一個已登入的使用者等。
Fixture 會在每次測試前自動執行，確保測試環境一致。

【使用方式】
運行測試：cd backend && pytest
運行特定測試：pytest tests/test_auth.py
顯示詳細輸出：pytest -v
"""

import pytest
import sys
import os

# 確保可以導入 backend 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from models import db, User


def create_test_app(config=None):
    """建立測試用的 Flask 應用程式"""
    test_app = Flask(__name__)
    
    # 測試設定
    test_app.config['TESTING'] = True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    test_app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    test_app.config['SECRET_KEY'] = 'test-secret-key'
    test_app.config['WTF_CSRF_ENABLED'] = False
    test_app.config['PASSWORD_MIN_LENGTH'] = 4  # 測試時降低密碼要求
    test_app.config['PASSWORD_REQUIRE_UPPERCASE'] = False
    test_app.config['PASSWORD_REQUIRE_NUMBERS'] = False
    test_app.config['PASSWORD_REQUIRE_SPECIAL'] = False
    
    # 覆蓋自訂設定
    if config:
        test_app.config.update(config)
    
    # 初始化擴展
    db.init_app(test_app)
    jwt = JWTManager(test_app)
    bcrypt = Bcrypt(test_app)
    test_app.extensions['bcrypt'] = bcrypt
    
    # 註冊 blueprints（從 api 模組導入）
    from api import (
        auth_bp,
        projects_bp,
        tasks_bp,
        notifications_bp,
        members_bp,
        uploads_bp,
        tags_bp
    )
    
    test_app.register_blueprint(auth_bp, url_prefix='/auth')
    test_app.register_blueprint(projects_bp, url_prefix='/projects')
    test_app.register_blueprint(tasks_bp)
    test_app.register_blueprint(notifications_bp, url_prefix='/api')
    test_app.register_blueprint(members_bp)
    test_app.register_blueprint(uploads_bp)
    test_app.register_blueprint(tags_bp)
    
    return test_app


@pytest.fixture
def app():
    """
    建立測試用的 Flask 應用程式
    
    這個 fixture 會：
    1. 建立一個使用記憶體資料庫的 Flask app
    2. 建立所有資料表
    3. 測試結束後清理資料庫
    """
    test_app = create_test_app()
    
    # 在 app context 中建立資料表
    with test_app.app_context():
        db.create_all()
    
    yield test_app
    
    # 測試結束後清理
    with test_app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """
    建立測試客戶端
    
    這個客戶端可以用來模擬發送 HTTP 請求到 API。
    例如：client.post('/register', json={...})
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """
    建立 CLI 測試運行器
    
    用於測試 Flask CLI 命令。
    """
    return app.test_cli_runner()


@pytest.fixture
def auth_headers(client):
    """
    建立已認證的 HTTP headers
    
    這個 fixture 會：
    1. 註冊一個測試使用者
    2. 登入取得 JWT token
    3. 回傳包含 token 的 headers
    
    使用範例：
        def test_protected_route(client, auth_headers):
            response = client.get('/projects', headers=auth_headers)
            assert response.status_code == 200
    """
    # 先註冊一個測試使用者（注意：auth blueprint 的 url_prefix 是 /auth）
    client.post('/auth/register', json={
        'email': 'test@example.com',
        'username': 'Test User',
        'password': 'password123',
        'department': 'Engineering'
    })
    
    # 登入取得 token
    response = client.post('/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    data = response.get_json()
    access_token = data['access_token']
    
    return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture
def sample_user(app):
    """
    建立一個範例使用者
    
    直接在資料庫建立，不經過 API。
    用於需要預設使用者的測試。
    """
    from flask_bcrypt import Bcrypt
    
    bcrypt = Bcrypt(app)
    
    with app.app_context():
        user = User(
            email='sample@example.com',
            username='Sample User',
            password_hash=bcrypt.generate_password_hash('password').decode('utf-8'),
            department='QA',
            role='member'
        )
        db.session.add(user)
        db.session.commit()
        
        # 返回使用者 ID（因為 session 會在 context 結束後失效）
        return {'id': user.id, 'email': user.email}

