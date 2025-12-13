"""
============================================
socket_events.py - WebSocket 即時通訊
============================================

【這個檔案的作用】
處理 WebSocket 連接和事件，提供即時功能：
- 即時通知推送
- 任務狀態即時同步
- 專案活動即時更新
- 線上使用者狀態

【如何使用】
前端使用 socket.io-client 連接：

import { io } from 'socket.io-client';
const socket = io('http://localhost:8888', {
    auth: { token: accessToken }
});

socket.on('notification', (data) => {
    console.log('New notification:', data);
});
"""

import sys
import os

# 從父目錄導入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# ============================================
# 建立 SocketIO 實例
# ============================================

socketio = SocketIO(
    cors_allowed_origins="*",  # 生產環境要設定特定來源
    async_mode='eventlet',  # 或 'gevent'
    logger=True,
    engineio_logger=True
)

# 儲存連線中的使用者
connected_users = {}  # {user_id: set(sid)}


def init_socketio(app):
    """初始化 SocketIO"""
    socketio.init_app(app)
    return socketio


# ============================================
# 認證裝飾器
# ============================================

def authenticated_only(f):
    """
    確保 Socket 連接已認證
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request
        
        # 從 auth 中取得 token
        auth = request.args.get('token') or (
            request.environ.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        )
        
        if not auth:
            logger.warning("Socket connection without auth")
            disconnect()
            return
        
        try:
            # 驗證 token
            decoded = decode_token(auth)
            user_id = decoded.get('sub')
            
            if not user_id:
                disconnect()
                return
            
            # 將 user_id 加入 request context
            request.user_id = user_id
            
        except Exception as e:
            logger.error(f"Socket auth error: {e}")
            disconnect()
            return
        
        return f(*args, **kwargs)
    
    return wrapper


# ============================================
# 連接事件
# ============================================

@socketio.on('connect')
def handle_connect(auth=None):
    """
    處理 WebSocket 連接
    """
    from flask import request
    
    # 嘗試從 auth 或 query string 取得 token
    token = None
    if auth and 'token' in auth:
        token = auth['token']
    elif request.args.get('token'):
        token = request.args.get('token')
    
    if not token:
        logger.warning("Socket connection rejected: no token")
        return False
    
    try:
        # 驗證 token
        decoded = decode_token(token)
        user_id = decoded.get('sub')
        
        if not user_id:
            return False
        
        # 記錄連接
        sid = request.sid
        if user_id not in connected_users:
            connected_users[user_id] = set()
        connected_users[user_id].add(sid)
        
        # 加入使用者專屬的 room
        join_room(f"user_{user_id}")
        
        logger.info(f"User {user_id} connected with sid {sid}")
        
        # 發送連接成功訊息
        emit('connected', {
            'status': 'connected',
            'user_id': user_id
        })
        
        return True
        
    except Exception as e:
        logger.error(f"Socket connect error: {e}")
        return False


@socketio.on('disconnect')
def handle_disconnect():
    """
    處理 WebSocket 斷開
    """
    from flask import request
    
    sid = request.sid
    
    # 從所有使用者中移除這個 sid
    for user_id, sids in list(connected_users.items()):
        if sid in sids:
            sids.remove(sid)
            logger.info(f"User {user_id} disconnected sid {sid}")
            
            # 如果使用者沒有其他連接，從字典中移除
            if not sids:
                del connected_users[user_id]
                leave_room(f"user_{user_id}")
            break


# ============================================
# 專案 Room 管理
# ============================================

@socketio.on('join_project')
def handle_join_project(data):
    """
    加入專案的即時更新 room
    """
    from flask import request
    
    project_id = data.get('project_id')
    if not project_id:
        return
    
    # 驗證使用者有權限存取這個專案
    # (這裡簡化處理，實際應該檢查權限)
    
    room = f"project_{project_id}"
    join_room(room)
    
    logger.info(f"Session {request.sid} joined room {room}")
    
    emit('joined_project', {
        'status': 'joined',
        'project_id': project_id
    })


@socketio.on('leave_project')
def handle_leave_project(data):
    """
    離開專案的即時更新 room
    """
    from flask import request
    
    project_id = data.get('project_id')
    if not project_id:
        return
    
    room = f"project_{project_id}"
    leave_room(room)
    
    logger.info(f"Session {request.sid} left room {room}")


# ============================================
# 通知推送函數
# ============================================

def emit_to_user(user_id, event, data):
    """
    發送事件給特定使用者
    
    使用方式：
    from socket_events import emit_to_user
    emit_to_user(user_id, 'notification', {'message': 'Hello!'})
    """
    room = f"user_{user_id}"
    socketio.emit(event, data, room=room)
    logger.debug(f"Emitted {event} to user {user_id}")


def emit_to_project(project_id, event, data, exclude_user=None):
    """
    發送事件給專案的所有成員
    
    使用方式：
    from socket_events import emit_to_project
    emit_to_project(project_id, 'task_updated', {'task': task_data})
    """
    room = f"project_{project_id}"
    
    if exclude_user:
        # 排除特定使用者
        socketio.emit(event, data, room=room, skip_sid=connected_users.get(exclude_user, set()))
    else:
        socketio.emit(event, data, room=room)
    
    logger.debug(f"Emitted {event} to project {project_id}")


def emit_notification(user_id, notification_data):
    """
    推送新通知給使用者
    """
    emit_to_user(user_id, 'notification', notification_data)


def emit_task_created(project_id, task_data, created_by=None):
    """
    推送新任務建立事件
    """
    emit_to_project(project_id, 'task_created', {
        'task': task_data,
        'created_by': created_by
    }, exclude_user=created_by)


def emit_task_updated(project_id, task_data, updated_by=None):
    """
    推送任務更新事件
    """
    emit_to_project(project_id, 'task_updated', {
        'task': task_data,
        'updated_by': updated_by
    }, exclude_user=updated_by)


def emit_task_deleted(project_id, task_id, deleted_by=None):
    """
    推送任務刪除事件
    """
    emit_to_project(project_id, 'task_deleted', {
        'task_id': task_id,
        'deleted_by': deleted_by
    }, exclude_user=deleted_by)


def emit_member_added(project_id, member_data, added_by=None):
    """
    推送成員加入事件
    """
    emit_to_project(project_id, 'member_added', {
        'member': member_data,
        'added_by': added_by
    }, exclude_user=added_by)


def emit_member_removed(project_id, user_id, removed_by=None):
    """
    推送成員移除事件
    """
    emit_to_project(project_id, 'member_removed', {
        'user_id': user_id,
        'removed_by': removed_by
    }, exclude_user=removed_by)


def emit_comment_added(project_id, task_id, comment_data, added_by=None):
    """
    推送評論新增事件
    """
    emit_to_project(project_id, 'comment_added', {
        'task_id': task_id,
        'comment': comment_data,
        'added_by': added_by
    }, exclude_user=added_by)


# ============================================
# 線上狀態
# ============================================

def get_online_users():
    """
    取得目前線上的使用者 ID 列表
    """
    return list(connected_users.keys())


def is_user_online(user_id):
    """
    檢查使用者是否在線
    """
    return str(user_id) in connected_users


@socketio.on('get_online_users')
def handle_get_online_users():
    """
    回應線上使用者查詢
    """
    emit('online_users', {
        'users': get_online_users(),
        'count': len(connected_users)
    })


# ============================================
# 即時訊息（可選功能）
# ============================================

@socketio.on('typing')
def handle_typing(data):
    """
    處理「正在輸入」狀態
    """
    from flask import request
    
    project_id = data.get('project_id')
    task_id = data.get('task_id')
    
    if project_id:
        emit_to_project(project_id, 'user_typing', {
            'user_id': getattr(request, 'user_id', None),
            'task_id': task_id
        })


@socketio.on('stop_typing')
def handle_stop_typing(data):
    """
    處理停止輸入狀態
    """
    from flask import request
    
    project_id = data.get('project_id')
    task_id = data.get('task_id')
    
    if project_id:
        emit_to_project(project_id, 'user_stop_typing', {
            'user_id': getattr(request, 'user_id', None),
            'task_id': task_id
        })


# ============================================
# 錯誤處理
# ============================================

@socketio.on_error()
def error_handler(e):
    """
    全域錯誤處理
    """
    logger.error(f"SocketIO error: {e}")


@socketio.on_error_default
def default_error_handler(e):
    """
    預設錯誤處理
    """
    logger.error(f"SocketIO default error: {e}")

