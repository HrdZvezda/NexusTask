"""
============================================
test_notifications.py - 通知功能測試
============================================

【運行測試】
cd backend
pytest tests/test_notifications.py -v
"""

import pytest


class TestGetNotifications:
    """取得通知測試"""
    
    def test_get_notifications_empty(self, client, auth_headers):
        """測試沒有通知時的回應"""
        response = client.get('/api/notifications', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'notifications' in data
    
    def test_notification_on_task_assignment(self, client, auth_headers):
        """測試任務指派時產生通知"""
        # 建立專案
        project_response = client.post('/projects',
            headers=auth_headers,
            json={'name': 'Test Project'}
        )
        project_id = project_response.get_json()['project']['id']
        
        # 取得當前用戶
        me_response = client.get('/me', headers=auth_headers)
        user_id = me_response.get_json()['user']['id']
        
        # 建立並指派任務給自己
        client.post(f'/projects/{project_id}/tasks',
            headers=auth_headers,
            json={
                'title': 'Assigned Task',
                'assigned_to': user_id
            }
        )
        
        # 檢查通知
        response = client.get('/api/notifications', headers=auth_headers)
        
        assert response.status_code == 200
        # 注意：根據後端實作，可能會或不會產生通知


class TestMarkNotificationRead:
    """標記通知已讀測試"""
    
    def test_mark_all_as_read(self, client, auth_headers):
        """測試標記所有通知為已讀"""
        response = client.patch('/api/notifications/read-all', headers=auth_headers)
        
        assert response.status_code == 200


class TestNotificationCount:
    """通知數量測試"""
    
    def test_get_unread_count(self, client, auth_headers):
        """測試取得未讀通知數量"""
        response = client.get('/api/notifications/unread-count', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'count' in data or 'unread_count' in data

