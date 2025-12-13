"""
============================================
test_tasks.py - 任務功能測試
============================================

【運行測試】
cd backend
pytest tests/test_tasks.py -v
"""

import pytest


class TestCreateTask:
    """建立任務測試"""
    
    def test_create_task_success(self, client, auth_headers):
        """測試正常建立任務"""
        # 先建立專案
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        # 建立任務
        response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={
                'title': 'Test Task',
                'description': 'This is a test task',
                'priority': 'high',
                'status': 'todo'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['task']['title'] == 'Test Task'
    
    def test_create_task_with_assignee(self, client, auth_headers):
        """測試建立任務並指派負責人"""
        # 建立專案
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        # 取得當前用戶 ID
        me_response = client.get('/me', headers=auth_headers)
        user_id = me_response.get_json()['user']['id']
        
        # 建立任務並指派
        response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={
                'title': 'Assigned Task',
                'assigned_to': user_id
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['task']['assignee_id'] == user_id
    
    def test_create_task_missing_title(self, client, auth_headers):
        """測試缺少標題"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={'description': 'No title'}
        )
        
        assert response.status_code == 400


class TestGetTasks:
    """取得任務測試"""
    
    def test_get_project_tasks(self, client, auth_headers):
        """測試取得專案任務列表"""
        # 建立專案
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        # 建立多個任務
        for i in range(3):
            client.post(f'/projects/{project_id}/tasks',
                headers=auth_headers,
                json={'title': f'Task {i+1}'}
            )
        
        # 取得任務列表
        response = client.get(f'/projects/{project_id}/tasks', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['tasks']) == 3
    
    def test_get_my_tasks(self, client, auth_headers):
        """測試取得我的任務"""
        # 建立專案和任務
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        me_response = client.get('/me', headers=auth_headers)
        user_id = me_response.get_json()['user']['id']
        
        # 建立指派給自己的任務
        client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={'title': 'My Task', 'assigned_to': user_id}
        )
        
        # 取得我的任務
        response = client.get('/tasks/my', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['tasks']) >= 1


class TestUpdateTask:
    """更新任務測試"""
    
    def test_update_task_status(self, client, auth_headers):
        """測試更新任務狀態"""
        # 建立專案和任務
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        task_response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={'title': 'Test Task'}
        )
        task_id = task_response.get_json()['task']['id']
        
        # 更新狀態
        response = client.patch(f'/tasks/{task_id}',
            headers=auth_headers,
            json={'status': 'in_progress'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['task']['status'] == 'in_progress'
    
    def test_update_task_priority(self, client, auth_headers):
        """測試更新任務優先級"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        task_response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={'title': 'Test Task', 'priority': 'low'}
        )
        task_id = task_response.get_json()['task']['id']
        
        response = client.patch(f'/tasks/{task_id}',
            headers=auth_headers,
            json={'priority': 'high'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['task']['priority'] == 'high'


class TestDeleteTask:
    """刪除任務測試"""
    
    def test_delete_task_success(self, client, auth_headers):
        """測試正常刪除任務"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        task_response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={'title': 'To Delete'}
        )
        task_id = task_response.get_json()['task']['id']
        
        response = client.delete(f'/tasks/{task_id}', headers=auth_headers)
        
        assert response.status_code == 200


class TestTaskComments:
    """任務評論測試"""
    
    def test_add_comment(self, client, auth_headers):
        """測試新增評論"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        task_response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={'title': 'Test Task'}
        )
        task_id = task_response.get_json()['task']['id']
        
        response = client.post(f'/tasks/{task_id}/comments',
            headers=auth_headers,
            json={'content': 'This is a comment'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['comment']['content'] == 'This is a comment'
    
    def test_get_comments(self, client, auth_headers):
        """測試取得評論列表"""
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        task_response = client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={'title': 'Test Task'}
        )
        task_id = task_response.get_json()['task']['id']
        
        # 新增評論
        client.post(f'/tasks/{task_id}/comments',
            headers=auth_headers,
            json={'content': 'Comment 1'}
        )
        client.post(f'/tasks/{task_id}/comments',
            headers=auth_headers,
            json={'content': 'Comment 2'}
        )
        
        response = client.get(f'/tasks/{task_id}/comments', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['comments']) == 2

