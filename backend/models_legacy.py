"""
============================================
models.py - 資料模型定義（資料庫結構）
============================================

【這個檔案的作用】
定義所有資料表的結構，就像是設計資料庫的「藍圖」。
每個 class 都對應到資料庫中的一個「表」（table）。

【什麼是 ORM？】
ORM (Object-Relational Mapping) 讓你用 Python 的 class 來操作資料庫，
不用直接寫 SQL 語法。

例如：
- 不用 ORM: SELECT * FROM user WHERE id = 1
- 用 ORM: User.query.get(1)

【資料模型之間的關係圖】

User（使用者）
  │
  ├──擁有──> Project（專案）──包含──> Task（任務）
  │                │                    │
  │                └──有多個成員         └──有多個評論
  │                     │                    │
  │                     v                    v
  └──加入──> ProjectMember           TaskComment
                                          │
  └──收到──> Notification（通知）<────關聯┘

【和前端的對應】
後端 models.py      ←→      前端 types.ts
─────────────────────────────────────────
User                ←→      User
Project             ←→      Project
Task                ←→      Task
TaskComment         ←→      Comment
Notification        ←→      Notification

【資料轉換】
後端資料會經過 apiService.ts 的 transform 函數轉換成前端格式
例如：transformUser(), transformTask(), transformProject()
"""

# ============================================
# 導入需要的模組
# ============================================

# SQLAlchemy 是 Python 最流行的 ORM 框架
# Flask-SQLAlchemy 是專門給 Flask 用的版本
from flask_sqlalchemy import SQLAlchemy

# datetime 用來處理日期和時間
from datetime import datetime

# ============================================
# 建立資料庫實例
# ============================================

"""
db = SQLAlchemy()
建立一個 SQLAlchemy 實例

這個 db 物件會在 app.py 中用 db.init_app(app) 初始化
之後所有的資料庫操作都會透過這個 db 物件
"""
db = SQLAlchemy()

# ============================================
# 1. User 模型（使用者）
# ============================================

class User(db.Model):
    """
    使用者模型
    
    【對應前端】types.ts 的 User interface
    
    【儲存的資料】
    - 帳號資訊（email、密碼）
    - 個人資料（名稱、頭像、部門等）
    - 系統資訊（上次登入時間、是否啟用等）
    
    【資料表名稱】
    SQLAlchemy 會自動把 class 名稱轉成小寫作為表名
    User → user
    
    【欄位說明】
    db.Column 定義一個欄位，參數說明：
    - 第一個參數：資料類型（Integer, String, Text 等）
    - primary_key=True：這是主鍵（唯一識別每筆資料）
    - unique=True：這個欄位的值不能重複
    - nullable=False：這個欄位不能是空的
    - index=True：建立索引，加快查詢速度
    - default=xxx：預設值
    """
    
    # 主鍵：每個使用者的唯一識別碼
    id = db.Column(db.Integer, primary_key=True)
    
    # Email：用來登入的帳號，必須唯一
    # String(255) 表示最多 255 個字元
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # 密碼雜湊：儲存加密後的密碼（不是明文！）
    password_hash = db.Column(db.String(225), nullable=False)
    
    # 使用者名稱：顯示用的名字
    username = db.Column(db.String(100), nullable=False)
    
    # ===== 選填欄位 =====
    
    # 頭像網址
    avatar_url = db.Column(db.String(500))
    
    # 個人簡介
    # Text 類型沒有長度限制，適合存放較長的文字
    bio = db.Column(db.Text)
    
    # 電話號碼
    phone = db.Column(db.String(20))
    
    # 部門
    department = db.Column(db.String(100))
    
    # 職位
    position = db.Column(db.String(100))
    
    # 帳號是否啟用（可以用來「軟刪除」使用者）
    is_active = db.Column(db.Boolean, default=True)
    
    # 上次登入時間
    last_login = db.Column(db.DateTime)
    
    # 建立時間（自動設定為現在時間）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ===== 角色系統 =====
    """
    使用者的系統角色
    - 'admin': 系統管理員，擁有最高權限
    - 'member': 一般成員（預設）
    
    這個角色是「系統層級」的角色，和專案內的角色（ProjectMember.role）不同
    """
    role = db.Column(db.String(20), nullable=False, default='member')
    
    def is_admin(self):
        """判斷使用者是否為系統管理員"""
        return self.role == 'admin'

    # ===== 關聯（Relationships）=====
    """
    db.relationship 定義和其他模型的關聯
    
    【什麼是關聯？】
    關聯讓你可以從一個物件存取相關的物件
    例如：user.owned_projects 可以取得這個使用者建立的所有專案
    
    【參數說明】
    - 第一個參數：關聯到哪個模型
    - backref：反向關聯的名稱（從另一邊存取回來）
    - lazy：載入策略（True 表示需要時才載入）
    - foreign_keys：指定用哪個外鍵建立關聯
    - cascade：串聯操作（刪除使用者時自動刪除相關資料）
    """
    
    # 使用者建立的專案（一對多：一個使用者可以建立多個專案）
    owned_projects = db.relationship('Project', backref='owner', lazy=True)
    
    # 指派給這個使用者的任務
    tasks_assigned = db.relationship('Task', foreign_keys='Task.assigned_to', backref='assignee', lazy=True)
    
    # 這個使用者建立的任務
    tasks_created = db.relationship('Task', foreign_keys='Task.created_by', backref='creator', lazy=True)
    
    # 使用者的通知（刪除使用者時也刪除通知）
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all,delete-orphan')
    
    # 使用者的活動記錄
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True)
    
    # 使用者發表的評論
    task_comments = db.relationship('TaskComment', backref='user', lazy=True)
    
    # 使用者上傳的檔案
    uploaded_files = db.relationship('Attachment', backref='uploader', lazy=True)
    
    # 使用者建立的任務範本
    created_templates = db.relationship('TaskTemplate', backref='creator', lazy=True)
    
    # 使用者的稽核記錄
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)

