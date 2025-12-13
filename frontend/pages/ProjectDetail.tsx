/**
 * ============================================
 * ProjectDetail.tsx - 專案詳情頁面（看板）
 * ============================================
 * 
 * 【這個頁面的作用】
 * 顯示單一專案的詳細資訊，使用看板（Kanban）形式顯示任務。
 * 功能包括：
 * - 看板式任務管理（TODO → IN_PROGRESS → REVIEW → DONE）
 * - 拖放更新任務狀態
 * - 篩選和排序任務
 * - 建立新任務
 * - 管理專案成員
 * - 查看任務詳情
 * 
 * 【看板結構圖】
 * ┌───────────────────────────────────────────────────────────────┐
 * │ ← Back to Projects                                            │
 * │ Project Name                           [Team] [+ Add Task]    │
 * │ Project description                                           │
 * ├───────────────────────────────────────────────────────────────┤
 * │ [Filter] Assignee... | Priority | Date▼    [Reset]           │
 * ├───────────────────────────────────────────────────────────────┤
 * │ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
 * │ │ ● TODO (3) │ │ ● IN_PROG  │ │ ● REVIEW   │ │ ● DONE     │  │
 * │ ├────────────┤ ├────────────┤ ├────────────┤ ├────────────┤  │
 * │ │ ┌────────┐ │ │ ┌────────┐ │ │ ┌────────┐ │ │ ┌────────┐ │  │
 * │ │ │ Task 1 │ │ │ │ Task 4 │ │ │ │ Task 6 │ │ │ │ Task 8 │ │  │
 * │ │ └────────┘ │ │ └────────┘ │ │ └────────┘ │ │ └────────┘ │  │
 * │ │ ┌────────┐ │ │ ┌────────┐ │ │            │ │            │  │
 * │ │ │ Task 2 │ │ │ │ Task 5 │ │ │            │ │            │  │
 * │ │ └────────┘ │ │ └────────┘ │ │            │ │            │  │
 * │ └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
 * └───────────────────────────────────────────────────────────────┘
 * 
 * 【路由】
 * 路徑: /projects/:projectId
 * 
 * 【API 串接】
 * - projectService.getProjects() → 取得專案列表
 * - projectService.getProjectMembers() → 取得專案成員
 * - projectService.addMember() → 添加成員
 * - projectService.removeMember() → 移除成員
 * - taskService.getTasksByProject() → 取得專案任務
 * - taskService.createTask() → 建立任務
 * - taskService.updateTaskStatus() → 更新任務狀態
 * - taskService.deleteTask() → 刪除任務
 * - memberService.getMembers() → 取得所有使用者
 */

// ============================================
// 導入 React 和相關模組
// ============================================

import React, { useEffect, useState, useMemo } from 'react';

// React Router
// useParams: 取得 URL 參數（如 :projectId）
import { useParams, useNavigate } from 'react-router-dom';

// API 服務
import { projectService, taskService, memberService } from '../services/apiService';

// 類型定義
import { Project, Task, TaskStatus, TaskPriority, User } from '../types';

// 認證 Context
import { useAuth } from '../context/AuthContext';

// 子組件
import { TaskDetailModal } from '../components/TaskDetailModal';

// 輔助函數
import { getDueDateStatusClass, getPriorityColor, formatDate } from '../utils/helpers';

// Lucide 圖示
import { 
  Plus,               // 新增圖示
  MoreHorizontal,     // 更多選項（水平）
  Calendar,           // 日曆圖示
  MessageSquare,      // 訊息圖示（評論數）
  X,                  // 關閉圖示
  Users,              // 成員圖示
  Trash2,             // 刪除圖示
  UserPlus,           // 添加成員圖示
  Filter,             // 篩選圖示
  Search,             // 搜尋圖示
  ChevronDown,        // 向下箭頭
  ArrowLeft,          // 返回箭頭
  User as UserIcon    // 使用者圖示
} from 'lucide-react';

// ============================================
// ProjectDetail 組件
// ============================================

