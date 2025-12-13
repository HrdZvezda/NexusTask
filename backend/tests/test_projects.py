"""
============================================
test_projects.py - 專案功能測試
============================================

【這個檔案的作用】
測試專案的 CRUD（建立、讀取、更新、刪除）操作。

【運行測試】
cd backend
pytest tests/test_projects.py -v
"""

import pytest


class TestCreateProject:
    """建立專案測試"""
    
    def test_create_project_success(self, client, auth_headers):
        """測試正常建立專案"""
        response = client.post('/projects', 
            headers=auth_headers,
            json={
                'name': 'Test Project',
                'description': 'A test project',
                'status': 'active'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['project']['name'] == 'Test Project'
    
    def test_create_project_without_auth(self, client):
        """測試未登入建立專案"""
        response = client.post('/projects', json={
            'name': 'Test Project'
        })
        
        assert response.status_code == 401
    
    def test_create_project_missing_name(self, client, auth_headers):
        """測試缺少專案名稱"""
        response = client.post('/projects',
            headers=auth_headers,
            json={
                'description': 'A project without name'
            }
        )
        
        assert response.status_code == 400


class TestGetProjects:
    """讀取專案測試"""
    
    def test_get_projects_empty(self, client, auth_headers):
        """測試沒有專案時的回應"""
        response = client.get('/projects', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'projects' in data
        assert len(data['projects']) == 0
    
    def test_get_projects_with_data(self, client, auth_headers):
        """測試有專案時的回應"""
        # 先建立專案
        client.post('/projects',
            headers=auth_headers,
            json={'name': 'Project 1'}
        )
        client.post('/projects',
            headers=auth_headers,
            json={'name': 'Project 2'}
        )
        
        # 取得專案列表
        response = client.get('/projects', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['projects']) == 2
    
    def test_get_project_by_id(self, client, auth_headers):
        """測試根據 ID 取得專案"""
        # 先建立專案
        create_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'My Project'}
        )
        project_id = create_response.get_json()['project']['id']
        
        # 取得該專案
        response = client.get(f'/projects/{project_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['project']['name'] == 'My Project'
    
    def test_get_nonexistent_project(self, client, auth_headers):
        """測試取得不存在的專案"""
        response = client.get('/projects/99999', headers=auth_headers)
        
        assert response.status_code == 404


class TestUpdateProject:
    """更新專案測試"""
    
    def test_update_project_success(self, client, auth_headers):
        """測試正常更新專案"""
        # 先建立專案
        create_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Original Name'}
        )
        project_id = create_response.get_json()['project']['id']
        
        # 更新專案
        response = client.patch(f'/projects/{project_id}',
            headers=auth_headers,
            json={'name': 'Updated Name'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['project']['name'] == 'Updated Name'


class TestDeleteProject:
    """刪除專案測試"""
    
    def test_delete_project_success(self, client, auth_headers):
        """測試正常刪除專案"""
        # 先建立專案
        create_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'To Delete'}
        )
        project_id = create_response.get_json()['project']['id']
        
        # 刪除專案
        response = client.delete(f'/projects/{project_id}', headers=auth_headers)
        
        assert response.status_code == 200
        
        # 確認已刪除
        get_response = client.get(f'/projects/{project_id}', headers=auth_headers)
        assert get_response.status_code == 404

