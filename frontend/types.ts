/**
 * ============================================
 * types.ts - TypeScript 類型定義檔案
 * ============================================
 * 
 * 【這個檔案的作用】
 * 定義整個前端應用程式會用到的「資料類型」。
 * 
 * 【什麼是類型？】
 * 類型就像是資料的「規格書」，告訴程式：
 * - 這個資料有哪些欄位
 * - 每個欄位是什麼格式（字串、數字、布林等）
 * - 哪些欄位是必填的，哪些是選填的
 * 
 * 【為什麼需要類型？】
 * 1. 避免錯誤：如果你打錯字或用錯格式，TypeScript 會在你寫程式時就告訴你
 * 2. 自動補全：編輯器會根據類型提供建議，加快開發速度
 * 3. 文件功能：類型定義本身就是一種文件，幫助理解資料結構
 * 
 * 【這些類型對應後端的哪些資料？】
 * 前端 types.ts     ←→    後端 models.py
 * ───────────────────────────────────────
 * User              ←→    User 模型
 * Project           ←→    Project 模型
 * Task              ←→    Task 模型
 * Comment           ←→    TaskComment 模型
 * Notification      ←→    Notification 模型
 */

// ============================================
// 枚舉類型（Enum）
// ============================================
/**
 * 【什麼是枚舉？】
 * 枚舉是一組固定的值，只能從這些值中選一個。
 * 就像一個下拉選單，你只能選擇選單裡有的選項。
 */

/**
 * 任務狀態枚舉
 * 
 * 【使用場景】
 * 在看板（Kanban Board）上，任務會分成四個欄位：
 * - TODO（待辦）：還沒開始做的任務
 * - IN_PROGRESS（進行中）：正在做的任務
 * - REVIEW（審核中）：做完等待檢查的任務
 * - DONE（已完成）：完成的任務
 * 
 * 【對應後端】
 * 後端 tasks.py 使用小寫：'todo', 'in_progress', 'review', 'done'
 * 轉換在 apiService.ts 的 transformTask() 函數中進行
 */
export enum TaskStatus {
  TODO = 'TODO',           // 待辦
  IN_PROGRESS = 'IN_PROGRESS',  // 進行中
  REVIEW = 'REVIEW',       // 審核中
  DONE = 'DONE'            // 已完成
}

/**
 * 任務優先級枚舉
 * 
 * 【使用場景】
 * 用來表示任務的緊急程度：
 * - LOW（低）：不急的任務，可以慢慢做
 * - MEDIUM（中）：一般任務
 * - HIGH（高）：緊急任務，需要優先處理
 * 
 * 【對應後端】
 * 後端 tasks.py 使用小寫：'low', 'medium', 'high'
 */
export enum TaskPriority {
  LOW = 'LOW',       // 低優先級
  MEDIUM = 'MEDIUM', // 中優先級
  HIGH = 'HIGH'      // 高優先級
}

// ============================================
// 介面類型（Interface）
// ============================================
/**
 * 【什麼是介面？】
 * 介面定義了一個物件「應該長什麼樣子」。
 * 它列出所有的屬性名稱和類型。
 * 
 * 【語法說明】
 * - propertyName: type        → 必填屬性
 * - propertyName?: type       → 選填屬性（問號表示可以沒有）
 * - 'value1' | 'value2'       → 聯合類型，只能是這些值之一
 */

/**
 * 使用者類型
 * 
 * 【資料範例】
 * {
 *   id: "1",
 *   name: "王小明",
 *   email: "xiaoming@example.com",
 *   avatar: "https://ui-avatars.com/api/?name=王小明",
 *   role: "admin",
 *   department: "Engineering"
 * }
 * 
 * 【對應後端】models.py 的 User 模型
 * 【轉換位置】apiService.ts 的 transformUser() 函數
 */
export interface User {
  id: string;                    // 使用者 ID（唯一識別碼）
  name: string;                  // 使用者名稱（顯示用）
  email: string;                 // 電子郵件（也用於登入）
  avatar?: string;               // 頭像網址（選填，沒有會自動產生）
  role: 'admin' | 'member';      // 角色：管理員或一般成員
  department?: string;           // 部門（選填）
}

/**
 * 評論類型
 * 
 * 【資料範例】
 * {
 *   id: "101",
 *   taskId: "5",
 *   userId: "1",
 *   userName: "王小明",
 *   content: "這個任務我已經完成了！",
 *   createdAt: "2024-01-15T10:30:00Z"
 * }
 * 
 * 【對應後端】models.py 的 TaskComment 模型
 * 【轉換位置】apiService.ts 的 transformComment() 函數
 */
export interface Comment {
  id: string;          // 評論 ID
  taskId: string;      // 所屬任務的 ID
  userId: string;      // 發表評論的使用者 ID
  userName: string;    // 發表評論的使用者名稱（方便顯示，不用再查一次）
  content: string;     // 評論內容
  createdAt: string;   // 建立時間（ISO 格式的日期字串）
}

