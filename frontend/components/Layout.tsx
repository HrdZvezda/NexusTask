/**
 * ============================================
 * Layout.tsx - 應用程式的共用佈局組件
 * ============================================
 * 
 * 【這個組件的作用】
 * 提供整個應用程式的共用外觀，包括：
 * - 側邊導航欄（Sidebar）
 * - 頂部導航欄（Header）
 * - 專案搜尋功能
 * - 通知下拉選單
 * - 使用者資訊顯示
 * 
 * 【組件結構圖】
 * ┌────────────────────────────────────────────────────┐
 * │  Header (頂部導航欄)                               │
 * │  ┌─────────────┬─────────────────────┬──────────┐ │
 * │  │ Menu Button │ Search Bar          │ 🔔 通知  │ │
 * │  └─────────────┴─────────────────────┴──────────┘ │
 * ├──────────┬─────────────────────────────────────────┤
 * │ Sidebar  │                                         │
 * │          │                                         │
 * │ Dashboard│         Page Content                    │
 * │ Projects │         (children)                      │
 * │ My Tasks │                                         │
 * │ Settings │                                         │
 * │          │                                         │
 * │──────────│                                         │
 * │ User Info│                                         │
 * │ Sign Out │                                         │
 * └──────────┴─────────────────────────────────────────┘
 * 
 * 【在哪裡被使用？】
 * 在 App.tsx 的 ProtectedRoute 組件中：
 * <Layout>{children}</Layout>
 * 
 * 所有需要登入的頁面都會被這個 Layout 包住
 * 
 * 【API 串接】
 * - notificationService.getNotifications() → 取得通知列表
 * - projectService.getProjects() → 取得專案列表（用於搜尋）
 */

// ============================================
// 導入 React 相關
// ============================================

import React, { useState, useEffect, useRef } from 'react';

// React Router 的導航相關
// Link: 建立連結，點擊後跳轉頁面
// useLocation: 取得目前的 URL 路徑
// useNavigate: 程式化導航（用程式碼跳轉頁面）
import { Link, useLocation, useNavigate } from 'react-router-dom';

// 認證相關的 Hook
import { useAuth } from '../context/AuthContext';

// API 服務
import { notificationService, projectService } from '../services/apiService';

// WebSocket Hook for real-time updates
import { useSocket } from '../hooks/useSocket';

// 類型定義
import { Notification, Project } from '../types';

// Lucide React 圖示庫
// 這是一個提供 SVG 圖示的套件，每個圖示都是一個 React 組件
import {
  LayoutDashboard,  // 儀表板圖示
  FolderKanban,     // 專案圖示
  CheckSquare,      // 任務圖示
  Settings,         // 設定圖示
  LogOut,           // 登出圖示
  Menu,             // 漢堡選單圖示
  X,                // 關閉圖示
  Bell,             // 通知鈴鐺圖示
  Search,           // 搜尋圖示
  Check,            // 勾選圖示
  Layers            // 圖層圖示
} from 'lucide-react';

// ============================================
// Layout 組件
// ============================================

/**
 * Layout 組件 - 應用程式的共用佈局
 * 
 * @param children - 被包住的頁面內容
 * 
 * 【使用方式】
 * <Layout>
 *   <Dashboard />  ← 這就是 children
 * </Layout>
 */