# ============================================
# 2. Project 模型（專案）
# ============================================

class Project(db.Model):
    """
    專案模型
    
    【對應前端】types.ts 的 Project interface
    
    【儲存的資料】
    - 基本資訊（名稱、描述）
    - 狀態（active, archived）
    - 時程（開始日期、結束日期）
    - 設定（預算、是否公開等）
    
    【和前端的對應】
    後端欄位名          ←→     前端欄位名
    ────────────────────────────────────
    id                  ←→     id
    name                ←→     name
    description         ←→     description
    owner_id            ←→     ownerId
    status              ←→     status
    created_at          ←→     createdAt
    """
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # 外鍵：連結到 User 表
    # db.ForeignKey('user.id') 表示這個欄位參照 user 表的 id 欄位
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 專案狀態：active（進行中）、archived（已封存）、completed（已完成）
    status = db.Column(db.String(20), default='active')
    
    # 時程相關
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    # 預算
    budget = db.Column(db.Float)
    
    # 是否公開（讓非成員也能看到）
    is_public = db.Column(db.Boolean, default=False)
    
    # 專案設定（JSON 格式，可以存任意資料）
    settings = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ===== 關聯 =====
    
    # 專案的任務（刪除專案時也刪除所有任務）
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all,delete-orphan')
    
    # 專案成員
    members = db.relationship('ProjectMember', backref='project', lazy=True, cascade='all,delete-orphan')
    
    # 專案相關的通知
    notifications = db.relationship('Notification', backref='project', lazy=True)
    
    # 專案的活動記錄
    activity_logs = db.relationship('ActivityLog', backref='project', lazy=True)
    
    # 專案的附件
    attachments = db.relationship('Attachment', backref='project', lazy=True)
    
    # 專案的標籤
    tags = db.relationship('Tag', backref='project', lazy=True, cascade='all,delete-orphan')
    
    # 任務範本
    templates = db.relationship('TaskTemplate', backref='project', lazy=True)
    
    # 統計快照
    stat_snapshots = db.relationship('ProjectStatSnapshot', backref='project', lazy=True)

    # ===== 索引（加快查詢速度）=====
    __table_args__ = (
        db.Index('idx_project_status', 'status'),      # 按狀態查詢
        db.Index('idx_project_owner', 'owner_id'),     # 按擁有者查詢
    )

# ============================================
# 3. ProjectMember 模型（專案成員）
# ============================================

