/**
 * ============================================
 * helpers.ts - 通用輔助函數
 * ============================================
 * 
 * 【這個檔案的作用】
 * 提供整個前端應用程式共用的輔助函數，包括：
 * - 日期格式化
 * - 顏色/樣式計算
 * - 其他通用功能
 * 
 * 【為什麼要把這些函數獨立出來？】
 * 1. 重複使用：多個組件都需要用到相同的功能
 * 2. 維護方便：修改一處，所有地方都會更新
 * 3. 程式碼整潔：組件只專注於 UI，邏輯抽離到這裡
 * 
 * 【使用方式】
 * import { formatDate, getPriorityColor } from '../utils/helpers';
 * 
 * const formattedDate = formatDate('2024-01-15');
 * const colorClass = getPriorityColor(TaskPriority.HIGH);
 */

// 導入類型定義
import { TaskPriority, TaskStatus } from "../types";

// ============================================
// 日期格式化函數
// ============================================

/**
 * 將日期字串格式化為易讀格式
 * 
 * @param dateString - ISO 格式的日期字串，如 "2024-01-15"
 * @returns 格式化後的日期，如 "Jan 15, 2024"
 * 
 * 【使用範例】
 * formatDate('2024-01-15')  → "Jan 15, 2024"
 * formatDate()              → "--/--"（沒有日期時）
 * formatDate(undefined)     → "--/--"
 * 
 * 【在哪裡使用？】
 * - ProjectDetail.tsx：顯示任務的截止日期
 * - MyTasks.tsx：顯示任務的截止日期
 */
export const formatDate = (dateString?: string) => {
  // 如果沒有傳入日期，回傳預設值
  if (!dateString) return '--/--';
  
  // 使用 JavaScript 內建的 Date 和 toLocaleDateString
  // toLocaleDateString 會根據使用者的地區設定格式化日期
  return new Date(dateString).toLocaleDateString(undefined, {
    year: 'numeric',   // 顯示完整年份，如 "2024"
    month: 'short',    // 顯示簡短月份，如 "Jan"
    day: 'numeric'     // 顯示日期數字，如 "15"
  });
};

/**
 * 將日期字串格式化為時間格式
 * 
 * @param dateString - ISO 格式的日期時間字串
 * @returns 格式化後的時間，如 "10:30"
 * 
 * 【使用範例】
 * formatTime('2024-01-15T10:30:00Z')  → "10:30"
 */
export const formatTime = (dateString: string) => {
  return new Date(dateString).toLocaleTimeString([], { 
    hour: '2-digit',    // 兩位數的小時
    minute: '2-digit'   // 兩位數的分鐘
  });
};

// ============================================
// 任務狀態樣式函數
// ============================================

/**
 * 根據任務狀態回傳對應的 CSS 類別
 * 
 * @param status - 任務狀態（TODO, IN_PROGRESS, REVIEW, DONE）
 * @returns Tailwind CSS 類別字串
 * 
 * 【顏色對應】
 * - TODO（待辦）：灰色
 * - IN_PROGRESS（進行中）：藍色
 * - REVIEW（審核中）：琥珀色
 * - DONE（已完成）：綠色
 * 
 * 【使用範例】
 * getStatusColor(TaskStatus.TODO)  → "bg-slate-100 text-slate-600"
 * 
 * 然後可以用在 className 中：
 * <span className={getStatusColor(task.status)}>...</span>
 */
export const getStatusColor = (status: TaskStatus) => {
  // switch 根據不同的狀態回傳不同的類別
  switch(status) {
    case TaskStatus.TODO: 
      return 'bg-slate-100 text-slate-600';       // 灰色背景，灰色文字
    case TaskStatus.IN_PROGRESS: 
      return 'bg-blue-50 text-blue-600';          // 淺藍背景，藍色文字
    case TaskStatus.REVIEW: 
      return 'bg-amber-50 text-amber-600';        // 淺琥珀背景，琥珀色文字
    case TaskStatus.DONE: 
      return 'bg-emerald-50 text-emerald-600';    // 淺綠背景，綠色文字
    default: 
      return 'bg-slate-100 text-slate-600';       // 預設灰色
  }
};

