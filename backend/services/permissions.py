"""
============================================
services/permissions.py - 權限檢查服務
============================================

【為什麼需要這個檔案？】
在一個團隊任務管理系統中，權限控制非常重要：
- 不是每個人都能看到所有專案
- 不是每個人都能編輯所有任務
- 只有管理員才能刪除專案或管理成員

這個檔案就是專門處理「誰可以做什麼事」的問題。

【為什麼要把權限邏輯獨立出來？】
1. 避免循環導入（Circular Import）問題：
   - 假設 tasks.py 需要檢查專案權限，它會 import projects.py
   - 假設 projects.py 也需要用到 tasks.py 的東西
   - 這樣就會造成 A import B，B import A 的循環，程式會出錯
   - 把共用的邏輯放到獨立的模組，大家都 import 這個模組就沒問題了

2. 程式碼重用（DRY - Don't Repeat Yourself）：
   - 權限檢查的邏輯可能在很多地方都用到
   - 與其複製貼上，不如寫成函數讓大家共用
   - 如果規則要改，只要改一個地方

3. 容易測試和維護：
   - 所有權限邏輯集中在一個地方
   - 方便寫單元測試
   - 新加入的開發者一看就知道權限規則在哪

【權限模型說明】
這個系統的權限是基於「專案」的：
┌─────────────────────────────────────────────────────────────┐
│                        專案 (Project)                         │
├─────────────────────────────────────────────────────────────┤
│  Owner (擁有者)     → 最高權限，可以做任何事                    │
│  Admin (管理員)     → 可以管理成員、編輯專案設定                 │
│  Member (一般成員)  → 可以檢視專案、建立和編輯任務               │
│  外部人員           → 完全無法存取專案內容                      │
└─────────────────────────────────────────────────────────────┘

任務的權限則繼承自專案：
- 如果你能存取專案，就能看到專案內的任務
- 如果你是專案管理員、任務建立者或任務負責人，就能編輯任務

【使用方式】
from services.permissions import check_project_access, check_project_admin

# 檢查使用者是否能存取專案
has_access, project, role = check_project_access(project_id, current_user.id)
if not has_access:
    return jsonify({'error': '沒有權限存取此專案'}), 403
"""

# ============================================
# 導入模組區域
# ============================================

from typing import Tuple, Optional
# Tuple: Python 的元組型別，用於回傳多個值
#   例如：Tuple[bool, str] 表示回傳 (布林值, 字串) 的組合
# Optional: 表示這個值可能是某個型別或是 None
#   例如：Optional[str] 等於 Union[str, None]，表示可能是字串或 None

from sqlalchemy.orm import joinedload
# joinedload 是 SQLAlchemy 的「預先載入」功能
#
# 【問題情境】
# 假設我們要查詢一個專案和它的擁有者：
#   project = Project.query.get(1)      # 查詢 1：取得專案
#   owner_name = project.owner.name     # 查詢 2：取得擁有者（觸發額外查詢！）
# 這就是「N+1 問題」：如果查 10 個專案，就會多 10 次查詢來取得各自的 owner
#
# 【使用 joinedload 解決】
#   project = Project.query.options(joinedload(Project.owner)).get(1)
# 這樣只需要一次查詢，用 SQL JOIN 一次把專案和擁有者都拿到
#
# 【效能比較】
#   沒有 joinedload：SELECT ... FROM projects; SELECT ... FROM users WHERE id=1;
#   有 joinedload：  SELECT ... FROM projects LEFT JOIN users ON ...（只有一次）

import logging
# Python 標準的日誌模組
# 比 print() 好的地方：
#   - 可以設定不同的日誌級別（DEBUG, INFO, WARNING, ERROR, CRITICAL）
#   - 可以輸出到檔案、遠端伺服器等不同地方
#   - 可以看到時間戳記、程式位置等資訊
#   - 生產環境可以關閉 DEBUG 訊息

# 建立這個模組專用的 logger
# __name__ 會是 'services.permissions'，這樣在日誌中可以看到是哪個模組產生的
logger = logging.getLogger(__name__)