class ProjectMember(db.Model):
    """
    專案成員模型（多對多關聯表）
    
    【為什麼需要這個表？】
    一個專案可以有多個成員，一個使用者可以加入多個專案。
    這種「多對多」的關係需要一個中間表來記錄。
    
    【儲存的資料】
    - 哪個使用者（user_id）
    - 加入哪個專案（project_id）
    - 在這個專案中的角色（admin 或 member）
    - 加入時間
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 外鍵：連結到使用者
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 外鍵：連結到專案
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    # 角色：admin（管理員）或 member（一般成員）
    role = db.Column(db.String(20), nullable=False, default='member')
    
    # 加入時間
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 關聯到使用者（可以用 member.user 取得使用者資料）
    user = db.relationship('User', backref='project_memberships')

    # 唯一性約束：同一個使用者不能重複加入同一個專案
    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='unique_project_member'),
    )

# ============================================
# 4. 多對多關聯表：任務與標籤
# ============================================

"""
這是一個簡單的關聯表，只有兩個外鍵
用來建立 Task 和 Tag 之間的多對多關係
（一個任務可以有多個標籤，一個標籤可以用在多個任務）
"""
task_tags = db.Table('task_tags',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# ============================================
# 5. Task 模型（任務）
# ============================================

class Task(db.Model):
    """
    任務模型
    
    【對應前端】types.ts 的 Task interface
    
    【儲存的資料】
    - 基本資訊（標題、描述）
    - 狀態和優先級
    - 負責人和建立者
    - 時程（截止日期、完成時間）
    - 工時（預估、實際）
    
    【狀態說明】
    - todo: 待辦
    - in_progress: 進行中
    - review: 審核中
    - done: 已完成
    
    【優先級說明】
    - low: 低
    - medium: 中
    - high: 高
    
    【和前端的對應】
    後端欄位名          ←→     前端欄位名
    ────────────────────────────────────
    id                  ←→     id
    project_id          ←→     projectId
    title               ←→     title
    description         ←→     description
    status              ←→     status（需轉換大小寫）
    priority            ←→     priority（需轉換大小寫）
    assigned_to         ←→     assigneeId
    due_date            ←→     dueDate
    notes               ←→     notes
    """
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # 狀態：todo, in_progress, review, done
    status = db.Column(db.String(20), nullable=False, default='todo')
    
    # 優先級：low, medium, high
    priority = db.Column(db.String(20), nullable=False, default='medium')
    
    # ===== 工時相關 =====
    
    # 預估工時（小時）
    estimated_hours = db.Column(db.Float)
    
    # 實際工時（小時）
    actual_hours = db.Column(db.Float)
    
    # 進度百分比（0-100）
    progress = db.Column(db.Integer, default=0)
    
    # 備註（非結構化的文字筆記）
    notes = db.Column(db.Text, nullable=True)

    # ===== 關聯欄位（外鍵）=====
    
    # 所屬專案
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    # 負責人（可以為空，表示尚未指派）
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # 建立者
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # ===== 時間欄位 =====
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 截止日期
    due_date = db.Column(db.DateTime, nullable=True)
    
    # 完成時間（當狀態變成 done 時設定）
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # ===== 關聯 =====
    
    # 任務的標籤（多對多）
    tags = db.relationship('Tag', secondary=task_tags, backref='tasks')
    
    # 任務的評論（刪除任務時也刪除評論）
    comments = db.relationship('TaskComment', backref='task', lazy=True, cascade='all,delete-orphan')
    
    # 任務的附件
    attachments = db.relationship('Attachment', backref='task', lazy=True)
    
    # 任務相關的通知
    notifications = db.relationship('Notification', backref='task', lazy=True)
    
    # 任務依賴關係
    dependencies = db.relationship('TaskDependency', foreign_keys='TaskDependency.task_id', 
                                  backref='dependent_task', cascade='all,delete-orphan')

    # ===== 索引（加快查詢速度）=====
    __table_args__ = (
        db.Index('idx_task_project_status', 'project_id', 'status'),   # 按專案和狀態查詢
        db.Index('idx_task_assigned_status', 'assigned_to', 'status'), # 按負責人和狀態查詢
        db.Index('idx_task_due_date', 'due_date'),                     # 按截止日期查詢
        db.Index('idx_task_created_at', 'created_at'),                 # 按建立時間查詢
        # 新增：效能優化索引
        db.Index('idx_task_assigned_due', 'assigned_to', 'due_date'),  # 查詢用戶即將到期的任務
        db.Index('idx_task_project_priority', 'project_id', 'priority'), # 按專案和優先級查詢
        db.Index('idx_task_project_assigned', 'project_id', 'assigned_to'), # 按專案和負責人查詢
    )

# ============================================
# 6. Notification 模型（通知）
# ============================================

class Notification(db.Model):
    """
    通知模型
    
    【對應前端】types.ts 的 Notification interface
    
    【儲存的資料】
    - 接收者（user_id）
    - 通知內容（type, title, content）
    - 是否已讀（is_read）
    - 相關的專案和任務（方便點擊跳轉）
    
    【通知類型】
    - task_assigned: 任務被指派給你
    - task_completed: 任務完成
    - comment_added: 有人在你的任務下留言
    - project_invite: 被邀請加入專案
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 接收通知的使用者
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 通知類型
    type = db.Column(db.String(50), nullable=False)
    
    # 通知標題
    title = db.Column(db.String(255), nullable=False)
    
    # 通知內容
    content = db.Column(db.Text)
    
    # 是否已讀
    is_read = db.Column(db.Boolean, default=False)
    
    # 相關的專案（可選）
    related_project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    
    # 相關的任務（可選）
    related_task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ===== 索引（加快查詢速度）=====
    __table_args__ = (
        db.Index('idx_notification_user_read', 'user_id', 'is_read'),     # 快速查詢未讀通知
        db.Index('idx_notification_user_created', 'user_id', 'created_at'), # 按時間排序的通知
        db.Index('idx_notification_type', 'type'),                         # 按類型查詢
    )

