/**
 * ============================================
 * useSocket.ts - WebSocket Hook
 * ============================================
 * 
 * 使用 Socket.IO 實現即時通訊功能
 * 
 * 【功能】
 * - 即時接收通知
 * - 任務狀態即時同步
 * - 專案活動即時更新
 * - 線上使用者狀態
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from './useApi';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8888';

// ============================================
// Socket 連接管理
// ============================================

let socket: Socket | null = null;

/**
 * 取得或建立 Socket 連接
 */
function getSocket(token: string): Socket {
  if (!socket) {
    socket = io(API_BASE_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
      autoConnect: false,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });
  }
  return socket;
}

/**
 * 斷開 Socket 連接
 */
export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

// ============================================
// Socket Hook
// ============================================

interface UseSocketOptions {
  enabled?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

/**
 * WebSocket 連接 Hook
 * 
 * 使用方式：
 * ```tsx
 * const { isConnected, emit, on } = useSocket({
 *   enabled: !!user,
 *   onConnect: () => console.log('Connected!'),
 * });
 * ```
 */
export function useSocket(options: UseSocketOptions = {}) {
  const { enabled = true, onConnect, onDisconnect, onError } = options;
  const [isConnected, setIsConnected] = useState(false);
  const queryClient = useQueryClient();
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const token = localStorage.getItem('nexus_access_token');
    if (!token) return;

    const socket = getSocket(token);
    socketRef.current = socket;

    // 連接事件
    socket.on('connect', () => {
      setIsConnected(true);
      onConnect?.();
      console.log('Socket connected');
    });

    // 斷開事件
    socket.on('disconnect', (reason) => {
      setIsConnected(false);
      onDisconnect?.();
      console.log('Socket disconnected:', reason);
    });

    // 錯誤事件
    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
      onError?.(error);
    });

    // 接收新通知
    socket.on('notification', (data) => {
      console.log('New notification:', data);
      // 使通知快取失效，觸發重新取得
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications });
    });

    // 任務建立
    socket.on('task_created', (data) => {
      console.log('Task created:', data);
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks });
    });

    // 任務更新
    socket.on('task_updated', (data) => {
      console.log('Task updated:', data);
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks });
      queryClient.invalidateQueries({ queryKey: queryKeys.myTasks });
    });

    // 任務刪除
    socket.on('task_deleted', (data) => {
      console.log('Task deleted:', data);
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks });
      queryClient.invalidateQueries({ queryKey: queryKeys.myTasks });
    });

    // 成員加入
    socket.on('member_added', (data) => {
      console.log('Member added:', data);
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    });

    // 成員移除
    socket.on('member_removed', (data) => {
      console.log('Member removed:', data);
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    });

    // 評論新增
    socket.on('comment_added', (data) => {
      console.log('Comment added:', data);
      if (data.task_id) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.taskComments(data.task_id) 
        });
      }
    });

    // 連接
    socket.connect();

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('connect_error');
      socket.off('notification');
      socket.off('task_created');
      socket.off('task_updated');
      socket.off('task_deleted');
      socket.off('member_added');
      socket.off('member_removed');
      socket.off('comment_added');
    };
  }, [enabled, queryClient, onConnect, onDisconnect, onError]);

  /**
   * 發送事件
   */
  const emit = useCallback((event: string, data?: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    }
  }, []);

  /**
   * 監聽事件
   */
  const on = useCallback((event: string, callback: (data: any) => void) => {
    socketRef.current?.on(event, callback);
    return () => {
      socketRef.current?.off(event, callback);
    };
  }, []);

  /**
   * 加入專案 Room
   */
  const joinProject = useCallback((projectId: string) => {
    emit('join_project', { project_id: projectId });
  }, [emit]);

  /**
   * 離開專案 Room
   */
  const leaveProject = useCallback((projectId: string) => {
    emit('leave_project', { project_id: projectId });
  }, [emit]);

  return {
    isConnected,
    emit,
    on,
    joinProject,
    leaveProject,
    disconnect: disconnectSocket,
  };
}

// ============================================
// 專案 Socket Hook
// ============================================

/**
 * 專案即時更新 Hook
 * 
 * 使用方式：
 * ```tsx
 * // 在 ProjectDetail 頁面使用
 * useProjectSocket(projectId);
 * ```
 */
export function useProjectSocket(projectId: string | undefined) {
  const { joinProject, leaveProject, isConnected } = useSocket();

  useEffect(() => {
    if (!projectId || !isConnected) return;

    // 加入專案 Room
    joinProject(projectId);

    // 清理：離開專案 Room
    return () => {
      leaveProject(projectId);
    };
  }, [projectId, isConnected, joinProject, leaveProject]);
}

// ============================================
// 線上狀態 Hook
// ============================================

/**
 * 取得線上使用者列表
 */
export function useOnlineUsers() {
  const [onlineUsers, setOnlineUsers] = useState<string[]>([]);
  const { on, emit, isConnected } = useSocket();

  useEffect(() => {
    if (!isConnected) return;

    // 監聽線上使用者更新
    const unsubscribe = on('online_users', (data: { users: string[] }) => {
      setOnlineUsers(data.users);
    });

    // 請求線上使用者列表
    emit('get_online_users');

    // 每 30 秒更新一次
    const interval = setInterval(() => {
      emit('get_online_users');
    }, 30000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, [isConnected, on, emit]);

  return onlineUsers;
}

// ============================================
// 輸入狀態 Hook
// ============================================

/**
 * 正在輸入狀態 Hook
 * 
 * 使用方式：
 * ```tsx
 * const { setTyping, typingUsers } = useTypingStatus(projectId, taskId);
 * 
 * <input onChange={() => setTyping(true)} />
 * {typingUsers.length > 0 && <p>有人正在輸入...</p>}
 * ```
 */
export function useTypingStatus(projectId: string, taskId?: string) {
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const { emit, on, isConnected } = useSocket();
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!isConnected) return;

    const handleTyping = (data: { user_id: string; task_id?: string }) => {
      if (taskId && data.task_id !== taskId) return;
      setTypingUsers(prev => 
        prev.includes(data.user_id) ? prev : [...prev, data.user_id]
      );
    };

    const handleStopTyping = (data: { user_id: string; task_id?: string }) => {
      if (taskId && data.task_id !== taskId) return;
      setTypingUsers(prev => prev.filter(id => id !== data.user_id));
    };

    const unsubTyping = on('user_typing', handleTyping);
    const unsubStop = on('user_stop_typing', handleStopTyping);

    return () => {
      unsubTyping();
      unsubStop();
    };
  }, [isConnected, on, taskId]);

  const setTyping = useCallback((isTyping: boolean) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    if (isTyping) {
      emit('typing', { project_id: projectId, task_id: taskId });
      
      // 3 秒後自動停止輸入狀態
      timeoutRef.current = setTimeout(() => {
        emit('stop_typing', { project_id: projectId, task_id: taskId });
      }, 3000);
    } else {
      emit('stop_typing', { project_id: projectId, task_id: taskId });
    }
  }, [emit, projectId, taskId]);

  return { typingUsers, setTyping };
}