# ============================================
# 專案權限檢查函數
# ============================================

def check_project_access(project_id: int, user_id: int) -> Tuple[bool, Optional[object], Optional[str]]:
    """
    檢查使用者是否有權限存取專案

    這是最基本的權限檢查：「這個使用者可以看到這個專案嗎？」

    【參數說明】
    Args:
        project_id: int
            專案的唯一識別碼
            在資料庫中，每個專案都有一個獨一無二的數字 ID

        user_id: int
            使用者的唯一識別碼
            通常來自 current_user.id（登入中的使用者）

    【回傳值說明】
    Returns:
        Tuple[bool, Optional[object], Optional[str]]
        回傳一個包含三個值的元組：

        1. has_access (bool): 是否有權限
           - True: 使用者可以存取這個專案
           - False: 使用者無法存取這個專案

        2. project (Optional[Project]): 專案物件
           - 有權限時：回傳完整的 Project 物件，包含專案的所有資訊
           - 無權限時：回傳 None
           - 為什麼要回傳專案？因為呼叫者通常需要用到專案，這樣就不用再查一次

        3. role (Optional[str]): 使用者在專案中的角色
           - 'owner': 專案擁有者（建立者）
           - 'admin': 專案管理員
           - 'member': 一般成員
           - None: 無權限時回傳
           - 為什麼要回傳角色？方便呼叫者做更細緻的權限控制

    【使用範例】
    Example:
        # 基本使用方式
        has_access, project, role = check_project_access(project_id, current_user.id)
        if not has_access:
            return jsonify({'error': 'Permission denied'}), 403

        # 根據角色做不同處理
        if role == 'owner':
            # 只有 owner 可以刪除專案
            project.delete()
        elif role in ['owner', 'admin']:
            # owner 和 admin 可以編輯專案設定
            project.name = new_name

    【函數內部運作流程】
    1. 查詢專案是否存在
    2. 檢查使用者是否為專案擁有者
    3. 如果不是擁有者，檢查是否為專案成員
    4. 回傳結果
    """
    # 延遲導入 models，避免循環導入問題
    #
    # 【為什麼要在函數內部導入？】
    # 正常情況下，import 語句放在檔案最上方是最佳實踐
    # 但這裡有特殊情況：
    #
    # 如果在檔案開頭寫 from models import Project，當 Python 載入這個檔案時：
    # 1. Python 開始載入 permissions.py
    # 2. 看到 from models import ...，去載入 models.py
    # 3. models.py 可能又 import 了其他模組
    # 4. 那些模組可能又 import permissions.py
    # 5. 但 permissions.py 還沒載入完成！→ 錯誤！
    #
    # 把 import 放在函數內部，只有在函數被呼叫時才會執行 import
    # 那時候所有模組都已經載入完成了，就不會有問題
    from models import Project, ProjectMember

    try:
        # ----------------------------------------
        # 步驟 1：查詢專案
        # ----------------------------------------
        # 使用 joinedload 預先載入 owner 關聯
        # 這樣在後續存取 project.owner 時不會產生額外的資料庫查詢
        #
        # .options() 是 SQLAlchemy 的方法，用來設定查詢選項
        # joinedload(Project.owner) 告訴 SQLAlchemy 用 JOIN 把 owner 一起查出來
        # .get(project_id) 是根據主鍵（Primary Key）查詢單一記錄
        project = Project.query.options(
            joinedload(Project.owner)
        ).get(project_id)

        # 如果專案不存在，直接回傳無權限
        # 這裡沒有分「專案不存在」和「沒有權限」兩種情況
        # 這是一個安全考量：不讓攻擊者知道專案是否存在
        if not project:
            return False, None, None

        # ----------------------------------------
        # 步驟 2：檢查是否為擁有者
        # ----------------------------------------
        # 專案的 owner_id 記錄了誰建立了這個專案
        # 如果 user_id 等於 owner_id，表示這個使用者就是專案擁有者
        if project.owner_id == user_id:
            return True, project, 'owner'

        # ----------------------------------------
        # 步驟 3：檢查是否為專案成員
        # ----------------------------------------
        # ProjectMember 是專案成員的關聯表
        # 記錄了「哪個使用者」以「什麼角色」加入了「哪個專案」
        #
        # filter_by() 是 SQLAlchemy 的篩選方法
        # 相當於 SQL 的 WHERE project_id = ? AND user_id = ?
        # .first() 取得第一筆符合的記錄，沒有則回傳 None
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()

        # 如果找到成員記錄，表示使用者是專案成員
        if member:
            # member.role 可能是 'admin' 或 'member'
            return True, project, member.role

        # 不是擁有者也不是成員，沒有權限
        return False, None, None

    except Exception as e:
        # 發生任何錯誤都記錄下來，並回傳無權限
        #
        # 【為什麼要 catch 所有例外？】
        # 權限檢查是安全相關的功能，如果出錯應該預設為「拒絕」
        # 這符合「失敗安全」(Fail-Safe) 原則
        #
        # exc_info=True 會在日誌中包含完整的錯誤堆疊（stack trace）
        # 方便開發者除錯
        logger.error(f"Error checking project access: {str(e)}", exc_info=True)
        return False, None, None


