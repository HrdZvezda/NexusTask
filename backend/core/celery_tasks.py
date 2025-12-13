"""
============================================
celery_tasks.py - 背景任務（物件導向版本）
============================================

【設計原則】
- 單一職責原則 (SRP): 每個類別只處理一類任務
- 開放封閉原則 (OCP): 新增任務類型不需修改現有程式碼
- 依賴反轉原則 (DIP): 依賴抽象而非具體實現
"""

import sys
import os

# 從父目錄導入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abc import ABC, abstractmethod
from celery import Celery
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any


# ============================================
# Celery 設定和初始化
# ============================================

class CeleryConfig:
    """Celery 設定類別"""
    
    BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    TASK_SERIALIZER = 'json'
    ACCEPT_CONTENT = ['json']
    RESULT_SERIALIZER = 'json'
    TIMEZONE = 'UTC'
    ENABLE_UTC = True
    TASK_TRACK_STARTED = True
    TASK_TIME_LIMIT = 30 * 60  # 30 分鐘
    WORKER_PREFETCH_MULTIPLIER = 1
    TASK_ACKS_LATE = True


class CeleryFactory:
    """Celery 工廠類別"""
    
    _instance: Optional[Celery] = None
    
    @classmethod
    def create(cls, app=None) -> Celery:
        """建立或取得 Celery 實例（單例模式）"""
        if cls._instance is None:
            cls._instance = Celery(
                'tasks',
                broker=CeleryConfig.BROKER_URL,
                backend=CeleryConfig.RESULT_BACKEND
            )
            
            cls._instance.conf.update(
                task_serializer=CeleryConfig.TASK_SERIALIZER,
                accept_content=CeleryConfig.ACCEPT_CONTENT,
                result_serializer=CeleryConfig.RESULT_SERIALIZER,
                timezone=CeleryConfig.TIMEZONE,
                enable_utc=CeleryConfig.ENABLE_UTC,
                task_track_started=CeleryConfig.TASK_TRACK_STARTED,
                task_time_limit=CeleryConfig.TASK_TIME_LIMIT,
                worker_prefetch_multiplier=CeleryConfig.WORKER_PREFETCH_MULTIPLIER,
                task_acks_late=CeleryConfig.TASK_ACKS_LATE,
            )
        
        if app:
            cls._instance.conf.update(app.config)
            
            class ContextTask(cls._instance.Task):
                def __call__(self, *args, **kwargs):
                    with app.app_context():
                        return self.run(*args, **kwargs)
            
            cls._instance.Task = ContextTask
        
        return cls._instance


# 建立全域 Celery 實例
celery = CeleryFactory.create()


# ============================================
# 任務結果資料類別
# ============================================

@dataclass
class TaskResult:
    """任務結果的資料類別"""
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        result = {'status': self.status}
        if self.message:
            result['message'] = self.message
        if self.data:
            result.update(self.data)
        return result


class TaskStatus(Enum):
    """任務狀態枚舉"""
    SUCCESS = 'success'
    FAILED = 'failed'
    SKIPPED = 'skipped'
    SENT = 'sent'
    CREATED = 'created'
    CLEANED = 'cleaned'
    SCHEDULED = 'scheduled'
    COMPLETED = 'completed'
    ERROR = 'error'


# ============================================
# 抽象任務基底類別
# ============================================

class BaseTaskHandler(ABC):
    """
    任務處理器的抽象基底類別
    
    遵循樣板方法模式（Template Method Pattern）
    """
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> TaskResult:
        """執行任務的抽象方法"""
        pass
    
    def validate(self, *args, **kwargs) -> bool:
        """驗證輸入（可覆寫）"""
        return True
    
    def on_success(self, result: TaskResult) -> None:
        """成功後的回調（可覆寫）"""
        pass
    
    def on_failure(self, error: Exception) -> None:
        """失敗後的回調（可覆寫）"""
        pass
    
    def run(self, *args, **kwargs) -> Dict:
        """執行任務（樣板方法）"""
        if not self.validate(*args, **kwargs):
            return TaskResult(TaskStatus.SKIPPED.value, 'Validation failed').to_dict()
        
        try:
            result = self.execute(*args, **kwargs)
            self.on_success(result)
            return result.to_dict()
        except Exception as e:
            self.on_failure(e)
            raise


# ============================================
# Email 任務類別
# ============================================

