"""
============================================
members.py - 成員管理 API
============================================

【這個檔案的作用】
提供獲取系統中所有使用者的 API。
主要用於：
- 專案成員選擇（添加成員到專案時）
- 任務負責人選擇（指派任務給誰）
- 搜尋使用者功能

【和前端的串接】

前端                              後端
───────────────────────────────────────────────────────
memberService.getMembers()    →   GET /members
                              →   get_all_members()
                              ←   回傳使用者列表

【API 端點】
- GET /members          : 取得所有成員
- GET /members/<id>     : 取得單一成員資訊

【對應前端】
- apiService.ts 的 memberService.getMembers()
- ProjectDetail.tsx 中選擇成員時使用
- Projects.tsx 中添加專案成員時使用
"""

# ============================================
# 導入需要的模組
# ============================================

# Flask Blueprint 用於模組化路由
from flask import Blueprint, request, jsonify

# JWT 認證裝飾器
from flask_jwt_extended import jwt_required

# 日誌記錄
import logging

# 從父目錄導入
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 資料庫和使用者模型
from models import db, User

# 取得當前登入使用者的輔助函數
from api.auth import get_current_user

# ============================================
# 建立 Blueprint
# ============================================

"""
Blueprint 是 Flask 的模組化路由機制

members_bp = Blueprint('members', __name__)
- 'members': Blueprint 的名稱（用於識別）
- __name__: 告訴 Flask 這個模組的位置

這個 Blueprint 會在 app.py 中註冊：
app.register_blueprint(members_bp)

因為沒有設定 url_prefix，所以路由就是 /members
"""
members_bp = Blueprint('members', __name__)

# 建立日誌記錄器
logger = logging.getLogger(__name__)

# ============================================
# GET /members - 獲取所有成員
# ============================================

@members_bp.route('/members', methods=['GET'])
@jwt_required()  # 需要 JWT token 才能存取
def get_all_members():
    """
    獲取所有使用者列表
    
    【用途】
    當使用者要：
    - 添加成員到專案
    - 指派任務負責人
    - 搜尋其他使用者
    時，會呼叫這個 API 取得可選的使用者列表
    
    【請求格式】
    GET /members
    GET /members?search=關鍵字  (可選的搜尋功能)
    
    Headers:
      Authorization: Bearer <access_token>
    
    【回應格式】
    {
        "members": [
            {
                "id": 1,
                "username": "王小明",
                "name": "王小明",
                "email": "xiaoming@example.com",
                "avatar_url": "https://...",
                "department": "Engineering",
                "role": "admin"
            },
            ...
        ],
        "total": 5
    }
    
    【前端呼叫位置】
    apiService.ts → memberService.getMembers()
    
    【對應前端類型】
    回傳的資料會被 transformUser() 轉換成 types.ts 的 User 類型
    """
    
    # 步驟 1: 驗證使用者身份
    # get_current_user() 會從 JWT token 中取得當前登入的使用者
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # 步驟 2: 處理搜尋參數
        # request.args.get('search', '') 從 URL 參數取得 search 值
        # 例如：GET /members?search=王 會得到 search = '王'
        search = request.args.get('search', '')
        
        # 步驟 3: 建立查詢
        # 只查詢啟用的帳號（is_active=True）
        query = User.query.filter_by(is_active=True)
        
        # 步驟 4: 如果有搜尋關鍵字，加上搜尋條件
        if search:
            # % 是 SQL 的萬用字元，%search% 表示「包含 search 的任何字串」
            search_term = f"%{search}%"
            
            # db.or_() 是 OR 條件
            # ilike() 是不分大小寫的 LIKE
            # 搜尋使用者名稱或 email 中包含關鍵字的
            query = query.filter(
                db.or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        # 步驟 5: 執行查詢，取得所有符合條件的使用者
        users = query.all()
        
        # 步驟 6: 組裝回應資料
        members_list = []
        for user in users:
            # 組裝每個使用者的資料
            # 使用 User 模型的 role 欄位，而不是硬編碼判斷
            members_list.append({
                'id': user.id,
                'username': user.username,
                'name': user.username,  # 前端期望的欄位名稱
                'email': user.email,
                # 如果沒有頭像，使用 ui-avatars.com 自動產生
                'avatar_url': user.avatar_url or f"https://ui-avatars.com/api/?name={user.username}&background=random",
                'department': user.department,
                'role': user.role  # 使用資料庫中的角色欄位
            })
        
        # 步驟 7: 回傳 JSON 格式的回應
        return jsonify({
            'members': members_list,
            'total': len(members_list)
        }), 200  # 200 = OK
        
    except Exception as e:
        # 發生錯誤時，記錄到日誌並回傳錯誤訊息
        # exc_info=True 會記錄完整的錯誤堆疊
        logger.error(f"Error fetching members: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch members'}), 500  # 500 = Server Error

# ============================================
# GET /members/<user_id> - 獲取單一成員資訊
# ============================================

@members_bp.route('/members/<int:user_id>', methods=['GET'])
@jwt_required()
def get_member(user_id):
    """
    獲取單一使用者的詳細資訊
    
    【用途】
    當需要查看某個特定使用者的資訊時使用
    
    【請求格式】
    GET /members/123
    
    Headers:
      Authorization: Bearer <access_token>
    
    【路徑參數】
    user_id: 要查詢的使用者 ID
    
    【回應格式】
    {
        "id": 123,
        "username": "王小明",
        "name": "王小明",
        "email": "xiaoming@example.com",
        "avatar_url": "https://...",
        "department": "Engineering",
        "role": "member"
    }
    """
    
    # 驗證使用者身份
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    # 查詢指定的使用者
    # User.query.get(id) 會根據主鍵查詢
    user = User.query.get(user_id)
    
    # 如果找不到使用者，回傳 404
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # 回傳使用者資訊（使用資料庫中的角色欄位）
    return jsonify({
        'id': user.id,
        'username': user.username,
        'name': user.username,
        'email': user.email,
        'avatar_url': user.avatar_url or f"https://ui-avatars.com/api/?name={user.username}&background=random",
        'department': user.department,
        'role': user.role  # 使用資料庫中的角色欄位
    }), 200
