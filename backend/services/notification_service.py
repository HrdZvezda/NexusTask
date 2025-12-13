"""
============================================
services/notification_service.py - 通知服務
============================================

【職責】
- 通知 CRUD
- 通知發送
- 批量通知
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import joinedload

from .base import BaseService, ServiceResult


# ============================================
# 資料傳輸物件（DTO）
# ============================================

@dataclass
class NotificationDTO:
    """通知資料"""
    id: int
    type: str
    title: str
    content: Optional[str]
    is_read: bool
    related_project_id: Optional[int]
    related_task_id: Optional[int]
    created_at: datetime
    
    @classmethod
    def from_model(cls, notification) -> 'NotificationDTO':
        return cls(
            id=notification.id,
            type=notification.type,
            title=notification.title,
            content=notification.content,
            is_read=notification.is_read,
            related_project_id=notification.related_project_id,
            related_task_id=notification.related_task_id,
            created_at=notification.created_at
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'is_read': self.is_read,
            'related_project_id': self.related_project_id,
            'related_task_id': self.related_task_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================
# 通知類型枚舉
# ============================================

class NotificationType:
    """通知類型"""
    TASK_ASSIGNED = 'task_assigned'
    TASK_COMPLETED = 'task_completed'
    TASK_COMMENTED = 'task_commented'
    TASK_DUE_SOON = 'task_due_soon'
    TASK_OVERDUE = 'task_overdue'
    PROJECT_INVITED = 'project_invited'
    PROJECT_UPDATED = 'project_updated'
    MEMBER_ADDED = 'member_added'
    MEMBER_REMOVED = 'member_removed'
    MENTION = 'mention'


# ============================================
# 通知服務
# ============================================

class NotificationService(BaseService):
    """
    通知服務
    
    處理：
    - 通知列表
    - 標記已讀
    - 建立通知
    - 批量通知
    """
    
    def get_user_notifications(self, user_id: int, 
                               unread_only: bool = False,
                               page: int = 1, 
                               per_page: int = 20) -> ServiceResult[dict]:
        """取得使用者通知"""
        from models import Notification
        
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        pagination = query.order_by(
            Notification.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        notifications = [
            NotificationDTO.from_model(n).to_dict()
            for n in pagination.items
        ]
        
        return ServiceResult.ok({
            'notifications': notifications,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'unread_count': Notification.query.filter_by(
                user_id=user_id, is_read=False
            ).count()
        })
    
    def get_unread_count(self, user_id: int) -> ServiceResult[int]:
        """取得未讀通知數量"""
        from models import Notification
        
        count = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()
        
        return ServiceResult.ok(count)
    
    def mark_as_read(self, notification_id: int, user_id: int) -> ServiceResult[bool]:
        """標記通知為已讀"""
        from models import db, Notification
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if not notification:
            return ServiceResult.not_found('Notification')
        
        notification.is_read = True
        db.session.commit()
        
        return ServiceResult.ok(True)
    
    def mark_all_as_read(self, user_id: int) -> ServiceResult[int]:
        """標記所有通知為已讀"""
        from models import db, Notification
        
        updated = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        
        return ServiceResult.ok(updated)
    
    def delete_notification(self, notification_id: int, user_id: int) -> ServiceResult[bool]:
        """刪除通知"""
        from models import db, Notification
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if not notification:
            return ServiceResult.not_found('Notification')
        
        db.session.delete(notification)
        db.session.commit()
        
        return ServiceResult.ok(True)
    
    def create_notification(self, user_id: int, notification_type: str,
                            title: str, content: str = None,
                            project_id: int = None, 
                            task_id: int = None) -> ServiceResult[NotificationDTO]:
        """建立通知"""
        from models import db, Notification
        
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            content=content,
            related_project_id=project_id,
            related_task_id=task_id
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # 使快取失效
        try:
            from cache import invalidate_notification_count
            invalidate_notification_count(user_id)
        except Exception:
            pass
        
        return ServiceResult.ok(NotificationDTO.from_model(notification))
    
    def create_bulk_notifications(self, user_ids: List[int], 
                                  notification_type: str,
                                  title: str, content: str = None,
                                  project_id: int = None,
                                  task_id: int = None) -> ServiceResult[int]:
        """批量建立通知"""
        from models import db, Notification
        
        notifications = []
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                content=content,
                related_project_id=project_id,
                related_task_id=task_id
            )
            notifications.append(notification)
        
        db.session.bulk_save_objects(notifications)
        db.session.commit()
        
        # 使快取失效
        try:
            from cache import invalidate_notification_count
            for user_id in user_ids:
                invalidate_notification_count(user_id)
        except Exception:
            pass
        
        return ServiceResult.ok(len(notifications))
    
    def notify_task_assigned(self, task, assignee_id: int, 
                             assigner_name: str) -> ServiceResult[NotificationDTO]:
        """通知任務指派"""
        return self.create_notification(
            user_id=assignee_id,
            notification_type=NotificationType.TASK_ASSIGNED,
            title=f'{assigner_name} assigned a task to you',
            content=f'Task: {task.title}',
            project_id=task.project_id,
            task_id=task.id
        )
    
    def notify_task_completed(self, task, completer_name: str,
                              notify_user_ids: List[int]) -> ServiceResult[int]:
        """通知任務完成"""
        return self.create_bulk_notifications(
            user_ids=notify_user_ids,
            notification_type=NotificationType.TASK_COMPLETED,
            title=f'{completer_name} completed a task',
            content=f'Task: {task.title}',
            project_id=task.project_id,
            task_id=task.id
        )
    
    def notify_task_commented(self, task, commenter_name: str,
                              notify_user_ids: List[int]) -> ServiceResult[int]:
        """通知任務評論"""
        return self.create_bulk_notifications(
            user_ids=notify_user_ids,
            notification_type=NotificationType.TASK_COMMENTED,
            title=f'{commenter_name} commented on a task',
            content=f'Task: {task.title}',
            project_id=task.project_id,
            task_id=task.id
        )
    
    def notify_project_invitation(self, project, invitee_id: int,
                                  inviter_name: str) -> ServiceResult[NotificationDTO]:
        """通知專案邀請"""
        return self.create_notification(
            user_id=invitee_id,
            notification_type=NotificationType.PROJECT_INVITED,
            title=f'{inviter_name} invited you to a project',
            content=f'Project: {project.name}',
            project_id=project.id
        )
    
    def notify_project_members(self, project_id: int, 
                               notification_type: str,
                               title: str, content: str = None,
                               exclude_user_id: int = None) -> ServiceResult[int]:
        """通知專案所有成員"""
        from models import Project, ProjectMember
        
        project = Project.query.get(project_id)
        if not project:
            return ServiceResult.not_found('Project')
        
        # 收集所有成員 ID
        user_ids = [project.owner_id]
        
        members = ProjectMember.query.filter_by(project_id=project_id).all()
        for member in members:
            if member.user_id not in user_ids:
                user_ids.append(member.user_id)
        
        # 排除指定使用者
        if exclude_user_id and exclude_user_id in user_ids:
            user_ids.remove(exclude_user_id)
        
        if not user_ids:
            return ServiceResult.ok(0)
        
        return self.create_bulk_notifications(
            user_ids=user_ids,
            notification_type=notification_type,
            title=title,
            content=content,
            project_id=project_id
        )


# ============================================
# 全域服務實例
# ============================================

_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """取得通知服務實例"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service

