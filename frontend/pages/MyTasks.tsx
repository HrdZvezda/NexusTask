/**
 * ============================================
 * MyTasks.tsx - 我的任務頁面
 * ============================================
 * 
 * 【這個頁面的作用】
 * 顯示所有指派給自己的任務（或所有團隊任務），
 * 提供列表式的任務管理介面。
 * 
 * 功能包括：
 * - 切換「我的任務」和「所有任務」視圖
 * - 按狀態篩選任務
 * - 按優先級排序
 * - 快速變更任務狀態
 * - 查看任務詳情
 * 
 * 【頁面結構圖】
 * ┌────────────────────────────────────────────────────┐
 * │ ← Back                                             │
 * │ My Assigned Tasks                                  │
 * │ Focus on what you need to do.                      │
 * │                                                    │
 * │ [My Tasks | All Tasks]    [Sort▼]    [Filter▼]   │
 * ├────────────────────────────────────────────────────┤
 * │ ┌────────────────────────────────────────────────┐│
 * │ │ [TODO▼]  Task Title 1       [HIGH]  📅 Jan 15 ││
 * │ │          Description...                        ││
 * │ ├────────────────────────────────────────────────┤│
 * │ │ [IN_PROGRESS▼] Task 2      [MED]   📅 Jan 20  ││
 * │ │                Description...                  ││
 * │ ├────────────────────────────────────────────────┤│
 * │ │ [DONE▼]  Task Title 3       [LOW]   📅 --/--  ││
 * │ │          Description...                        ││
 * │ └────────────────────────────────────────────────┘│
 * └────────────────────────────────────────────────────┘
 * 
 * 【路由】
 * 路徑: /tasks/my
 * 
 * 【API 串接】
 * - taskService.getAllTasks() → 取得所有任務
 * - taskService.updateTaskStatus() → 更新任務狀態
 * - memberService.getMembers() → 取得成員列表（用於顯示負責人資訊）
 */

// ============================================
// 導入 React 和相關模組
// ============================================

import React, { useEffect, useState, useMemo } from 'react';

// React Router
import { useNavigate } from 'react-router-dom';

// API 服務
import { taskService, memberService } from '../services/apiService';

// 認證 Context
import { useAuth } from '../context/AuthContext';

// 類型定義
import { Task, TaskStatus, TaskPriority, User } from '../types';

// 子組件
import { TaskDetailModal } from '../components/TaskDetailModal';

// 輔助函數
import { getDueDateStatusClass, getPriorityColor, formatDate, getStatusColor } from '../utils/helpers';

// Lucide 圖示
import { 
  ChevronDown,        // 向下箭頭
  ArrowLeft,          // 返回箭頭
  Calendar,           // 日曆圖示
  Filter,             // 篩選圖示
  Check,              // 勾選圖示
  Users,              // 多人圖示
  User as UserIcon,   // 單人圖示
  ArrowDownUp         // 排序圖示
} from 'lucide-react';

// ============================================
// MyTasks 組件
// ============================================

