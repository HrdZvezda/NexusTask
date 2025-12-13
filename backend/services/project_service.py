"""
============================================
services/project_service.py - 專案服務
============================================

【職責】
- 專案 CRUD
- 專案成員管理
- 專案權限檢查
- 專案統計
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import joinedload
from sqlalchemy import func, case, and_

from .base import BaseService, ServiceResult, ServiceErrorCode, PermissionMixin


# ============================================
# 資料傳輸物件（DTO）
# ============================================

@dataclass
class ProjectDTO:
    """專案資料"""
    id: int
    name: str
    description: Optional[str]
    status: str
    owner_id: int
    owner_name: Optional[str] = None
    member_count: int = 0
    task_count: int = 0
    completed_tasks: int = 0
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_model(cls, project, include_stats: bool = False) -> 'ProjectDTO':
        dto = cls(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            owner_id=project.owner_id,
            owner_name=project.owner.username if project.owner else None,
            created_at=project.created_at
        )
        return dto
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'owner_id': self.owner_id,
            'owner_name': self.owner_name,
            'member_count': self.member_count,
            'task_count': self.task_count,
            'completed_tasks': self.completed_tasks,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class ProjectMemberDTO:
    """專案成員資料"""
    user_id: int
    username: str
    email: str
    role: str
    is_owner: bool = False
    avatar_url: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_owner': self.is_owner,
            'avatar_url': self.avatar_url
        }


# ============================================
# 專案權限服務
# ============================================

class ProjectPermissionService(BaseService, PermissionMixin):
    """
    專案權限服務
    
    集中處理專案相關的權限檢查
    """
    
    def check_access(self, project_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        檢查使用者是否可以存取專案
        
        Returns:
            Tuple[bool, str]: (有權限, 角色)
        """
        from models import Project, ProjectMember
        
        project = Project.query.get(project_id)
        if not project:
            return False, None
        
        # Owner
        if project.owner_id == user_id:
            return True, 'owner'
        
        # Member
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()
        
        if member:
            return True, member.role
        
        return False, None
    
    def check_admin_access(self, project_id: int, user_id: int) -> bool:
        """檢查使用者是否為專案管理員"""
        has_access, role = self.check_access(project_id, user_id)
        return has_access and role in ('owner', 'admin')
    
    def can_modify(self, project_id: int, user_id: int) -> bool:
        """檢查使用者是否可以修改專案"""
        return self.check_admin_access(project_id, user_id)
    
    def can_delete(self, project_id: int, user_id: int) -> bool:
        """檢查使用者是否可以刪除專案（只有 owner）"""
        from models import Project
        project = Project.query.get(project_id)
        return project and project.owner_id == user_id


# ============================================
# 專案服務
# ============================================