def check_project_admin(project_id: int, user_id: int) -> bool:
    """
    檢查使用者是否為專案管理員

    這個函數回答的問題是：「這個使用者可以管理這個專案嗎？」
    管理權限包括：邀請/移除成員、編輯專案設定、刪除任務等

    【誰算是管理員？】
    - 專案擁有者（Owner）：建立專案的人，擁有最高權限
    - 管理員（Admin）：被指定為 admin 角色的成員

    【參數說明】
    Args:
        project_id: int - 要檢查的專案 ID
        user_id: int - 要檢查的使用者 ID

    【回傳值說明】
    Returns:
        bool:
            - True: 使用者是專案管理員（可以管理專案）
            - False: 使用者不是管理員或無法存取專案

    【使用範例】
    Example:
        # 只有管理員才能邀請新成員
        if not check_project_admin(project_id, current_user.id):
            return jsonify({'error': 'Admin privileges required'}), 403

        # 執行需要管理員權限的操作
        new_member = ProjectMember(project_id=project_id, user_id=invited_user_id)
        db.session.add(new_member)

    【與 check_project_access 的差異】
    - check_project_access: 檢查是否能「看到」專案（包含一般成員）
    - check_project_admin: 檢查是否能「管理」專案（只有 owner 和 admin）

    ┌─────────────────────────────────────────────────────┐
    │  角色    │ check_project_access │ check_project_admin │
    ├─────────────────────────────────────────────────────┤
    │  owner   │        True          │        True         │
    │  admin   │        True          │        True         │
    │  member  │        True          │        False        │
    │  外部人  │        False         │        False        │
    └─────────────────────────────────────────────────────┘
    """
    from models import Project, ProjectMember

    try:
        # 先查詢專案是否存在
        project = Project.query.get(project_id)

        if not project:
            return False

        # 擁有者自動視為管理員
        # 這是一個設計決策：擁有者應該能做任何事
        if project.owner_id == user_id:
            return True

        # 檢查是否為 admin 角色的成員
        # 注意這裡多了一個條件 role='admin'
        # 只有 admin 角色才會符合，一般 member 不會
        member = ProjectMember.query.filter_by(
            project_id=project_id,
            user_id=user_id,
            role='admin'  # 只找 admin 角色
        ).first()

        # 如果找到 admin 成員記錄，回傳 True
        # member is not None 等於 bool(member)，但更明確
        return member is not None

    except Exception as e:
        logger.error(f"Error checking project admin: {str(e)}", exc_info=True)
        # 出錯時預設為沒有權限（失敗安全原則）
        return False