// ============================================
// 任務優先級樣式函數
// ============================================

/**
 * 根據任務優先級回傳對應的 CSS 類別
 * 
 * @param priority - 任務優先級（HIGH, MEDIUM, LOW）
 * @returns Tailwind CSS 類別字串（包含背景色、文字色、邊框色）
 * 
 * 【顏色對應】
 * - HIGH（高）：紅色 - 緊急、重要
 * - MEDIUM（中）：琥珀色 - 一般
 * - LOW（低）：灰色 - 不急
 * 
 * 【使用範例】
 * getPriorityColor(TaskPriority.HIGH)  → "bg-red-50 text-red-600 border-red-100"
 * 
 * 【在哪裡使用？】
 * - ProjectDetail.tsx：任務卡片的優先級標籤
 * - TaskDetailModal.tsx：任務詳情的優先級顯示
 */
export const getPriorityColor = (priority: TaskPriority) => {
  switch(priority) {
    case TaskPriority.HIGH: 
      return 'bg-red-50 text-red-600 border-red-100';       // 紅色系
    case TaskPriority.MEDIUM: 
      return 'bg-amber-50 text-amber-600 border-amber-100'; // 琥珀色系
    case TaskPriority.LOW: 
      return 'bg-slate-50 text-slate-500 border-slate-100'; // 灰色系
    default: 
      return 'bg-slate-50 text-slate-500 border-slate-100'; // 預設灰色
  }
};

// ============================================
// 截止日期狀態樣式函數
// ============================================

/**
 * 根據截止日期計算顯示的樣式類別
 * 
 * @param dateString - 截止日期字串，格式為 "YYYY-MM-DD"
 * @returns Tailwind CSS 類別字串
 * 
 * 【邏輯說明】
 * - 已逾期（截止日期 < 今天）：紅色加粗
 * - 今天到期：琥珀色加粗
 * - 未來日期：普通灰色
 * - 沒有日期：淺灰色
 * 
 * 【使用範例】
 * // 假設今天是 2024-01-15
 * getDueDateStatusClass('2024-01-14')  → "text-red-500 font-bold"（已逾期）
 * getDueDateStatusClass('2024-01-15')  → "text-amber-500 font-bold"（今天到期）
 * getDueDateStatusClass('2024-01-20')  → "text-slate-500"（未來日期）
 * getDueDateStatusClass()              → "text-slate-400"（沒有日期）
 * 
 * 【在哪裡使用？】
 * - ProjectDetail.tsx：任務卡片上的截止日期顯示
 */
export const getDueDateStatusClass = (dateString?: string) => {
  // 沒有日期就回傳淺灰色
  if (!dateString) return 'text-slate-400';
  
  // 取得今天的日期（只要日期，不要時間）
  const today = new Date();
  today.setHours(0, 0, 0, 0);  // 把時間設為 00:00:00
  
  // 解析截止日期字串
  // split('-') 把 "2024-01-15" 拆成 ["2024", "01", "15"]
  // .map(Number) 把每個字串轉成數字
  const [y, m, d] = dateString.split('-').map(Number);
  
  // 建立截止日期物件
  // 注意：月份要 -1，因為 JavaScript 的月份是從 0 開始的
  const taskDate = new Date(y, m - 1, d);
  
  // 比較日期
  if (taskDate < today) {
    // 已逾期：紅色加粗
    return 'text-red-500 font-bold';
  }
  if (taskDate.getTime() === today.getTime()) {
    // 今天到期：琥珀色加粗
    return 'text-amber-500 font-bold';
  }
  // 未來日期：普通灰色
  return 'text-slate-500';
};