class ProjectService(BaseService, PermissionMixin):
    """
    專案服務
    
    處理：
    - 專案 CRUD
    - 專案統計
    - 成員管理
    """
    
    def __init__(self):
        super().__init__()
        self._permission_service = ProjectPermissionService()
    
    def get_user_projects(self, user_id: int, page: int = 1, 
                          per_page: int = 20) -> ServiceResult[dict]:
        """
        取得使用者的專案列表（擁有的 + 參與的）
        """
        from models import Project, ProjectMember, Task
        
        # 子查詢：任務統計
        task_stats = Project.query.outerjoin(Task).with_entities(
            Project.id,
            func.count(Task.id).label('task_count'),
            func.sum(case((Task.status == 'done', 1), else_=0)).label('completed_tasks')
        ).group_by(Project.id).subquery()
        
        # 子查詢：成員數量
        member_counts = ProjectMember.query.with_entities(
            ProjectMember.project_id,
            func.count(ProjectMember.id).label('member_count')
        ).group_by(ProjectMember.project_id).subquery()
        
        # 主查詢
        owned_projects = Project.query.filter_by(owner_id=user_id)
        
        member_project_ids = ProjectMember.query.filter_by(
            user_id=user_id
        ).with_entities(ProjectMember.project_id)
        
        member_projects = Project.query.filter(
            Project.id.in_(member_project_ids)
        )
        
        # 合併並分頁
        all_projects = owned_projects.union(member_projects).options(
            joinedload(Project.owner)
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        # 取得統計資料
        project_ids = [p.id for p in all_projects.items]
        
        stats = dict(Project.query.filter(Project.id.in_(project_ids)).outerjoin(
            Task
        ).with_entities(
            Project.id,
            func.count(Task.id).label('task_count')
        ).group_by(Project.id).all())
        
        # 組合結果
        projects = []
        for project in all_projects.items:
            dto = ProjectDTO.from_model(project)
            dto.task_count = stats.get(project.id, 0)
            projects.append(dto.to_dict())
        
        return ServiceResult.ok({
            'projects': projects,
            'total': all_projects.total,
            'page': page,
            'per_page': per_page,
            'total_pages': all_projects.pages
        })
    
    def get_project(self, project_id: int, user_id: int) -> ServiceResult[ProjectDTO]:
        """取得單一專案"""
        from models import Project
        
        # 檢查權限
        has_access, role = self._permission_service.check_access(project_id, user_id)
        if not has_access:
            return ServiceResult.forbidden('You are not a member of this project')
        
        project = Project.query.options(joinedload(Project.owner)).get(project_id)
        if not project:
            return ServiceResult.not_found('Project')
        
        return ServiceResult.ok(ProjectDTO.from_model(project))
    
    def create_project(self, user_id: int, name: str, 
                       description: str = None, **kwargs) -> ServiceResult[ProjectDTO]:
        """建立專案"""
        from models import db, Project, ActivityLog
        
        project = Project(
            name=name,
            description=description,
            owner_id=user_id,
            **kwargs
        )
        
        db.session.add(project)
        
        # 記錄活動
        log = ActivityLog(
            user_id=user_id,
            action='create',
            entity_type='project',
            description=f'Created project: {name}'
        )
        db.session.add(log)
        
        db.session.commit()
        
        self._log_info(f"Project created: {name} by user {user_id}")
        
        return ServiceResult.ok(ProjectDTO.from_model(project))
    
    def update_project(self, project_id: int, user_id: int, 
                       **kwargs) -> ServiceResult[ProjectDTO]:
        """更新專案"""
        from models import db, Project
        
        # 檢查權限
        if not self._permission_service.can_modify(project_id, user_id):
            return ServiceResult.forbidden('You do not have permission to modify this project')
        
        project = Project.query.get(project_id)
        if not project:
            return ServiceResult.not_found('Project')
        
        # 更新允許的欄位
        allowed_fields = ['name', 'description', 'status', 'start_date', 'end_date']
        for field in allowed_fields:
            if field in kwargs:
                setattr(project, field, kwargs[field])
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return ServiceResult.ok(ProjectDTO.from_model(project))
    
    def delete_project(self, project_id: int, user_id: int) -> ServiceResult[bool]:
        """刪除專案"""
        from models import db, Project
        
        # 檢查權限（只有 owner 可以刪除）
        if not self._permission_service.can_delete(project_id, user_id):
            return ServiceResult.forbidden('Only the project owner can delete the project')
        
        project = Project.query.get(project_id)
        if not project:
            return ServiceResult.not_found('Project')
        
        project_name = project.name
        db.session.delete(project)
        db.session.commit()
        
        self._log_info(f"Project deleted: {project_name} by user {user_id}")
        
        return ServiceResult.ok(True)
    
    def get_members(self, project_id: int, user_id: int) -> ServiceResult[List[ProjectMemberDTO]]:
        """取得專案成員"""
        from models import Project, ProjectMember
        
        # 檢查權限
        has_access, _ = self._permission_service.check_access(project_id, user_id)
        if not has_access:
            return ServiceResult.forbidden('You are not a member of this project')
        
        project = Project.query.options(joinedload(Project.owner)).get(project_id)
        if not project:
            return ServiceResult.not_found('Project')
        
        members = []
        
        # 加入 Owner
        members.append(ProjectMemberDTO(
            user_id=project.owner.id,
            username=project.owner.username,
            email=project.owner.email,
            role='admin',
            is_owner=True,
            avatar_url=project.owner.avatar_url
        ))
        
        # 加入其他成員
        project_members = ProjectMember.query.filter_by(
            project_id=project_id
        ).options(joinedload(ProjectMember.user)).all()
        
        for pm in project_members:
            if pm.user_id != project.owner_id:
                members.append(ProjectMemberDTO(
                    user_id=pm.user.id,
                    username=pm.user.username,
                    email=pm.user.email,
                    role=pm.role,
                    is_owner=False,
                    avatar_url=pm.user.avatar_url
                ))
        
        return ServiceResult.ok(members)
    
    def add_member(self, project_id: int, user_id: int, 
                   member_email: str, role: str = 'member') -> ServiceResult[ProjectMemberDTO]:
        """新增成員"""
        from models import db, Project, ProjectMember, User
        
        # 檢查權限
        if not self._permission_service.check_admin_access(project_id, user_id):
            return ServiceResult.forbidden('Only admins can add members')
        
        # 查找使用者
        new_member = User.query.filter_by(email=member_email).first()
        if not new_member:
            return ServiceResult.not_found('User')
        
        # 檢查是否已經是成員
        existing = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=new_member.id
        ).first()
        
        if existing:
            return ServiceResult.conflict('User is already a member of this project')
        
        # 檢查是否為 owner
        project = Project.query.get(project_id)
        if project.owner_id == new_member.id:
            return ServiceResult.conflict('Owner is already part of the project')
        
        # 新增成員
        member = ProjectMember(
            project_id=project_id,
            user_id=new_member.id,
            role=role
        )
        
        db.session.add(member)
        db.session.commit()
        
        return ServiceResult.ok(ProjectMemberDTO(
            user_id=new_member.id,
            username=new_member.username,
            email=new_member.email,
            role=role,
            avatar_url=new_member.avatar_url
        ))
    
    def remove_member(self, project_id: int, user_id: int, 
                      member_id: int) -> ServiceResult[bool]:
        """移除成員"""
        from models import db, Project, ProjectMember
        
        # 檢查權限
        if not self._permission_service.check_admin_access(project_id, user_id):
            return ServiceResult.forbidden('Only admins can remove members')
        
        # 不能移除 owner
        project = Project.query.get(project_id)
        if project.owner_id == member_id:
            return ServiceResult.fail(
                ServiceErrorCode.VALIDATION_ERROR,
                'Cannot remove the project owner'
            )
        
        # 查找成員
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=member_id
        ).first()
        
        if not member:
            return ServiceResult.not_found('Member')
        
        db.session.delete(member)
        db.session.commit()
        
        return ServiceResult.ok(True)
    
    def get_stats(self, project_id: int, user_id: int) -> ServiceResult[dict]:
        """取得專案統計"""
        from models import Project, Task, ProjectMember
        
        # 檢查權限
        has_access, _ = self._permission_service.check_access(project_id, user_id)
        if not has_access:
            return ServiceResult.forbidden('You are not a member of this project')
        
        project = Project.query.get(project_id)
        if not project:
            return ServiceResult.not_found('Project')
        
        # 任務統計
        task_stats = Task.query.filter_by(project_id=project_id).with_entities(
            func.count(Task.id).label('total'),
            func.sum(case((Task.status == 'todo', 1), else_=0)).label('todo'),
            func.sum(case((Task.status == 'in_progress', 1), else_=0)).label('in_progress'),
            func.sum(case((Task.status == 'review', 1), else_=0)).label('review'),
            func.sum(case((Task.status == 'done', 1), else_=0)).label('done')
        ).first()
        
        # 成員數量
        member_count = ProjectMember.query.filter_by(project_id=project_id).count() + 1
        
        return ServiceResult.ok({
            'task_stats': {
                'total': task_stats.total or 0,
                'todo': task_stats.todo or 0,
                'in_progress': task_stats.in_progress or 0,
                'review': task_stats.review or 0,
                'done': task_stats.done or 0
            },
            'member_count': member_count,
            'completion_rate': (
                (task_stats.done or 0) / task_stats.total * 100 
                if task_stats.total else 0
            )
        })


# ============================================
# 全域服務實例
# ============================================

_project_service: Optional[ProjectService] = None


def get_project_service() -> ProjectService:
    """取得專案服務實例"""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService()
    return _project_service