def check_project_member(project_id: int, user_id: int) -> bool:
    """
    檢查使用者是否為專案成員（包含擁有者）

    這是一個「簡化版」的權限檢查，只回傳 True/False，
    不回傳專案物件和角色資訊。

    【為什麼需要這個函數？】
    有時候我們只想知道「有沒有權限」，不需要其他資訊。
    這個函數讓程式碼更簡潔：

    ┌─────────────────────────────────────────────────────────────────┐
    │ 使用 check_project_access（需要解構三個值）：                      │
    │   has_access, _, _ = check_project_access(project_id, user_id)  │
    │   if not has_access:                                            │
    │       return 403                                                │
    │                                                                 │
    │ 使用 check_project_member（更簡潔）：                            │
    │   if not check_project_member(project_id, user_id):             │
    │       return 403                                                │
    └─────────────────────────────────────────────────────────────────┘

    【參數說明】
    Args:
        project_id: int - 專案 ID
        user_id: int - 使用者 ID

    【回傳值說明】
    Returns:
        bool: 是否為專案成員
            - True: 使用者可以存取專案（是 owner、admin 或 member）
            - False: 使用者無法存取專案
    """
    # 重用 check_project_access 函數的邏輯
    # 只取第一個回傳值（has_access），忽略專案和角色
    #
    # 這展示了 Python 的解構賦值（destructuring）：
    # has_access, _, _ = check_project_access(...)
    # 底線 _ 是 Python 慣例，表示「這個值我不需要」
    has_access, _, _ = check_project_access(project_id, user_id)
    return has_access


# ============================================
# 任務權限檢查函數
# ============================================

def check_task_access(task_id: int, user_id: int) -> Tuple[bool, Optional[object], Optional[str]]:
    """
    檢查使用者是否有權限存取任務

    任務的權限繼承自專案：
    如果你能存取專案，你就能看到專案內的所有任務。

    【權限繼承圖解】
    ┌─────────────────────────────────────────────────────┐
    │              專案 (Project)                          │
    │              ↑                                       │
    │         使用者有權限？                                │
    │              ↓                                       │
    │    ┌─────────────────────────────────────┐          │
    │    │         任務 (Task)                  │          │
    │    │   使用者的權限 = 繼承自專案權限        │          │
    │    └─────────────────────────────────────┘          │
    └─────────────────────────────────────────────────────┘

    【參數說明】
    Args:
        task_id: int - 任務的唯一識別碼
        user_id: int - 使用者的唯一識別碼

    【回傳值說明】
    Returns:
        Tuple[bool, Optional[Task], Optional[str]]:
            - has_access: 是否有權限存取任務
            - task: 任務物件（有權限時）或 None（無權限時）
            - project_role: 使用者在專案中的角色
              （因為任務權限繼承自專案，所以回傳的是專案角色）

    【使用範例】
    Example:
        has_access, task, role = check_task_access(task_id, current_user.id)
        if not has_access:
            return jsonify({'error': 'Cannot access this task'}), 403

        # 現在可以安全地使用 task
        print(task.title)
    """
    from models import Task

    try:
        # ----------------------------------------
        # 步驟 1：查詢任務
        # ----------------------------------------
        task = Task.query.get(task_id)

        if not task:
            # 任務不存在
            return False, None, None

        # ----------------------------------------
        # 步驟 2：檢查專案權限
        # ----------------------------------------
        # 每個任務都屬於一個專案（task.project_id）
        # 只要使用者能存取該專案，就能看到任務
        has_access, _, role = check_project_access(task.project_id, user_id)

        if has_access:
            # 回傳任務物件和專案角色
            return True, task, role

        return False, None, None

    except Exception as e:
        logger.error(f"Error checking task access: {str(e)}", exc_info=True)
        return False, None, None