# ============================================
# 7. ActivityLog 模型（活動記錄）
# ============================================

class ActivityLog(db.Model):
    """
    活動記錄模型
    
    【用途】
    記錄專案中發生的所有事情，例如：
    - 誰在什麼時候建立了任務
    - 誰修改了什麼
    - 誰刪除了什麼
    
    這對於追蹤變更歷史和除錯非常有用
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 在哪個專案中
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    # 誰執行的
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 什麼動作（create_task, update_task, delete_task 等）
    action = db.Column(db.String(100), nullable=False)
    
    # 操作的資源類型（task, project, comment 等）
    resource_type = db.Column(db.String(50))
    
    # 操作的資源 ID
    resource_id = db.Column(db.Integer)
    
    # 詳細資訊（JSON 格式，記錄變更的內容）
    details = db.Column(db.JSON)
    
    # 發生時間
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================
# 8. TaskComment 模型（任務評論）
# ============================================

class TaskComment(db.Model):
    """
    任務評論模型
    
    【對應前端】types.ts 的 Comment interface
    
    【儲存的資料】
    - 在哪個任務下的評論（task_id）
    - 誰發表的（user_id）
    - 評論內容（content）
    - 是回覆哪則評論（parent_id，支援巢狀回覆）
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 所屬任務
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    
    # 發表者
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 父評論（如果是回覆的話）
    parent_id = db.Column(db.Integer, db.ForeignKey('task_comment.id'), nullable=True)
    
    # 評論內容
    content = db.Column(db.Text, nullable=False)
    
    # 是否被編輯過
    is_edited = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # 自我關聯（用於巢狀回覆）
    # 可以用 comment.replies 取得這則評論的所有回覆
    # 可以用 comment.parent 取得這則評論回覆的對象
    replies = db.relationship('TaskComment', backref=db.backref('parent', remote_side=[id]))

# ============================================
# 9. Attachment 模型（附件）
# ============================================

