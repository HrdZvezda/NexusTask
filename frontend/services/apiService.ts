/**
 * ============================================
 * API Service - 前端與後端串接的核心檔案
 * ============================================
 * 
 * 【這個檔案的作用】
 * 這是前端應用程式和後端伺服器溝通的「橋樑」。
 * 當使用者在網頁上做任何操作（登入、建立專案、新增任務等），
 * 這個檔案會負責把請求送到後端伺服器，並把伺服器的回應傳回給前端。
 * 
 * 【串接流程圖】
 * 
 *   使用者操作 (點擊按鈕)
 *        ↓
 *   前端頁面 (React 組件，如 Dashboard.tsx)
 *        ↓
 *   apiService.ts (這個檔案) ← 你現在在這裡
 *        ↓
 *   HTTP 請求 (透過 fetch 送出)
 *        ↓
 *   後端伺服器 (Flask，如 auth.py, tasks.py)
 *        ↓
 *   資料庫 (SQLite)
 *        ↓
 *   回傳資料給前端
 * 
 * 【重要概念】
 * - API (Application Programming Interface): 程式之間溝通的介面
 * - HTTP 請求方法:
 *   - GET: 取得資料 (像是「給我看看」)
 *   - POST: 建立新資料 (像是「幫我新增一個」)
 *   - PATCH: 更新部分資料 (像是「幫我改一下這個」)
 *   - DELETE: 刪除資料 (像是「幫我刪掉這個」)
 * - JWT (JSON Web Token): 一種身份驗證的方式，像是「通行證」
 */

// ============================================
// 導入類型定義
// ============================================
// 從 types.ts 導入我們定義好的資料類型
// 這些類型告訴 TypeScript「這個資料長什麼樣子」
import { User, Project, Task, TaskStatus, TaskPriority, ProjectStats, Notification, Comment, Tag, Attachment } from '../types';

// ============================================
// 設定後端伺服器的網址
// ============================================
/**
 * API_BASE_URL 是後端伺服器的網址
 * 
 * import.meta.env.VITE_API_URL: 這是從環境變數讀取的網址（可以在部署時設定）
 * 如果沒有設定環境變數，就使用預設值 'http://localhost:8888'
 * 
 * localhost:8888 的意思是：
 * - localhost = 本機電腦（你自己的電腦）
 * - 8888 = 連接埠號碼（像是門牌號碼，告訴電腦要連到哪個「門」）
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8888';

// ============================================
// Token 管理函數
// ============================================
/**
 * 【什麼是 Token？】
 * Token 就像是一張「通行證」。當你登入成功後，伺服器會給你一張通行證。
 * 之後每次你要做任何操作，都要出示這張通行證，伺服器才知道「你是誰」。
 * 
 * 我們有兩種 Token:
 * 1. Access Token (存取令牌): 短期有效，用來做日常操作
 * 2. Refresh Token (刷新令牌): 長期有效，用來換新的 Access Token
 */

/**
 * 從瀏覽器的 localStorage 取得 access token
 * 
 * localStorage 是瀏覽器提供的儲存空間，資料會一直保存，即使關閉瀏覽器也不會消失
 * 就像是把東西放在抽屜裡，下次打開還是在
 */
const getAccessToken = (): string | null => {
  // getItem('key') 會取得儲存在 localStorage 中對應 key 的值
  // 如果找不到，會回傳 null
  return localStorage.getItem('nexus_access_token');
};

/**
 * 從 localStorage 取得 refresh token
 */
const getRefreshToken = (): string | null => {
  return localStorage.getItem('nexus_refresh_token');
};

/**
 * 儲存 tokens 到 localStorage
 * 
 * @param accessToken - 存取令牌
 * @param refreshToken - 刷新令牌
 */
const saveTokens = (accessToken: string, refreshToken: string): void => {
  // setItem('key', 'value') 會把值儲存到 localStorage
  localStorage.setItem('nexus_access_token', accessToken);
  localStorage.setItem('nexus_refresh_token', refreshToken);
};

/**
 * 清除所有 tokens（登出時使用）
 * 
 * 當使用者登出時，我們要把所有的「通行證」都銷毀
 * 這樣即使有人偷到舊的 token，也無法使用
 */
const clearTokens = (): void => {
  // removeItem('key') 會刪除 localStorage 中對應的項目
  localStorage.removeItem('nexus_access_token');
  localStorage.removeItem('nexus_refresh_token');
  localStorage.removeItem('nexus_user');
};

// ============================================
// 通用 API 請求函數
// ============================================
/**
 * 這是最核心的函數！所有的 API 請求都會經過這裡
 * 
 * 【功能說明】
 * 1. 自動帶上 Token（通行證）
 * 2. 自動處理 JSON 格式
 * 3. 當 Token 過期時，自動嘗試刷新
 * 4. 統一處理錯誤
 * 
 * @param endpoint - API 端點，例如 '/auth/login'
 * @param options - 請求選項，包含方法(GET/POST等)和資料
 * @returns 伺服器回傳的資料
 * 
 * 【泛型 <T> 是什麼？】
 * <T> 是 TypeScript 的泛型，讓這個函數可以回傳任何類型的資料
 * 例如：apiRequest<User>() 會回傳 User 類型
 *       apiRequest<Task[]>() 會回傳 Task 陣列
 */