def can_modify_task(task_id: int, user_id: int) -> Tuple[bool, Optional[object]]:
    """
    檢查使用者是否可以修改任務

    這個函數回答的問題是：「這個使用者可以編輯這個任務嗎？」

    【誰可以修改任務？】
    可以修改任務的人（符合任一條件即可）：

    1. 專案擁有者（Owner）
       → 專案的建立者，對專案內的所有任務都有完全控制權

    2. 專案管理員（Admin）
       → 被賦予 admin 角色的成員，可以管理專案內的所有任務

    3. 任務建立者（Task Creator）
       → 建立這個任務的人，可以編輯自己建立的任務

    4. 任務負責人（Assignee）
       → 被指派處理這個任務的人，可以更新任務狀態等

    【權限判斷流程圖】
    ┌─────────────────────────────────────────────────────────────┐
    │                   使用者想要修改任務                          │
    │                          ↓                                   │
    │             ┌───────────────────────────┐                    │
    │             │ 是任務建立者或負責人嗎？     │                    │
    │             └───────────────────────────┘                    │
    │                    ↓ 是         ↓ 否                         │
    │               ┌──────┐    ┌────────────────────┐             │
    │               │ 允許 │    │ 是專案管理員嗎？    │             │
    │               └──────┘    └────────────────────┘             │
    │                               ↓ 是        ↓ 否               │
    │                          ┌──────┐    ┌──────┐                │
    │                          │ 允許 │    │ 拒絕 │                │
    │                          └──────┘    └──────┘                │
    └─────────────────────────────────────────────────────────────┘

    【參數說明】
    Args:
        task_id: int - 要修改的任務 ID
        user_id: int - 要檢查權限的使用者 ID

    【回傳值說明】
    Returns:
        Tuple[bool, Optional[Task]]:
            - can_modify: 是否可以修改任務
            - task: 任務物件（可修改時）或 None（無權限時）

    【使用範例】
    Example:
        can_modify, task = can_modify_task(task_id, current_user.id)
        if not can_modify:
            return jsonify({'error': 'You cannot modify this task'}), 403

        # 現在可以安全地修改任務
        task.title = new_title
        task.status = new_status
        db.session.commit()

    【設計思考：為什麼只回傳兩個值？】
    與 check_task_access 不同，這個函數不回傳角色。
    因為對於「能否修改」這個問題，我們只需要 Yes/No 的答案。
    角色資訊在這個情境下不重要，簡化回傳值讓使用更方便。
    """
    from models import Task

    try:
        # ----------------------------------------
        # 步驟 1：查詢任務
        # ----------------------------------------
        task = Task.query.get(task_id)

        if not task:
            return False, None

        # ----------------------------------------
        # 步驟 2：檢查是否為任務建立者或負責人
        # ----------------------------------------
        # task.created_by: 建立任務的使用者 ID
        # task.assigned_to: 被指派的使用者 ID（可能為 None）
        #
        # 使用 or 運算子，只要符合其中一個條件就為 True
        if task.created_by == user_id or task.assigned_to == user_id:
            return True, task

        # ----------------------------------------
        # 步驟 3：檢查是否為專案管理員
        # ----------------------------------------
        # 如果不是任務的直接相關人員，檢查是否有專案管理權限
        if check_project_admin(task.project_id, user_id):
            return True, task

        # 以上都不符合，沒有修改權限
        return False, None

    except Exception as e:
        logger.error(f"Error checking task modification permission: {str(e)}", exc_info=True)
        return False, None


# ============================================
# 補充說明：權限系統的設計原則
# ============================================
#
# 1. 最小權限原則（Principle of Least Privilege）
#    使用者只應該擁有完成任務所需的最小權限。
#    一般成員不需要管理專案的權限，所以不給。
#
# 2. 預設拒絕（Default Deny）
#    遇到不確定或錯誤的情況，預設回傳「沒有權限」。
#    這樣比較安全，寧可誤拒合法使用者，也不要讓非法存取通過。
#
# 3. 明確的角色定義
#    使用清楚的角色名稱（owner, admin, member）而不是數字等級。
#    這樣程式碼更容易理解和維護。
#
# 4. 權限繼承
#    任務的權限繼承自專案，減少複雜度。
#    不需要為每個任務個別設定權限。
#
# ============================================
# 未來可能的擴展方向
# ============================================
#
# 1. 更細緻的權限控制
#    例如：只能編輯某些欄位、只能在某些時間編輯
#
# 2. 權限組（Permission Groups）
#    預設的權限組合，方便批量設定
#
# 3. 臨時權限
#    設定權限的有效期限
#
# 4. 權限審計日誌
#    記錄所有權限檢查的結果，用於安全分析
