/**
 * ============================================
 * NotificationContext.tsx - 通知狀態管理
 * ============================================
 * 
 * 【這個 Context 的作用】
 * 在整個應用程式中共享通知狀態，確保：
 * - Dashboard 的 Recent Activity 和 Notifications 頁面同步
 * - Mark all as read 後所有頁面都會更新
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { notificationService } from '../services/apiService';
import { Notification } from '../types';

// ============================================
// Context 類型定義
// ============================================

interface NotificationContextType {
    notifications: Notification[];
    unreadCount: number;
    isLoading: boolean;
    fetchNotifications: () => Promise<void>;
    markAllAsRead: () => Promise<void>;
    markAsRead: (id: string) => Promise<void>;
}

// ============================================
// 建立 Context
// ============================================

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

// ============================================
// Provider 組件
// ============================================

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    // 計算未讀數量
    const unreadCount = notifications.filter(n => !n.read).length;

    // 取得通知列表
    const fetchNotifications = useCallback(async () => {
        try {
            setIsLoading(true);
            const data = await notificationService.getNotifications();
            setNotifications(data);
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    // 標記所有為已讀
    const markAllAsRead = useCallback(async () => {
        try {
            await notificationService.markAllAsRead();
            setNotifications(prev => prev.map(n => ({ ...n, read: true })));
        } catch (error) {
            console.error('Failed to mark all notifications as read:', error);
        }
    }, []);

    // 標記單一通知為已讀
    const markAsRead = useCallback(async (id: string) => {
        try {
            await notificationService.markAsRead(id);
            setNotifications(prev =>
                prev.map(n => n.id === id ? { ...n, read: true } : n)
            );
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    }, []);

    // 初始載入
    useEffect(() => {
        fetchNotifications();
    }, [fetchNotifications]);

    return (
        <NotificationContext.Provider
            value={{
                notifications,
                unreadCount,
                isLoading,
                fetchNotifications,
                markAllAsRead,
                markAsRead,
            }}
        >
            {children}
        </NotificationContext.Provider>
    );
};

// ============================================
// 自定義 Hook
// ============================================

export const useNotifications = () => {
    const context = useContext(NotificationContext);
    if (context === undefined) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
};