export const ProjectDetail: React.FC = () => {
  // ============================================
  // 從 URL 和 Context 取得資料
  // ============================================
  
  // 從 URL 取得專案 ID
  // 例如：/projects/123 → projectId = "123"
  const { projectId } = useParams<{ projectId: string }>();
  
  // 取得目前登入的使用者
  const { user } = useAuth();
  
  const navigate = useNavigate();
  
  // ============================================
  // 狀態管理
  // ============================================
  
  // 專案資料
  const [project, setProject] = useState<Project | null>(null);
  
  // 任務列表
  const [tasks, setTasks] = useState<Task[]>([]);

  // ===== 篩選和排序狀態 =====
  const [filterAssignee, setFilterAssignee] = useState('all');           // 負責人篩選
  const [filterAssigneeSearch, setFilterAssigneeSearch] = useState('All Members');
  const [isFilterAssigneeOpen, setIsFilterAssigneeOpen] = useState(false);
  const [filterPriority, setFilterPriority] = useState('all');           // 優先級篩選
  const [filterDueDate, setFilterDueDate] = useState('all');             // 截止日期篩選
  const [isFilterDateOpen, setIsFilterDateOpen] = useState(false);
  const [sortBy, setSortBy] = useState<'none' | 'dueDate' | 'priority'>('none');  // 排序方式
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');         // 排序方向
  const [isSortOpen, setIsSortOpen] = useState(false);

  // ===== 建立任務彈窗狀態 =====
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDesc, setNewTaskDesc] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState<TaskPriority>(TaskPriority.MEDIUM);
  const [newTaskAssigneeId, setNewTaskAssigneeId] = useState('');
  const [createAssigneeSearch, setCreateAssigneeSearch] = useState('');
  const [isCreateAssigneeOpen, setIsCreateAssigneeOpen] = useState(false);
  const [newTaskDueDate, setNewTaskDueDate] = useState('');

  // ===== 任務詳情彈窗狀態 =====
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  // ===== 成員管理彈窗狀態 =====
  const [isMembersModalOpen, setIsMembersModalOpen] = useState(false);
  const [projectMembers, setProjectMembers] = useState<User[]>([]);      // 專案成員
  const [allUsers, setAllUsers] = useState<User[]>([]);                  // 所有使用者
  const [inviteSearchQuery, setInviteSearchQuery] = useState('');
  const [isInviteDropdownOpen, setIsInviteDropdownOpen] = useState(false);

  // ============================================
  // 副作用：載入資料
  // ============================================
  
  /**
   * 當 projectId 改變時，載入專案資料
   * 
   * 【API 呼叫】
   * - projectService.getProjects() → 取得專案列表（然後找出對應的專案）
   * - taskService.getTasksByProject() → 取得該專案的任務
   * - projectService.getProjectMembers() → 取得專案成員
   * - memberService.getMembers() → 取得所有使用者（用於邀請成員）
   */
  useEffect(() => {
    if (projectId) {
      // 取得專案資料
      projectService.getProjects().then(ps => 
        setProject(ps.find(p => p.id === projectId) || null)
      );
      // 載入任務
      refreshTasks();
      // 載入成員
      loadMembers();
      // 取得所有使用者（用於邀請）
      memberService.getMembers().then(setAllUsers);
    }
  }, [projectId]);

  /**
   * 載入專案成員
   */
  const loadMembers = () => {
    if (projectId) {
      projectService.getProjectMembers(projectId).then(setProjectMembers);
    }
  };

  /**
   * 重新載入任務列表
   */
  const refreshTasks = () => {
    if (projectId) {
      taskService.getTasksByProject(projectId).then(setTasks);
    }
  };

  // ============================================
  // 拖放功能
  // ============================================
  
  /**
   * 開始拖動任務
   * @param e - 拖動事件
   * @param taskId - 被拖動的任務 ID
   */
  const handleDragStart = (e: React.DragEvent, taskId: string) => {
    // 把任務 ID 存到拖動資料中
    e.dataTransfer.setData('taskId', taskId);
  };

  /**
   * 放下任務到新欄位
   * @param e - 放下事件
   * @param status - 目標狀態
   * 
   * 【API 呼叫】
   * taskService.updateTaskStatus(taskId, status)
   * → PATCH /tasks/{taskId}
   * → 後端 tasks.py update_task()
   */
  const handleDrop = async (e: React.DragEvent, status: TaskStatus) => {
    const taskId = e.dataTransfer.getData('taskId');
    if (taskId) {
      // 樂觀更新 UI
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status } : t));
      // 如果任務詳情彈窗開著，也要更新
      if (selectedTask?.id === taskId) {
        setSelectedTask(prev => prev ? { ...prev, status } : null);
      }
      // 呼叫 API 更新
      await taskService.updateTaskStatus(taskId, status);
    }
  };

  /**
   * 允許放下（必須阻止預設行為）
   */
  const handleDragOver = (e: React.DragEvent) => e.preventDefault();

  // ============================================
  // 任務操作函數
  // ============================================
  
  /**
   * 刪除任務
   * 
   * 【API 呼叫】
   * taskService.deleteTask(id)
   * → DELETE /tasks/{id}
   * → 後端 tasks.py delete_task()
   */
  const deleteTask = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();  // 阻止事件冒泡（不要打開詳情彈窗）
    if (confirm("Delete this task?")) {
      await taskService.deleteTask(id);
      if (selectedTask?.id === id) setSelectedTask(null);
      refreshTasks();
    }
  };

  /**
   * 建立新任務
   * 
   * 【API 呼叫】
   * taskService.createTask({ projectId, title, description, priority, status, assigneeId, dueDate })
   * → POST /tasks
   * → 後端 tasks.py create_task()
   */
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!project) return;

    try {
      await taskService.createTask({
        projectId: project.id,
        title: newTaskTitle,
        description: newTaskDesc,
        priority: newTaskPriority,
        status: TaskStatus.TODO,  // 新任務預設在 TODO 欄位
        assigneeId: newTaskAssigneeId || undefined,
        dueDate: newTaskDueDate || undefined
      });
      
      // 關閉彈窗並重設表單
      setIsCreateTaskModalOpen(false);
      setNewTaskTitle('');
      setNewTaskDesc('');
      setNewTaskPriority(TaskPriority.MEDIUM);
      setNewTaskAssigneeId('');
      setCreateAssigneeSearch('');
      setNewTaskDueDate('');
      
      // 重新載入任務
      refreshTasks();
    } catch (error) {
      console.error("Failed to create task", error);
    }
  };

  /**
   * 從任務詳情彈窗更新任務
   * @param updatedTask - 更新後的任務資料
   */
  const handleUpdateTaskFromModal = (updatedTask: Task) => {
    setTasks(prev => prev.map(t => t.id === updatedTask.id ? updatedTask : t));
    setSelectedTask(updatedTask);
  };

  // ============================================
  // 成員管理函數
  // ============================================
  
  /**
   * 添加成員到專案
   * 
   * 【API 呼叫】
   * projectService.addMember(projectId, email)
   * → POST /projects/{id}/members
   * → 後端 projects.py add_member()
   */
  const handleAddMember = async (userEmail: string) => {
    if (!project || !userEmail) return;
    try {
      await projectService.addMember(project.id, userEmail);
      loadMembers();
      setInviteSearchQuery('');
      setIsInviteDropdownOpen(false);
    } catch (err: any) {
      alert(err.message || "Failed to add member");
    }
  };

  /**
   * 從專案移除成員
   * 
   * 【API 呼叫】
   * projectService.removeMember(projectId, userId)
   * → DELETE /projects/{id}/members/{userId}
   * → 後端 projects.py remove_member()
   */
  const handleRemoveMember = async (userId: string) => {
    if (!project) return;
    if (confirm("Are you sure you want to remove this member?")) {
      await projectService.removeMember(project.id, userId);
      loadMembers();
    }
  };

  /**
   * 根據 userId 取得成員的頭像
   */
  const getAssigneeAvatar = (userId?: string) => {
    const member = projectMembers.find(m => m.id === userId);
    return member?.avatar;
  };

  // ============================================
  // 篩選和排序邏輯
  // ============================================
  
  /**
   * 根據篩選和排序條件處理任務列表
   * 使用 useMemo 避免不必要的重新計算
   */
  const processedTasks = useMemo(() => {
    let result = [...tasks];
    
    // 負責人篩選
    if (filterAssignee !== 'all') {
      result = result.filter(t => 
        filterAssignee === 'unassigned' ? !t.assigneeId : t.assigneeId === filterAssignee
      );
    }
    
    // 優先級篩選
    if (filterPriority !== 'all') {
      result = result.filter(t => t.priority === filterPriority);
    }
    
    // 截止日期篩選
    if (filterDueDate !== 'all') {
      const today = new Date(); 
      today.setHours(0, 0, 0, 0);
      const nextWeek = new Date(today); 
      nextWeek.setDate(today.getDate() + 7);
      
      result = result.filter(t => {
        if (!t.dueDate) return false;
        const [y, m, d] = t.dueDate.split('-').map(Number);
        const taskDate = new Date(y, m - 1, d);
        
        if (filterDueDate === 'overdue') return taskDate < today;
        if (filterDueDate === 'today') return taskDate.getTime() === today.getTime();
        if (filterDueDate === 'week') return taskDate >= today && taskDate <= nextWeek;
        return true;
      });
    }
    
    // 排序
    if (sortBy !== 'none') {
      result.sort((a, b) => {
        let comparison = 0;
        if (sortBy === 'priority') {
          // 優先級排序：HIGH > MEDIUM > LOW
          const weight = { [TaskPriority.HIGH]: 3, [TaskPriority.MEDIUM]: 2, [TaskPriority.LOW]: 1 };
          comparison = weight[a.priority] - weight[b.priority];
        } else if (sortBy === 'dueDate') {
          // 日期排序：沒有日期的排在最後
          if (!a.dueDate) return 1;
          if (!b.dueDate) return -1;
          comparison = new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
        }
        return sortDir === 'asc' ? comparison : -comparison;
      });
    }
    
    return result;
  }, [tasks, filterAssignee, filterPriority, filterDueDate, sortBy, sortDir]);

  /**
   * 根據搜尋條件過濾成員
   */
  const getFilteredMembers = (searchTerm: string) => {
    if (!searchTerm) return projectMembers;
    const lower = searchTerm.toLowerCase();
    return projectMembers.filter(m => 
      m.name.toLowerCase().includes(lower) || m.email.toLowerCase().includes(lower)
    );
  };

  // 載入中狀態
  if (!project) return <div>Loading...</div>;

  // ============================================
  // 渲染 UI
  // ============================================
  
  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* 返回按鈕 */}
      <button 
        onClick={() => navigate('/projects')} 
        className="flex items-center gap-2 text-slate-500 hover:text-slate-800 mb-2 transition-colors text-sm font-medium w-fit"
      >
        <ArrowLeft size={16} /> Back to Projects
      </button>

      {/* ===== 頁面標題 ===== */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{project.name}</h1>
          <p className="text-slate-500">{project.description}</p>
        </div>
        <div className="flex gap-3">
          {/* 成員管理按鈕 */}
          <button 
            onClick={() => setIsMembersModalOpen(true)} 
            className="flex items-center gap-2 px-4 py-2 bg-white text-slate-700 rounded-lg hover:bg-slate-50 border border-slate-200 transition-colors shadow-sm"
          >
            <Users size={18} /> Team
          </button>
          {/* 新增任務按鈕 */}
          <button 
            onClick={() => setIsCreateTaskModalOpen(true)} 
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Plus size={18} /> Add Task
          </button>
        </div>
      </div>

      {/* ===== 篩選工具列 ===== */}
      <div className="bg-white p-3 rounded-xl shadow-sm border border-slate-200 mb-4 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2 border-r border-slate-100 pr-4">
          <Filter size={16} className="text-slate-400" />
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Filter</span>
        </div>
        
        {/* 負責人篩選 */}
        <div className="relative min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" size={14} />
            <input 
              type="text" 
              value={filterAssigneeSearch} 
              onChange={(e) => { setFilterAssigneeSearch(e.target.value); setIsFilterAssigneeOpen(true); }} 
              onFocus={() => { setFilterAssigneeSearch(''); setIsFilterAssigneeOpen(true); }} 
              placeholder="Assignee..." 
              className="w-full pl-8 pr-3 py-1.5 text-sm bg-slate-50 border border-transparent hover:bg-slate-100 rounded-md focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none" 
            />
          </div>
          {isFilterAssigneeOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsFilterAssigneeOpen(false)}></div>
              <div className="absolute top-full left-0 mt-1 w-full bg-white rounded-lg shadow-lg border border-slate-100 py-1 z-20 max-h-60 overflow-auto">
                <button onClick={() => { setFilterAssignee('all'); setFilterAssigneeSearch('All Members'); setIsFilterAssigneeOpen(false); }} className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700">All Members</button>
                <button onClick={() => { setFilterAssignee('unassigned'); setFilterAssigneeSearch('Unassigned'); setIsFilterAssigneeOpen(false); }} className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700">Unassigned</button>
                {getFilteredMembers(filterAssigneeSearch).map(m => (
                  <button key={m.id} onClick={() => { setFilterAssignee(m.id); setFilterAssigneeSearch(m.name); setIsFilterAssigneeOpen(false); }} className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700 flex items-center gap-2">
                    <img src={m.avatar} className="w-5 h-5 rounded-full"/> {m.name}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {/* 優先級篩選按鈕組 */}
        <div className="flex items-center bg-slate-100 rounded-lg p-1">
          <button onClick={() => setFilterPriority('all')} className={`px-3 py-1 text-xs font-medium rounded-md ${filterPriority === 'all' ? 'bg-white shadow-sm' : 'text-slate-500'}`}>All</button>
          <button onClick={() => setFilterPriority(TaskPriority.HIGH)} className={`px-3 py-1 text-xs font-medium rounded-md ${filterPriority === TaskPriority.HIGH ? 'bg-red-500 text-white shadow-sm' : 'text-slate-500'}`}>High</button>
          <button onClick={() => setFilterPriority(TaskPriority.MEDIUM)} className={`px-3 py-1 text-xs font-medium rounded-md ${filterPriority === TaskPriority.MEDIUM ? 'bg-amber-500 text-white shadow-sm' : 'text-slate-500'}`}>Med</button>
          <button onClick={() => setFilterPriority(TaskPriority.LOW)} className={`px-3 py-1 text-xs font-medium rounded-md ${filterPriority === TaskPriority.LOW ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-500'}`}>Low</button>
        </div>

        {/* 截止日期篩選 */}
        <div className="relative">
          <button onClick={() => setIsFilterDateOpen(!isFilterDateOpen)} className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium ${filterDueDate !== 'all' ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-white border-slate-200 text-slate-600'}`}>
            <Calendar size={14} /> {filterDueDate === 'all' ? 'Any Date' : filterDueDate} <ChevronDown size={14} />
          </button>
          {isFilterDateOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsFilterDateOpen(false)}></div>
              <div className="absolute top-full left-0 mt-1 w-40 bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-20">
                {['all', 'overdue', 'today', 'week'].map((val) => (
                  <button key={val} onClick={() => { setFilterDueDate(val); setIsFilterDateOpen(false); }} className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700 capitalize">{val}</button>
                ))}
              </div>
            </>
          )}
        </div>
        
        {/* 重設篩選 */}
        <button onClick={() => { setFilterAssignee('all'); setFilterAssigneeSearch('All Members'); setFilterPriority('all'); setFilterDueDate('all'); }} className="ml-auto text-xs text-red-500 hover:text-red-700 font-medium px-2">Reset</button>
      </div>

      {/* ===== 看板（Kanban Board）===== */}
      <div className="flex-1 overflow-x-auto pb-4">
        <div className="flex gap-6 min-w-[1000px] h-full">
          {/* 為每個狀態建立一個欄位 */}
          {Object.values(TaskStatus).map(status => {
            // 篩選出這個欄位的任務
            const columnTasks = processedTasks.filter(t => t.status === status);
            
            return (
              <div 
                key={status} 
                onDragOver={handleDragOver} 
                onDrop={(e) => handleDrop(e, status)} 
                className="w-80 flex-shrink-0 bg-slate-100/50 rounded-xl p-4 flex flex-col border border-slate-200/60"
              >
                {/* 欄位標題 */}
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-700 text-sm uppercase tracking-wider flex items-center gap-2">
                    {/* 狀態指示點 */}
                    <div className={`w-2 h-2 rounded-full ${
                      status === 'TODO' ? 'bg-slate-400' : 
                      status === 'IN_PROGRESS' ? 'bg-blue-400' : 
                      status === 'REVIEW' ? 'bg-amber-400' : 'bg-emerald-400'
                    }`}></div>
                    {status.replace('_', ' ')}
                  </h3>
                  {/* 任務數量 */}
                  <span className="bg-slate-200 text-slate-600 text-xs px-2 py-0.5 rounded-full">
                    {columnTasks.length}
                  </span>
                </div>
                
                {/* 任務卡片列表 */}
                <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                  {columnTasks.map(task => (
                    <div 
                      key={task.id} 
                      draggable 
                      onDragStart={(e) => handleDragStart(e, task.id)} 
                      onClick={() => setSelectedTask(task)} 
                      className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 cursor-move hover:shadow-md hover:border-indigo-300 transition-all group relative select-none"
                    >
                      {/* 卡片頂部：優先級和刪除按鈕 */}
                      <div className="flex justify-between items-start mb-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getPriorityColor(task.priority)}`}>
                          {task.priority}
                        </span>
                        <button 
                          onClick={(e) => deleteTask(e, task.id)} 
                          className="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity p-1"
                        >
                          <MoreHorizontal size={16} />
                        </button>
                      </div>
                      
                      {/* 任務標題和描述 */}
                      <h4 className="font-medium text-slate-900 mb-1">{task.title}</h4>
                      <p className="text-xs text-slate-500 mb-3 line-clamp-2">{task.description}</p>
                      
                      {/* 卡片底部：日期、評論數、負責人頭像 */}
                      <div className="flex items-center justify-between pt-2 border-t border-slate-50">
                        <div className="flex items-center gap-2 text-xs">
                          {/* 截止日期 */}
                          {task.dueDate && (
                            <div className={`flex items-center gap-1 ${getDueDateStatusClass(task.dueDate)}`}>
                              <Calendar size={12} />
                              <span>{formatDate(task.dueDate)}</span>
                            </div>
                          )}
                          {/* 評論數 */}
                          <div className="flex items-center gap-1 text-slate-400">
                            <MessageSquare size={12} />
                            <span>{task.commentsCount}</span>
                          </div>
                        </div>
                        {/* 負責人頭像 */}
                        {task.assigneeId && (
                          getAssigneeAvatar(task.assigneeId) 
                            ? <img src={getAssigneeAvatar(task.assigneeId)} className="w-6 h-6 rounded-full object-cover" /> 
                            : <div className="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center text-[10px] font-bold text-indigo-600">{task.assigneeName?.charAt(0)}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ===== 任務詳情彈窗 ===== */}
      {selectedTask && (
        <TaskDetailModal 
          task={selectedTask}
          currentUser={user}
          projectMembers={projectMembers}
          onClose={() => setSelectedTask(null)}
          onUpdateTask={handleUpdateTaskFromModal}
        />
      )}

      {/* ===== 建立任務彈窗 ===== */}
      {isCreateTaskModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm" onClick={() => setIsCreateTaskModalOpen(false)}>
          <div className="bg-white rounded-xl w-full max-w-md shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-100 flex justify-between items-center">
              <h2 className="text-lg font-bold text-slate-900">Create New Task</h2>
              <button onClick={() => setIsCreateTaskModalOpen(false)} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
            </div>
            <form onSubmit={handleCreateTask} className="p-6 space-y-5">
              {/* 任務標題 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Task Title</label>
                <input type="text" value={newTaskTitle} onChange={(e) => setNewTaskTitle(e.target.value)} required autoFocus className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="e.g., Design Landing Page" />
              </div>
              
              {/* 任務描述 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <textarea value={newTaskDesc} onChange={(e) => setNewTaskDesc(e.target.value)} required className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none h-24 resize-none" placeholder="Detailed description..." />
              </div>
              
              {/* 優先級選擇 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Priority</label>
                <div className="flex items-center gap-3">
                  {[TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW].map(p => (
                    <button 
                      key={p} 
                      type="button" 
                      onClick={() => setNewTaskPriority(p)} 
                      className={`flex-1 py-2 text-sm font-medium rounded-lg border ${
                        newTaskPriority === p 
                          ? (p === 'HIGH' ? 'bg-red-500 text-white' : p === 'MEDIUM' ? 'bg-amber-500 text-white' : 'bg-slate-600 text-white') 
                          : 'bg-white border-slate-200 text-slate-600'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* 負責人選擇 */}
              <div className="relative">
                <label className="block text-sm font-medium text-slate-700 mb-1">Assignee</label>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                  <input 
                    type="text" 
                    value={createAssigneeSearch} 
                    onChange={(e) => { setCreateAssigneeSearch(e.target.value); setIsCreateAssigneeOpen(true); }} 
                    onFocus={() => setIsCreateAssigneeOpen(true)}
                    placeholder="Search member to assign..." 
                    className="w-full border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" 
                  />
                </div>
                {isCreateAssigneeOpen && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setIsCreateAssigneeOpen(false)}></div>
                    <div className="absolute top-full left-0 mt-1 w-full bg-white rounded-lg shadow-lg border border-slate-100 py-1 z-20 max-h-48 overflow-y-auto">
                      <button 
                        type="button"
                        onClick={() => { setNewTaskAssigneeId(''); setCreateAssigneeSearch('Unassigned'); setIsCreateAssigneeOpen(false); }} 
                        className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-500"
                      >
                        Unassigned
                      </button>
                      {projectMembers.filter(m => m.name.toLowerCase().includes(createAssigneeSearch.toLowerCase()) || createAssigneeSearch === '').map(member => (
                        <button 
                          key={member.id} 
                          type="button"
                          onClick={() => { setNewTaskAssigneeId(member.id); setCreateAssigneeSearch(member.name); setIsCreateAssigneeOpen(false); }} 
                          className="w-full text-left px-3 py-2 text-sm hover:bg-indigo-50 flex items-center gap-2"
                        >
                          <img src={member.avatar} className="w-6 h-6 rounded-full" alt={member.name} />
                          <span className="text-slate-700">{member.name}</span>
                          {member.department && <span className="text-xs text-slate-400 ml-auto">{member.department}</span>}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>

              {/* 截止日期 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Due Date</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                  <input 
                    type="date" 
                    value={newTaskDueDate} 
                    onChange={(e) => setNewTaskDueDate(e.target.value)} 
                    className="w-full border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" 
                  />
                </div>
              </div>

              {/* 按鈕 */}
              <div className="pt-4 flex justify-end gap-3 border-t border-slate-100 mt-4">
                <button type="button" onClick={() => setIsCreateTaskModalOpen(false)} className="px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-lg font-medium">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium shadow-sm">Create Task</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===== 成員管理彈窗 ===== */}
      {isMembersModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm" onClick={() => setIsMembersModalOpen(false)}>
          <div className="bg-white rounded-xl w-full max-w-md shadow-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
            {/* 彈窗標題 */}
            <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Users size={20} /> Team Members
              </h2>
              <button onClick={() => setIsMembersModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-5">
              {/* 添加成員區塊 */}
              <div className="mb-6 relative">
                <label className="block text-xs font-medium text-slate-500 mb-2">ADD NEW MEMBER</label>
                <div className="relative">
                  <UserPlus className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                  <input 
                    type="text" 
                    value={inviteSearchQuery} 
                    onChange={(e) => { setInviteSearchQuery(e.target.value); setIsInviteDropdownOpen(true); }} 
                    onFocus={() => setIsInviteDropdownOpen(true)} 
                    placeholder="Search name to add..." 
                    className="w-full border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none" 
                  />
                  
                  {/* 搜尋下拉選單 */}
                  {isInviteDropdownOpen && inviteSearchQuery && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setIsInviteDropdownOpen(false)}></div>
                      <div className="absolute top-full left-0 mt-1 w-full bg-white rounded-lg shadow-lg border border-slate-100 py-1 z-20 max-h-48 overflow-y-auto">
                        {allUsers.filter(u => !projectMembers.some(pm => pm.id === u.id) && u.name.toLowerCase().includes(inviteSearchQuery.toLowerCase())).map(user => (
                          <button 
                            key={user.id} 
                            onClick={() => handleAddMember(user.email)} 
                            className="w-full text-left px-3 py-2 hover:bg-indigo-50 flex items-center gap-3 transition-colors"
                          >
                            <img src={user.avatar} className="w-8 h-8 rounded-full" />
                            <div>
                              <p className="text-sm font-medium text-slate-900">{user.name}</p>
                            </div>
                            <Plus size={14} className="ml-auto text-indigo-600" />
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </div>
              
              {/* 目前成員列表 */}
              <div>
                <label className="block text-xs font-medium text-slate-500 mb-3">CURRENT MEMBERS ({projectMembers.length})</label>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {projectMembers.map(member => (
                    <div key={member.id} className="flex items-center justify-between p-2 hover:bg-slate-50 rounded-lg group transition-colors">
                      <div className="flex items-center gap-3">
                        <img src={member.avatar} className="w-8 h-8 rounded-full" />
                        <div>
                          <p className="text-sm font-medium text-slate-900">{member.name}</p>
                          <p className="text-xs text-slate-500">{member.email}</p>
                        </div>
                      </div>
                      {/* 不能移除專案擁有者 */}
                      {member.id !== project?.ownerId && (
                        <button 
                          onClick={() => handleRemoveMember(member.id)} 
                          className="text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all p-1"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
