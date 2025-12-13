"""
============================================
api_docs.py - API 文件 (Swagger/OpenAPI)
============================================

【這個檔案的作用】
提供 Swagger UI 介面和 OpenAPI 規格文件，
讓開發者可以查看和測試 API。

【如何存取】
- Swagger UI: http://localhost:8888/api/docs
- OpenAPI JSON: http://localhost:8888/api/docs/swagger.json
"""

import sys
import os

# 從父目錄導入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flasgger import Swagger, swag_from
from flask import Blueprint

# ============================================
# Swagger 設定
# ============================================

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/api/docs/swagger.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "NexusTeam API",
        "description": """
## 團隊任務管理系統 API 文件

### 認證方式
大部分 API 需要在 Header 中帶上 JWT Token：
```
Authorization: Bearer <your_access_token>
```

### 取得 Token
1. 呼叫 `/auth/login` 取得 access_token
2. 將 token 放入 Authorization header

### 回應格式
所有 API 回應都遵循統一格式：

**成功回應：**
```json
{
    "success": true,
    "data": { ... },
    "meta": { ... }
}
```

**錯誤回應：**
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Error message",
        "details": { ... }
    }
}
```

### Rate Limiting
API 有請求頻率限制，超過限制會回傳 429 狀態碼。
預設限制：100 requests/minute

### 錯誤代碼
| 代碼 | 說明 |
|------|------|
| AUTH_REQUIRED | 需要認證 |
| INVALID_CREDENTIALS | 認證失敗 |
| TOKEN_EXPIRED | Token 已過期 |
| VALIDATION_ERROR | 輸入驗證失敗 |
| NOT_FOUND | 資源不存在 |
| PERMISSION_DENIED | 權限不足 |
| RATE_LIMIT_EXCEEDED | 超過請求限制 |
        """,
        "version": "2.1.0",
        "contact": {
            "name": "API Support",
            "email": "support@nexusteam.com"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "host": "localhost:8888",
    "basePath": "/",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: \"Bearer {token}\""
        }
    },
    "security": [
        {"Bearer": []}
    ],
    "tags": [
        {
            "name": "認證 (Auth)",
            "description": "使用者認證相關 API：登入、註冊、Token 管理"
        },
        {
            "name": "專案 (Projects)",
            "description": "專案管理 API：建立、查詢、更新、刪除專案"
        },
        {
            "name": "任務 (Tasks)",
            "description": "任務管理 API：建立、查詢、更新、刪除任務"
        },
        {
            "name": "通知 (Notifications)",
            "description": "通知管理 API：查詢、標記已讀、刪除通知"
        },
        {
            "name": "成員 (Members)",
            "description": "成員管理 API：查詢所有成員"
        },
        {
            "name": "標籤 (Tags)",
            "description": "標籤管理 API：建立、更新、刪除標籤"
        },
        {
            "name": "健康檢查 (Health)",
            "description": "系統健康檢查 API"
        }
    ],
    "definitions": {
        "User": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "email": {"type": "string", "example": "user@example.com"},
                "username": {"type": "string", "example": "John Doe"},
                "avatar_url": {"type": "string", "example": "https://..."},
                "department": {"type": "string", "example": "Engineering"},
                "role": {"type": "string", "enum": ["admin", "member"]},
                "is_active": {"type": "boolean", "example": True}
            }
        },
        "Project": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "name": {"type": "string", "example": "My Project"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["active", "archived"]},
                "owner_id": {"type": "integer"},
                "created_at": {"type": "string", "format": "date-time"}
            }
        },
        "Task": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "title": {"type": "string", "example": "Implement feature"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "review", "done"]},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "project_id": {"type": "integer"},
                "assigned_to": {"type": "integer"},
                "due_date": {"type": "string", "format": "date"},
                "created_at": {"type": "string", "format": "date-time"}
            }
        },
        "Notification": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "type": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "is_read": {"type": "boolean"},
                "created_at": {"type": "string", "format": "date-time"}
            }
        },
        "Error": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": False},
                "error": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "example": "VALIDATION_ERROR"},
                        "message": {"type": "string", "example": "Invalid input"},
                        "details": {"type": "object"}
                    }
                }
            }
        },
        "SuccessResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": True},
                "data": {"type": "object"},
                "meta": {"type": "object"}
            }
        },
        "PaginatedResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": True},
                "data": {"type": "object"},
                "meta": {
                    "type": "object",
                    "properties": {
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "total": {"type": "integer"},
                                "page": {"type": "integer"},
                                "per_page": {"type": "integer"},
                                "total_pages": {"type": "integer"},
                                "has_next": {"type": "boolean"},
                                "has_prev": {"type": "boolean"}
                            }
                        }
                    }
                }
            }
        }
    }
}


