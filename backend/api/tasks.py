from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, timedelta
import logging

# 從父目錄導入
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, Task, Project, ProjectMember, Notification, ActivityLog, TaskComment
from api.auth import get_current_user

tasks_bp = Blueprint('tasks', __name__)
logger = logging.getLogger(__name__)

# ============================================
# 效能優化：Comments Count Subquery
# ============================================

def get_comments_count_subquery():
    """
    建立 comments_count 的 subquery
    避免 N+1 查詢問題
    """
    return db.session.query(
        TaskComment.task_id,
        func.count(TaskComment.id).label('comments_count')
    ).group_by(TaskComment.task_id).subquery()

def get_task_ids_to_comments_count(task_ids):
    """
    批次取得多個任務的評論數量
    
    Args:
        task_ids: 任務 ID 列表
    
    Returns:
        dict: {task_id: comments_count}
    """
    if not task_ids:
        return {}
    
    counts = db.session.query(
        TaskComment.task_id,
        func.count(TaskComment.id).label('count')
    ).filter(
        TaskComment.task_id.in_(task_ids)
    ).group_by(TaskComment.task_id).all()
    
    return {task_id: count for task_id, count in counts}

# ============================================
# Input Validation Schemas
# ============================================

class CreateTaskSchema(Schema):
    """建立任務驗證"""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255),
        error_messages={'required': 'Task title is required'}
    )
    description = fields.Str(validate=validate.Length(max=5000))
    status = fields.Str(
        validate=validate.OneOf(['todo', 'in_progress', 'review', 'done']),
        missing='todo'
    )
    priority = fields.Str(
        validate=validate.OneOf(['low', 'medium', 'high']),
        missing='medium'
    )
    assigned_to = fields.Int(allow_none=True)
    due_date = fields.Str(allow_none=True)  # 接受日期字串
    estimated_hours = fields.Float(allow_none=True)
    notes = fields.Str(validate=validate.Length(max=10000), allow_none=True)

class UpdateTaskSchema(Schema):
    """更新任務驗證"""
    title = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(validate=validate.Length(max=5000))
    status = fields.Str(validate=validate.OneOf(['todo', 'in_progress', 'review', 'done']))
    priority = fields.Str(validate=validate.OneOf(['low', 'medium', 'high']))
    assigned_to = fields.Int(allow_none=True)
    due_date = fields.Str(allow_none=True)  # 接受日期字串
    estimated_hours = fields.Float(allow_none=True)
    actual_hours = fields.Float(allow_none=True)
    progress = fields.Int(validate=validate.Range(min=0, max=100))
    notes = fields.Str(validate=validate.Length(max=10000), allow_none=True)

# ============================================
# 輔助函數 (改進版)
# ============================================

def check_task_access(task_id, user_id):
    """
    檢查使用者是否有權限訪問任務

    改進點:
    1. 使用 eager loading
    2. 加上錯誤處理
    3. 回傳更多資訊
    4. 使用獨立的 permissions 模組避免循環導入
    """
    try:
        task = Task.query.options(
            joinedload(Task.project)
        ).get(task_id)

        if not task:
            return False, None, None

        # 使用獨立的 permissions 模組檢查專案訪問權限
        from services.permissions import check_project_access
        has_access, project, role = check_project_access(task.project_id, user_id)

        return has_access, task, role

    except Exception as e:
        logger.error(f"Error checking task access: {str(e)}", exc_info=True)
        return False, None, None

def validate_request_data(schema_class, data):
    """
    統一的輸入驗證

    注意：這是本地版本，也可以使用 utils.validators.validate_request_data
    """
    schema = schema_class()
    try:
        validated_data = schema.load(data)
        return True, validated_data
    except ValidationError as err:
        return False, err.messages

