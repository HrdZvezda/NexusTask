"""
============================================
tags.py - 標籤管理 API
============================================

【這個檔案的作用】
處理任務標籤的建立、管理和使用。

【API 端點】
- GET    /projects/<project_id>/tags     : 取得專案的所有標籤
- POST   /projects/<project_id>/tags     : 建立新標籤
- PATCH  /tags/<id>                      : 更新標籤
- DELETE /tags/<id>                      : 刪除標籤
- POST   /tasks/<task_id>/tags           : 為任務添加標籤
- DELETE /tasks/<task_id>/tags/<tag_id>  : 移除任務的標籤

【標籤顏色建議】
提供一組預設顏色供使用者選擇：
- 紅色: #ef4444 (緊急)
- 橙色: #f97316 (重要)
- 黃色: #eab308 (注意)
- 綠色: #22c55e (完成)
- 藍色: #3b82f6 (進行中)
- 紫色: #8b5cf6 (功能)
- 粉色: #ec4899 (設計)
- 灰色: #6b7280 (其他)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, validate
import logging

# 從父目錄導入
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, Tag, Task, Project, task_tags
from api.auth import get_current_user
from api.projects import check_project_access

# ============================================
# 設定
# ============================================

tags_bp = Blueprint('tags', __name__)
logger = logging.getLogger(__name__)

# 預設標籤顏色選項
DEFAULT_COLORS = [
    '#ef4444',  # 紅色
    '#f97316',  # 橙色
    '#eab308',  # 黃色
    '#22c55e',  # 綠色
    '#3b82f6',  # 藍色
    '#8b5cf6',  # 紫色
    '#ec4899',  # 粉色
    '#6b7280',  # 灰色
    '#14b8a6',  # 青色
    '#f43f5e',  # 玫瑰色
]


# ============================================
# 驗證 Schema
# ============================================

class CreateTagSchema(Schema):
    """建立標籤的驗證"""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'), missing='#667eea')


class UpdateTagSchema(Schema):
    """更新標籤的驗證"""
    name = fields.Str(validate=validate.Length(min=1, max=50))
    color = fields.Str(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'))


def validate_request_data(schema_class, data):
    """驗證請求資料"""
    schema = schema_class()
    errors = schema.validate(data)
    if errors:
        return False, errors
    return True, schema.load(data)


# ============================================
# GET /projects/<project_id>/tags - 取得專案標籤
# ============================================

@tags_bp.route('/projects/<int:project_id>/tags', methods=['GET'])
@jwt_required()
def get_project_tags(project_id):
    """
    取得專案的所有標籤
    
    【回應格式】
    {
        "tags": [
            {
                "id": 1,
                "name": "bug",
                "color": "#ef4444",
                "task_count": 5
            },
            ...
        ],
        "default_colors": ["#ef4444", ...]
    }
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    # 檢查專案存取權限
    has_access, project, role = check_project_access(project_id, current_user.id)
    if not has_access:
        return jsonify({'error': 'Permission denied'}), 403
    
    # 取得標籤並計算每個標籤的任務數量
    tags = Tag.query.filter_by(project_id=project_id).all()
    
    tags_list = []
    for tag in tags:
        # 計算使用此標籤的任務數量
        task_count = db.session.query(task_tags).filter_by(tag_id=tag.id).count()
        tags_list.append({
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
            'task_count': task_count
        })
    
    return jsonify({
        'tags': tags_list,
        'default_colors': DEFAULT_COLORS
    }), 200


# ============================================
# POST /projects/<project_id>/tags - 建立標籤
# ============================================