/**
 * 任務類型
 * 
 * 【資料範例】
 * {
 *   id: "5",
 *   projectId: "1",
 *   title: "設計首頁介面",
 *   description: "根據需求文件設計網站首頁的 UI",
 *   status: TaskStatus.IN_PROGRESS,
 *   priority: TaskPriority.HIGH,
 *   assigneeId: "2",
 *   assigneeName: "李小花",
 *   dueDate: "2024-02-01",
 *   commentsCount: 3,
 *   notes: "請參考競品分析報告"
 * }
 * 
 * 【對應後端】models.py 的 Task 模型
 * 【轉換位置】apiService.ts 的 transformTask() 函數
 * 
 * 【前後端欄位對照】
 * 前端 (types.ts)    ←→    後端 (models.py)
 * ─────────────────────────────────────────
 * id                 ←→    id
 * projectId          ←→    project_id
 * title              ←→    title
 * description        ←→    description
 * status             ←→    status (需轉換大小寫)
 * priority           ←→    priority (需轉換大小寫)
 * assigneeId         ←→    assigned_to
 * assigneeName       ←→    assignee.username
 * dueDate            ←→    due_date
 * commentsCount      ←→    comments_count (計算得出)
 * notes              ←→    notes
 */
export interface Task {
  id: string;                 // 任務 ID
  projectId: string;          // 所屬專案的 ID
  title: string;              // 任務標題
  description: string;        // 任務描述
  status: TaskStatus;         // 任務狀態（使用上面定義的枚舉）
  priority: TaskPriority;     // 優先級（使用上面定義的枚舉）
  assigneeId?: string;        // 負責人 ID（選填，可能還沒指派）
  assigneeName?: string;      // 負責人名稱（方便顯示）
  dueDate?: string;           // 截止日期（YYYY-MM-DD 格式）
  commentsCount: number;      // 評論數量
  notes?: string;             // 備註（非結構化的文字筆記）
  tags?: Tag[];               // 任務標籤（選填）
  attachments?: Attachment[]; // 任務附件（選填）
}

/**
 * 專案類型
 * 
 * 【資料範例】
 * {
 *   id: "1",
 *   name: "網站改版專案",
 *   description: "將公司官網改版成新的設計風格",
 *   ownerId: "1",
 *   members: ["1", "2", "3"],
 *   status: "active",
 *   progress: 45,
 *   createdAt: "2024-01-01T00:00:00Z"
 * }
 * 
 * 【對應後端】models.py 的 Project 模型
 * 【轉換位置】apiService.ts 的 transformProject() 函數
 */
export interface Project {
  id: string;                      // 專案 ID
  name: string;                    // 專案名稱
  description: string;             // 專案描述
  ownerId: string;                 // 擁有者（建立者）的使用者 ID
  members: string[];               // 成員 ID 陣列
  status: 'active' | 'archived';   // 狀態：啟用中或已封存
  progress: number;                // 進度百分比（0-100）
  createdAt: string;               // 建立時間
}

/**
 * 通知類型
 * 
 * 【資料範例】
 * {
 *   id: "50",
 *   userId: "1",
 *   message: "王小明 完成了任務「設計首頁」",
 *   read: false,
 *   createdAt: "5 mins ago",
 *   type: "success"
 * }
 * 
 * 【對應後端】models.py 的 Notification 模型
 * 【轉換位置】apiService.ts 的 transformNotification() 函數
 */
export interface Notification {
  id: string;                           // 通知 ID
  userId: string;                       // 接收通知的使用者 ID
  message: string;                      // 通知訊息內容
  read: boolean;                        // 是否已讀
  createdAt: string;                    // 建立時間（人類易讀格式，如「5 分鐘前」）
  type: 'info' | 'success' | 'warning'; // 通知類型（影響顯示樣式）
  projectId?: string;                   // 相關專案 ID（點擊跳轉用）
  projectName?: string;                 // 相關專案名稱
  taskId?: string;                      // 相關任務 ID
  taskTitle?: string;                   // 相關任務標題
}

/**
 * 專案統計類型
 * 
 * 【資料範例】
 * {
 *   totalTasks: 10,
 *   completedTasks: 4,
 *   pendingTasks: 5,
 *   overdueTasks: 1
 * }
 * 
 * 【用途】
 * 顯示在儀表板上，快速了解專案的任務狀況
 * 
 * 【對應後端】projects.py 的 get_project_stats() 函數
 */
export interface ProjectStats {
  totalTasks: number;      // 總任務數
  completedTasks: number;  // 已完成任務數
  pendingTasks: number;    // 待處理任務數（待辦 + 進行中）
  overdueTasks: number;    // 逾期任務數
}

/**
 * 標籤類型
 * 
 * 【資料範例】
 * {
 *   id: "1",
 *   name: "bug",
 *   color: "#ef4444",
 *   taskCount: 5
 * }
 * 
 * 【對應後端】models.py 的 Tag 模型
 */
export interface Tag {
  id: string;          // 標籤 ID
  name: string;        // 標籤名稱
  color: string;       // 標籤顏色（十六進位色碼）
  taskCount?: number;  // 使用此標籤的任務數量（選填）
}

/**
 * 附件類型
 * 
 * 【資料範例】
 * {
 *   id: "1",
 *   filename: "abc123.pdf",
 *   originalFilename: "報告.pdf",
 *   fileSize: 102400,
 *   fileType: "application/pdf",
 *   uploadedAt: "2024-01-15T10:30:00Z",
 *   uploadedBy: 1
 * }
 * 
 * 【對應後端】models.py 的 Attachment 模型
 */
export interface Attachment {
  id: string;              // 附件 ID
  filename: string;        // 伺服器上的檔名
  originalFilename: string; // 原始檔名
  fileSize: number;        // 檔案大小（bytes）
  fileType: string;        // MIME type
  uploadedAt: string;      // 上傳時間
  uploadedBy: string;      // 上傳者 ID
}