def create_task_notification(task, action_type, actor_user, additional_users=None, include_self=False):
    """
    建立任務相關通知的輔助函數
    
    參數:
        task: 任務物件
        action_type: 動作類型 ('assigned', 'completed', 'commented', 'created')
        actor_user: 執行動作的使用者
        additional_users: 額外要通知的使用者 ID 列表
        include_self: 是否也通知操作者自己（預設 False）
    """
    notifications = []
    
    # 通知內容對應
    notification_config = {
        'assigned': {
            'type': 'task_assigned',
            'title': f'{actor_user.username} assigned a task to you',
            'content': f'Task: {task.title}'
        },
        'completed': {
            'type': 'task_completed',
            'title': f'{actor_user.username} completed a task',
            'content': f'Task: {task.title}'
        },
        'commented': {
            'type': 'comment_added',
            'title': f'{actor_user.username} commented on a task',
            'content': f'Task: {task.title}'
        },
        'created': {
            'type': 'task_created',
            'title': f'{actor_user.username} created a new task',
            'content': f'Task: {task.title}'
        }
    }
    
    config = notification_config.get(action_type)
    if not config:
        return notifications
    
    # 要通知的使用者列表
    notify_users = set()
    
    # 如果 include_self 為 True，加入操作者自己
    if include_self:
        notify_users.add(actor_user.id)
    
    # 任務指派者（如果不是操作者本身）
    if task.assigned_to and task.assigned_to != actor_user.id:
        notify_users.add(task.assigned_to)
    
    # 任務建立者（如果不是操作者本身）
    if task.created_by != actor_user.id:
        notify_users.add(task.created_by)
    
    # 額外指定的使用者（排除操作者，除非 include_self）
    if additional_users:
        for uid in additional_users:
            if include_self or uid != actor_user.id:
                notify_users.add(uid)
    
    # 導入 WebSocket 發送函數
    try:
        from core import emit_notification
    except ImportError:
        emit_notification = None
    
    # 建立通知
    for user_id in notify_users:
        notification = Notification(
            user_id=user_id,
            type=config['type'],
            title=config['title'],
            content=config['content'],
            related_project_id=task.project_id,
            related_task_id=task.id
        )
        notifications.append(notification)
        db.session.add(notification)
        
        # 發送即時 WebSocket 通知
        if emit_notification:
            try:
                emit_notification(user_id, {
                    'type': config['type'],
                    'title': config['title'],
                    'content': config['content'],
                    'project_id': task.project_id,
                    'task_id': task.id
                })
            except Exception as e:
                logger.warning(f"Failed to emit WebSocket notification: {e}")
    
    return notifications

# ============================================
# 建立任務 (改進版)
# ============================================