class EmailTaskHandler(BaseTaskHandler):
    """Email 任務處理器"""
    
    def __init__(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None):
        self.to_email = to_email
        self.subject = subject
        self.body = body
        self.html_body = html_body
    
    def validate(self) -> bool:
        return bool(self.to_email and self.subject and self.body)
    
    def execute(self) -> TaskResult:
        from flask import current_app
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        mail_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = current_app.config.get('MAIL_PORT', 587)
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@taskmanager.com')
        
        if not mail_username or not mail_password:
            current_app.logger.warning("Email not configured, skipping send")
            return TaskResult(TaskStatus.SKIPPED.value, 'Email not configured')
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = self.subject
        msg['From'] = mail_sender
        msg['To'] = self.to_email
        
        msg.attach(MIMEText(self.body, 'plain'))
        if self.html_body:
            msg.attach(MIMEText(self.html_body, 'html'))
        
        with smtplib.SMTP(mail_server, mail_port) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_sender, self.to_email, msg.as_string())
        
        return TaskResult(TaskStatus.SENT.value, data={'to': self.to_email})


class PasswordResetEmailHandler(BaseTaskHandler):
    """密碼重設 Email 處理器"""
    
    def __init__(self, user_email: str, reset_token: str, reset_url: Optional[str] = None):
        self.user_email = user_email
        self.reset_token = reset_token
        self.reset_url = reset_url or f"http://localhost:3000/reset-password?token={reset_token}"
    
    def execute(self) -> TaskResult:
        subject = "Password Reset Request - NexusTeam"
        body = f"""
        You requested a password reset for your NexusTeam account.
        
        Click the link below to reset your password:
        {self.reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Password Reset Request</h2>
            <p>You requested a password reset for your NexusTeam account.</p>
            <p>
                <a href="{self.reset_url}" 
                   style="display: inline-block; padding: 12px 24px; 
                          background-color: #4F46E5; color: white; 
                          text-decoration: none; border-radius: 6px;">
                    Reset Password
                </a>
            </p>
            <p style="color: #666; font-size: 14px;">
                This link will expire in 1 hour.
            </p>
            <p style="color: #999; font-size: 12px;">
                If you didn't request this, please ignore this email.
            </p>
        </body>
        </html>
        """
        
        email_handler = EmailTaskHandler(self.user_email, subject, body, html_body)
        send_email_task.delay(self.user_email, subject, body, html_body)
        return TaskResult(TaskStatus.SCHEDULED.value)


# ============================================
# 清理任務類別
# ============================================

class CleanupTaskHandler(BaseTaskHandler):
    """清理任務的基底類別"""
    
    def __init__(self, days: int):
        self.days = days
        self.cutoff_date = datetime.utcnow() - timedelta(days=days)


class LoginAttemptsCleanupHandler(CleanupTaskHandler):
    """登入嘗試清理處理器"""
    
    def execute(self) -> TaskResult:
        from models import LoginAttempt, db
        
        deleted = LoginAttempt.query.filter(
            LoginAttempt.timestamp < self.cutoff_date
        ).delete()
        
        db.session.commit()
        return TaskResult(TaskStatus.CLEANED.value, data={'deleted_count': deleted})


class PasswordResetTokenCleanupHandler(BaseTaskHandler):
    """密碼重設 Token 清理處理器"""
    
    def execute(self) -> TaskResult:
        from models import PasswordResetToken, db
        
        expired_deleted = PasswordResetToken.query.filter(
            PasswordResetToken.expires_at < datetime.utcnow()
        ).delete()
        
        used_cutoff = datetime.utcnow() - timedelta(days=7)
        used_deleted = PasswordResetToken.query.filter(
            PasswordResetToken.used.is_(True),
            PasswordResetToken.used_at < used_cutoff
        ).delete()
        
        db.session.commit()
        return TaskResult(
            TaskStatus.CLEANED.value,
            data={'expired_deleted': expired_deleted, 'used_deleted': used_deleted}
        )


class NotificationCleanupHandler(CleanupTaskHandler):
    """通知清理處理器"""
    
    def execute(self) -> TaskResult:
        from models import Notification, db
        
        deleted = Notification.query.filter(
            Notification.is_read.is_(True),
            Notification.created_at < self.cutoff_date
        ).delete()
        
        db.session.commit()
        return TaskResult(TaskStatus.CLEANED.value, data={'deleted_count': deleted})


class ActivityLogCleanupHandler(CleanupTaskHandler):
    """活動記錄清理處理器"""
    
    def execute(self) -> TaskResult:
        from models import ActivityLog, db
        
        deleted = ActivityLog.query.filter(
            ActivityLog.timestamp < self.cutoff_date
        ).delete()
        
        db.session.commit()
        return TaskResult(TaskStatus.CLEANED.value, data={'deleted_count': deleted})


# ============================================
# 通知任務類別
# ============================================

