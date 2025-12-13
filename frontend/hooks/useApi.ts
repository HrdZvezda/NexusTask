/**
 * ============================================
 * useApi.ts - React Query Hooks
 * ============================================
 * 
 * 使用 TanStack Query (React Query) 來管理伺服器狀態
 * 
 * 【優點】
 * - 自動快取資料
 * - 自動重新取得資料（失去焦點後回來、網路重連等）
 * - 樂觀更新支援
 * - Loading/Error 狀態管理
 * - 減少重複請求
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { 
  projectService, 
  taskService, 
  authService, 
  notificationService,
  memberService 
} from '../services/apiService';
import { Project, Task, User, Notification, TaskStatus } from '../types';

// ============================================
// Query Keys
// ============================================

/**
 * 統一管理所有 Query 的 key
 * 方便快取失效和重新取得
 */
export const queryKeys = {
  // 專案相關
  projects: ['projects'] as const,
  project: (id: string) => ['projects', id] as const,
  projectStats: (id: string) => ['projects', id, 'stats'] as const,
  projectMembers: (id: string) => ['projects', id, 'members'] as const,
  
  // 任務相關
  tasks: ['tasks'] as const,
  projectTasks: (projectId: string) => ['tasks', 'project', projectId] as const,
  myTasks: ['tasks', 'my'] as const,
  task: (id: string) => ['tasks', id] as const,
  taskComments: (taskId: string) => ['tasks', taskId, 'comments'] as const,
  
  // 使用者相關
  currentUser: ['user', 'current'] as const,
  members: ['members'] as const,
  
  // 通知相關
  notifications: ['notifications'] as const,
};

// ============================================
// 專案 Hooks
// ============================================

/**
 * 取得專案列表
 */
export function useProjects() {
  return useQuery({
    queryKey: queryKeys.projects,
    queryFn: () => projectService.getProjectsWithDetails(),
    staleTime: 5 * 60 * 1000, // 5 分鐘內視為新鮮資料
  });
}

/**
 * 取得專案統計
 */
export function useProjectStats(projectId: string) {
  return useQuery({
    queryKey: queryKeys.projectStats(projectId),
    queryFn: () => projectService.getProjectStats(projectId),
    enabled: !!projectId,
    staleTime: 10 * 60 * 1000, // 10 分鐘
  });
}

/**
 * 取得專案成員
 */
export function useProjectMembers(projectId: string) {
  return useQuery({
    queryKey: queryKeys.projectMembers(projectId),
    queryFn: () => projectService.getProjectMembers(projectId),
    enabled: !!projectId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 建立專案
 */
export function useCreateProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (project: Partial<Project>) => projectService.createProject(project),
    onSuccess: () => {
      // 使專案列表快取失效，觸發重新取得
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    },
  });
}

/**
 * 更新專案狀態
 */
export function useUpdateProjectStatus() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ projectId, status }: { projectId: string; status: 'active' | 'archived' }) =>
      projectService.updateProjectStatus(projectId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    },
  });
}

/**
 * 刪除專案
 */
export function useDeleteProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (projectId: string) => projectService.deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    },
  });
}

/**
 * 新增專案成員
 */
export function useAddProjectMember(projectId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (email: string) => projectService.addMember(projectId, email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projectMembers(projectId) });
    },
  });
}

/**
 * 移除專案成員
 */
export function useRemoveProjectMember(projectId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (userId: string) => projectService.removeMember(projectId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projectMembers(projectId) });
    },
  });
}

// ============================================
// 任務 Hooks
// ============================================

/**
 * 取得專案任務
 */
export function useProjectTasks(projectId: string) {
  return useQuery({
    queryKey: queryKeys.projectTasks(projectId),
    queryFn: () => taskService.getTasksByProject(projectId),
    enabled: !!projectId,
    staleTime: 2 * 60 * 1000, // 2 分鐘
  });
}

/**
 * 取得我的任務
 */
export function useMyTasks() {
  return useQuery({
    queryKey: queryKeys.myTasks,
    queryFn: () => taskService.getMyTasks(),
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * 取得所有任務
 */
export function useAllTasks() {
  return useQuery({
    queryKey: queryKeys.tasks,
    queryFn: () => taskService.getAllTasks(),
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * 建立任務
 */
export function useCreateTask() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (task: Partial<Task>) => taskService.createTask(task),
    onSuccess: (_, variables) => {
      // 使相關快取失效
      if (variables.projectId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.projectTasks(variables.projectId) });
      }
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks });
      queryClient.invalidateQueries({ queryKey: queryKeys.myTasks });
    },
  });
}

/**
 * 更新任務
 */
export function useUpdateTask() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ taskId, updates }: { taskId: string; updates: Partial<Task> }) =>
      taskService.updateTask(taskId, updates),
    onMutate: async ({ taskId, updates }) => {
      // 樂觀更新
      await queryClient.cancelQueries({ queryKey: queryKeys.tasks });
      
      const previousTasks = queryClient.getQueryData(queryKeys.tasks);
      
      queryClient.setQueryData(queryKeys.tasks, (old: Task[] | undefined) => {
        if (!old) return old;
        return old.map(task => 
          task.id === taskId ? { ...task, ...updates } : task
        );
      });
      
      return { previousTasks };
    },
    onError: (err, variables, context) => {
      // 回滾
      if (context?.previousTasks) {
        queryClient.setQueryData(queryKeys.tasks, context.previousTasks);
      }
    },
    onSettled: (_, __, variables) => {
      // 重新取得資料
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks });
      queryClient.invalidateQueries({ queryKey: queryKeys.myTasks });
    },
  });
}