@tasks_bp.route('/projects/<int:project_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(project_id):
    """
    在專案中建立任務
    
    改進點:
    1. 加上 input validation
    2. 統一 transaction
    3. 自動建立通知和活動日誌
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    # 檢查專案訪問權限
    from api.projects import check_project_access
    has_access, project, role = check_project_access(project_id, current_user.id)
    
    if not has_access:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    # 驗證輸入
    is_valid, result = validate_request_data(CreateTaskSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    # 驗證 assigned_to 是否是專案成員
    if result.get('assigned_to'):
        is_member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=result['assigned_to']
        ).first()
        
        if not is_member:
            return jsonify({'error': 'Assigned user is not a member of this project'}), 400
    
    # 處理日期格式
    due_date = None
    if result.get('due_date'):
        try:
            from datetime import datetime as dt
            due_date = dt.fromisoformat(result['due_date'].replace('Z', '+00:00')) if 'T' in result['due_date'] else dt.strptime(result['due_date'], '%Y-%m-%d')
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid due_date format: {result['due_date']}, error: {e}")
            due_date = None
    
    # 建立任務
    task = Task(
        title=result['title'],
        description=result.get('description'),
        project_id=project_id,
        created_by=current_user.id,
        assigned_to=result.get('assigned_to'),
        status=result.get('status', 'todo'),
        priority=result.get('priority', 'medium'),
        due_date=due_date,
        estimated_hours=result.get('estimated_hours'),
        notes=result.get('notes')
    )
    
    try:
        db.session.add(task)
        db.session.flush()  # 取得 task.id
        
        # 建立通知 (如果有指派對象，且不是自己)
        if task.assigned_to and task.assigned_to != current_user.id:
            create_task_notification(task, 'assigned', current_user)
        
        # 建立任務建立通知（通知專案擁有者 + 操作者自己作為確認）
        extra_users = []
        if project and project.owner_id != current_user.id:
            extra_users.append(project.owner_id)
        create_task_notification(task, 'created', current_user, additional_users=extra_users, include_self=True)
        
        # 建立活動日誌
        activity = ActivityLog(
            project_id=project_id,
            user_id=current_user.id,
            action='create_task',
            resource_type='task',
            resource_id=task.id,
            details={
                'title': task.title,
                'assigned_to': task.assigned_to,
                'priority': task.priority
            }
        )
        db.session.add(activity)
        
        # 一次性 commit
        db.session.commit()
        
        logger.info(f"Task created: {task.title} in project {project_id} by user {current_user.email}")
        
        # 使用 eager loading 取得關聯資料
        task = Task.query.options(
            joinedload(Task.assignee),
            joinedload(Task.creator)
        ).get(task.id)
        
        return jsonify({
            'message': 'Task created successfully',
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'project_id': task.project_id,
                'assignee_id': task.assigned_to,
                'assignee_name': task.assignee.username if task.assignee else None,
                'assigned_to': {
                    'id': task.assignee.id,
                    'username': task.assignee.username
                } if task.assigned_to else None,
                'created_by': {
                    'id': task.creator.id,
                    'username': task.creator.username
                },
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'notes': task.notes,
                'comments_count': 0,
                'created_at': task.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Task creation error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Task creation failed due to server error'}), 500

# ============================================
# 查詢專案的所有任務 (改進版)
# ============================================

@tasks_bp.route('/projects/<int:project_id>/tasks', methods=['GET'])
@jwt_required()
def get_project_tasks(project_id):
    """
    查詢專案的任務列表
    
    改進點:
    1. 使用 eager loading 避免 N+1
    2. 加上更多篩選選項
    3. 加上分頁
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    # 檢查專案訪問權限
    from api.projects import check_project_access
    has_access, project, role = check_project_access(project_id, current_user.id)
    
    if not has_access:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        # 基本查詢 (使用 eager loading)
        query = Task.query.filter_by(project_id=project_id).options(
            joinedload(Task.creator),
            joinedload(Task.assignee)
        )
        
        # 篩選: 按狀態
        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)
        
        # 篩選: 按負責人
        assigned_to = request.args.get('assigned_to', type=int)
        if assigned_to:
            query = query.filter_by(assigned_to=assigned_to)
        
        # 篩選: 按優先級
        priority = request.args.get('priority')
        if priority:
            query = query.filter_by(priority=priority)
        
        # 篩選: 逾期任務
        overdue = request.args.get('overdue', type=bool)
        if overdue:
            query = query.filter(
                Task.due_date < datetime.utcnow(),
                Task.status != 'done'
            )
        
        # 排序
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if sort_by == 'due_date':
            order_column = Task.due_date
        elif sort_by == 'priority':
            order_column = Task.priority
        else:
            order_column = Task.created_at
        
        if sort_order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 分頁
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(per_page, 100)
        
        tasks_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 批次取得所有任務的評論數量（避免 N+1 查詢）
        task_ids = [task.id for task in tasks_paginated.items]
        comments_counts = get_task_ids_to_comments_count(task_ids)
        
        tasks_list = []
        for task in tasks_paginated.items:
            comments_count = comments_counts.get(task.id, 0)
            tasks_list.append({
                'id': task.id,
                'project_id': task.project_id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'progress': task.progress,
                'created_by': {
                    'id': task.creator.id,
                    'username': task.creator.username
                },
                'assignee_id': task.assigned_to,
                'assignee_name': task.assignee.username if task.assignee else None,
                'assigned_to': {
                    'id': task.assignee.id,
                    'username': task.assignee.username
                } if task.assigned_to else None,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'notes': task.notes,
                'comments_count': comments_count,
                'created_at': task.created_at.isoformat(),
                'completed_at': task.completed_at.isoformat() if task.completed_at else None
            })
        
        return jsonify({
            'tasks': tasks_list,
            'total': tasks_paginated.total,
            'page': page,
            'per_page': per_page,
            'total_pages': tasks_paginated.pages
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch tasks'}), 500

# ============================================
# 更新任務 (改進版)
# ============================================

@tasks_bp.route('/tasks/<int:task_id>', methods=['PATCH'])
@jwt_required()
def update_task(task_id):
    """
    更新任務資訊
    
    改進點:
    1. 加上 input validation
    2. 記錄變更內容
    3. 自動通知相關人員
    4. 自動更新 completed_at
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    # 檢查權限
    has_access, task, role = check_task_access(task_id, current_user.id)
    
    if not has_access:
        return jsonify({'error': 'Permission denied or task not found'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    # 驗證輸入
    is_valid, result = validate_request_data(UpdateTaskSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    # 驗證 assigned_to 是否是專案成員
    if 'assigned_to' in result and result['assigned_to']:
        is_member = ProjectMember.query.filter_by(
            project_id=task.project_id,
            user_id=result['assigned_to']
        ).first()
        
        if not is_member:
            return jsonify({'error': 'Assigned user is not a member of this project'}), 400
    
    # 記錄變更
    changes = {}
    old_status = task.status
    old_assigned_to = task.assigned_to
    
    # 處理日期格式
    if 'due_date' in result:
        if result['due_date']:
            try:
                from datetime import datetime as dt
                result['due_date'] = dt.fromisoformat(result['due_date'].replace('Z', '+00:00')) if 'T' in result['due_date'] else dt.strptime(result['due_date'], '%Y-%m-%d')
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid due_date format in update: {result['due_date']}, error: {e}")
                result['due_date'] = None
        else:
            result['due_date'] = None
    
    # 更新欄位
    for field in ['title', 'description', 'status', 'priority', 'due_date', 
                  'estimated_hours', 'actual_hours', 'progress', 'notes']:
        if field in result:
            old_value = getattr(task, field)
            new_value = result[field]
            if old_value != new_value:
                changes[field] = {'old': str(old_value), 'new': str(new_value)}
                setattr(task, field, new_value)
    
    # 特殊處理: assigned_to
    if 'assigned_to' in result:
        if task.assigned_to != result['assigned_to']:
            changes['assigned_to'] = {'old': task.assigned_to, 'new': result['assigned_to']}
            task.assigned_to = result['assigned_to']
    
    # 特殊處理: 狀態變更時自動更新 completed_at
    if 'status' in result:
        if old_status != 'done' and result['status'] == 'done':
            task.completed_at = datetime.utcnow()
            changes['completed_at'] = {'old': None, 'new': task.completed_at.isoformat()}
        elif old_status == 'done' and result['status'] != 'done':
            task.completed_at = None
            changes['completed_at'] = {'old': 'set', 'new': None}
    
    if not changes:
        return jsonify({'message': 'No changes to update'}), 200
    
    try:
        db.session.flush()
        
        # 建立通知
        # 1. 如果狀態變為 done,通知建立者和操作者確認
        if 'status' in changes and changes['status']['new'] == 'done':
            create_task_notification(task, 'completed', current_user, include_self=True)
        
        # 2. 如果 assigned_to 改變,通知新的負責人
        if 'assigned_to' in changes and task.assigned_to:
            create_task_notification(task, 'assigned', current_user)
        
        # 3. 通用任務更新通知（給操作者自己確認）
        if changes and 'status' not in changes:  # 避免與狀態通知重複
            from models import Notification as NotifModel
            self_notif = NotifModel(
                user_id=current_user.id,
                type='task_updated',
                title='Task updated',
                content=f'You updated "{task.title}"',
                related_project_id=task.project_id,
                related_task_id=task.id
            )
            db.session.add(self_notif)
        
        # 建立活動日誌
        activity = ActivityLog(
            project_id=task.project_id,
            user_id=current_user.id,
            action='update_task',
            resource_type='task',
            resource_id=task_id,
            details={'changes': changes}
        )
        db.session.add(activity)
        
        db.session.commit()
        
        logger.info(f"Task {task_id} updated by user {current_user.email}")
        
        # 重新載入 task 取得關聯資料
        task = Task.query.options(
            joinedload(Task.assignee),
            joinedload(Task.creator)
        ).get(task_id)
        
        comments_count = TaskComment.query.filter_by(task_id=task.id).count()
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': {
                'id': task.id,
                'project_id': task.project_id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'progress': task.progress,
                'assignee_id': task.assigned_to,
                'assignee_name': task.assignee.username if task.assignee else None,
                'assigned_to': {
                    'id': task.assignee.id,
                    'username': task.assignee.username
                } if task.assigned_to else None,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'notes': task.notes,
                'comments_count': comments_count,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None
            },
            'changes': changes
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Task update error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Task update failed due to server error'}), 500

# ============================================
# 刪除任務 (改進版)
# ============================================

@tasks_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """
    刪除任務
    
    改進點:記錄刪除日誌
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    # 檢查權限
    has_access, task, role = check_task_access(task_id, current_user.id)
    
    if not has_access:
        return jsonify({'error': 'Permission denied or task not found'}), 403
    
    # 只有建立者或專案管理員能刪除
    from api.projects import check_project_admin
    is_admin = check_project_admin(task.project_id, current_user.id)
    
    if task.created_by != current_user.id and not is_admin:
        return jsonify({'error': 'Only task creator or project admin can delete task'}), 403
    
    try:
        task_title = task.title
        project_id = task.project_id
        
        # 刪除任務 (cascade 會自動刪除評論等)
        db.session.delete(task)
        db.session.commit()
        
        logger.info(f"Task deleted: {task_title} by user {current_user.email}")
        
        return jsonify({
            'message': 'Task deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Task deletion error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Task deletion failed due to server error'}), 500

# ============================================
# 任務評論 (改進版)
# ============================================

class CreateCommentSchema(Schema):
    """評論驗證"""
    content = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=2000)
    )

