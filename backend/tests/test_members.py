"""
============================================
test_members.py - 成員功能測試
============================================

【運行測試】
cd backend
pytest tests/test_members.py -v
"""

import pytest


class TestGetMembers:
    """取得成員測試"""
    
    def test_get_all_members(self, client, auth_headers):
        """測試取得所有成員"""
        response = client.get('/members', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'members' in data
        assert len(data['members']) >= 1  # 至少有當前用戶
    
    def test_get_members_with_search(self, client, auth_headers):
        """測試搜尋成員"""
        response = client.get('/members?search=test', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'members' in data
    
    def test_get_single_member(self, client, auth_headers):
        """測試取得單一成員資訊"""
        # 取得成員列表
        members_response = client.get('/members', headers=auth_headers)
        members = members_response.get_json()['members']
        
        if members:
            member_id = members[0]['id']
            response = client.get(f'/members/{member_id}', headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['id'] == member_id
    
    def test_get_nonexistent_member(self, client, auth_headers):
        """測試取得不存在的成員"""
        response = client.get('/members/99999', headers=auth_headers)
        
        assert response.status_code == 404


class TestMemberRole:
    """成員角色測試"""
    
    def test_first_user_is_admin(self, client):
        """測試第一個用戶是管理員"""
        # 註冊第一個用戶
        client.post('/register', json={
            'email': 'first@example.com',
            'username': 'First User',
            'password': 'password123'
        })
        
        # 登入
        login_response = client.post('/login', json={
            'email': 'first@example.com',
            'password': 'password123'
        })
        
        data = login_response.get_json()
        assert data['user']['role'] == 'admin'
    
    def test_second_user_is_member(self, client):
        """測試第二個用戶是普通成員"""
        # 註冊第一個用戶（會是 admin）
        client.post('/register', json={
            'email': 'first@example.com',
            'username': 'First User',
            'password': 'password123'
        })
        
        # 註冊第二個用戶
        client.post('/register', json={
            'email': 'second@example.com',
            'username': 'Second User',
            'password': 'password123'
        })
        
        # 登入第二個用戶
        login_response = client.post('/login', json={
            'email': 'second@example.com',
            'password': 'password123'
        })
        
        data = login_response.get_json()
        assert data['user']['role'] == 'member'

