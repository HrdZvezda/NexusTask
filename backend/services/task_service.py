"""
============================================
services/task_service.py - 任務服務
============================================

【職責】
- 任務 CRUD
- 任務狀態管理
- 任務評論
- 任務指派
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import joinedload
from sqlalchemy import func

from .base import BaseService, ServiceResult, ServiceErrorCode, PermissionMixin
from .project_service import ProjectPermissionService


# ============================================
# 資料傳輸物件（DTO）
# ============================================

@dataclass
class TaskDTO:
    """任務資料"""
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    project_id: int
    assigned_to: Optional[int]
    assignee_name: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    due_date: Optional[datetime] = None
    progress: int = 0
    comments_count: int = 0
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_model(cls, task, comments_count: int = 0) -> 'TaskDTO':
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            project_id=task.project_id,
            assigned_to=task.assigned_to,
            assignee_name=task.assignee.username if task.assignee else None,
            created_by=task.created_by,
            creator_name=task.creator.username if task.creator else None,
            due_date=task.due_date,
            progress=task.progress or 0,
            comments_count=comments_count,
            created_at=task.created_at
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'project_id': self.project_id,
            'assigned_to': self.assigned_to,
            'assignee_name': self.assignee_name,
            'created_by': self.created_by,
            'creator_name': self.creator_name,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'progress': self.progress,
            'comments_count': self.comments_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class CommentDTO:
    """評論資料"""
    id: int
    content: str
    user_id: int
    user_name: str
    created_at: datetime
    
    @classmethod
    def from_model(cls, comment) -> 'CommentDTO':
        return cls(
            id=comment.id,
            content=comment.content,
            user_id=comment.user_id,
            user_name=comment.user.username if comment.user else 'Unknown',
            created_at=comment.created_at
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'content': self.content,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================
# 任務服務
# ============================================

class TaskService(BaseService, PermissionMixin):
    """
    任務服務
    
    處理：
    - 任務 CRUD
    - 任務狀態更新
    - 任務指派
    - 評論管理
    """
    
    def __init__(self):
        super().__init__()
        self._permission_service = ProjectPermissionService()
    
    def _get_comments_count_map(self, task_ids: List[int]) -> dict:
        """批次取得評論數量"""
        from models import TaskComment
        
        if not task_ids:
            return {}
        
        counts = TaskComment.query.filter(
            TaskComment.task_id.in_(task_ids)
        ).with_entities(
            TaskComment.task_id,
            func.count(TaskComment.id).label('count')
        ).group_by(TaskComment.task_id).all()
        
        return {task_id: count for task_id, count in counts}
    
    def get_project_tasks(self, project_id: int, user_id: int, 
                          page: int = 1, per_page: int = 50) -> ServiceResult[dict]:
        """取得專案任務"""
        from models import Task
        
        # 檢查權限
        has_access, _ = self._permission_service.check_access(project_id, user_id)
        if not has_access:
            return ServiceResult.forbidden('You are not a member of this project')
        
        # 查詢任務
        pagination = Task.query.filter_by(
            project_id=project_id
        ).options(
            joinedload(Task.assignee),
            joinedload(Task.creator)
        ).order_by(Task.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 取得評論數量
        task_ids = [t.id for t in pagination.items]
        comments_map = self._get_comments_count_map(task_ids)
        
        # 組合結果
        tasks = [
            TaskDTO.from_model(t, comments_map.get(t.id, 0)).to_dict()
            for t in pagination.items
        ]
        
        return ServiceResult.ok({
            'tasks': tasks,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
    
    def get_user_tasks(self, user_id: int, page: int = 1, 
                       per_page: int = 50) -> ServiceResult[dict]:
        """取得使用者的任務"""
        from models import Task
        
        pagination = Task.query.filter_by(
            assigned_to=user_id
        ).options(
            joinedload(Task.assignee),
            joinedload(Task.creator),
            joinedload(Task.project)
        ).order_by(Task.due_date.asc().nullslast()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        task_ids = [t.id for t in pagination.items]
        comments_map = self._get_comments_count_map(task_ids)
        
        tasks = [
            TaskDTO.from_model(t, comments_map.get(t.id, 0)).to_dict()
            for t in pagination.items
        ]
        
        return ServiceResult.ok({
            'tasks': tasks,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })
    
    def get_task(self, task_id: int, user_id: int) -> ServiceResult[TaskDTO]:
        """取得單一任務"""
        from models import Task, TaskComment
        
        task = Task.query.options(
            joinedload(Task.assignee),
            joinedload(Task.creator),
            joinedload(Task.project)
        ).get(task_id)
        
        if not task:
            return ServiceResult.not_found('Task')
        
        # 檢查權限
        has_access, _ = self._permission_service.check_access(task.project_id, user_id)
        if not has_access:
            return ServiceResult.forbidden('You are not a member of this project')
        
        comments_count = TaskComment.query.filter_by(task_id=task_id).count()
        
        return ServiceResult.ok(TaskDTO.from_model(task, comments_count))
    
    def create_task(self, project_id: int, user_id: int, title: str,
                    **kwargs) -> ServiceResult[TaskDTO]:
        """建立任務"""
        from models import db, Task, Project, ActivityLog
        
        # 檢查權限
        has_access, _ = self._permission_service.check_access(project_id, user_id)
        if not has_access:
            return ServiceResult.forbidden('You are not a member of this project')
        
        # 檢查專案存在
        project = Project.query.get(project_id)
        if not project:
            return ServiceResult.not_found('Project')
        
        # 處理 due_date
        due_date = kwargs.pop('due_date', None)
        if due_date and isinstance(due_date, str):
            try:
                due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError:
                due_date = None
        
        # 建立任務
        task = Task(
            title=title,
            project_id=project_id,
            created_by=user_id,
            due_date=due_date,
            **kwargs
        )
        
        db.session.add(task)
        
        # 記錄活動
        log = ActivityLog(
            user_id=user_id,
            project_id=project_id,
            action='create',
            entity_type='task',
            entity_id=task.id,
            description=f'Created task: {title}'
        )
        db.session.add(log)
        
        db.session.commit()
        
        # 重新載入以取得關聯
        task = Task.query.options(
            joinedload(Task.assignee),
            joinedload(Task.creator)
        ).get(task.id)
        
        self._log_info(f"Task created: {title} in project {project_id}")
        
        return ServiceResult.ok(TaskDTO.from_model(task))
    
    def update_task(self, task_id: int, user_id: int, 
                    **kwargs) -> ServiceResult[TaskDTO]:
        """更新任務"""
        from models import db, Task
        
        task = Task.query.get(task_id)
        if not task:
            return ServiceResult.not_found('Task')
        
        # 檢查權限
        has_access, _ = self._permission_service.check_access(task.project_id, user_id)
        if not has_access:
            return ServiceResult.forbidden('You are not a member of this project')
        
        # 處理 due_date
        if 'due_date' in kwargs:
            due_date = kwargs['due_date']
            if due_date and isinstance(due_date, str):
                try:
                    kwargs['due_date'] = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    kwargs['due_date'] = None
        
        # 更新允許的欄位
        allowed_fields = [
            'title', 'description', 'status', 'priority', 
            'assigned_to', 'due_date', 'progress', 'notes',
            'estimated_hours', 'actual_hours'
        ]
        
        for field in allowed_fields:
            if field in kwargs:
                setattr(task, field, kwargs[field])
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 重新載入
        task = Task.query.options(
            joinedload(Task.assignee),
            joinedload(Task.creator)
        ).get(task.id)
        
        return ServiceResult.ok(TaskDTO.from_model(task))
    
    def update_status(self, task_id: int, user_id: int, 
                      status: str) -> ServiceResult[TaskDTO]:
        """更新任務狀態"""
        valid_statuses = ['todo', 'in_progress', 'review', 'done']
        if status not in valid_statuses:
            return ServiceResult.validation_error(
                f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            )
        
        return self.update_task(task_id, user_id, status=status)
    
    def delete_task(self, task_id: int, user_id: int) -> ServiceResult[bool]:
        """刪除任務"""
        from models import db, Task
        
        task = Task.query.get(task_id)
        if not task:
            return ServiceResult.not_found('Task')
        
        # 檢查權限
        has_access, _ = self._permission_service.check_access(task.project_id, user_id)
        if not has_access:
            return ServiceResult.forbidden('You are not a member of this project')
        
        task_title = task.title
        db.session.delete(task)
        db.session.commit()
        
        self._log_info(f"Task deleted: {task_title}")
        
        return ServiceResult.ok(True)
    
    def get_comments(self, task_id: int, user_id: int) -> ServiceResult[List[CommentDTO]]:
        """取得任務評論"""
        from models import Task, TaskComment
        
        task = Task.query.get(task_id)
        if not task:
            return ServiceResult.not_found('Task')
        
        # 檢查權限
        has_access, _ = self._permission_service.check_access(task.project_id, user_id)
        if not has_access:
            return ServiceResult.forbidden('You are not a member of this project')
        
        comments = TaskComment.query.filter_by(
            task_id=task_id
        ).options(
            joinedload(TaskComment.user)
        ).order_by(TaskComment.created_at.asc()).all()
        
        return ServiceResult.ok([CommentDTO.from_model(c) for c in comments])
    
    def add_comment(self, task_id: int, user_id: int, 
                    content: str) -> ServiceResult[CommentDTO]:
        """新增評論"""
        from models import db, Task, TaskComment
        
        task = Task.query.get(task_id)
        if not task:
            return ServiceResult.not_found('Task')
        
        # 檢查權限
        has_access, _ = self._permission_service.check_access(task.project_id, user_id)
        if not has_access:
            return ServiceResult.forbidden('You are not a member of this project')
        
        # 建立評論
        comment = TaskComment(
            task_id=task_id,
            user_id=user_id,
            content=content
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # 重新載入
        comment = TaskComment.query.options(
            joinedload(TaskComment.user)
        ).get(comment.id)
        
        return ServiceResult.ok(CommentDTO.from_model(comment))


# ============================================
# 全域服務實例
# ============================================

_task_service: Optional[TaskService] = None


def get_task_service() -> TaskService:
    """取得任務服務實例"""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service