@tags_bp.route('/projects/<int:project_id>/tags', methods=['POST'])
@jwt_required()
def create_tag(project_id):
    """
    建立新標籤
    
    【請求格式】
    {
        "name": "bug",
        "color": "#ef4444"
    }
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    # 檢查專案存取權限
    has_access, project, role = check_project_access(project_id, current_user.id)
    if not has_access:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    # 驗證輸入
    is_valid, result = validate_request_data(CreateTagSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    # 檢查標籤名稱是否已存在
    existing = Tag.query.filter_by(project_id=project_id, name=result['name']).first()
    if existing:
        return jsonify({'error': 'Tag name already exists in this project'}), 409
    
    try:
        tag = Tag(
            name=result['name'],
            color=result.get('color', '#667eea'),
            project_id=project_id
        )
        db.session.add(tag)
        db.session.commit()
        
        logger.info(f"Tag created: {tag.name} in project {project_id} by user {current_user.id}")
        
        return jsonify({
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'task_count': 0
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create tag error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to create tag'}), 500


# ============================================
# PATCH /tags/<id> - 更新標籤
# ============================================

@tags_bp.route('/tags/<int:tag_id>', methods=['PATCH'])
@jwt_required()
def update_tag(tag_id):
    """
    更新標籤
    
    【請求格式】
    {
        "name": "新名稱",
        "color": "#3b82f6"
    }
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    # 檢查專案存取權限
    has_access, project, role = check_project_access(tag.project_id, current_user.id)
    if not has_access:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    # 驗證輸入
    is_valid, result = validate_request_data(UpdateTagSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    try:
        # 如果要改名稱，檢查是否衝突
        if 'name' in result and result['name'] != tag.name:
            existing = Tag.query.filter_by(
                project_id=tag.project_id, 
                name=result['name']
            ).first()
            if existing:
                return jsonify({'error': 'Tag name already exists'}), 409
            tag.name = result['name']
        
        if 'color' in result:
            tag.color = result['color']
        
        db.session.commit()
        
        task_count = db.session.query(task_tags).filter_by(tag_id=tag.id).count()
        
        return jsonify({
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'task_count': task_count
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update tag error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to update tag'}), 500


# ============================================
# DELETE /tags/<id> - 刪除標籤
# ============================================

@tags_bp.route('/tags/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def delete_tag(tag_id):
    """
    刪除標籤（同時會從所有任務移除此標籤）
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    # 檢查專案存取權限
    has_access, project, role = check_project_access(tag.project_id, current_user.id)
    if not has_access:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        db.session.delete(tag)
        db.session.commit()
        
        logger.info(f"Tag deleted: {tag.name} by user {current_user.id}")
        
        return jsonify({'message': 'Tag deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete tag error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to delete tag'}), 500


# ============================================
# POST /tasks/<task_id>/tags - 為任務添加標籤
# ============================================

@tags_bp.route('/tasks/<int:task_id>/tags', methods=['POST'])
@jwt_required()
def add_tag_to_task(task_id):
    """
    為任務添加標籤
    
    【請求格式】
    {
        "tag_id": 1
    }
    或
    {
        "tag_ids": [1, 2, 3]
    }
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # 檢查專案存取權限
    has_access, project, role = check_project_access(task.project_id, current_user.id)
    if not has_access:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    # 支援單個或多個標籤
    tag_ids = data.get('tag_ids') or [data.get('tag_id')]
    if not tag_ids or tag_ids[0] is None:
        return jsonify({'error': 'tag_id or tag_ids required'}), 400
    
    try:
        added_tags = []
        for tag_id in tag_ids:
            tag = Tag.query.get(tag_id)
            if not tag:
                continue
            
            # 確保標籤屬於同一專案
            if tag.project_id != task.project_id:
                continue
            
            # 檢查是否已經添加
            if tag not in task.tags:
                task.tags.append(tag)
                added_tags.append({
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color
                })
        
        db.session.commit()
        
        return jsonify({
            'message': 'Tags added successfully',
            'added_tags': added_tags,
            'all_tags': [{
                'id': t.id,
                'name': t.name,
                'color': t.color
            } for t in task.tags]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Add tag error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to add tags'}), 500


# ============================================
# DELETE /tasks/<task_id>/tags/<tag_id> - 移除任務標籤
# ============================================

@tags_bp.route('/tasks/<int:task_id>/tags/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def remove_tag_from_task(task_id, tag_id):
    """
    從任務移除標籤
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # 檢查專案存取權限
    has_access, project, role = check_project_access(task.project_id, current_user.id)
    if not has_access:
        return jsonify({'error': 'Permission denied'}), 403
    
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404
    
    try:
        if tag in task.tags:
            task.tags.remove(tag)
            db.session.commit()
        
        return jsonify({
            'message': 'Tag removed successfully',
            'remaining_tags': [{
                'id': t.id,
                'name': t.name,
                'color': t.color
            } for t in task.tags]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Remove tag error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to remove tag'}), 500


# ============================================
# GET /tasks/<task_id>/tags - 取得任務的標籤
# ============================================

@tags_bp.route('/tasks/<int:task_id>/tags', methods=['GET'])
@jwt_required()
def get_task_tags(task_id):
    """
    取得任務的所有標籤
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'tags': [{
            'id': t.id,
            'name': t.name,
            'color': t.color
        } for t in task.tags]
    }), 200

