"""
============================================
test_auth.py - 認證功能測試
============================================

【這個檔案的作用】
測試使用者註冊、登入、登出等認證相關的 API。

【運行測試】
cd backend
pytest tests/test_auth.py -v

【測試命名規則】
- test_<功能>_<預期行為>
- 例如：test_register_success（測試註冊成功）
"""

import pytest


class TestRegister:
    """註冊功能測試"""
    
    def test_register_success(self, client):
        """測試正常註冊流程"""
        response = client.post('/auth/register', json={
            'email': 'new@example.com',
            'username': 'New User',
            'password': 'password123',
            'department': 'Engineering'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'user' in data
        assert data['user']['email'] == 'new@example.com'
    
    # auth.py把admin移除都改成member
    # def test_register_first_user_is_admin(self, client):
    #     """測試第一個註冊的使用者自動成為管理員"""
    #     # 註冊第一個使用者
    #     response = client.post('/auth/register', json={
    #         'email': 'admin@example.com',
    #         'username': 'Admin',
    #         'password': 'password123'
    #     })
    #     assert response.status_code == 201
        
    #     # 登入並檢查角色
    #     response = client.post('/auth/login', json={
    #         'email': 'admin@example.com',
    #         'password': 'password123'
    #     })
    #     data = response.get_json()
    #     assert data['user']['role'] == 'admin'
    
    # def test_register_second_user_is_member(self, client):
    #     """測試第二個註冊的使用者是一般成員"""
    #     # 註冊第一個使用者（管理員）
    #     client.post('/auth/register', json={
    #         'email': 'admin@example.com',
    #         'username': 'Admin',
    #         'password': 'password123'
    #     })
        
    #     # 註冊第二個使用者
    #     client.post('/auth/register', json={
    #         'email': 'member@example.com',
    #         'username': 'Member',
    #         'password': 'password123'
    #     })
        
    #     # 登入第二個使用者並檢查角色
    #     response = client.post('/auth/login', json={
    #         'email': 'member@example.com',
    #         'password': 'password123'
    #     })
    #     data = response.get_json()
    #     assert data['user']['role'] == 'member'
    
    def test_register_duplicate_email(self, client):
        """測試重複 email 註冊失敗"""
        # 先註冊一個使用者
        client.post('/auth/register', json={
            'email': 'test@example.com',
            'username': 'Test',
            'password': 'password123'
        })
        
        # 用相同 email 再註冊一次
        response = client.post('/auth/register', json={
            'email': 'test@example.com',
            'username': 'Another',
            'password': 'password456'
        })
        
        assert response.status_code == 409
    
    def test_register_missing_fields(self, client):
        """測試缺少必填欄位"""
        response = client.post('/auth/register', json={
            'email': 'test@example.com'
            # 缺少 username 和 password
        })
        
        assert response.status_code == 400
    
    def test_register_invalid_email(self, client):
        """測試無效的 email 格式"""
        response = client.post('/auth/register', json={
            'email': 'not-an-email',
            'username': 'Test',
            'password': 'password123'
        })
        
        assert response.status_code == 400


class TestLogin:
    """登入功能測試"""
    
    def test_login_success(self, client):
        """測試正常登入流程"""
        # 先註冊
        client.post('/auth/register', json={
            'email': 'test@example.com',
            'username': 'Test',
            'password': 'password123'
        })
        
        # 登入
        response = client.post('/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data
    
    def test_login_wrong_password(self, client):
        """測試錯誤密碼"""
        # 先註冊
        client.post('/auth/register', json={
            'email': 'test@example.com',
            'username': 'Test',
            'password': 'password123'
        })
        
        # 用錯誤密碼登入
        response = client.post('/auth/login', json={
            'email': 'test@example.com',
            'password': 'wrong-password'
        })
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """測試不存在的使用者"""
        response = client.post('/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 401


class TestProtectedRoutes:
    """受保護路由測試"""
    
    def test_access_without_token(self, client):
        """測試未帶 token 存取受保護路由"""
        response = client.get('/auth/me')
        assert response.status_code == 401
    
    def test_access_with_valid_token(self, client, auth_headers):
        """測試帶有效 token 存取受保護路由"""
        response = client.get('/auth/me', headers=auth_headers)
        assert response.status_code == 200
    
    def test_access_with_invalid_token(self, client):
        """測試帶無效 token 存取受保護路由"""
        headers = {'Authorization': 'Bearer invalid-token'}
        response = client.get('/auth/me', headers=headers)
        assert response.status_code == 422  # JWT decode error


class TestRefreshToken:
    """Token 刷新測試"""
    
    def test_refresh_token_success(self, client):
        """測試刷新 token"""
        # 註冊並登入
        client.post('/auth/register', json={
            'email': 'test@example.com',
            'username': 'Test',
            'password': 'password123'
        })
        
        response = client.post('/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        refresh_token = response.get_json()['refresh_token']
        
        # 使用 refresh token 換新的 access token
        response = client.post('/auth/refresh', headers={
            'Authorization': f'Bearer {refresh_token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data


class TestAccountLockout:
    """帳號鎖定功能測試"""
    
    def test_account_locks_after_failed_attempts(self, client):
        """測試登入失敗 5 次後帳號被鎖定"""
        # 先註冊
        client.post('/auth/register', json={
            'email': 'test@example.com',
            'username': 'Test',
            'password': 'password123'
        })
        
        # 連續登入失敗 5 次
        for i in range(5):
            client.post('/auth/login', json={
                'email': 'test@example.com',
                'password': 'wrong-password'
            })
        
        # 第 6 次應該收到帳號鎖定訊息
        response = client.post('/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'  # 即使密碼正確也應該被鎖定
        })
        
        assert response.status_code == 429
        data = response.get_json()
        assert 'locked' in data


class TestForgotPassword:
    """忘記密碼功能測試"""
    
    def test_forgot_password_returns_success_for_existing_email(self, client):
        """測試忘記密碼 API 對存在的 email 回傳成功"""
        # 先註冊
        client.post('/auth/register', json={
            'email': 'test@example.com',
            'username': 'Test',
            'password': 'password123'
        })
        
        response = client.post('/auth/forgot-password', json={
            'email': 'test@example.com'
        })
        
        assert response.status_code == 200
    
    def test_forgot_password_returns_success_for_nonexistent_email(self, client):
        """測試忘記密碼 API 對不存在的 email 也回傳成功（防止帳號枚舉）"""
        response = client.post('/auth/forgot-password', json={
            'email': 'nonexistent@example.com'
        })
        
        assert response.status_code == 200

