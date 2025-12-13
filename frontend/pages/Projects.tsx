/**
 * ============================================
 * Projects.tsx - 專案列表頁面
 * ============================================
 * 
 * 【這個頁面的作用】
 * 顯示所有專案，並提供以下功能：
 * - 查看專案列表（卡片式顯示）
 * - 篩選專案（Active/Archived）
 * - 建立新專案
 * - 編輯專案
 * - 刪除專案
 * - 變更專案狀態
 * 
 * 【頁面結構圖】
 * ┌────────────────────────────────────────────────────┐
 * │ ← Back                                             │
 * │ Projects                                           │
 * │ Manage your team's initiatives                     │
 * │                              [Filter▼] [+ New]     │
 * ├────────────────────────────────────────────────────┤
 * │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
 * │ │ [P] ⋮       │ │ [Q] ⋮       │ │ [+]         │   │
 * │ │ Project A   │ │ Project B   │ │ Create New  │   │
 * │ │ Description │ │ Description │ │             │   │
 * │ │ ████░░ 60%  │ │ ██████ 100% │ │             │   │
 * │ │ 📅 👤 Active│ │ 📅 👤 Done  │ │             │   │
 * │ └─────────────┘ └─────────────┘ └─────────────┘   │
 * └────────────────────────────────────────────────────┘
 * 
 * 【路由】
 * 路徑: /projects
 * 
 * 【API 串接】
 * - projectService.getProjectsWithDetails() → 取得專案列表
 * - projectService.createProject() → 建立專案
 * - projectService.deleteProject() → 刪除專案
 * - projectService.updateProjectStatus() → 更新專案狀態
 * - memberService.getMembers() → 取得可選成員列表
 */

// ============================================
// 導入 React 和相關模組
// ============================================

import React, { useEffect, useState, useRef } from 'react';

// React Router
import { Link, useNavigate } from 'react-router-dom';

// API 服務
import { memberService, projectService } from '../services/apiService';

// 認證 Context
import { useAuth } from '../context/AuthContext';

// 類型定義
import { Project, User } from '../types';

// Lucide 圖示
import { 
  Plus,           // 新增圖示
  MoreVertical,   // 更多選項圖示（垂直三點）
  Layers,         // 圖層圖示
  Crown,          // 皇冠圖示（表示擁有者）
  ArrowLeft,      // 返回箭頭
  Check,          // 勾選圖示
  Search,         // 搜尋圖示
  X,              // 關閉圖示
  Edit,           // 編輯圖示
  Trash2,         // 刪除圖示
  ChevronDown,    // 向下箭頭
  Filter,         // 篩選圖示
  Calendar        // 日曆圖示
} from 'lucide-react';

// ============================================
// 類型定義
// ============================================

/**
 * 擴展的專案類型
 * 在基本 Project 類型上加上額外的顯示資訊
 */
type ProjectWithDetails = Project & { 
  owner?: User;      // 擁有者資訊
  taskCount: number; // 任務數量
};

// ============================================
// Projects 組件
// ============================================