const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  // 步驟 1: 取得目前的 access token
  const token = getAccessToken();
  
  // 步驟 2: 設定 HTTP 請求的標頭（Headers）
  // Headers 就像信封上的資訊，告訴伺服器這封信的格式
  const headers: HeadersInit = {
    // 告訴伺服器：我送的資料是 JSON 格式
    'Content-Type': 'application/json',
    // 如果有 token，就帶上去（像是出示通行證）
    // Bearer 是一種標準格式，意思是「持有者認證」
    ...(token && { 'Authorization': `Bearer ${token}` }),
    // 保留原本傳入的 headers
    ...options.headers,
  };

  // 步驟 3: 發送 HTTP 請求到後端
  // fetch 是瀏覽器提供的函數，用來發送網路請求
  // await 會等待請求完成才繼續執行
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,      // 展開傳入的選項（方法、body 等）
    headers,         // 使用我們設定好的 headers
  });

  // 步驟 4: 檢查是否收到 401 錯誤（未授權）
  // 401 表示 token 可能過期了或無效
  if (response.status === 401) {
    // 嘗試用 refresh token 換一個新的 access token
    const refreshed = await tryRefreshToken();
    
    if (refreshed) {
      // 刷新成功！用新的 token 重試原本的請求
      const newToken = getAccessToken();
      const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          ...headers,
          'Authorization': `Bearer ${newToken}`,
        },
      });
      
      // 如果重試還是失敗，拋出錯誤
      if (!retryResponse.ok) {
        const error = await retryResponse.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(error.message || error.error || 'Request failed');
      }
      
      // 重試成功，回傳資料
      return retryResponse.json();
    } else {
      // 刷新失敗，清除所有 token 並導向登入頁面
      clearTokens();
      window.location.href = '/#/login';
      throw new Error('Session expired');
    }
  }

  // 步驟 5: 檢查請求是否成功
  // response.ok 為 true 表示 HTTP 狀態碼是 200-299（成功）
  if (!response.ok) {
    // 請求失敗，嘗試讀取錯誤訊息
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || error.error || 'Request failed');
  }

  // 步驟 6: 請求成功，回傳 JSON 格式的資料
  return response.json();
};

/**
 * 嘗試用 refresh token 換新的 access token
 * 
 * 【為什麼需要這個？】
 * Access token 通常只有 15 分鐘到 1 小時的有效期
 * 過期後，我們不想讓使用者重新登入
 * 所以用長效的 refresh token 來自動換新的 access token
 * 
 * @returns true 表示刷新成功，false 表示失敗
 */
const tryRefreshToken = async (): Promise<boolean> => {
  // 取得 refresh token
  const refreshToken = getRefreshToken();

  // 如果沒有 refresh token，直接回傳失敗
  if (!refreshToken) return false;

  try {
    // 發送請求到後端的 /auth/refresh 端點
    // 這會對應到後端 auth.py 的 refresh() 函數
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // 注意：這裡用 refresh token，不是 access token
        'Authorization': `Bearer ${refreshToken}`,
      },
    });

    // 如果請求失敗，回傳 false
    if (!response.ok) {
      console.warn('Token refresh failed with status:', response.status);
      return false;
    }

    // 請求成功，取得新的 access token 並儲存
    const data = await response.json();
    localStorage.setItem('nexus_access_token', data.access_token);
    return true;
  } catch (error) {
    // 記錄錯誤以便除錯
    console.error('Token refresh error:', error instanceof Error ? error.message : 'Unknown error');
    return false;
  }
};

// ============================================
// 資料轉換函數
// ============================================
/**
 * 【為什麼需要資料轉換？】
 * 
 * 後端（Python/Flask）和前端（TypeScript/React）使用不同的命名習慣：
 * - 後端用 snake_case（蛇形命名）：user_name, created_at
 * - 前端用 camelCase（駝峰命名）：userName, createdAt
 * 
 * 這些轉換函數就是把後端格式轉成前端格式
 */

/**
 * 將後端的 User 資料轉換成前端格式
 * 
 * @param backendUser - 後端回傳的使用者資料
 * @returns 前端格式的使用者資料
 * 
 * 【對應關係】
 * 後端 (auth.py)          →  前端 (User type)
 * ─────────────────────────────────────────
 * id                      →  id (轉成字串)
 * username / name         →  name
 * email                   →  email
 * avatar_url              →  avatar
 * role                    →  role
 * department              →  department
 */