class Attachment(db.Model):
    """
    附件模型
    
    【用途】
    儲存上傳到任務或專案的檔案資訊
    注意：實際檔案存在檔案系統或雲端儲存，這裡只存元資料
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 儲存時的檔名（可能會改名避免衝突）
    filename = db.Column(db.String(255), nullable=False)
    
    # 原始檔名（使用者上傳時的名稱）
    original_filename = db.Column(db.String(255), nullable=False)
    
    # 檔案在伺服器上的路徑
    file_path = db.Column(db.String(500))
    
    # 檔案的網址（如果存在雲端）
    file_url = db.Column(db.String(500))
    
    # 檔案大小（bytes）
    file_size = db.Column(db.Integer)
    
    # 檔案類型（MIME type，如 image/jpeg）
    file_type = db.Column(db.String(100))
    
    # 關聯到任務（可選）
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    
    # 關聯到專案（可選）
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    
    # 上傳者
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================
# 10. Tag 模型（標籤）
# ============================================

class Tag(db.Model):
    """
    標籤模型
    
    【用途】
    用來分類和標記任務，例如：「bug」、「feature」、「urgent」
    每個專案有自己的標籤，標籤可以有顏色
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 標籤名稱
    name = db.Column(db.String(50), nullable=False)
    
    # 標籤顏色（十六進位色碼）
    color = db.Column(db.String(7), default='#667eea')
    
    # 所屬專案
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 唯一性約束：同一個專案中不能有同名的標籤
    __table_args__ = (
        db.UniqueConstraint('project_id', 'name', name='unique_project_tag'),
    )

# ============================================
# 11. TaskDependency 模型（任務依賴）
# ============================================

class TaskDependency(db.Model):
    """
    任務依賴模型
    
    【用途】
    定義任務之間的依賴關係，例如：
    - 任務 A 必須等任務 B 完成才能開始
    - 任務 C 和任務 D 相關
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 這個任務
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    
    # 依賴的任務
    depends_on_task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    
    # 依賴類型
    # blocks: 阻擋（必須等另一個完成）
    # requires: 需要（前置任務）
    # relates_to: 相關（只是相關，沒有強制關係）
    dependency_type = db.Column(db.String(20), default='blocks')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯到被依賴的任務
    depends_on = db.relationship('Task', foreign_keys=[depends_on_task_id])
    
    # 唯一性約束：同一個依賴關係不能重複
    __table_args__ = (
        db.UniqueConstraint('task_id', 'depends_on_task_id', name='unique_dependency'),
    )

# ============================================
# 12. TaskTemplate 模型（任務範本）
# ============================================

class TaskTemplate(db.Model):
    """
    任務範本模型
    
    【用途】
    儲存常用的任務結構，方便快速建立類似的任務
    例如：「Bug 回報範本」、「新功能開發範本」
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 範本名稱
    name = db.Column(db.String(255), nullable=False)
    
    # 範本描述
    description = db.Column(db.Text)
    
    # 所屬專案
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    # 建立者
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 範本資料（JSON 格式，包含預設的標題、描述、標籤等）
    template_data = db.Column(db.JSON)
    
    # 是否公開（讓其他專案也能使用）
    is_public = db.Column(db.Boolean, default=False)
    
    # 使用次數
    usage_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

# ============================================
# 13. AuditLog 模型（稽核記錄）
# ============================================

class AuditLog(db.Model):
    """
    稽核記錄模型
    
    【用途】
    記錄所有敏感操作，用於安全稽核和問題追蹤
    比 ActivityLog 更詳細，包含 IP、User Agent 等資訊
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 執行操作的使用者
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 操作類型
    action = db.Column(db.String(100), nullable=False)
    
    # 操作的資源類型
    resource_type = db.Column(db.String(50))
    
    # 操作的資源 ID
    resource_id = db.Column(db.Integer)
    
    # 來源 IP 位址
    ip_address = db.Column(db.String(45))
    
    # 使用者瀏覽器資訊
    user_agent = db.Column(db.String(255))
    
    # HTTP 請求方法
    request_method = db.Column(db.String(10))
    
    # 請求路徑
    request_path = db.Column(db.String(255))
    
    # 回應狀態碼
    response_status = db.Column(db.Integer)
    
    # 詳細資訊
    details = db.Column(db.JSON)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================
# 14. UserPreference 模型（使用者偏好設定）
# ============================================

class UserPreference(db.Model):
    """
    使用者偏好設定模型
    
    【用途】
    儲存使用者的個人化設定，例如：
    - 通知偏好（要不要收 email、推播）
    - 介面設定（深色/淺色主題、語言）
    - 預設值（預設的任務檢視方式）
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 使用者（一對一關係）
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # ===== 通知設定 =====
    
    # 是否接收 email 通知
    email_notifications = db.Column(db.Boolean, default=True)
    
    # 是否接收推播通知
    push_notifications = db.Column(db.Boolean, default=True)
    
    # 要接收哪些類型的通知（JSON 格式）
    notification_types = db.Column(db.JSON)
    
    # ===== 介面設定 =====
    
    # 主題（light 或 dark）
    theme = db.Column(db.String(20), default='light')
    
    # 語言
    language = db.Column(db.String(10), default='zh-TW')
    
    # 時區
    timezone = db.Column(db.String(50), default='Asia/Taipei')
    
    # 日期格式
    date_format = db.Column(db.String(20), default='YYYY-MM-DD')
    
    # ===== 預設值 =====
    
    # 預設的任務檢視方式（list 或 kanban）
    default_task_view = db.Column(db.String(20), default='list')
    
    # 預設的專案排序方式
    default_project_sort = db.Column(db.String(20), default='updated')
    
    # 其他設定（JSON 格式，可擴展）
    settings = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # 關聯到使用者（一對一）
    user = db.relationship('User', backref=db.backref('preference', uselist=False))