class BulkNotificationHandler(BaseTaskHandler):
    """批量通知處理器"""
    
    def __init__(self, user_ids: List[int], notification_type: str, 
                 title: str, content: str, 
                 project_id: Optional[int] = None, 
                 task_id: Optional[int] = None):
        self.user_ids = user_ids
        self.notification_type = notification_type
        self.title = title
        self.content = content
        self.project_id = project_id
        self.task_id = task_id
    
    def validate(self) -> bool:
        return bool(self.user_ids and self.notification_type and self.title)
    
    def execute(self) -> TaskResult:
        from models import db, Notification
        
        notifications = []
        for user_id in self.user_ids:
            notification = Notification(
                user_id=user_id,
                type=self.notification_type,
                title=self.title,
                content=self.content,
                related_project_id=self.project_id,
                related_task_id=self.task_id
            )
            notifications.append(notification)
        
        db.session.bulk_save_objects(notifications)
        db.session.commit()
        
        from cache import invalidate_notification_count
        for user_id in self.user_ids:
            invalidate_notification_count(user_id)
        
        return TaskResult(TaskStatus.CREATED.value, data={'count': len(notifications)})


class TaskReminderHandler(BaseTaskHandler):
    """任務提醒處理器"""
    
    def __init__(self, task_id: int):
        self.task_id = task_id
    
    def execute(self) -> TaskResult:
        from models import Task, User, Notification, db
        
        task = Task.query.get(self.task_id)
        if not task or not task.assigned_to:
            return TaskResult(TaskStatus.SKIPPED.value, 'Task not found or not assigned')
        
        user = User.query.get(task.assigned_to)
        if not user:
            return TaskResult(TaskStatus.SKIPPED.value, 'User not found')
        
        notification = Notification(
            user_id=user.id,
            type='task_reminder',
            title='Task Due Soon',
            content=f'Task "{task.title}" is due on {task.due_date.strftime("%Y-%m-%d")}',
            related_project_id=task.project_id,
            related_task_id=task.id
        )
        db.session.add(notification)
        db.session.commit()
        
        send_notification_email.delay(
            user.email,
            'Task Due Soon',
            f'Your task "{task.title}" is due on {task.due_date.strftime("%Y-%m-%d")}.'
        )
        
        return TaskResult(TaskStatus.SENT.value, data={'task_id': self.task_id, 'user_id': user.id})


# ============================================
# 統計任務類別
# ============================================

class ProjectStatSnapshotHandler(BaseTaskHandler):
    """專案統計快照處理器"""
    
    def __init__(self, project_id: int):
        self.project_id = project_id
    
    def execute(self) -> TaskResult:
        from models import db, Task, ProjectMember, ProjectStatSnapshot
        from sqlalchemy import func, case, and_
        
        task_stats = db.session.query(
            func.count(Task.id).label('total'),
            func.sum(case((Task.status == 'todo', 1), else_=0)).label('todo'),
            func.sum(case((Task.status == 'in_progress', 1), else_=0)).label('in_progress'),
            func.sum(case((Task.status == 'done', 1), else_=0)).label('done'),
            func.sum(case((and_(Task.due_date < datetime.utcnow(), Task.status != 'done'), 1), else_=0)).label('overdue')
        ).filter(Task.project_id == self.project_id).first()
        
        member_count = ProjectMember.query.filter_by(project_id=self.project_id).count() + 1
        
        snapshot = ProjectStatSnapshot(
            project_id=self.project_id,
            total_tasks=task_stats.total or 0,
            completed_tasks=task_stats.done or 0,
            in_progress_tasks=task_stats.in_progress or 0,
            todo_tasks=task_stats.todo or 0,
            overdue_tasks=task_stats.overdue or 0,
            member_count=member_count,
            snapshot_date=datetime.utcnow().date()
        )
        
        db.session.add(snapshot)
        
        try:
            db.session.commit()
            return TaskResult(TaskStatus.CREATED.value, data={'project_id': self.project_id})
        except Exception as e:
            db.session.rollback()
            return TaskResult(TaskStatus.ERROR.value, str(e))


class OverdueTasksChecker(BaseTaskHandler):
    """逾期任務檢查處理器"""
    
    def execute(self) -> TaskResult:
        from models import Task, Notification, db
        from datetime import date
        
        today = date.today()
        
        due_today = Task.query.filter(
            Task.due_date <= datetime.combine(today, datetime.max.time()),
            Task.due_date >= datetime.combine(today, datetime.min.time()),
            Task.status != 'done',
            Task.assigned_to.isnot(None)
        ).all()
        
        overdue = Task.query.filter(
            Task.due_date < datetime.combine(today, datetime.min.time()),
            Task.status != 'done',
            Task.assigned_to.isnot(None)
        ).all()
        
        notifications_created = 0
        
        for task in due_today:
            notification = Notification(
                user_id=task.assigned_to,
                type='task_due_today',
                title='Task Due Today',
                content=f'Task "{task.title}" is due today!',
                related_project_id=task.project_id,
                related_task_id=task.id
            )
            db.session.add(notification)
            notifications_created += 1
        
        for task in overdue:
            notification = Notification(
                user_id=task.assigned_to,
                type='task_overdue',
                title='Task Overdue',
                content=f'Task "{task.title}" is overdue!',
                related_project_id=task.project_id,
                related_task_id=task.id
            )
            db.session.add(notification)
            notifications_created += 1
        
        db.session.commit()
        
        return TaskResult(
            TaskStatus.COMPLETED.value,
            data={
                'due_today': len(due_today),
                'overdue': len(overdue),
                'notifications_created': notifications_created
            }
        )