export const Projects: React.FC = () => {
  // ============================================
  // 從 Context 取得使用者資訊
  // ============================================
  
  const { user } = useAuth();
  
  // ============================================
  // 狀態管理
  // ============================================
  
  // 專案列表
  const [projects, setProjects] = useState<ProjectWithDetails[]>([]);
  
  // 建立/編輯彈窗開關
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // ===== 篩選狀態 =====
  // 狀態篩選：active（啟用中）、archived（已封存）、all（全部）
  const [showStatusFilter, setShowStatusFilter] = useState<'active' | 'archived' | 'all'>('active');
  const [isStatusFilterOpen, setIsStatusFilterOpen] = useState(false);

  // ===== 建立/編輯表單狀態 =====
  const [editingProject, setEditingProject] = useState<Project | null>(null);  // 正在編輯的專案（null 表示新建）
  const [newProjectName, setNewProjectName] = useState('');                    // 專案名稱
  const [newProjectDesc, setNewProjectDesc] = useState('');                    // 專案描述
  
  // ===== 選單狀態 =====
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);       // 哪個專案的選單是開啟的
  const [activeStatusMenuId, setActiveStatusMenuId] = useState<string | null>(null);  // 狀態子選單
  
  // ===== 成員選擇狀態 =====
  const [availableMembers, setAvailableMembers] = useState<User[]>([]);        // 可選的成員列表
  const [selectedMemberIds, setSelectedMemberIds] = useState<string[]>([]);    // 已選擇的成員 ID
  const [memberSearchQuery, setMemberSearchQuery] = useState('');              // 成員搜尋關鍵字
  const [isMemberDropdownOpen, setIsMemberDropdownOpen] = useState(false);     // 成員下拉選單開關
  
  const navigate = useNavigate();

  // ============================================
  // 副作用：載入資料
  // ============================================
  
  /**
   * 組件載入時，取得專案列表和成員列表
   * 
   * 【API 呼叫】
   * - projectService.getProjectsWithDetails()
   *   → GET /projects
   *   → 後端 projects.py get_my_projects()
   * 
   * - memberService.getMembers()
   *   → GET /members
   *   → 後端 members.py get_all_members()
   */
  useEffect(() => {
    loadProjects();
    memberService.getMembers().then(setAvailableMembers);
  }, []);

  /**
   * 點擊任意位置關閉下拉選單
   * 這是常見的 UX 模式
   */
  useEffect(() => {
    const handleClick = () => {
      setActiveMenuId(null);
      setActiveStatusMenuId(null);
      setIsStatusFilterOpen(false);
    };
    // 只有當有選單開啟時才監聽
    if (activeMenuId || activeStatusMenuId || isStatusFilterOpen) {
      document.addEventListener('click', handleClick);
    }
    return () => document.removeEventListener('click', handleClick);
  }, [activeMenuId, activeStatusMenuId, isStatusFilterOpen]);

  // ============================================
  // 資料載入函數
  // ============================================
  
  /**
   * 載入專案列表
   */
  const loadProjects = () => {
    projectService.getProjectsWithDetails().then(setProjects);
  };

  // ============================================
  // 彈窗操作函數
  // ============================================
  
  /**
   * 開啟建立專案彈窗
   */
  const openCreateModal = () => {
    setEditingProject(null);  // 清除編輯狀態
    setNewProjectName('');
    setNewProjectDesc('');
    // 預設把自己加入成員
    setSelectedMemberIds(user ? [user.id] : []);
    setIsModalOpen(true);
  };

  /**
   * 開啟編輯專案彈窗
   * @param project - 要編輯的專案
   */
  const openEditModal = (project: Project) => {
    setEditingProject(project);
    setNewProjectName(project.name);
    setNewProjectDesc(project.description);
    setSelectedMemberIds(project.members);
    setIsModalOpen(true);
  };

  // ============================================
  // 表單處理函數
  // ============================================
  
  /**
   * 儲存專案（建立或更新）
   * 
   * @param e - 表單提交事件
   * 
   * 【API 呼叫】
   * projectService.createProject({ name, description, members })
   * → POST /projects
   * → 後端 projects.py create_project()
   */
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (editingProject) {
      // 更新專案（目前 API 不完全支援，只顯示提示）
      alert("Project updated! (Simulation)");
    } else {
      // 建立新專案
      await projectService.createProject({ 
        name: newProjectName, 
        description: newProjectDesc,
        members: selectedMemberIds
      });
    }
    
    // 重設表單狀態
    setNewProjectName('');
    setNewProjectDesc('');
    setSelectedMemberIds([]);
    setMemberSearchQuery('');
    setEditingProject(null);
    setIsModalOpen(false);
    
    // 重新載入專案列表
    loadProjects();
  };

  /**
   * 刪除專案
   * 
   * @param id - 要刪除的專案 ID
   * 
   * 【API 呼叫】
   * projectService.deleteProject(id)
   * → DELETE /projects/{id}
   * → 後端 projects.py delete_project()
   */
  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to delete this project?")) {
      await projectService.deleteProject(id);
      loadProjects();
    }
  };
  
  /**
   * 變更專案狀態
   * 
   * @param projectId - 專案 ID
   * @param newStatus - 新狀態 ('active' 或 'archived')
   * 
   * 【API 呼叫】
   * projectService.updateProjectStatus(projectId, newStatus)
   * → PATCH /projects/{id}
   * → 後端 projects.py update_project()
   */
  const handleStatusChange = async (projectId: string, newStatus: 'active' | 'archived') => {
    // 樂觀更新：先更新 UI，再送 API
    // 這樣使用者體驗更好，不用等待
    setProjects(prev => prev.map(p => 
      p.id === projectId ? { ...p, status: newStatus } : p
    ));
    
    try {
      await projectService.updateProjectStatus(projectId, newStatus);
    } catch (e) {
      console.error("Failed to update status", e);
      // 如果失敗，應該要回滾更新（這裡簡化處理）
    }
    setActiveStatusMenuId(null);
  };

  // ============================================
  // 成員選擇函數
  // ============================================
  
  /**
   * 切換成員的選擇狀態
   * 
   * @param userId - 成員 ID
   */
  const toggleMemberSelection = (userId: string) => {
    setSelectedMemberIds(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)  // 已選擇則移除
        : [...prev, userId]                  // 未選擇則加入
    );
    // 選擇後清空搜尋
    if (!selectedMemberIds.includes(userId)) {
      setMemberSearchQuery('');
    }
  };

  /**
   * 取得成員建議列表
   * 分為「推薦」（同部門）和「其他」兩組
   */
  const getMemberSuggestions = () => {
    const query = memberSearchQuery.toLowerCase();
    
    // 過濾已選擇的和不符合搜尋的
    let filtered = availableMembers.filter(m => 
      !selectedMemberIds.includes(m.id) && 
      (m.name.toLowerCase().includes(query) || m.email.toLowerCase().includes(query))
    );
    
    // 同部門的放在「推薦」區
    const recommended = filtered.filter(m => 
      m.department === user?.department && m.id !== user?.id
    );
    
    // 其他的放在「所有成員」區
    const others = filtered.filter(m => 
      m.department !== user?.department || m.id === user?.id
    );
    
    return { recommended, others };
  };

  const { recommended, others } = getMemberSuggestions();

  // ============================================
  // 篩選邏輯
  // ============================================
  
  /**
   * 根據篩選條件過濾專案列表
   */
  const filteredProjects = projects.filter(p => {
    if (showStatusFilter === 'active') return p.status === 'active';
    if (showStatusFilter === 'archived') return p.status === 'archived';
    return true;  // 'all' 顯示全部
  });

  /**
   * 取得篩選按鈕的標籤文字
   */
  const getFilterLabel = () => {
    switch (showStatusFilter) {
      case 'active': return 'Active Only';
      case 'archived': return 'Archived Only';
      default: return 'All Projects';
    }
  };

  // ============================================
  // 渲染 UI
  // ============================================
  
  return (
    <div>
      {/* 返回按鈕 */}
      <button 
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-slate-500 hover:text-slate-800 mb-4 transition-colors text-sm font-medium"
      >
        <ArrowLeft size={16} /> Back
      </button>

      {/* 頁面標題和操作按鈕 */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Projects</h1>
          <p className="text-slate-500 mt-1">Manage your team's initiatives</p>
        </div>
        <div className="flex items-center gap-3">
          {/* ===== 狀態篩選下拉選單 ===== */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsStatusFilterOpen(!isStatusFilterOpen);
              }}
              className="flex items-center gap-2 px-3 py-2 bg-white text-slate-700 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors text-sm font-medium shadow-sm"
            >
              <Filter size={16} className="text-slate-400" />
              {getFilterLabel()}
              <ChevronDown size={14} className="text-slate-400" />
            </button>
            {isStatusFilterOpen && (
              <div className="absolute right-0 top-full mt-1 w-44 bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-20">
                <button
                  onClick={() => {
                    setShowStatusFilter('active');
                    setIsStatusFilterOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700 flex justify-between items-center"
                >
                  Active Only
                  {showStatusFilter === 'active' && <Check size={14} className="text-indigo-600" />}
                </button>
                <button
                  onClick={() => {
                    setShowStatusFilter('archived');
                    setIsStatusFilterOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700 flex justify-between items-center"
                >
                  Archived Only
                  {showStatusFilter === 'archived' && <Check size={14} className="text-indigo-600" />}
                </button>
                <div className="h-px bg-slate-100 my-1"></div>
                <button
                  onClick={() => {
                    setShowStatusFilter('all');
                    setIsStatusFilterOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700 flex justify-between items-center"
                >
                  All Projects
                  {showStatusFilter === 'all' && <Check size={14} className="text-indigo-600" />}
                </button>
              </div>
            )}
          </div>

          {/* ===== 新增專案按鈕 ===== */}
          <button
            onClick={openCreateModal}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-indigo-700 transition-colors shadow-sm text-sm font-medium"
          >
            <Plus size={18} /> New Project
          </button>
        </div>
      </div>

      {/* ===== 專案卡片網格 ===== */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredProjects.map((project) => (
          <div key={project.id} className="relative group isolate h-full">
            {/* 專案卡片（連結到詳情頁） */}
            <Link to={`/projects/${project.id}`} className="block h-full">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:border-indigo-300 hover:shadow-md transition-all h-full flex flex-col">
                {/* 卡片標題區 */}
                <div className="flex justify-between items-start mb-4">
                  <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-lg">
                    {project.name.charAt(0)}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium bg-slate-100 text-slate-500 px-2 py-1 rounded-full flex items-center gap-1">
                      <Layers size={12} /> {project.taskCount} Tasks
                    </span>
                    {/* 選單按鈕的佔位空間 */}
                    <div className="w-6"></div>
                  </div>
                </div>
                
                {/* 專案名稱和描述 */}
                <h3 className="text-lg font-semibold text-slate-900 mb-2 group-hover:text-indigo-600 transition-colors">
                  {project.name}
                </h3>
                <p className="text-slate-500 text-sm mb-6 line-clamp-2 flex-1">
                  {project.description}
                </p>

                {/* 進度條 */}
                <div className="mt-auto">
                  <div className="flex justify-between text-xs text-slate-500 mb-2">
                    <span>Progress</span>
                    <span>{project.progress}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-indigo-600 h-full rounded-full transition-all duration-500"
                      style={{ width: `${project.progress}%` }}
                    ></div>
                  </div>
                  
                  {/* 底部資訊：日期、擁有者、狀態 */}
                  <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between relative">
                    <div className="flex items-center gap-3">
                      {/* 建立日期 */}
                      <div className="flex items-center gap-1 text-xs text-slate-400" title={`Created: ${new Date(project.createdAt).toLocaleDateString()}`}>
                        <Calendar size={12} />
                        {new Date(project.createdAt).toLocaleDateString(undefined, {month: 'short', day: 'numeric'})}
                      </div>

                      {/* 擁有者頭像 */}
                      <div className="flex items-center gap-1">
                        {project.owner && (
                          <>
                            <div className="w-5 h-5 rounded-full bg-slate-200 overflow-hidden" title={`Owner: ${project.owner.name}`}>
                              <img src={project.owner.avatar} alt={project.owner.name} className="w-full h-full object-cover" />
                            </div>
                          </>
                        )}
                        {/* 如果是自己的專案，顯示皇冠圖示 */}
                        {project.ownerId === user?.id && <Crown size={12} className="text-amber-500" />}
                      </div>
                    </div>

                    {/* 狀態標籤 */}
                    <div className={`text-xs font-medium px-2 py-0.5 rounded-full flex items-center gap-1 ${
                      project.status === 'active' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'
                    }`}>
                      <div className={`w-1.5 h-1.5 rounded-full ${
                        project.status === 'active' ? 'bg-emerald-500' : 'bg-slate-400'
                      }`}></div>
                      {project.status === 'active' ? 'Active' : 'Archived'}
                    </div>
                  </div>
                </div>
              </div>
            </Link>

            {/* ===== 更多選項按鈕（獨立於 Link）===== */}
            <div className="absolute top-4 right-4 z-10">
              <button 
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setActiveMenuId(activeMenuId === project.id ? null : project.id);
                  setActiveStatusMenuId(null);
                }}
                className="p-1.5 bg-white hover:bg-slate-50 text-slate-400 hover:text-slate-600 rounded-lg transition-colors border border-transparent hover:border-slate-100 shadow-sm"
              >
                <MoreVertical size={16} />
              </button>

              {/* 下拉選單 */}
              {activeMenuId === project.id && (
                <div 
                  className="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-20 animate-in fade-in zoom-in-95 duration-100 origin-top-right"
                  onClick={(e) => e.stopPropagation()}
                >
                  {/* 編輯選項 */}
                  <button 
                    onClick={() => {
                      openEditModal(project);
                      setActiveMenuId(null);
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                  >
                    <Edit size={14} /> Edit Project
                  </button>
                  
                  {/* 狀態子選單 */}
                  <div className="relative">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveStatusMenuId(activeStatusMenuId === project.id ? null : project.id);
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2 justify-between group/status"
                    >
                      <span className="flex items-center gap-2"><Check size={14} /> Set Status</span>
                      <ChevronDown size={12} className="text-slate-400" />
                    </button>
                    
                    {/* 狀態選項 */}
                    {activeStatusMenuId === project.id && (
                      <div className="absolute right-full top-0 mr-1 w-32 bg-white rounded-lg shadow-lg border border-slate-100 py-1 overflow-hidden">
                        <button
                          onClick={() => handleStatusChange(project.id, 'active')}
                          className={`w-full text-left px-4 py-2 text-sm hover:bg-slate-50 flex items-center gap-2 ${project.status === 'active' ? 'text-indigo-600 font-medium' : 'text-slate-600'}`}
                        >
                          Active
                        </button>
                        <button
                          onClick={() => handleStatusChange(project.id, 'archived')}
                          className={`w-full text-left px-4 py-2 text-sm hover:bg-slate-50 flex items-center gap-2 ${project.status === 'archived' ? 'text-indigo-600 font-medium' : 'text-slate-600'}`}
                        >
                          Archived
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="h-px bg-slate-100 my-1"></div>
                  
                  {/* 刪除選項 */}
                  <button 
                    onClick={() => {
                      handleDelete(project.id);
                      setActiveMenuId(null);
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                  >
                    <Trash2 size={14} /> Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* ===== 新增專案卡片 ===== */}
        <button 
          onClick={openCreateModal}
          className="bg-slate-50 border-2 border-dashed border-slate-200 rounded-xl p-6 flex flex-col items-center justify-center text-slate-400 hover:text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50/30 transition-all min-h-[200px] group"
        >
          <div className="w-12 h-12 rounded-full bg-white shadow-sm flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <Plus size={24} />
          </div>
          <span className="font-medium">Create New Project</span>
        </button>
      </div>

      {/* ===== 建立/編輯專案彈窗 ===== */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm" onClick={() => setIsModalOpen(false)}>
          <div className="bg-white rounded-xl w-full max-w-lg shadow-2xl" onClick={e => e.stopPropagation()}>
            {/* 彈窗標題 */}
            <div className="p-6 border-b border-slate-100 flex justify-between items-center">
              <h2 className="text-lg font-bold text-slate-900">
                {editingProject ? 'Edit Project' : 'Create Project'}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            
            {/* 表單 */}
            <form onSubmit={handleSave} className="p-6 space-y-4">
              {/* 專案名稱 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Project Name</label>
                <input 
                  type="text" 
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  required
                  autoFocus
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none"
                  placeholder="e.g. Q4 Marketing Campaign"
                />
              </div>
              
              {/* 專案描述 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <textarea 
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  required
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 outline-none h-24 resize-none"
                  placeholder="Describe the goals..."
                />
              </div>

              {/* 成員選擇 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Team Members</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                  <input 
                    type="text"
                    value={memberSearchQuery}
                    onChange={(e) => {
                      setMemberSearchQuery(e.target.value);
                      setIsMemberDropdownOpen(true);
                    }}
                    onFocus={() => setIsMemberDropdownOpen(true)}
                    placeholder="Search members..."
                    className="w-full border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none mb-2"
                  />

                  {/* 成員搜尋下拉選單 */}
                  {isMemberDropdownOpen && memberSearchQuery && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setIsMemberDropdownOpen(false)}></div>
                      <div className="absolute top-full left-0 mt-1 w-full bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-20 max-h-48 overflow-y-auto">
                        {/* 推薦成員（同部門）*/}
                        {recommended.length > 0 && (
                          <div className="px-3 py-1 text-xs font-bold text-slate-400 uppercase">Suggested</div>
                        )}
                        {recommended.map(m => (
                          <button 
                            type="button" 
                            key={m.id} 
                            onClick={() => toggleMemberSelection(m.id)} 
                            className="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2"
                          >
                            <img src={m.avatar} className="w-6 h-6 rounded-full" />
                            <span className="text-sm text-slate-700">{m.name}</span>
                          </button>
                        ))}
                        
                        {/* 其他成員 */}
                        {(others.length > 0) && (
                          <div className="px-3 py-1 text-xs font-bold text-slate-400 uppercase mt-2">All Members</div>
                        )}
                        {others.map(m => (
                          <button 
                            type="button" 
                            key={m.id} 
                            onClick={() => toggleMemberSelection(m.id)} 
                            className="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2"
                          >
                            <img src={m.avatar} className="w-6 h-6 rounded-full" />
                            <span className="text-sm text-slate-700">{m.name}</span>
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>
                
                {/* 已選擇的成員標籤 */}
                <div className="flex flex-wrap gap-2 mt-2">
                  {selectedMemberIds.map(id => {
                    const member = availableMembers.find(m => m.id === id);
                    if (!member) return null;
                    return (
                      <span key={id} className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 px-2 py-1 rounded-full text-xs font-medium">
                        <img src={member.avatar} className="w-4 h-4 rounded-full" />
                        {member.name}
                        {/* 自己不能被移除 */}
                        {member.id !== user?.id && (
                          <button type="button" onClick={() => toggleMemberSelection(id)} className="hover:text-indigo-900">
                            <X size={12} />
                          </button>
                        )}
                      </span>
                    );
                  })}
                </div>
              </div>

              {/* 按鈕 */}
              <div className="pt-4 flex justify-end gap-3 border-t border-slate-100 mt-4">
                <button 
                  type="button" 
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-lg font-medium"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium shadow-sm"
                >
                  {editingProject ? 'Save Changes' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