const transformUser = (backendUser: any): User => ({
  // String() 把數字轉成字串，因為前端的 id 是字串類型
  id: String(backendUser.id),
  // || 是「或」的意思，如果左邊是空的就用右邊的值
  name: backendUser.username || backendUser.name,
  email: backendUser.email,
  // 如果沒有頭像，就用 ui-avatars.com 自動產生一個
  avatar: backendUser.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(backendUser.username || backendUser.name)}&background=random`,
  role: backendUser.role || 'member',
  department: backendUser.department,
});

/**
 * 將後端的 Project 資料轉換成前端格式
 * 
 * @param backendProject - 後端回傳的專案資料
 * @returns 前端格式的專案資料
 * 
 * 【對應關係】
 * 後端 (projects.py)      →  前端 (Project type)
 * ─────────────────────────────────────────
 * id                      →  id (轉成字串)
 * name                    →  name
 * description             →  description
 * owner_id / owner.id     →  ownerId
 * member_ids              →  members
 * status                  →  status
 * progress                →  progress
 * created_at              →  createdAt
 */
const transformProject = (backendProject: any): Project => ({
  id: String(backendProject.id),
  name: backendProject.name,
  // 如果沒有描述就用空字串
  description: backendProject.description || '',
  // 優先用 owner_id，如果沒有就從 owner 物件取 id
  ownerId: String(backendProject.owner_id || backendProject.owner?.id),
  // ?. 是可選鏈，如果 member_ids 不存在就不會出錯
  // .map(String) 把每個成員 ID 都轉成字串
  members: backendProject.member_ids?.map(String) || [],
  // 三元運算子：條件 ? 真的值 : 假的值
  status: backendProject.status === 'archived' ? 'archived' : 'active',
  progress: backendProject.progress || 0,
  createdAt: backendProject.created_at,
});

/**
 * 將後端的 Task 資料轉換成前端格式
 * 
 * @param backendTask - 後端回傳的任務資料
 * @returns 前端格式的任務資料
 * 
 * 【重要！狀態和優先級的轉換】
 * 後端用小寫：'todo', 'in_progress', 'done', 'low', 'medium', 'high'
 * 前端用大寫枚舉：TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskPriority.HIGH
 * 
 * 【對應關係】
 * 後端 (tasks.py)         →  前端 (Task type)
 * ─────────────────────────────────────────
 * id                      →  id
 * project_id              →  projectId
 * title                   →  title
 * description             →  description
 * status                  →  status (需要轉換！)
 * priority                →  priority (需要轉換！)
 * assigned_to.id          →  assigneeId
 * assigned_to.username    →  assigneeName
 * due_date                →  dueDate
 * comments_count          →  commentsCount
 * notes                   →  notes
 */
const transformTask = (backendTask: any): Task => {
  // 狀態映射表：把後端的小寫轉成前端的枚舉
  const statusMap: Record<string, TaskStatus> = {
    'todo': TaskStatus.TODO,
    'in_progress': TaskStatus.IN_PROGRESS,
    'review': TaskStatus.REVIEW,
    'done': TaskStatus.DONE,
  };
  
  // 優先級映射表
  const priorityMap: Record<string, TaskPriority> = {
    'low': TaskPriority.LOW,
    'medium': TaskPriority.MEDIUM,
    'high': TaskPriority.HIGH,
  };

  return {
    id: String(backendTask.id),
    projectId: String(backendTask.project_id),
    title: backendTask.title,
    description: backendTask.description || '',
    // 用映射表轉換，如果找不到就預設 TODO
    // ?.toLowerCase() 先轉小寫，避免大小寫問題
    status: statusMap[backendTask.status?.toLowerCase()] || TaskStatus.TODO,
    priority: priorityMap[backendTask.priority?.toLowerCase()] || TaskPriority.MEDIUM,
    // 負責人 ID：優先從 assigned_to 物件取，否則用 assignee_id
    assigneeId: backendTask.assigned_to?.id ? String(backendTask.assigned_to.id) : backendTask.assignee_id ? String(backendTask.assignee_id) : undefined,
    assigneeName: backendTask.assigned_to?.username || backendTask.assignee_name,
    // 日期只取 YYYY-MM-DD 部分（去掉時間）
    dueDate: backendTask.due_date ? backendTask.due_date.split('T')[0] : undefined,
    commentsCount: backendTask.comments_count || 0,
    notes: backendTask.notes || '',
  };
};

/**
 * 將後端的 Comment 資料轉換成前端格式
 */
const transformComment = (backendComment: any): Comment => ({
  id: String(backendComment.id),
  taskId: String(backendComment.task_id),
  userId: String(backendComment.user_id || backendComment.user?.id),
  userName: backendComment.user?.username || backendComment.user_name,
  content: backendComment.content,
  createdAt: backendComment.created_at,
});

/**
 * 將後端的 Notification 資料轉換成前端格式
 */
const transformNotification = (backendNotif: any): Notification => ({
  id: String(backendNotif.id),
  userId: String(backendNotif.user_id),
  message: backendNotif.title || backendNotif.content,
  read: backendNotif.is_read,
  // 把時間轉成「幾分鐘前」的格式
  createdAt: formatRelativeTime(backendNotif.created_at),
  // 根據通知類型設定顯示樣式
  type: backendNotif.type === 'task_completed' ? 'success' : 
        backendNotif.type === 'warning' ? 'warning' : 'info',
  // 相關專案 / 任務資訊（方便點擊導覽）
  projectId: backendNotif.project?.id ? String(backendNotif.project.id) : backendNotif.related_project_id ? String(backendNotif.related_project_id) : undefined,
  projectName: backendNotif.project?.name,
  taskId: backendNotif.task?.id ? String(backendNotif.task.id) : backendNotif.related_task_id ? String(backendNotif.related_task_id) : undefined,
  taskTitle: backendNotif.task?.title,
});

/**
 * 把時間戳轉成「幾分鐘前」這種人類易讀的格式
 * 
 * @param dateString - ISO 格式的時間字串，如 "2024-01-15T10:30:00" 或 "2024-01-15T10:30:00Z"
 * @returns 人類易讀的時間，如 "5 mins ago"
 * 
 * 注意：後端使用 UTC 時間（datetime.utcnow()），但 isoformat() 不會加上 'Z'
 * 所以我們需要手動將沒有時區標記的時間視為 UTC
 */
const formatRelativeTime = (dateString: string): string => {
  if (!dateString) return 'Unknown time';
  
  // 如果時間字串沒有時區標記（沒有 Z 或 +/-），視為 UTC 時間
  let normalizedDateString = dateString;
  if (!dateString.endsWith('Z') && !dateString.includes('+') && !dateString.match(/[-+]\d{2}:\d{2}$/)) {
    normalizedDateString = dateString + 'Z';  // 加上 Z 表示 UTC
  }
  
  const date = new Date(normalizedDateString);  // 把字串轉成日期物件
  const now = new Date();                        // 取得現在時間（本地時間，但會自動轉換）
  const diffMs = now.getTime() - date.getTime(); // 計算時間差（毫秒）
  
  // 處理未來時間（可能因為時鐘不同步）
  if (diffMs < 0) return 'just now';
  
  const diffSecs = Math.floor(diffMs / 1000);     // 轉換成秒
  const diffMins = Math.floor(diffMs / 60000);    // 轉換成分鐘
  const diffHours = Math.floor(diffMs / 3600000); // 轉換成小時
  const diffDays = Math.floor(diffMs / 86400000); // 轉換成天

  // 根據時間差回傳不同的文字
  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  return date.toLocaleDateString();  // 超過一週就顯示完整日期
};

// ============================================
// Auth Service（認證服務）
// ============================================
/**
 * 處理所有與使用者身份認證相關的 API 呼叫
 * 
 * 【對應的後端檔案】backend/auth.py
 * 
 * 【包含功能】
 * - 登入 (login)
 * - 註冊 (register)
 * - 取得個人資料 (getCurrentUser)
 * - 更新個人資料 (updateProfile)
 * - 修改密碼 (changePassword)
 * - 登出 (logout)
 */
export const authService = {
  /**
   * 使用者登入
   * 
   * 【串接流程】
   * 前端 Login.tsx → authService.login() → POST /auth/login → 後端 auth.py login()
   * 
   * @param email - 使用者的電子郵件
   * @param password - 使用者的密碼
   * @returns 登入成功的使用者資料
   */
  login: async (email: string, password: string): Promise<User> => {
    // 發送 POST 請求到 /auth/login
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',  // HTTP 方法：POST 用於提交資料
      headers: { 'Content-Type': 'application/json' },  // 告訴伺服器我們送的是 JSON
      // JSON.stringify 把 JavaScript 物件轉成 JSON 字串
      body: JSON.stringify({ email, password }),
    });

    // 檢查登入是否成功
    if (!response.ok) {
      // 登入失敗，讀取錯誤訊息並拋出
      const error = await response.json().catch(() => ({ message: 'Login failed' }));
      throw new Error(error.message || error.error || 'Invalid credentials');
    }

    // 登入成功，取得回傳的資料
    const data = await response.json();
    
    // 儲存 tokens 到瀏覽器
    // 後端回傳：{ access_token: "xxx", refresh_token: "yyy", user: {...} }
    saveTokens(data.access_token, data.refresh_token);
    
    // 把後端格式的使用者資料轉換成前端格式，然後回傳
    return transformUser(data.user);
  },

  /**
   * 使用者註冊
   * 
   * 【串接流程】
   * 前端 Register.tsx → authService.register() → POST /auth/register → 後端 auth.py register()
   * 
   * @param name - 使用者名稱
   * @param email - 電子郵件
   * @param password - 密碼
   * @param department - 部門
   * @returns 註冊成功的使用者資料
   */
  register: async (name: string, email: string, password: string, department: string): Promise<User> => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: name,  // 注意：後端用 username，前端用 name
        email,
        password,
        department,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Registration failed' }));
      throw new Error(error.message || error.error || 'Registration failed');
    }

    // 註冊成功後，自動執行登入
    // 這樣使用者註冊完就直接登入了，不用再輸入一次
    return authService.login(email, password);
  },

  /**
   * 取得目前登入的使用者資料
   * 
   * 【串接流程】
   * 前端 AuthContext.tsx → authService.getCurrentUser() → GET /auth/me → 後端 auth.py get_me()
   * 
   * @returns 目前使用者的資料
   */
  getCurrentUser: async (): Promise<User> => {
    // 使用通用的 apiRequest 函數，它會自動帶上 token
    const data = await apiRequest<any>('/auth/me');
    return transformUser(data);
  },

  /**
   * 更新個人資料
   * 
   * 【串接流程】
   * 前端 Settings.tsx → authService.updateProfile() → PATCH /auth/me → 後端 auth.py update_me()
   * 
   * @param profileData - 要更新的資料（可以只更新部分欄位）
   * @returns 更新後的使用者資料
   */
  updateProfile: async (profileData: Partial<User>): Promise<User> => {
    const data = await apiRequest<any>('/auth/me', {
      method: 'PATCH',  // PATCH 用於部分更新
      body: JSON.stringify({
        username: profileData.name,  // 前端用 name，後端用 username
        department: profileData.department,
      }),
    });
    return transformUser(data.user || data);
  },

  /**
   * 修改密碼
   * 
   * 【串接流程】
   * 前端 Settings.tsx → authService.changePassword() → POST /auth/change-password → 後端 auth.py change_password()
   * 
   * @param currentPassword - 目前的密碼（用來驗證身份）
   * @param newPassword - 新密碼
   */
  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await apiRequest<any>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: currentPassword,  // 注意命名：前端 camelCase，後端 snake_case
        new_password: newPassword,
      }),
    });
  },

  /**
   * 登出
   * 
   * 【串接流程】
   * 前端 Layout.tsx → authService.logout() → POST /auth/logout → 後端 auth.py logout()
   */
  logout: async (): Promise<void> => {
    try {
      // 嘗試通知後端使用者登出（讓後端可以記錄或撤銷 token）
      await apiRequest<any>('/auth/logout', { method: 'POST' });
    } catch (error) {
      // 即使 API 呼叫失敗也沒關係，我們還是要清除本地的 token
      // 但記錄錯誤以便除錯
      console.warn('Logout API call failed:', error instanceof Error ? error.message : 'Unknown error');
    }
    // 清除瀏覽器中的所有 token
    clearTokens();
  },
};

// ============================================
// Project Service（專案服務）
// ============================================
/**
 * 處理所有與專案相關的 API 呼叫
 * 
 * 【對應的後端檔案】backend/projects.py
 * 
 * 【包含功能】
 * - 取得專案列表 (getProjects)
 * - 取得專案詳細資訊 (getProjectsWithDetails)
 * - 取得專案統計 (getProjectStats)
 * - 建立專案 (createProject)
 * - 更新專案狀態 (updateProjectStatus)
 * - 刪除專案 (deleteProject)
 * - 管理專案成員 (addMember, removeMember, getProjectMembers)
 */
export const projectService = {
  /**
   * 取得所有專案列表
   * 
   * 【串接流程】
   * 前端 Dashboard.tsx/Projects.tsx → projectService.getProjects() → GET /projects → 後端 projects.py get_my_projects()
   * 
   * @returns 專案陣列
   */
  getProjects: async (): Promise<Project[]> => {
    // 發送 GET 請求到 /projects
    const data = await apiRequest<any>('/projects');
    // 後端可能回傳 { projects: [...] } 或直接回傳陣列
    const projects = data.projects || data;
    
    // 把每個專案都轉換成前端格式
    return projects.map((p: any) => {
      const project = transformProject(p);
      // 計算專案進度：完成任務數 / 總任務數 * 100
      const totalTasks = p.task_count || 0;
      const completedTasks = p.completed_task_count || 0;
      project.progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
      return project;
    });
  },

  /**
   * 取得專案列表（包含擁有者資訊和任務數量）
   * 
   * 這個方法和 getProjects 類似，但會額外回傳擁有者資訊
   * 
   * @returns 包含額外資訊的專案陣列
   */
  getProjectsWithDetails: async (): Promise<(Project & { owner?: User; taskCount: number })[]> => {
    const data = await apiRequest<any>('/projects');
    const projects = data.projects || data;
    
    return projects.map((p: any) => {
      const project = transformProject(p);
      const totalTasks = p.task_count || 0;
      const completedTasks = p.completed_task_count || 0;
      project.progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
      
      return {
        ...project,  // 展開專案的所有屬性
        // 如果有擁有者資訊，也轉換成前端格式
        owner: p.owner ? transformUser(p.owner) : undefined,
        taskCount: totalTasks,
      };
    });
  },

  /**
   * 取得專案統計資料
   * 
   * 【串接流程】
   * 前端 Dashboard.tsx → projectService.getProjectStats() → GET /projects/{id}/stats → 後端 projects.py get_project_stats()
   * 
   * @param projectId - 專案 ID
   * @returns 專案統計資料
   */
  getProjectStats: async (projectId: string): Promise<ProjectStats> => {
    const data = await apiRequest<any>(`/projects/${projectId}/stats`);
    return {
      totalTasks: data.tasks?.total || 0,
      completedTasks: data.tasks?.done || 0,
      // 待處理 = 待辦 + 進行中
      pendingTasks: (data.tasks?.todo || 0) + (data.tasks?.in_progress || 0),
      overdueTasks: data.tasks?.overdue || 0,
    };
  },

  /**
   * 建立新專案
   * 
   * 【串接流程】
   * 前端 Projects.tsx → projectService.createProject() → POST /projects → 後端 projects.py create_project()
   * 
   * @param project - 新專案的資料
   * @returns 建立成功的專案
   */
  createProject: async (project: Partial<Project>): Promise<Project> => {
    // 先建立專案
    const data = await apiRequest<any>('/projects', {
      method: 'POST',
      body: JSON.stringify({
        name: project.name,
        description: project.description,
      }),
    });
    
    // 如果有指定成員，逐一添加到專案中
    if (project.members && project.members.length > 0) {
      for (const memberId of project.members) {
        try {
          await projectService.addMemberById(data.project.id.toString(), memberId);
        } catch (error) {
          // 添加成員失敗時不中斷，繼續添加其他成員
          // 記錄錯誤以便除錯
          console.warn(`Failed to add member ${memberId}:`, error instanceof Error ? error.message : 'Unknown error');
        }
      }
    }
    
    return transformProject(data.project);
  },

  /**
   * 更新專案狀態（啟用/封存）
   * 
   * 【串接流程】
   * 前端 Projects.tsx → projectService.updateProjectStatus() → PATCH /projects/{id} → 後端 projects.py update_project()
   * 
   * @param projectId - 專案 ID
   * @param status - 新狀態：'active' 或 'archived'
   */
  updateProjectStatus: async (projectId: string, status: 'active' | 'archived'): Promise<void> => {
    await apiRequest<any>(`/projects/${projectId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },

  /**
   * 刪除專案
   * 
   * 【串接流程】
   * 前端 Projects.tsx → projectService.deleteProject() → DELETE /projects/{id} → 後端 projects.py delete_project()
   * 
   * @param id - 要刪除的專案 ID
   */
  deleteProject: async (id: string): Promise<void> => {
    await apiRequest<any>(`/projects/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * 透過 Email 添加成員到專案
   * 
   * 【串接流程】
   * 前端 ProjectDetail.tsx → projectService.addMember() → POST /projects/{id}/members → 後端 projects.py add_project_member()
   * 
   * @param projectId - 專案 ID
   * @param email - 要添加的成員的 Email
   * @returns 添加成功的使用者資料
   */
  addMember: async (projectId: string, email: string): Promise<User> => {
    // 步驟 1: 先用 email 找到對應的使用者
    const users = await memberService.getMembers();
    const user = users.find(u => u.email.toLowerCase() === email.toLowerCase());
    
    if (!user) {
      throw new Error('User not found with that email');
    }
    
    // 步驟 2: 用使用者 ID 添加到專案
    await apiRequest<any>(`/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify({ user_id: parseInt(user.id) }),
    });
    
    return user;
  },

  /**
   * 透過 ID 添加成員到專案
   * 
   * @param projectId - 專案 ID
   * @param userId - 使用者 ID
   */
  addMemberById: async (projectId: string, userId: string): Promise<void> => {
    await apiRequest<any>(`/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify({ user_id: parseInt(userId) }),
    });
  },

  /**
   * 從專案移除成員
   * 
   * 【串接流程】
   * 前端 ProjectDetail.tsx → projectService.removeMember() → DELETE /projects/{id}/members/{userId} → 後端 projects.py remove_project_member()
   * 
   * @param projectId - 專案 ID
   * @param userId - 要移除的使用者 ID
   */
  removeMember: async (projectId: string, userId: string): Promise<void> => {
    await apiRequest<any>(`/projects/${projectId}/members/${userId}`, {
      method: 'DELETE',
    });
  },

  /**
   * 取得專案的所有成員
   * 
   * 【串接流程】
   * 前端 ProjectDetail.tsx → projectService.getProjectMembers() → GET /projects/{id}/members → 後端 projects.py get_project_members()
   * 
   * @param projectId - 專案 ID
   * @returns 成員陣列
   */
  getProjectMembers: async (projectId: string): Promise<User[]> => {
    const data = await apiRequest<any>(`/projects/${projectId}/members`);
    const members = data.members || data;
    return members.map(transformUser);
  },
};

// ============================================
// Task Service（任務服務）
// ============================================
/**
 * 處理所有與任務相關的 API 呼叫
 * 
 * 【對應的後端檔案】backend/tasks.py
 * 
 * 【包含功能】
 * - 取得任務列表 (getAllTasks, getTasksByProject, getMyTasks)
 * - 建立任務 (createTask)
 * - 更新任務 (updateTask, updateTaskStatus)
 * - 刪除任務 (deleteTask)
 * - 管理任務評論 (getComments, addComment, updateComment)
 */
export const taskService = {
  /**
   * 取得所有任務（使用者可存取的所有專案的任務）
   * 
   * 【串接流程】
   * 前端 Dashboard.tsx → taskService.getAllTasks() → GET /tasks/all → 後端 tasks.py get_all_tasks()
   * 
   * @returns 任務陣列
   */
  getAllTasks: async (): Promise<Task[]> => {
    const data = await apiRequest<any>('/tasks/all');
    const tasks = data.tasks || data;
    return tasks.map(transformTask);
  },

  /**
   * 取得特定專案的所有任務
   * 
   * 【串接流程】
   * 前端 ProjectDetail.tsx → taskService.getTasksByProject() → GET /projects/{id}/tasks → 後端 tasks.py get_project_tasks()
   * 
   * @param projectId - 專案 ID
   * @returns 該專案的任務陣列
   */
  getTasksByProject: async (projectId: string): Promise<Task[]> => {
    const data = await apiRequest<any>(`/projects/${projectId}/tasks`);
    const tasks = data.tasks || data;
    return tasks.map(transformTask);
  },

  /**
   * 取得指派給我的任務
   * 
   * 【串接流程】
   * 前端 MyTasks.tsx → taskService.getMyTasks() → GET /tasks/my → 後端 tasks.py get_my_tasks()
   * 
   * @returns 我的任務陣列
   */
  getMyTasks: async (): Promise<Task[]> => {
    const data = await apiRequest<any>('/tasks/my');
    const tasks = data.tasks || data;
    return tasks.map(transformTask);
  },

  /**
   * 更新任務狀態（拖拉看板時使用）
   * 
   * 【串接流程】
   * 前端 ProjectDetail.tsx (拖拉任務) → taskService.updateTaskStatus() → PATCH /tasks/{id} → 後端 tasks.py update_task()
   * 
   * @param taskId - 任務 ID
   * @param status - 新狀態
   * @returns 更新後的任務
   */
  updateTaskStatus: async (taskId: string, status: TaskStatus): Promise<Task> => {
    // 狀態映射：前端大寫 → 後端小寫
    const statusMap: Record<TaskStatus, string> = {
      [TaskStatus.TODO]: 'todo',
      [TaskStatus.IN_PROGRESS]: 'in_progress',
      [TaskStatus.REVIEW]: 'review',
      [TaskStatus.DONE]: 'done',
    };
    
    const data = await apiRequest<any>(`/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: statusMap[status] }),
    });
    return transformTask(data.task || data);
  },

  /**
   * 更新任務（可更新多個欄位）
   * 
   * 【串接流程】
   * 前端 TaskDetailModal.tsx → taskService.updateTask() → PATCH /tasks/{id} → 後端 tasks.py update_task()
   * 
   * @param taskId - 任務 ID
   * @param updates - 要更新的欄位
   * @returns 更新後的任務
   */
  updateTask: async (taskId: string, updates: Partial<Task>): Promise<Task> => {
    // 狀態映射
    const statusMap: Record<TaskStatus, string> = {
      [TaskStatus.TODO]: 'todo',
      [TaskStatus.IN_PROGRESS]: 'in_progress',
      [TaskStatus.REVIEW]: 'review',
      [TaskStatus.DONE]: 'done',
    };
    
    // 優先級映射
    const priorityMap: Record<TaskPriority, string> = {
      [TaskPriority.LOW]: 'low',
      [TaskPriority.MEDIUM]: 'medium',
      [TaskPriority.HIGH]: 'high',
    };

    // 建立要送給後端的資料
    // 只有有值的欄位才會被加入
    const payload: any = {};
    
    if (updates.title !== undefined) payload.title = updates.title;
    if (updates.description !== undefined) payload.description = updates.description;
    if (updates.status !== undefined) payload.status = statusMap[updates.status];
    if (updates.priority !== undefined) payload.priority = priorityMap[updates.priority];
    // 負責人：前端用字串 ID，後端用數字 ID
    if (updates.assigneeId !== undefined) payload.assigned_to = updates.assigneeId ? parseInt(updates.assigneeId) : null;
    if (updates.dueDate !== undefined) payload.due_date = updates.dueDate;
    if (updates.notes !== undefined) payload.notes = updates.notes;

    const data = await apiRequest<any>(`/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return transformTask(data.task || data);
  },

  /**
   * 建立新任務
   * 
   * 【串接流程】
   * 前端 ProjectDetail.tsx → taskService.createTask() → POST /projects/{id}/tasks → 後端 tasks.py create_task()
   * 
   * @param task - 新任務的資料
   * @returns 建立成功的任務
   */
  createTask: async (task: Partial<Task>): Promise<Task> => {
    // 狀態映射
    const statusMap: Record<TaskStatus, string> = {
      [TaskStatus.TODO]: 'todo',
      [TaskStatus.IN_PROGRESS]: 'in_progress',
      [TaskStatus.REVIEW]: 'review',
      [TaskStatus.DONE]: 'done',
    };
    
    // 優先級映射
    const priorityMap: Record<TaskPriority, string> = {
      [TaskPriority.LOW]: 'low',
      [TaskPriority.MEDIUM]: 'medium',
      [TaskPriority.HIGH]: 'high',
    };

    // 發送 POST 請求到 /projects/{projectId}/tasks
    const data = await apiRequest<any>(`/projects/${task.projectId}/tasks`, {
      method: 'POST',
      body: JSON.stringify({
        title: task.title,
        description: task.description,
        status: task.status ? statusMap[task.status] : 'todo',
        priority: task.priority ? priorityMap[task.priority] : 'medium',
        // assigned_to 是指派給誰，parseInt 把字串轉成數字
        assigned_to: task.assigneeId ? parseInt(task.assigneeId) : null,
        due_date: task.dueDate,
      }),
    });
    return transformTask(data.task);
  },

  /**
   * 刪除任務
   * 
   * 【串接流程】
   * 前端 ProjectDetail.tsx → taskService.deleteTask() → DELETE /tasks/{id} → 後端 tasks.py delete_task()
   * 
   * @param taskId - 要刪除的任務 ID
   */
  deleteTask: async (taskId: string): Promise<void> => {
    await apiRequest<any>(`/tasks/${taskId}`, {
      method: 'DELETE',
    });
  },

  /**
   * 取得任務的所有評論
   * 
   * 【串接流程】
   * 前端 TaskDetailModal.tsx → taskService.getComments() → GET /tasks/{id}/comments → 後端 tasks.py get_task_comments()
   * 
   * @param taskId - 任務 ID
   * @returns 評論陣列
   */
  getComments: async (taskId: string): Promise<Comment[]> => {
    const data = await apiRequest<any>(`/tasks/${taskId}/comments`);
    const comments = data.comments || data;
    return comments.map(transformComment);
  },

  /**
   * 新增評論
   * 
   * 【串接流程】
   * 前端 TaskDetailModal.tsx → taskService.addComment() → POST /tasks/{id}/comments → 後端 tasks.py create_task_comment()
   * 
   * @param taskId - 任務 ID
   * @param content - 評論內容
   * @param userId - 使用者 ID（用於本地顯示）
   * @param userName - 使用者名稱（用於本地顯示）
   * @returns 新增的評論
   */
  addComment: async (taskId: string, content: string, userId: string, userName: string): Promise<Comment> => {
    const data = await apiRequest<any>(`/tasks/${taskId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
    
    // 後端可能不會回傳完整的使用者資訊，所以我們用傳入的參數補充
    const comment = data.comment || data;
    return {
      id: String(comment.id),
      taskId: taskId,
      userId: userId,
      userName: userName,
      content: comment.content,
      createdAt: comment.created_at,
    };
  },

  /**
   * 更新評論
   * 
   * 【串接流程】
   * 前端 TaskDetailModal.tsx → taskService.updateComment() → PATCH /comments/{id} → 後端 tasks.py update_comment()
   * 
   * @param commentId - 評論 ID
   * @param content - 新的評論內容
   * @returns 更新後的評論
   */
  updateComment: async (commentId: string, content: string): Promise<Comment> => {
    const data = await apiRequest<any>(`/comments/${commentId}`, {
      method: 'PATCH',
      body: JSON.stringify({ content }),
    });
    return transformComment(data.comment || data);
  },
};

// ============================================
// Notification Service（通知服務）
// ============================================
/**
 * 處理所有與通知相關的 API 呼叫
 * 
 * 【對應的後端檔案】backend/notifications.py
 * 
 * 【包含功能】
 * - 取得通知列表 (getNotifications)
 * - 標記通知為已讀 (markAsRead, markAllAsRead)
 */
export const notificationService = {
  /**
   * 取得所有通知
   * 
   * 【串接流程】
   * 前端 Layout.tsx → notificationService.getNotifications() → GET /api/notifications → 後端 notifications.py get_notifications()
   * 
   * 注意：通知 API 的前綴是 /api，不是 /notifications
   * 
   * @returns 通知陣列
   */
  getNotifications: async (): Promise<Notification[]> => {
    const data = await apiRequest<any>('/api/notifications');
    const notifications = data.notifications || data;
    return notifications.map(transformNotification);
  },

  /**
   * 標記單一通知為已讀
   * 
   * 【串接流程】
   * 前端 → notificationService.markAsRead() → PATCH /api/notifications/{id}/read → 後端 notifications.py mark_notification_read()
   * 
   * @param notificationId - 通知 ID
   */
  markAsRead: async (notificationId: string): Promise<void> => {
    await apiRequest<any>(`/api/notifications/${notificationId}/read`, {
      method: 'PATCH',
    });
  },

  /**
   * 標記所有通知為已讀
   * 
   * 【串接流程】
   * 前端 Layout.tsx → notificationService.markAllAsRead() → PATCH /api/notifications/read-all → 後端 notifications.py mark_all_notifications_read()
   */
  markAllAsRead: async (): Promise<void> => {
    await apiRequest<any>('/api/notifications/read-all', {
      method: 'PATCH',
    });
  },
};

// ============================================
// Member Service（成員服務）
// ============================================
/**
 * 處理與成員相關的 API 呼叫
 * 
 * 【對應的後端檔案】backend/members.py
 * 
 * 【包含功能】
 * - 取得所有成員 (getMembers)
 */
export const memberService = {
  /**
   * 取得所有成員（用於選擇專案成員或任務負責人）
   * 
   * 【串接流程】
   * 前端 ProjectDetail.tsx/Projects.tsx → memberService.getMembers() → GET /members → 後端 members.py get_all_members()
   * 
   * @returns 所有使用者的陣列
   */
  getMembers: async (): Promise<User[]> => {
    const data = await apiRequest<any>('/members');
    const members = data.members || data;
    return members.map(transformUser);
  },
};

// ============================================
// Tag Service（標籤服務）
// ============================================
/**
 * 處理與標籤相關的 API 呼叫
 * 
 * 【對應的後端檔案】backend/tags.py
 * 
 * 【包含功能】
 * - 取得專案標籤 (getProjectTags)
 * - 建立標籤 (createTag)
 * - 更新標籤 (updateTag)
 * - 刪除標籤 (deleteTag)
 * - 為任務添加標籤 (addTagToTask)
 * - 移除任務標籤 (removeTagFromTask)
 */
export const tagService = {
  /**
   * 取得專案的所有標籤
   * 
   * @param projectId - 專案 ID
   * @returns 標籤陣列和預設顏色選項
   */
  getProjectTags: async (projectId: string): Promise<{ tags: Tag[], defaultColors: string[] }> => {
    const data = await apiRequest<any>(`/projects/${projectId}/tags`);
    return {
      tags: (data.tags || []).map((tag: any) => ({
        id: String(tag.id),
        name: tag.name,
        color: tag.color,
        taskCount: tag.task_count
      })),
      defaultColors: data.default_colors || []
    };
  },

  /**
   * 建立新標籤
   * 
   * @param projectId - 專案 ID
   * @param name - 標籤名稱
   * @param color - 標籤顏色
   */
  createTag: async (projectId: string, name: string, color: string): Promise<Tag> => {
    const data = await apiRequest<any>(`/projects/${projectId}/tags`, {
      method: 'POST',
      body: JSON.stringify({ name, color }),
    });
    const tag = data.tag;
    return {
      id: String(tag.id),
      name: tag.name,
      color: tag.color,
      taskCount: tag.task_count
    };
  },

  /**
   * 更新標籤
   * 
   * @param tagId - 標籤 ID
   * @param updates - 要更新的欄位
   */
  updateTag: async (tagId: string, updates: { name?: string; color?: string }): Promise<Tag> => {
    const data = await apiRequest<any>(`/tags/${tagId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
    const tag = data.tag;
    return {
      id: String(tag.id),
      name: tag.name,
      color: tag.color,
      taskCount: tag.task_count
    };
  },

  /**
   * 刪除標籤
   * 
   * @param tagId - 標籤 ID
   */
  deleteTag: async (tagId: string): Promise<void> => {
    await apiRequest<any>(`/tags/${tagId}`, {
      method: 'DELETE',
    });
  },

  /**
   * 為任務添加標籤
   * 
   * @param taskId - 任務 ID
   * @param tagIds - 標籤 ID 陣列
   */
  addTagsToTask: async (taskId: string, tagIds: string[]): Promise<Tag[]> => {
    const data = await apiRequest<any>(`/tasks/${taskId}/tags`, {
      method: 'POST',
      body: JSON.stringify({ tag_ids: tagIds.map(id => parseInt(id)) }),
    });
    return (data.all_tags || []).map((tag: any) => ({
      id: String(tag.id),
      name: tag.name,
      color: tag.color
    }));
  },

  /**
   * 移除任務的標籤
   * 
   * @param taskId - 任務 ID
   * @param tagId - 標籤 ID
   */
  removeTagFromTask: async (taskId: string, tagId: string): Promise<Tag[]> => {
    const data = await apiRequest<any>(`/tasks/${taskId}/tags/${tagId}`, {
      method: 'DELETE',
    });
    return (data.remaining_tags || []).map((tag: any) => ({
      id: String(tag.id),
      name: tag.name,
      color: tag.color
    }));
  },

  /**
   * 取得任務的標籤
   * 
   * @param taskId - 任務 ID
   */
  getTaskTags: async (taskId: string): Promise<Tag[]> => {
    const data = await apiRequest<any>(`/tasks/${taskId}/tags`);
    return (data.tags || []).map((tag: any) => ({
      id: String(tag.id),
      name: tag.name,
      color: tag.color
    }));
  },
};

// ============================================
// Attachment Service（附件服務）
// ============================================
/**
 * 處理與附件相關的 API 呼叫
 * 
 * 【對應的後端檔案】backend/uploads.py
 * 
 * 【包含功能】
 * - 上傳附件 (uploadAttachment)
 * - 取得任務附件 (getTaskAttachments)
 * - 下載附件 (downloadAttachment)
 * - 刪除附件 (deleteAttachment)
 */
export const attachmentService = {
  /**
   * 上傳附件到任務
   * 
   * @param taskId - 任務 ID
   * @param file - 檔案物件
   */
  uploadAttachment: async (taskId: string, file: File): Promise<Attachment> => {
    const formData = new FormData();
    formData.append('file', file);

    const accessToken = localStorage.getItem('nexus_access_token');
    
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/attachments`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Upload failed');
    }

    const data = await response.json();
    const attachment = data.attachment;
    
    return {
      id: String(attachment.id),
      filename: attachment.filename,
      originalFilename: attachment.original_filename,
      fileSize: attachment.file_size,
      fileType: attachment.file_type,
      uploadedAt: attachment.uploaded_at,
      uploadedBy: String(attachment.uploaded_by?.id || attachment.uploaded_by)
    };
  },

  /**
   * 取得任務的所有附件
   * 
   * @param taskId - 任務 ID
   */
  getTaskAttachments: async (taskId: string): Promise<Attachment[]> => {
    const data = await apiRequest<any>(`/tasks/${taskId}/attachments`);
    return (data.attachments || []).map((a: any) => ({
      id: String(a.id),
      filename: a.filename,
      originalFilename: a.original_filename,
      fileSize: a.file_size,
      fileType: a.file_type,
      uploadedAt: a.uploaded_at,
      uploadedBy: String(a.uploaded_by)
    }));
  },

  /**
   * 下載附件
   * 
   * @param attachmentId - 附件 ID
   * @param originalFilename - 原始檔名
   */
  downloadAttachment: async (attachmentId: string, originalFilename: string): Promise<void> => {
    const accessToken = localStorage.getItem('nexus_access_token');
    
    const response = await fetch(`${API_BASE_URL}/attachments/${attachmentId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Download failed');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = originalFilename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  /**
   * 刪除附件
   * 
   * @param attachmentId - 附件 ID
   */
  deleteAttachment: async (attachmentId: string): Promise<void> => {
    await apiRequest<any>(`/attachments/${attachmentId}`, {
      method: 'DELETE',
    });
  },
};

// 導出 API_BASE_URL 供需要直接使用的地方
export { API_BASE_URL };
