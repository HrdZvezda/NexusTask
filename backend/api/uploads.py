"""
============================================
uploads.py - 檔案上傳 API
============================================

【這個檔案的作用】
處理任務附件的上傳、下載、刪除等功能。

【API 端點】
- POST /tasks/<task_id>/attachments    : 上傳附件到任務
- GET  /tasks/<task_id>/attachments    : 取得任務的所有附件
- GET  /attachments/<id>               : 下載附件
- DELETE /attachments/<id>             : 刪除附件

【支援的檔案類型】
- 圖片：jpg, jpeg, png, gif, webp
- 文件：pdf, doc, docx, xls, xlsx, ppt, pptx
- 文字：txt, md, csv
- 壓縮：zip, rar, 7z
"""

import os
import sys
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
import logging

# 從父目錄導入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, Attachment, Task
from api.auth import get_current_user

# ============================================
# 設定
# ============================================

uploads_bp = Blueprint('uploads', __name__)
logger = logging.getLogger(__name__)

# 允許的檔案類型
ALLOWED_EXTENSIONS = {
    # 圖片
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg',
    # 文件
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    # 文字
    'txt', 'md', 'csv', 'json',
    # 壓縮檔
    'zip', 'rar', '7z', 'tar', 'gz'
}

# 最大檔案大小 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# 上傳目錄
UPLOAD_FOLDER = 'uploads'


def allowed_file(filename):
    """檢查檔案類型是否允許"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """取得檔案副檔名"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def get_mime_type(extension):
    """根據副檔名取得 MIME type"""
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'txt': 'text/plain',
        'md': 'text/markdown',
        'csv': 'text/csv',
        'json': 'application/json',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        '7z': 'application/x-7z-compressed',
        'tar': 'application/x-tar',
        'gz': 'application/gzip'
    }
    return mime_types.get(extension, 'application/octet-stream')


def ensure_upload_folder():
    """確保上傳目錄存在"""
    upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    return upload_path


# ============================================
# POST /tasks/<task_id>/attachments - 上傳附件
# ============================================

@uploads_bp.route('/tasks/<int:task_id>/attachments', methods=['POST'])
@jwt_required()
def upload_attachment(task_id):
    """
    上傳附件到任務
    
    【請求格式】
    POST /tasks/123/attachments
    Content-Type: multipart/form-data
    
    file: <檔案>
    
    【回應格式】
    {
        "attachment": {
            "id": 1,
            "filename": "abc123.pdf",
            "original_filename": "報告.pdf",
            "file_size": 102400,
            "file_type": "application/pdf",
            "uploaded_at": "2024-01-15T10:30:00Z",
            "uploaded_by": {
                "id": 1,
                "name": "王小明"
            }
        }
    }
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    # 檢查任務是否存在
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # 檢查是否有檔案
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # 檢查檔案類型
    if not allowed_file(file.filename):
        return jsonify({
            'error': 'File type not allowed',
            'allowed_types': list(ALLOWED_EXTENSIONS)
        }), 400
    
    # 檢查檔案大小
    file.seek(0, 2)  # 移到檔案結尾
    file_size = file.tell()  # 取得檔案大小
    file.seek(0)  # 移回開頭
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({
            'error': 'File too large',
            'max_size_mb': MAX_FILE_SIZE / (1024 * 1024)
        }), 400
    
    try:
        # 產生唯一檔名
        original_filename = secure_filename(file.filename)
        extension = get_file_extension(original_filename)
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        
        # 確保上傳目錄存在
        upload_path = ensure_upload_folder()
        file_path = os.path.join(upload_path, unique_filename)
        
        # 儲存檔案
        file.save(file_path)
        
        # 建立資料庫記錄
        attachment = Attachment(
            filename=unique_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=get_mime_type(extension),
            task_id=task_id,
            project_id=task.project_id,
            uploaded_by=current_user.id
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        logger.info(f"File uploaded: {original_filename} -> {unique_filename} by user {current_user.id}")
        
        return jsonify({
            'attachment': {
                'id': attachment.id,
                'filename': attachment.filename,
                'original_filename': attachment.original_filename,
                'file_size': attachment.file_size,
                'file_type': attachment.file_type,
                'uploaded_at': attachment.uploaded_at.isoformat(),
                'uploaded_by': {
                    'id': current_user.id,
                    'name': current_user.username
                }
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Upload failed'}), 500


# ============================================
# GET /tasks/<task_id>/attachments - 取得任務附件列表
# ============================================

@uploads_bp.route('/tasks/<int:task_id>/attachments', methods=['GET'])
@jwt_required()
def get_task_attachments(task_id):
    """
    取得任務的所有附件
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    # 檢查任務是否存在
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    attachments = Attachment.query.filter_by(task_id=task_id).order_by(Attachment.uploaded_at.desc()).all()
    
    return jsonify({
        'attachments': [{
            'id': a.id,
            'filename': a.filename,
            'original_filename': a.original_filename,
            'file_size': a.file_size,
            'file_type': a.file_type,
            'uploaded_at': a.uploaded_at.isoformat(),
            'uploaded_by': a.uploaded_by
        } for a in attachments]
    }), 200


# ============================================
# GET /attachments/<id> - 下載附件
# ============================================

@uploads_bp.route('/attachments/<int:attachment_id>', methods=['GET'])
@jwt_required()
def download_attachment(attachment_id):
    """
    下載附件
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    attachment = Attachment.query.get(attachment_id)
    if not attachment:
        return jsonify({'error': 'Attachment not found'}), 404
    
    # 檢查檔案是否存在
    if not os.path.exists(attachment.file_path):
        return jsonify({'error': 'File not found on server'}), 404
    
    return send_file(
        attachment.file_path,
        mimetype=attachment.file_type,
        as_attachment=True,
        download_name=attachment.original_filename
    )


# ============================================
# DELETE /attachments/<id> - 刪除附件
# ============================================

@uploads_bp.route('/attachments/<int:attachment_id>', methods=['DELETE'])
@jwt_required()
def delete_attachment(attachment_id):
    """
    刪除附件
    """
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Authentication required'}), 401
    
    attachment = Attachment.query.get(attachment_id)
    if not attachment:
        return jsonify({'error': 'Attachment not found'}), 404
    
    # 只有上傳者可以刪除
    if attachment.uploaded_by != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        # 刪除實體檔案
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)
        
        # 刪除資料庫記錄
        db.session.delete(attachment)
        db.session.commit()
        
        logger.info(f"Attachment deleted: {attachment.original_filename} by user {current_user.id}")
        
        return jsonify({'message': 'Attachment deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Delete failed'}), 500

