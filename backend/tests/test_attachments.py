"""
============================================
test_attachments.py - 附件功能測試
============================================

【運行測試】
cd backend
pytest tests/test_attachments.py -v
"""

import pytest
import io


class TestUploadAttachment:
    """上傳附件測試"""
    
    def test_upload_attachment_success(self, client, auth_headers):
        """測試正常上傳附件"""
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
        
        # 建立測試檔案
        data = {
            'file': (io.BytesIO(b'test file content'), 'test.txt')
        }
        
        response = client.post(
            f'/tasks/{task_id}/attachments',
            headers=auth_headers,
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 201
        result = response.get_json()
        assert 'attachment' in result
        assert result['attachment']['original_filename'] == 'test.txt'
    
    def test_upload_invalid_file_type(self, client, auth_headers):
        """測試上傳不允許的檔案類型"""
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
        
        # 建立不允許的檔案類型
        data = {
            'file': (io.BytesIO(b'fake executable'), 'test.exe')
        }
        
        response = client.post(
            f'/tasks/{task_id}/attachments',
            headers=auth_headers,
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
    
    def test_upload_no_file(self, client, auth_headers):
        """測試未提供檔案"""
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
        
        response = client.post(
            f'/tasks/{task_id}/attachments',
            headers=auth_headers,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400


class TestGetAttachments:
    """取得附件測試"""
    
    def test_get_task_attachments(self, client, auth_headers):
        """測試取得任務附件列表"""
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
        
        # 上傳附件
        data = {
            'file': (io.BytesIO(b'test file'), 'test1.txt')
        }
        client.post(
            f'/tasks/{task_id}/attachments',
            headers=auth_headers,
            data=data,
            content_type='multipart/form-data'
        )
        
        # 取得附件列表
        response = client.get(f'/tasks/{task_id}/attachments', headers=auth_headers)
        
        assert response.status_code == 200
        result = response.get_json()
        assert len(result['attachments']) == 1


class TestDeleteAttachment:
    """刪除附件測試"""
    
    def test_delete_own_attachment(self, client, auth_headers):
        """測試刪除自己上傳的附件"""
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
        
        # 上傳附件
        data = {
            'file': (io.BytesIO(b'test file'), 'test.txt')
        }
        upload_response = client.post(
            f'/tasks/{task_id}/attachments',
            headers=auth_headers,
            data=data,
            content_type='multipart/form-data'
        )
        attachment_id = upload_response.get_json()['attachment']['id']
        
        # 刪除附件
        response = client.delete(f'/attachments/{attachment_id}', headers=auth_headers)
        
        assert response.status_code == 200