@tasks_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def create_task_comment(task_id):
    """
    新增任務評論
    
    改進點:
    1. 加上 validation
    2. 統一 transaction
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    has_access, task, role = check_task_access(task_id, current_user.id)
    
    if not has_access:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    # 驗證輸入
    is_valid, result = validate_request_data(CreateCommentSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    try:
        comment = TaskComment(
            task_id=task_id,
            user_id=current_user.id,
            content=result['content']
        )
        db.session.add(comment)
        db.session.flush()
        
        # 建立通知
        create_task_notification(task, 'commented', current_user)
        
        # 建立活動日誌
        activity = ActivityLog(
            project_id=task.project_id,
            user_id=current_user.id,
            action='add_comment',
            resource_type='comment',
            resource_id=comment.id,
            details={'task_id': task_id, 'comment_preview': result['content'][:100]}
        )
        db.session.add(activity)
        
        db.session.commit()
        
        logger.info(f"Comment added to task {task_id} by user {current_user.email}")
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': {
                'id': comment.id,
                'task_id': task_id,
                'user_id': current_user.id,
                'user_name': current_user.username,
                'content': comment.content,
                'created_at': comment.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Comment creation error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to add comment due to server error'}), 500

# ============================================
# 逾期任務提醒 (新增)
# ============================================

@tasks_bp.route('/reminders/overdue', methods=['POST'])
@jwt_required()
def send_overdue_reminders():
    """
    為逾期任務建立提醒通知
    
    - 會提醒任務指派者與建立者
    - 24 小時內同一任務不會重複提醒同一個人
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    
    overdue_tasks = Task.query.filter(
        Task.due_date.isnot(None),
        Task.due_date < now,
        Task.status != 'done'
    ).all()
    
    reminders_created = 0
    
    for task in overdue_tasks:
        recipients = set()
        if task.assigned_to:
            recipients.add(task.assigned_to)
        recipients.add(task.created_by)
        
        for user_id in recipients:
            if not user_id:
                continue
            
            existing = Notification.query.filter(
                Notification.user_id == user_id,
                Notification.related_task_id == task.id,
                Notification.type == 'task_overdue',
                Notification.created_at >= day_ago
            ).first()
            
            if existing:
                continue
            
            notification = Notification(
                user_id=user_id,
                type='task_overdue',
                title=f'Task overdue: {task.title}',
                content='This task is past its due date. Please review and take action.',
                related_project_id=task.project_id,
                related_task_id=task.id
            )
            db.session.add(notification)
            reminders_created += 1
    
    if reminders_created > 0:
        db.session.commit()
    else:
        db.session.rollback()
    
    return jsonify({
        'message': 'Overdue reminders processed',
        'reminders_count': reminders_created
    }), 200