# ============================================
# 15. ProjectStatSnapshot 模型（專案統計快照）
# ============================================

class ProjectStatSnapshot(db.Model):
    """
    專案統計快照模型
    
    【用途】
    定期儲存專案的統計數據，用於：
    - 顯示歷史趨勢圖
    - 分析專案進度
    - 產生報表
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 哪個專案
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    # ===== 任務統計 =====
    
    total_tasks = db.Column(db.Integer, default=0)         # 總任務數
    completed_tasks = db.Column(db.Integer, default=0)     # 已完成
    in_progress_tasks = db.Column(db.Integer, default=0)   # 進行中
    todo_tasks = db.Column(db.Integer, default=0)          # 待辦
    overdue_tasks = db.Column(db.Integer, default=0)       # 逾期
    
    # ===== 成員統計 =====
    
    member_count = db.Column(db.Integer, default=0)        # 總成員數
    active_member_count = db.Column(db.Integer, default=0) # 活躍成員數
    
    # ===== 平均值 =====
    
    # 平均任務完成時間（小時）
    avg_task_completion_time = db.Column(db.Float)
    
    # 每個成員平均任務數
    avg_tasks_per_member = db.Column(db.Float)
    
    # 更詳細的統計（JSON 格式）
    detailed_stats = db.Column(db.JSON)
    
    # 快照日期
    snapshot_date = db.Column(db.Date, default=datetime.utcnow().date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 唯一性約束：每個專案每天只能有一個快照
    __table_args__ = (
        db.UniqueConstraint('project_id', 'snapshot_date', name='unique_daily_snapshot'),
    )

# ============================================
# 16. LoginAttempt 模型（登入嘗試記錄）
# ============================================

class LoginAttempt(db.Model):
    """
    登入嘗試記錄模型
    
    【用途】
    記錄所有登入嘗試，用於：
    - 偵測暴力破解攻擊
    - 實作帳號鎖定機制
    - 安全稽核
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 嘗試登入的 email
    email = db.Column(db.String(255), nullable=False, index=True)
    
    # 來源 IP 位址
    ip_address = db.Column(db.String(45))
    
    # 登入是否成功
    success = db.Column(db.Boolean, default=False)
    
    # 失敗原因（如果失敗）
    failure_reason = db.Column(db.String(100))
    
    # 嘗試時間
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 索引：加快查詢速度
    __table_args__ = (
        db.Index('idx_login_attempt_email_time', 'email', 'timestamp'),
    )

# ============================================
# 17. PasswordResetToken 模型（密碼重設 Token）
# ============================================

class PasswordResetToken(db.Model):
    """
    密碼重設 Token 模型
    
    【用途】
    儲存「忘記密碼」功能產生的重設 token
    
    【安全措施】
    - Token 有過期時間（預設 1 小時）
    - 使用後會標記為已使用
    - 一個使用者同時只能有一個有效的 token
    """
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 使用者 ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 重設 token（安全隨機字串）
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # 過期時間
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # 是否已使用
    used = db.Column(db.Boolean, default=False)
    
    # 建立時間
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 使用時間（如果已使用）
    used_at = db.Column(db.DateTime)
    
    # 關聯到使用者
    user = db.relationship('User', backref='password_reset_tokens')
