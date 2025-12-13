/**
 * ============================================
 * Dashboard.tsx - 儀表板頁面
 * ============================================
 * 
 * 【這個頁面的作用】
 * 應用程式的首頁，顯示整體概況，包括：
 * - 關鍵指標（活躍專案數、本週完成率、通知數）
 * - 專案進度圖表（長條圖）
 * - 任務分佈圖表（圓餅圖）
 * - 最近活動列表
 * 
 * 【頁面結構圖】
 * ┌────────────────────────────────────────────────────┐
 * │ Dashboard Overview                     2024/01/15 │
 * ├────────────────────────────────────────────────────┤
 * │ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
 * │ │ Active   │ │ Weekly   │ │ Notifica-│            │
 * │ │ Projects │ │ Complete │ │  tions   │  ← 指標卡  │
 * │ │   5      │ │   75%    │ │    3     │            │
 * │ └──────────┘ └──────────┘ └──────────┘            │
 * ├────────────────────────────────────────────────────┤
 * │ ┌────────────────────┐ ┌────────────────────┐     │
 * │ │                    │ │                    │     │
 * │ │  專案進度長條圖    │ │  任務分佈圓餅圖    │     │
 * │ │                    │ │                    │     │
 * │ └────────────────────┘ └────────────────────┘     │
 * ├────────────────────────────────────────────────────┤
 * │ Recent Activity                                   │
 * │ • Task completed...                               │
 * │ • New comment...                                  │
 * └────────────────────────────────────────────────────┘
 * 
 * 【路由】
 * 路徑: / (首頁)
 * 
 * 【API 串接】
 * - projectService.getProjects() → 取得專案列表
 * - taskService.getAllTasks() → 取得所有任務
 * - notificationService.getNotifications() → 取得通知
 */

// ============================================
// 導入 React 和相關模組
// ============================================

import React, { useEffect, useState } from 'react';

// API 服務
import { projectService, notificationService, taskService } from '../services/apiService';

// 類型定義
import { Project, TaskStatus, Task } from '../types';

// 通知 Context
import { useNotifications } from '../context/NotificationContext';

// Lucide 圖示
import { ArrowRight, Target } from 'lucide-react';

// React Router 的 Link 組件
import { Link } from 'react-router-dom';

// ============================================
// Dashboard 組件
// ============================================