# ============================================
# 獲取所有任務 (改進版：加入分頁和效能優化)
# ============================================

@tasks_bp.route('/tasks/all', methods=['GET'])
@jwt_required()
def get_all_tasks():
    """
    獲取所有任務 (用戶可訪問的所有專案的任務)
    
    改進點:
    1. 加入分頁功能
    2. 批次查詢評論數（避免 N+1）
    3. 支援篩選和排序
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        from models import ProjectMember
        
        # 獲取用戶有權訪問的專案 ID
        owned_projects = Project.query.filter_by(owner_id=current_user.id).all()
        member_projects = ProjectMember.query.filter_by(user_id=current_user.id).all()
        
        project_ids = set([p.id for p in owned_projects])
        project_ids.update([m.project_id for m in member_projects])
        
        if not project_ids:
            return jsonify({'tasks': [], 'total': 0, 'page': 1, 'per_page': 50, 'total_pages': 0}), 200
        
        # 基本查詢
        query = Task.query.filter(Task.project_id.in_(project_ids)).options(
            joinedload(Task.assignee),
            joinedload(Task.creator)
        )
        
        # 篩選: 按狀態
        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)
        
        # 篩選: 按優先級
        priority = request.args.get('priority')
        if priority:
            query = query.filter_by(priority=priority)
        
        # 排序
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if sort_by == 'due_date':
            order_column = Task.due_date
        elif sort_by == 'priority':
            order_column = Task.priority
        else:
            order_column = Task.created_at
        
        if sort_order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 分頁
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(per_page, 100)  # 最多 100 筆
        
        tasks_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 批次取得所有任務的評論數量（避免 N+1 查詢）
        task_ids = [task.id for task in tasks_paginated.items]
        comments_counts = get_task_ids_to_comments_count(task_ids)
        
        tasks_list = []
        for task in tasks_paginated.items:
            comments_count = comments_counts.get(task.id, 0)
            tasks_list.append({
                'id': task.id,
                'project_id': task.project_id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'assignee_id': task.assigned_to,
                'assignee_name': task.assignee.username if task.assignee else None,
                'assigned_to': {
                    'id': task.assignee.id,
                    'username': task.assignee.username
                } if task.assignee else None,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'notes': task.notes,
                'comments_count': comments_count,
                'created_at': task.created_at.isoformat()
            })
        
        return jsonify({
            'tasks': tasks_list,
            'total': tasks_paginated.total,
            'page': page,
            'per_page': per_page,
            'total_pages': tasks_paginated.pages
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching all tasks: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch tasks'}), 500

# ============================================
# 獲取我的任務 (改進版：加入分頁和效能優化)
# ============================================

@tasks_bp.route('/tasks/my', methods=['GET'])
@jwt_required()
def get_my_tasks():
    """
    獲取分配給當前用戶的任務
    
    改進點:
    1. 加入分頁功能
    2. 批次查詢評論數（避免 N+1）
    3. 支援篩選和排序
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # 基本查詢
        query = Task.query.filter_by(assigned_to=current_user.id).options(
            joinedload(Task.assignee),
            joinedload(Task.creator)
        )
        
        # 篩選: 按狀態
        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)
        
        # 篩選: 按優先級
        priority = request.args.get('priority')
        if priority:
            query = query.filter_by(priority=priority)
        
        # 排序
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        if sort_by == 'due_date':
            order_column = Task.due_date
        elif sort_by == 'priority':
            order_column = Task.priority
        else:
            order_column = Task.created_at
        
        if sort_order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # 分頁
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(per_page, 100)  # 最多 100 筆
        
        tasks_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 批次取得所有任務的評論數量（避免 N+1 查詢）
        task_ids = [task.id for task in tasks_paginated.items]
        comments_counts = get_task_ids_to_comments_count(task_ids)
        
        tasks_list = []
        for task in tasks_paginated.items:
            comments_count = comments_counts.get(task.id, 0)
            tasks_list.append({
                'id': task.id,
                'project_id': task.project_id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'assignee_id': task.assigned_to,
                'assignee_name': task.assignee.username if task.assignee else None,
                'assigned_to': {
                    'id': task.assignee.id,
                    'username': task.assignee.username
                } if task.assignee else None,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'notes': task.notes,
                'comments_count': comments_count,
                'created_at': task.created_at.isoformat()
            })
        
        return jsonify({
            'tasks': tasks_list,
            'total': tasks_paginated.total,
            'page': page,
            'per_page': per_page,
            'total_pages': tasks_paginated.pages
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching my tasks: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch tasks'}), 500

# ============================================
# 獲取任務評論 (新增)
# ============================================

@tasks_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
@jwt_required()
def get_task_comments(task_id):
    """
    獲取任務的所有評論
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    has_access, task, role = check_task_access(task_id, current_user.id)
    
    if not has_access:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        comments = TaskComment.query.filter_by(task_id=task_id).options(
            joinedload(TaskComment.user)
        ).order_by(TaskComment.created_at.asc()).all()
        
        comments_list = [{
            'id': c.id,
            'task_id': c.task_id,
            'user_id': c.user_id,
            'user_name': c.user.username if c.user else 'Unknown',
            'content': c.content,
            'created_at': c.created_at.isoformat()
        } for c in comments]
        
        return jsonify({'comments': comments_list}), 200
        
    except Exception as e:
        logger.error(f"Error fetching comments: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch comments'}), 500

# ============================================
# 更新評論 (新增)
# ============================================

class UpdateCommentSchema(Schema):
    """更新評論驗證"""
    content = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=2000)
    )

@tasks_bp.route('/comments/<int:comment_id>', methods=['PATCH'])
@jwt_required()
def update_comment(comment_id):
    """
    更新評論 (只有作者可以)
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    comment = TaskComment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    # 只有作者可以更新
    if comment.user_id != current_user.id:
        return jsonify({'error': 'Only comment author can update'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    is_valid, result = validate_request_data(UpdateCommentSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400
    
    try:
        comment.content = result['content']
        comment.is_edited = True
        db.session.commit()
        
        return jsonify({
            'message': 'Comment updated successfully',
            'comment': {
                'id': comment.id,
                'task_id': comment.task_id,
                'user_id': comment.user_id,
                'user_name': current_user.username,
                'content': comment.content,
                'created_at': comment.created_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Comment update error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to update comment'}), 500