export const MyTasks: React.FC = () => {
  // ============================================
  // 從 Context 取得使用者資訊
  // ============================================
  
  const { user } = useAuth();
  
  // ============================================
  // 狀態管理
  // ============================================
  
  // 所有任務列表
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  
  // 所有成員列表（用於任務詳情彈窗）
  const [allMembers, setAllMembers] = useState<User[]>([]);
  
  // 視圖模式：'my'（我的任務）或 'all'（所有任務）
  const [viewMode, setViewMode] = useState<'my' | 'all'>('my');
  
  // 正在展開狀態選單的任務 ID
  const [openStatusId, setOpenStatusId] = useState<string | null>(null);
  
  // 任務詳情彈窗
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  
  // 篩選狀態
  const [filterStatus, setFilterStatus] = useState<'ALL' | TaskStatus>('ALL');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  
  // 排序狀態
  const [sortBy, setSortBy] = useState<'none' | 'priority-desc' | 'priority-asc'>('none');
  const [isSortOpen, setIsSortOpen] = useState(false);
  
  const navigate = useNavigate();

  // ============================================
  // 副作用：載入資料
  // ============================================
  
  /**
   * 組件載入時，取得所有任務和成員列表
   * 
   * 【API 呼叫】
   * - taskService.getAllTasks()
   *   → GET /tasks/all
   *   → 後端 tasks.py get_all_tasks()
   * 
   * - memberService.getMembers()
   *   → GET /members
   *   → 後端 members.py get_all_members()
   */
  useEffect(() => {
    taskService.getAllTasks().then(setAllTasks);
    memberService.getMembers().then(setAllMembers);
  }, []);

  /**
   * 點擊任意位置關閉下拉選單
   */
  useEffect(() => {
    const handleClickOutside = () => {
      setOpenStatusId(null);
      setIsFilterOpen(false);
      setIsSortOpen(false);
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  // ============================================
  // 任務操作函數
  // ============================================
  
  /**
   * 變更任務狀態
   * 
   * @param taskId - 任務 ID
   * @param newStatus - 新狀態
   * 
   * 【API 呼叫】
   * taskService.updateTaskStatus(taskId, newStatus)
   * → PATCH /tasks/{taskId}
   * → 後端 tasks.py update_task()
   */
  const handleStatusChange = async (taskId: string, newStatus: TaskStatus) => {
    // 樂觀更新 UI
    setAllTasks(prev => prev.map(t => t.id === taskId ? {...t, status: newStatus} : t));
    // 呼叫 API
    await taskService.updateTaskStatus(taskId, newStatus);
    // 關閉狀態選單
    setOpenStatusId(null);
  };

  /**
   * 從任務詳情彈窗更新任務
   * @param updatedTask - 更新後的任務
   */
  const handleTaskUpdate = (updatedTask: Task) => {
    setAllTasks(prev => prev.map(t => t.id === updatedTask.id ? updatedTask : t));
    setSelectedTask(updatedTask);
  };

  // ============================================
  // 篩選和排序邏輯
  // ============================================
  
  /**
   * 根據篩選和排序條件處理任務列表
   * 使用 useMemo 避免不必要的重新計算
   */
  const filteredTasks = useMemo(() => {
    let result = [...allTasks];
    
    // 視圖模式篩選：只顯示自己的任務或全部
    if (viewMode === 'my' && user) {
      result = result.filter(t => t.assigneeId === user.id);
    }
    
    // 狀態篩選
    if (filterStatus !== 'ALL') {
      result = result.filter(t => t.status === filterStatus);
    }
    
    // 優先級排序
    if (sortBy !== 'none') {
      // 優先級權重：HIGH=3, MEDIUM=2, LOW=1
      const weight = { [TaskPriority.HIGH]: 3, [TaskPriority.MEDIUM]: 2, [TaskPriority.LOW]: 1 };
      result.sort((a, b) => {
        const diff = weight[a.priority] - weight[b.priority];
        // priority-desc: 高優先級在前（diff 為負）
        // priority-asc: 低優先級在前（diff 為正）
        return sortBy === 'priority-desc' ? -diff : diff;
      });
    }
    
    return result;
  }, [allTasks, filterStatus, viewMode, user, sortBy]);

  // ============================================
  // 渲染 UI
  // ============================================
  
  return (
    <div className="max-w-4xl mx-auto">
      {/* 返回按鈕 */}
      <button 
        onClick={() => navigate('/')} 
        className="flex items-center gap-2 text-slate-500 hover:text-slate-800 mb-4 transition-colors text-sm font-medium"
      >
        <ArrowLeft size={16} /> Back
      </button>

      {/* ===== 頁面標題和操作按鈕 ===== */}
      <div className="flex flex-col gap-4 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              {viewMode === 'my' ? 'My Assigned Tasks' : 'All Team Tasks'}
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              {viewMode === 'my' ? 'Focus on what you need to do.' : 'Overview of all tasks across projects.'}
            </p>
          </div>
          
          {/* 操作按鈕區 */}
          <div className="flex items-center gap-3">
            {/* 視圖切換按鈕 */}
            <div className="bg-slate-100 p-1 rounded-lg flex items-center">
              <button 
                onClick={() => setViewMode('my')} 
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'my' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <UserIcon size={14} /> My Tasks
              </button>
              <button 
                onClick={() => setViewMode('all')} 
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'all' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <Users size={14} /> All Tasks
              </button>
            </div>

            {/* 排序下拉選單 */}
            <div className="relative">
              <button 
                onClick={(e) => { 
                  e.stopPropagation(); 
                  setIsSortOpen(!isSortOpen); 
                  setIsFilterOpen(false); 
                  setOpenStatusId(null); 
                }} 
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors shadow-sm ${
                  sortBy !== 'none' ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <ArrowDownUp size={16} /> Sort 
                <ChevronDown size={14} className={`transition-transform ${isSortOpen ? 'rotate-180' : ''}`} />
              </button>
              {isSortOpen && (
                <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-20 animate-in fade-in zoom-in-95 duration-100">
                  <div className="px-3 py-2 text-xs font-bold text-slate-400 uppercase tracking-wider">Priority</div>
                  {/* 高優先級在前 */}
                  <button 
                    onClick={() => { setSortBy('priority-desc'); setIsSortOpen(false); }} 
                    className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700 flex justify-between items-center"
                  >
                    High to Low 
                    {sortBy === 'priority-desc' && <Check size={14} className="text-indigo-600" />}
                  </button>
                  {/* 低優先級在前 */}
                  <button 
                    onClick={() => { setSortBy('priority-asc'); setIsSortOpen(false); }} 
                    className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700 flex justify-between items-center"
                  >
                    Low to High 
                    {sortBy === 'priority-asc' && <Check size={14} className="text-indigo-600" />}
                  </button>
                  {/* 清除排序 */}
                  {sortBy !== 'none' && (
                    <>
                      <div className="h-px bg-slate-100 my-1"></div>
                      <button 
                        onClick={() => { setSortBy('none'); setIsSortOpen(false); }} 
                        className="w-full text-left px-3 py-2 text-sm text-red-500 hover:bg-red-50"
                      >
                        Clear Sort
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* 狀態篩選下拉選單 */}
            <div className="relative">
              <button 
                onClick={(e) => { 
                  e.stopPropagation(); 
                  setIsFilterOpen(!isFilterOpen); 
                  setIsSortOpen(false); 
                  setOpenStatusId(null); 
                }} 
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors shadow-sm ${
                  filterStatus !== 'ALL' ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <Filter size={16} /> 
                {filterStatus === 'ALL' ? 'Filter' : filterStatus.replace('_', ' ')} 
                <ChevronDown size={14} className={`transition-transform ${isFilterOpen ? 'rotate-180' : ''}`} />
              </button>
              {isFilterOpen && (
                <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-20 animate-in fade-in zoom-in-95 duration-100">
                  {/* 全部狀態 */}
                  <button 
                    onClick={() => { setFilterStatus('ALL'); setIsFilterOpen(false); }} 
                    className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700 flex justify-between items-center"
                  >
                    All Statuses 
                    {filterStatus === 'ALL' && <Check size={14} className="text-indigo-600" />}
                  </button>
                  <div className="h-px bg-slate-100 my-1"></div>
                  {/* 各個狀態選項 */}
                  {Object.values(TaskStatus).map((status) => (
                    <button 
                      key={status} 
                      onClick={() => { setFilterStatus(status); setIsFilterOpen(false); }} 
                      className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700 flex justify-between items-center"
                    >
                      {status.replace('_', ' ')} 
                      {filterStatus === status && <Check size={14} className="text-indigo-600" />}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* ===== 任務列表 ===== */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 min-h-[200px]">
        <div className="divide-y divide-slate-100">
          {/* 沒有任務時的提示 */}
          {filteredTasks.length === 0 ? (
            <div className="p-12 text-center flex flex-col items-center text-slate-500">
              <div className="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3">
                <Check size={24} className="text-slate-300" />
              </div>
              <p>
                No tasks found {filterStatus !== 'ALL' ? ` in ${filterStatus.replace('_', ' ')}` : ''}
                {viewMode === 'my' ? ' assigned to you.' : '.'}
              </p>
            </div>
          ) : (
            // 任務項目列表
            filteredTasks.map((task) => (
              <div 
                key={task.id} 
                onClick={() => setSelectedTask(task)} 
                className="p-4 flex items-center gap-4 hover:bg-slate-50 transition-colors group cursor-pointer relative"
              >
                {/* ===== 狀態切換按鈕 ===== */}
                <div className="relative flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                  <button 
                    onClick={(e) => { 
                      e.stopPropagation(); 
                      setOpenStatusId(openStatusId === task.id ? null : task.id); 
                      setIsFilterOpen(false); 
                    }} 
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold transition-colors border border-transparent hover:border-slate-200 ${getStatusColor(task.status)}`}
                  >
                    {task.status.replace('_', ' ')} <ChevronDown size={12} />
                  </button>
                  
                  {/* 狀態選單 */}
                  {openStatusId === task.id && (
                    <div className="absolute top-full left-0 mt-1 w-36 bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-50">
                      {Object.values(TaskStatus).map(status => (
                        <button 
                          key={status} 
                          onClick={() => handleStatusChange(task.id, status)} 
                          className={`w-full text-left px-3 py-2 text-xs font-medium hover:bg-slate-50 ${
                            task.status === status ? 'text-indigo-600 bg-indigo-50' : 'text-slate-600'
                          }`}
                        >
                          {status.replace('_', ' ')}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* ===== 任務資訊 ===== */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    {/* 任務標題（已完成的會加刪除線）*/}
                    <h3 className={`text-sm font-medium ${
                      task.status === TaskStatus.DONE ? 'text-slate-400 line-through' : 'text-slate-900'
                    }`}>
                      {task.title}
                    </h3>
                    
                    {/* 如果是「所有任務」視圖且不是自己的任務，顯示負責人名稱 */}
                    {viewMode === 'all' && task.assigneeId !== user?.id && task.assigneeName && (
                      <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded border border-slate-200">
                        {task.assigneeName}
                      </span>
                    )}
                  </div>
                  {/* 任務描述（截斷過長的文字）*/}
                  <p className="text-xs text-slate-500 truncate">{task.description}</p>
                </div>
                
                {/* ===== 優先級和截止日期 ===== */}
                <div className="flex items-center gap-4 text-xs text-slate-400">
                  {/* 優先級標籤 */}
                  <span className={`px-2 py-1 rounded-full border ${getPriorityColor(task.priority)}`}>
                    {task.priority}
                  </span>
                  {/* 截止日期 */}
                  <div className={`flex items-center gap-1 w-28 justify-end ${getDueDateStatusClass(task.dueDate)}`}>
                    <Calendar size={14} />
                    {formatDate(task.dueDate)}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ===== 任務詳情彈窗 ===== */}
      {selectedTask && (
        <TaskDetailModal 
          task={selectedTask}
          currentUser={user}
          projectMembers={allMembers}
          onClose={() => setSelectedTask(null)}
          onUpdateTask={handleTaskUpdate}
        />
      )}
    </div>
  );
};