/**
 * 更新任務狀態（拖拉看板用）
 */
export function useUpdateTaskStatus() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: TaskStatus }) =>
      taskService.updateTaskStatus(taskId, status),
    onMutate: async ({ taskId, status }) => {
      // 樂觀更新
      await queryClient.cancelQueries({ queryKey: queryKeys.tasks });
      
      const previousData = {
        tasks: queryClient.getQueryData(queryKeys.tasks),
        myTasks: queryClient.getQueryData(queryKeys.myTasks),
      };
      
      // 更新所有包含這個任務的 query
      const updateTasks = (old: Task[] | undefined) => {
        if (!old) return old;
        return old.map(task => 
          task.id === taskId ? { ...task, status } : task
        );
      };
      
      queryClient.setQueryData(queryKeys.tasks, updateTasks);
      queryClient.setQueryData(queryKeys.myTasks, updateTasks);
      
      return previousData;
    },
    onError: (err, variables, context) => {
      // 回滾
      if (context) {
        queryClient.setQueryData(queryKeys.tasks, context.tasks);
        queryClient.setQueryData(queryKeys.myTasks, context.myTasks);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks });
      queryClient.invalidateQueries({ queryKey: queryKeys.myTasks });
    },
  });
}

/**
 * 刪除任務
 */
export function useDeleteTask() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (taskId: string) => taskService.deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks });
      queryClient.invalidateQueries({ queryKey: queryKeys.myTasks });
    },
  });
}

/**
 * 取得任務評論
 */
export function useTaskComments(taskId: string) {
  return useQuery({
    queryKey: queryKeys.taskComments(taskId),
    queryFn: () => taskService.getComments(taskId),
    enabled: !!taskId,
    staleTime: 1 * 60 * 1000, // 1 分鐘
  });
}

/**
 * 新增評論
 */
export function useAddComment(taskId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ content, userId, userName }: { content: string; userId: string; userName: string }) =>
      taskService.addComment(taskId, content, userId, userName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.taskComments(taskId) });
    },
  });
}

// ============================================
// 使用者 Hooks
// ============================================

/**
 * 取得目前登入的使用者
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.currentUser,
    queryFn: () => authService.getCurrentUser(),
    staleTime: 10 * 60 * 1000, // 10 分鐘
    retry: false, // 失敗不重試（可能是未登入）
  });
}

/**
 * 取得所有成員
 */
export function useMembers() {
  return useQuery({
    queryKey: queryKeys.members,
    queryFn: () => memberService.getMembers(),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 更新個人資料
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: Partial<User>) => authService.updateProfile(data),
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(queryKeys.currentUser, updatedUser);
    },
  });
}

/**
 * 修改密碼
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: ({ currentPassword, newPassword }: { currentPassword: string; newPassword: string }) =>
      authService.changePassword(currentPassword, newPassword),
  });
}

// ============================================
// 通知 Hooks
// ============================================

/**
 * 取得通知列表
 */
export function useNotifications() {
  return useQuery({
    queryKey: queryKeys.notifications,
    queryFn: () => notificationService.getNotifications(),
    staleTime: 1 * 60 * 1000, // 1 分鐘
    refetchInterval: 30 * 1000, // 每 30 秒自動重新取得
  });
}

/**
 * 標記通知為已讀
 */
export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (notificationId: string) => notificationService.markAsRead(notificationId),
    onMutate: async (notificationId) => {
      // 樂觀更新
      await queryClient.cancelQueries({ queryKey: queryKeys.notifications });
      
      const previousNotifications = queryClient.getQueryData(queryKeys.notifications);
      
      queryClient.setQueryData(queryKeys.notifications, (old: Notification[] | undefined) => {
        if (!old) return old;
        return old.map(n => 
          n.id === notificationId ? { ...n, read: true } : n
        );
      });
      
      return { previousNotifications };
    },
    onError: (err, variables, context) => {
      if (context?.previousNotifications) {
        queryClient.setQueryData(queryKeys.notifications, context.previousNotifications);
      }
    },
  });
}

/**
 * 標記所有通知為已讀
 */
export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => notificationService.markAllAsRead(),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: queryKeys.notifications });
      
      const previousNotifications = queryClient.getQueryData(queryKeys.notifications);
      
      queryClient.setQueryData(queryKeys.notifications, (old: Notification[] | undefined) => {
        if (!old) return old;
        return old.map(n => ({ ...n, read: true }));
      });
      
      return { previousNotifications };
    },
    onError: (err, variables, context) => {
      if (context?.previousNotifications) {
        queryClient.setQueryData(queryKeys.notifications, context.previousNotifications);
      }
    },
  });
}

// ============================================
// 工具 Hooks
// ============================================

/**
 * 使所有快取失效（登出時使用）
 */
export function useInvalidateAll() {
  const queryClient = useQueryClient();
  
  return () => {
    queryClient.clear();
  };
}

/**
 * 預先載入資料（進入頁面前）
 */
export function usePrefetchProjects() {
  const queryClient = useQueryClient();
  
  return () => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.projects,
      queryFn: () => projectService.getProjectsWithDetails(),
    });
  };
}

