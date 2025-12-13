"""
============================================
test_tags.py - 標籤功能測試
============================================

【運行測試】
cd backend
pytest tests/test_tags.py -v
"""

import pytest


class TestCreateTag:
    """建立標籤測試"""
    
    def test_create_tag_success(self, client, auth_headers):
        """測試正常建立標籤"""
        # 建立專案
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        # 建立標籤
        response = client.post(f'/projects/{project_id}/tags',
            headers=auth_headers,
            json={
                'name': 'bug',
                'color': '#ef4444'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['tag']['name'] == 'bug'
        assert data['tag']['color'] == '#ef4444'
    
    def test_create_tag_default_color(self, client, auth_headers):
        """測試使用預設顏色建立標籤"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        response = client.post(f'/projects/{project_id}/tags',
            headers=auth_headers,
            json={'name': 'feature'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['tag']['color'] == '#667eea'  # 預設顏色
    
    def test_create_duplicate_tag(self, client, auth_headers):
        """測試重複標籤名稱"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        # 建立第一個標籤
        client.post(f'/projects/{project_id}/tags',
            headers=auth_headers,
            json={'name': 'bug'}
        )
        
        # 嘗試建立同名標籤
        response = client.post(f'/projects/{project_id}/tags',
            headers=auth_headers,
            json={'name': 'bug'}
        )
        
        assert response.status_code == 409


class TestGetTags:
    """取得標籤測試"""
    
    def test_get_project_tags(self, client, auth_headers):
        """測試取得專案標籤列表"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        # 建立多個標籤
        for name in ['bug', 'feature', 'urgent']:
            client.post(f'/projects/{project_id}/tags',
                headers=auth_headers,
                json={'name': name}
            )
        
        response = client.get(f'/projects/{project_id}/tags', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['tags']) == 3
        assert 'default_colors' in data


class TestTagTaskOperations:
    """任務標籤操作測試"""
    
    def test_add_tag_to_task(self, client, auth_headers):
        """測試為任務添加標籤"""
        # 建立專案
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        # 建立標籤
        tag_response = client.post(f'/projects/{project_id}/tags',
            headers=auth_headers,
            json={'name': 'bug'}
        )
        tag_id = tag_response.get_json()['tag']['id']
        
        # 建立任務
        task_response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={'title': 'Test Task'}
        )
        task_id = task_response.get_json()['task']['id']
        
        # 添加標籤到任務
        response = client.post(f'/tasks/{task_id}/tags',
            headers=auth_headers,
            json={'tag_id': tag_id}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['all_tags']) == 1
    
    def test_add_multiple_tags(self, client, auth_headers):
        """測試添加多個標籤"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        # 建立多個標籤
        tag_ids = []
        for name in ['bug', 'urgent']:
            tag_response = client.post(f'/projects/{project_id}/tags',
                headers=auth_headers,
                json={'name': name}
            )
            tag_ids.append(tag_response.get_json()['tag']['id'])
        
        # 建立任務
        task_response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={'title': 'Test Task'}
        )
        task_id = task_response.get_json()['task']['id']
        
        # 添加多個標籤
        response = client.post(f'/tasks/{task_id}/tags',
            headers=auth_headers,
            json={'tag_ids': tag_ids}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['all_tags']) == 2
    
    def test_remove_tag_from_task(self, client, auth_headers):
        """測試從任務移除標籤"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        # 建立標籤
        tag_response = client.post(f'/projects/{project_id}/tags',
            headers=auth_headers,
            json={'name': 'bug'}
        )
        tag_id = tag_response.get_json()['tag']['id']
        
        # 建立任務
        task_response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={'title': 'Test Task'}
        )
        task_id = task_response.get_json()['task']['id']
        
        # 添加標籤
        client.post(f'/tasks/{task_id}/tags',
            headers=auth_headers,
            json={'tag_id': tag_id}
        )
        
        # 移除標籤
        response = client.delete(f'/tasks/{task_id}/tags/{tag_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['remaining_tags']) == 0


class TestUpdateDeleteTag:
    """更新和刪除標籤測試"""
    
    def test_update_tag(self, client, auth_headers):
        """測試更新標籤"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        tag_response = client.post(f'/projects/{project_id}/tags',
            headers=auth_headers,
            json={'name': 'bug'}
        )
        tag_id = tag_response.get_json()['tag']['id']
        
        response = client.patch(f'/tags/{tag_id}',
            headers=auth_headers,
            json={'name': 'critical', 'color': '#dc2626'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['tag']['name'] == 'critical'
        assert data['tag']['color'] == '#dc2626'
    
    def test_delete_tag(self, client, auth_headers):
        """測試刪除標籤"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        tag_response = client.post(f'/projects/{project_id}/tags',
            headers=auth_headers,
            json={'name': 'bug'}
        )
        tag_id = tag_response.get_json()['tag']['id']
        
        response = client.delete(f'/tags/{tag_id}', headers=auth_headers)
        
        assert response.status_code == 200