export const Dashboard: React.FC = () => {
  // ============================================
  // 狀態管理
  // ============================================

  // 專案列表
  const [projects, setProjects] = useState<Project[]>([]);

  // 任務列表
  const [tasks, setTasks] = useState<Task[]>([]);

  // 通知列表（從共享 Context 取得）
  const { notifications } = useNotifications();

  // 本週完成率（百分比）
  const [weeklyCompletion, setWeeklyCompletion] = useState(0);

  // 載入狀態
  const [isLoading, setIsLoading] = useState(true);

  // ============================================
  // 副作用：載入資料
  // ============================================

  /**
   * 組件載入時，從後端取得所有需要的資料
   * 
   * 【API 呼叫】
   * 1. projectService.getProjects()
   *    → GET /projects
   *    → 後端 projects.py get_my_projects()
   * 
   * 2. taskService.getAllTasks()
   *    → GET /tasks/all
   *    → 後端 tasks.py get_all_tasks()
   * 
   * 3. notificationService.getNotifications()
   *    → GET /api/notifications
   *    → 後端 notifications.py get_notifications()
   * 
   * 【效能優化】
   * 使用 Promise.all() 同時發送所有請求，
   * 而不是一個一個等待，這樣載入速度更快
   */
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [fetchedProjects, fetchedTasks] = await Promise.all([
          projectService.getProjects(),
          taskService.getAllTasks()
        ]);

        // 設定狀態
        setProjects(fetchedProjects);
        setTasks(fetchedTasks);
        // 通知從 NotificationContext 自動取得，不需要在此設定

        // 計算本週統計
        calculateWeeklyStats(fetchedTasks);
      } catch (error) {
        console.error("Dashboard fetch error:", error);
      } finally {
        // 不管成功或失敗，都結束載入狀態
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);  // 空陣列表示只在組件載入時執行一次

  // ============================================
  // 計算本週統計
  // ============================================

  /**
   * 計算本週任務完成率
   * 
   * @param allTasks - 所有任務列表
   * 
   * 【邏輯說明】
   * 1. 找出本週（週日到週六）到期的任務
   * 2. 計算其中已完成的數量
   * 3. 算出完成率百分比
   */
  const calculateWeeklyStats = (allTasks: Task[]) => {
    // 取得今天的日期（不含時間）
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // 計算本週的開始（週日）
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - today.getDay());

    // 計算本週的結束（週六）
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);

    // 篩選出本週到期的任務
    const tasksDueThisWeek = allTasks.filter(t => {
      if (!t.dueDate) return false;  // 沒有設定截止日期的不算
      const d = new Date(t.dueDate);
      const dTime = d.getTime();
      return dTime >= startOfWeek.getTime() && dTime <= endOfWeek.getTime();
    });

    // 計算已完成的數量
    const completedCount = tasksDueThisWeek.filter(t => t.status === TaskStatus.DONE).length;

    // 計算完成率
    setWeeklyCompletion(
      tasksDueThisWeek.length > 0
        ? Math.round((completedCount / tasksDueThisWeek.length) * 100)
        : 0
    );
  };

  // ============================================
  // 計算衍生資料
  // ============================================

  const findProjectById = (projectId: string) =>
    projects.find(project => project.id === projectId);

  // 即將到期的任務（依截止日期排序，僅顯示前 5 筆）
  const upcomingTasks = [...tasks]
    .filter(task => task.dueDate && task.status !== TaskStatus.DONE)
    .sort((a, b) => new Date(a.dueDate || '').getTime() - new Date(b.dueDate || '').getTime())
    .slice(0, 5);

  // 每個專案的統計資訊
  const projectInsights = projects.map(project => {
    const projectTasks = tasks.filter(task => task.projectId === project.id);
    const totalTasks = projectTasks.length;
    const completedTasks = projectTasks.filter(task => task.status === TaskStatus.DONE).length;
    const inProgressTasks = projectTasks.filter(task => task.status === TaskStatus.IN_PROGRESS).length;
    const overdueTasks = projectTasks.filter(task => {
      if (!task.dueDate) return false;
      const due = new Date(task.dueDate);
      return due.getTime() < Date.now() && task.status !== TaskStatus.DONE;
    }).length;
    const nextDeadlineTask = [...projectTasks]
      .filter(task => task.dueDate && task.status !== TaskStatus.DONE)
      .sort((a, b) => new Date(a.dueDate || '').getTime() - new Date(b.dueDate || '').getTime())[0];

    const computedProgress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : project.progress;

    return {
      project,
      totalTasks,
      completedTasks,
      inProgressTasks,
      overdueTasks,
      progress: computedProgress,
      nextDeadline: nextDeadlineTask?.dueDate,
    };
  });

  // Top N (4) 專案，依進度排序
  const topProjects = [...projectInsights]
    .sort((a, b) => b.progress - a.progress)
    .slice(0, 4);

  const formatDate = (dateString?: string) => {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  };

  // ============================================
  // 載入中狀態
  // ============================================

  if (isLoading) {
    return <div className="p-8 text-center text-slate-500">Loading dashboard data...</div>;
  }

  // ============================================
  // 渲染 UI
  // ============================================

  return (
    <div className="space-y-6">
      {/* 頁面標題 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard Overview</h1>
        <span className="text-sm text-slate-500">{new Date().toLocaleDateString()}</span>
      </div>

      {/* ========================================
          洞察區塊
          左邊：即將到期的任務
          右邊：Top N 專案進度卡
      ======================================== */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* 即將到期的任務 */}
        <div className="bg-white p-8 rounded-2xl shadow-md border border-slate-100 min-h-[360px]">
          <h2 className="text-lg font-semibold mb-4 text-slate-800">Upcoming Deadlines</h2>
          <div className="space-y-3">
            {upcomingTasks.length === 0 && (
              <p className="text-sm text-slate-500">No upcoming deadlines 🎉</p>
            )}
            {upcomingTasks.map(task => {
              const project = findProjectById(task.projectId);
              return (
                <Link
                  key={task.id}
                  to={`/projects/${task.projectId}?task=${task.id}`}
                  className="p-4 border border-slate-100 rounded-xl flex justify-between items-center hover:border-indigo-100 hover:bg-indigo-50/30 transition-colors"
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{task.title}</p>
                    <p className="text-xs text-slate-500">
                      {project?.name || 'Unknown project'} • Due {formatDate(task.dueDate)}
                    </p>
                  </div>
                  <span className={`text-xs px-3 py-1 rounded-full font-medium ${task.priority === 'HIGH'
                    ? 'bg-rose-100 text-rose-600'
                    : task.priority === 'MEDIUM'
                      ? 'bg-amber-100 text-amber-600'
                      : 'bg-slate-100 text-slate-600'
                    }`}>
                    {task.priority}
                  </span>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Top Projects */}
        <div className="bg-white p-8 rounded-2xl shadow-md border border-slate-100 min-h-[360px]">
          <h2 className="text-lg font-semibold mb-4 text-slate-800 flex items-center gap-2">
            <Target size={18} className="text-indigo-600" />
            Top Performing Projects
          </h2>
          {topProjects.length === 0 && (
            <p className="text-sm text-slate-500">No project data available.</p>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {topProjects.map(({ project, totalTasks, completedTasks, inProgressTasks, overdueTasks, progress, nextDeadline }) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="border border-slate-100 rounded-xl p-4 shadow-sm hover:shadow-lg transition-shadow"
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 truncate">{project.name}</p>
                    <p className="text-xs text-slate-500">Owner: {project.ownerId}</p>
                  </div>
                  <div className="flex items-center gap-1 text-indigo-600 text-sm font-semibold">
                    <Target size={16} />
                    {progress}%
                  </div>
                </div>
                <div className="flex flex-wrap gap-3 text-xs text-slate-500 mb-3">
                  <span>Tasks: {completedTasks}/{totalTasks}</span>
                  <span>In Progress: {inProgressTasks}</span>
                  <span className={overdueTasks > 0 ? 'text-rose-500 font-semibold' : ''}>
                    Overdue: {overdueTasks}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  Next deadline: {formatDate(nextDeadline)}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* ========================================
          最近活動區塊
          顯示最近的通知（只顯示前 5 筆）
      ======================================== */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-slate-800">Recent Activity</h2>
          <Link
            to="/notifications"
            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
          >
            View All <ArrowRight size={16} />
          </Link>
        </div>
        <div className="divide-y divide-slate-50">
          {notifications.slice(0, 5).map(n => {
            // 建立連結路徑：如果有 projectId 則連結到專案頁面
            const linkPath = n.projectId
              ? n.taskId
                ? `/projects/${n.projectId}?task=${n.taskId}`  // 有任務 ID 則連到任務詳情
                : `/projects/${n.projectId}`                   // 否則只連到專案頁面
              : null;

            // 通知項目的內容
            const notificationContent = (
              <>
                {/* 狀態指示點 */}
                <div className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${n.type === 'success' ? 'bg-emerald-500' : 'bg-blue-500'
                  }`}></div>
                <div className="flex-1 min-w-0">
                  <p className="text-slate-800 text-sm">{n.message}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <p className="text-slate-400 text-xs">{n.createdAt}</p>
                    {n.projectName && (
                      <span className="text-xs text-indigo-500 bg-indigo-50 px-2 py-0.5 rounded-full">
                        {n.projectName}
                      </span>
                    )}
                  </div>
                </div>
                {linkPath && (
                  <ArrowRight size={16} className="text-slate-300 flex-shrink-0" />
                )}
              </>
            );

            // 如果有連結路徑則使用 Link，否則使用 div
            return linkPath ? (
              <Link
                key={n.id}
                to={linkPath}
                className="p-4 hover:bg-indigo-50/50 transition-colors flex items-start gap-4 cursor-pointer"
              >
                {notificationContent}
              </Link>
            ) : (
              <div
                key={n.id}
                className="p-4 hover:bg-slate-50 transition-colors flex items-start gap-4"
              >
                {notificationContent}
              </div>
            );
          })}
          {notifications.length === 0 && (
            <div className="p-8 text-center text-slate-500">No recent activity</div>
          )}
        </div>
      </div>
    </div>
  );
};