# ============================================
# Celery 任務定義（使用處理器類別）
# ============================================

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None):
    """寄送 Email 的背景任務"""
    try:
        handler = EmailTaskHandler(to_email, subject, body, html_body)
        return handler.run()
    except Exception as e:
        self.retry(exc=e)


@celery.task
def send_password_reset_email(user_email: str, reset_token: str, reset_url: Optional[str] = None):
    """寄送密碼重設 Email"""
    handler = PasswordResetEmailHandler(user_email, reset_token, reset_url)
    return handler.run()


@celery.task
def send_notification_email(user_email: str, notification_title: str, notification_content: str):
    """寄送通知 Email"""
    subject = f"[NexusTeam] {notification_title}"
    body = f"{notification_content}\n\n---\nLogin to NexusTeam to see more details."
    return send_email_task.delay(user_email, subject, body)


@celery.task
def create_bulk_notifications(user_ids: List[int], notification_type: str, title: str, 
                              content: str, project_id: Optional[int] = None, 
                              task_id: Optional[int] = None):
    """批量建立通知"""
    handler = BulkNotificationHandler(user_ids, notification_type, title, content, project_id, task_id)
    return handler.run()


@celery.task
def send_task_reminder(task_id: int):
    """發送任務提醒"""
    handler = TaskReminderHandler(task_id)
    return handler.run()


@celery.task
def cleanup_old_login_attempts(days: int = 30):
    """清理舊的登入嘗試記錄"""
    handler = LoginAttemptsCleanupHandler(days)
    return handler.run()


@celery.task
def cleanup_expired_password_reset_tokens():
    """清理過期和已使用的密碼重設 Token"""
    handler = PasswordResetTokenCleanupHandler()
    return handler.run()


@celery.task
def cleanup_old_notifications(days: int = 90):
    """清理舊的已讀通知"""
    handler = NotificationCleanupHandler(days)
    return handler.run()


@celery.task
def cleanup_old_activity_logs(days: int = 180):
    """清理舊的活動記錄"""
    handler = ActivityLogCleanupHandler(days)
    return handler.run()


@celery.task
def generate_project_stat_snapshot(project_id: int):
    """產生專案統計快照"""
    handler = ProjectStatSnapshotHandler(project_id)
    return handler.run()


@celery.task
def generate_all_project_snapshots():
    """為所有活躍專案產生統計快照"""
    from models import Project
    
    projects = Project.query.filter_by(status='active').all()
    results = []
    
    for project in projects:
        result = generate_project_stat_snapshot.delay(project.id)
        results.append({'project_id': project.id, 'task_id': result.id})
    
    return {'status': 'scheduled', 'projects': results}


@celery.task
def check_overdue_tasks():
    """檢查並發送逾期任務提醒"""
    handler = OverdueTasksChecker()
    return handler.run()


# ============================================
# Celery Beat 排程設定
# ============================================

class ScheduleConfig:
    """排程設定類別"""
    
    DAILY = 86400  # 每天（秒）
    HOURLY = 3600  # 每小時（秒）
    
    @classmethod
    def get_beat_schedule(cls) -> Dict:
        """取得排程設定"""
        return {
            'cleanup-old-data': {
                'task': 'celery_tasks.cleanup_old_login_attempts',
                'schedule': cls.DAILY,
                'args': (30,)
            },
            'cleanup-expired-tokens': {
                'task': 'celery_tasks.cleanup_expired_password_reset_tokens',
                'schedule': cls.DAILY,
            },
            'cleanup-old-notifications': {
                'task': 'celery_tasks.cleanup_old_notifications',
                'schedule': cls.DAILY,
                'args': (90,)
            },
            'generate-daily-snapshots': {
                'task': 'celery_tasks.generate_all_project_snapshots',
                'schedule': cls.DAILY,
            },
            'check-overdue-tasks': {
                'task': 'celery_tasks.check_overdue_tasks',
                'schedule': cls.DAILY,
            },
        }


celery.conf.beat_schedule = ScheduleConfig.get_beat_schedule()