def init_swagger(app):
    """
    初始化 Swagger
    """
    swagger = Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)
    return swagger


# ============================================
# API 文件裝飾器範例
# ============================================

# 這些可以用來為個別端點加上文件
LOGIN_DOCS = {
    "tags": ["認證 (Auth)"],
    "summary": "使用者登入",
    "description": "使用 email 和密碼登入，取得 JWT token",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {
                        "type": "string",
                        "example": "user@example.com"
                    },
                    "password": {
                        "type": "string",
                        "example": "password123"
                    }
                }
            }
        }
    ],
    "responses": {
        "200": {
            "description": "登入成功",
            "schema": {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "refresh_token": {"type": "string"},
                    "user": {"$ref": "#/definitions/User"}
                }
            }
        },
        "401": {
            "description": "認證失敗",
            "schema": {"$ref": "#/definitions/Error"}
        },
        "429": {
            "description": "帳號被鎖定",
            "schema": {"$ref": "#/definitions/Error"}
        }
    }
}

REGISTER_DOCS = {
    "tags": ["認證 (Auth)"],
    "summary": "使用者註冊",
    "description": "建立新使用者帳號",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["email", "password", "username"],
                "properties": {
                    "email": {"type": "string", "example": "newuser@example.com"},
                    "password": {"type": "string", "example": "password123"},
                    "username": {"type": "string", "example": "New User"},
                    "department": {"type": "string", "example": "Engineering"}
                }
            }
        }
    ],
    "responses": {
        "201": {
            "description": "註冊成功",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "user": {"$ref": "#/definitions/User"}
                }
            }
        },
        "400": {
            "description": "輸入驗證失敗",
            "schema": {"$ref": "#/definitions/Error"}
        },
        "409": {
            "description": "Email 已存在",
            "schema": {"$ref": "#/definitions/Error"}
        }
    }
}

GET_PROJECTS_DOCS = {
    "tags": ["專案 (Projects)"],
    "summary": "取得專案列表",
    "description": "取得目前使用者擁有或參與的所有專案",
    "parameters": [
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "default": 1,
            "description": "頁碼"
        },
        {
            "name": "per_page",
            "in": "query",
            "type": "integer",
            "default": 20,
            "description": "每頁筆數"
        }
    ],
    "responses": {
        "200": {
            "description": "成功",
            "schema": {
                "type": "object",
                "properties": {
                    "projects": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/Project"}
                    },
                    "total": {"type": "integer"},
                    "page": {"type": "integer"},
                    "per_page": {"type": "integer"},
                    "total_pages": {"type": "integer"}
                }
            }
        },
        "401": {
            "description": "未認證",
            "schema": {"$ref": "#/definitions/Error"}
        }
    },
    "security": [{"Bearer": []}]
}

CREATE_TASK_DOCS = {
    "tags": ["任務 (Tasks)"],
    "summary": "建立新任務",
    "description": "在指定專案中建立新任務",
    "parameters": [
        {
            "name": "project_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "專案 ID"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string", "example": "New Task"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["todo", "in_progress", "review", "done"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "assigned_to": {"type": "integer"},
                    "due_date": {"type": "string", "format": "date"}
                }
            }
        }
    ],
    "responses": {
        "201": {
            "description": "任務建立成功",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "task": {"$ref": "#/definitions/Task"}
                }
            }
        },
        "400": {
            "description": "輸入驗證失敗",
            "schema": {"$ref": "#/definitions/Error"}
        },
        "403": {
            "description": "權限不足",
            "schema": {"$ref": "#/definitions/Error"}
        }
    },
    "security": [{"Bearer": []}]
}