export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // ============================================
  // 從 Context 取得認證資訊
  // ============================================

  // useAuth() 是我們自訂的 Hook，從 AuthContext 取得使用者資訊和登出函數
  const { user, logout } = useAuth();

  // ============================================
  // 狀態管理
  // ============================================

  // 側邊欄開關狀態（手機版才需要，桌面版固定顯示）
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // 通知下拉選單開關狀態
  const [isNotifOpen, setIsNotifOpen] = useState(false);

  // 通知列表
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // 通知按鈕的 ref，用來偵測點擊外部關閉下拉選單
  const notifRef = useRef<HTMLDivElement>(null);

  // React Router Hooks
  const location = useLocation();    // 取得目前的 URL
  const navigate = useNavigate();    // 用來跳轉頁面

  // ============================================
  // 搜尋功能狀態
  // ============================================

  // 搜尋關鍵字
  const [searchQuery, setSearchQuery] = useState('');

  // 搜尋框是否獲得焦點（顯示下拉選單）
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  // 搜尋用的專案列表
  const [searchProjects, setSearchProjects] = useState<Project[]>([]);

  // 搜尋區塊的 ref
  const searchRef = useRef<HTMLDivElement>(null);

  // ============================================
  // 副作用：載入資料
  // ============================================

  /**
   * 組件載入時，取得通知和專案列表
   * 
   * 【API 呼叫】
   * - notificationService.getNotifications()
   *   → GET /api/notifications
   *   → 後端 notifications.py get_notifications()
   * 
   * - projectService.getProjects()
   *   → GET /projects
   *   → 後端 projects.py get_my_projects()
   */
  useEffect(() => {
    // 取得通知列表
    notificationService.getNotifications().then(setNotifications);
    // 取得專案列表（用於搜尋功能）
    projectService.getProjects().then(setSearchProjects);
  }, []);  // 空陣列表示只在組件載入時執行一次

  // ============================================
  // WebSocket 即時通知
  // ============================================

  /**
   * 使用 WebSocket 監聽即時通知
   * 當有新通知時，自動重新取得通知列表
   */
  const { isConnected } = useSocket({
    enabled: !!user,
    onConnect: () => {
      console.log('Socket connected - notifications will update in real-time');
    },
  });

  // 當 socket 連接後，設定定期刷新通知（作為 fallback）
  useEffect(() => {
    if (!isConnected) return;

    // Socket 連接成功時，重新取得通知
    notificationService.getNotifications().then(setNotifications);

    // 設定每 30 秒輪詢一次作為 fallback（如果 WebSocket 事件沒觸發）
    const interval = setInterval(() => {
      notificationService.getNotifications().then(setNotifications);
    }, 30000);

    return () => clearInterval(interval);
  }, [isConnected]);

  // ============================================
  // 副作用：點擊外部關閉下拉選單
  // ============================================

  /**
   * 偵測點擊事件，如果點擊在下拉選單外面，就關閉它
   * 這是常見的 UX 模式
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // 如果點擊的位置不在通知區塊內，關閉通知下拉選單
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setIsNotifOpen(false);
      }
      // 如果點擊的位置不在搜尋區塊內，關閉搜尋下拉選單
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsSearchFocused(false);
      }
    };

    // 監聽 mousedown 事件
    document.addEventListener('mousedown', handleClickOutside);

    // 清理函數：組件卸載時移除監聽器
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ============================================
  // 導航項目設定
  // ============================================

  /**
   * 側邊欄的導航項目列表
   * 每個項目包含：
   * - label: 顯示的文字
   * - path: 對應的 URL 路徑
   * - icon: 顯示的圖示組件
   */
  const navItems = [
    { label: 'Projects', path: '/projects', icon: FolderKanban },
    { label: 'My Tasks', path: '/tasks/my', icon: CheckSquare },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  /**
   * 判斷某個路徑是否是目前的頁面
   * 用來高亮顯示目前所在的導航項目
   */
  const isActive = (path: string) => location.pathname === path;

  // ============================================
  // 通知相關函數
  // ============================================

  /**
   * 標記所有通知為已讀
   * 
   * 呼叫後端 API 持久化已讀狀態
   */
  const markAllRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  /**
   * 點擊通知：若有附帶專案/任務資訊，就跳轉到對應頁面
   */
  const handleNotificationClick = (notification: Notification) => {
    // 先把這則通知標記為已讀（前端狀態）
    setNotifications(prev => prev.map(n => n.id === notification.id ? { ...n, read: true } : n));

    if (notification.projectId) {
      navigate(`/projects/${notification.projectId}`);
      setIsNotifOpen(false);
    }
  };

  // 計算未讀通知數量
  const unreadCount = notifications.filter(n => !n.read).length;

  // ============================================
  // 搜尋相關函數
  // ============================================

  /**
   * 過濾專案列表
   * 
   * 如果有輸入搜尋關鍵字，就過濾出名稱包含關鍵字的專案
   * 如果沒有輸入，就顯示前 3 個專案（推薦）
   */
  const filteredProjects = searchQuery.trim()
    ? searchProjects.filter(p => p.name.toLowerCase().includes(searchQuery.toLowerCase()))
    : searchProjects.slice(0, 3);

  /**
   * 處理專案點擊事件
   * 跳轉到專案詳情頁面，並關閉搜尋下拉選單
   */
  const handleProjectClick = (projectId: string) => {
    navigate(`/projects/${projectId}`);
    setIsSearchFocused(false);
    setSearchQuery('');
  };

  // ============================================
  // 渲染 UI
  // ============================================

  return (
    // 最外層容器：全螢幕高度，使用 flexbox 水平排列
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden">

      {/* ========================================
          手機版：側邊欄的半透明背景遮罩
          點擊遮罩會關閉側邊欄
          lg:hidden 表示在大螢幕上隱藏
      ======================================== */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* ========================================
          側邊欄（Sidebar）
          
          手機版：預設隱藏，點擊漢堡選單後滑入
          桌面版：固定顯示在左側
      ======================================== */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-slate-200 transform transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        {/* Logo 區塊 - 點擊導向 Dashboard */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-slate-100">
          <Link
            to="/"
            onClick={() => setIsSidebarOpen(false)}
            className="flex items-center gap-2 font-bold text-xl text-indigo-600 hover:text-indigo-700 transition-colors"
          >
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white">N</div>
            NexusTeam
          </Link>
          {/* 手機版的關閉按鈕 */}
          <button onClick={() => setIsSidebarOpen(false)} className="lg:hidden text-slate-500">
            <X size={20} />
          </button>
        </div>

        {/* 導航連結 */}
        <nav className="p-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setIsSidebarOpen(false)}  // 點擊後關閉側邊欄（手機版）
              className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${isActive(item.path)
                ? 'bg-indigo-50 text-indigo-600'  // 目前頁面的樣式
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'  // 其他頁面的樣式
                }`}
            >
              <item.icon size={20} />
              {item.label}
            </Link>
          ))}
        </nav>

        {/* 使用者資訊和登出按鈕（固定在底部）*/}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-100">
          <div className="flex items-center gap-3 mb-4 px-2">
            {/* 使用者頭像 */}
            <img
              src={user?.avatar || "https://via.placeholder.com/40"}
              alt="User"
              className="w-9 h-9 rounded-full object-cover border border-slate-200"
            />
            <div className="flex-1 min-w-0">
              {/* truncate 會在文字太長時顯示 ... */}
              <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>
          {/* 登出按鈕 */}
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut size={18} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* ========================================
          主要內容區域
          包含頂部導航欄和頁面內容
      ======================================== */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* 頂部導航欄（Header）*/}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 lg:px-8">

          {/* 手機版的漢堡選單按鈕 */}
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="lg:hidden p-2 text-slate-500 hover:bg-slate-100 rounded-lg"
          >
            <Menu size={20} />
          </button>

          {/* 搜尋區塊 */}
          <div className="flex-1 max-w-xl ml-4 lg:ml-0 relative" ref={searchRef}>
            <div className="relative group">
              {/* 搜尋圖示 */}
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500" size={18} />
              {/* 搜尋輸入框 */}
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchFocused(true);
                }}
                onFocus={() => setIsSearchFocused(true)}
                placeholder="Search projects..."
                className="w-full bg-slate-100 text-sm border-none rounded-full py-2 pl-10 pr-4 focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
              />
            </div>

            {/* 搜尋結果下拉選單 */}
            {isSearchFocused && (
              <div className="absolute top-full left-0 mt-2 w-full bg-white rounded-xl shadow-xl border border-slate-100 overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-100">
                <div className="p-2">
                  <h3 className="text-xs font-semibold text-slate-400 px-3 py-2 uppercase tracking-wider">
                    {searchQuery ? 'Projects' : 'Recommended'}
                  </h3>
                  {filteredProjects.length > 0 ? (
                    filteredProjects.map(p => (
                      <button
                        key={p.id}
                        onClick={() => handleProjectClick(p.id)}
                        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-slate-50 rounded-lg transition-colors text-left"
                      >
                        {/* 專案名稱首字母 */}
                        <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-sm">
                          {p.name.charAt(0)}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-900">{p.name}</p>
                          <p className="text-xs text-slate-500 truncate max-w-[300px]">{p.description}</p>
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="px-3 py-4 text-sm text-slate-500 text-center">
                      No projects found for "{searchQuery}"
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* 通知區塊 */}
          <div className="flex items-center gap-4 ml-4 relative" ref={notifRef}>
            {/* 通知鈴鐺按鈕 */}
            <button
              onClick={() => setIsNotifOpen(!isNotifOpen)}
              className={`relative p-2 rounded-full transition-colors ${isNotifOpen ? 'bg-indigo-50 text-indigo-600' : 'text-slate-500 hover:bg-slate-100'}`}
            >
              <Bell size={20} />
              {/* 未讀通知的紅點 */}
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
              )}
            </button>

            {/* 通知下拉選單 */}
            {isNotifOpen && (
              <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-100 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100 origin-top-right">
                {/* 標題列 */}
                <div className="p-3 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                  <h3 className="text-sm font-semibold text-slate-800">Notifications</h3>
                  {unreadCount > 0 && (
                    <button onClick={markAllRead} className="text-xs text-indigo-600 hover:text-indigo-700 font-medium">
                      Mark all read
                    </button>
                  )}
                </div>
                {/* 通知列表 */}
                <div className="max-h-[300px] overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="p-8 text-center text-slate-400 text-sm">No new notifications</div>
                  ) : (
                    notifications.map(n => {
                      const isClickable = Boolean(n.projectId);
                      return (
                        <button
                          key={n.id}
                          onClick={() => isClickable && handleNotificationClick(n)}
                          className={`w-full text-left p-4 border-b border-slate-50 last:border-0 flex gap-3 transition-colors ${!n.read ? 'bg-indigo-50/30' : ''
                            } ${isClickable ? 'hover:bg-slate-50 cursor-pointer' : 'cursor-default'}`}
                        >
                          {/* 通知類型指示點 */}
                          <div className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${n.type === 'success' ? 'bg-emerald-500' :
                            n.type === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                            }`}></div>
                          <div className="flex-1">
                            <p className={`text-sm text-slate-800 ${!n.read ? 'font-semibold' : ''}`}>{n.message}</p>
                            <p className="text-xs text-slate-400 mt-1">{n.createdAt}</p>
                            {n.projectName && (
                              <p className="text-xs text-indigo-500 mt-1">
                                {isClickable ? 'View project: ' : ''}{n.projectName}
                              </p>
                            )}
                          </div>
                        </button>
                      );
                    })
                  )}
                </div>
                {/* 底部連結 */}
                <div className="p-2 border-t border-slate-100 text-center">
                  <Link
                    to="/notifications"
                    onClick={() => setIsNotifOpen(false)}
                    className="text-xs text-slate-500 hover:text-indigo-600 font-medium"
                  >
                    View All History
                  </Link>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* 頁面內容區域 */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          <div className="max-w-6xl mx-auto">
            {/* children 是從父組件傳入的頁面內容 */}
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
