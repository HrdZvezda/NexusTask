/**
 * ============================================
 * Notifications.tsx - 通知列表頁面
 * ============================================
 * 
 * 顯示所有通知的完整列表
 * 
 * 【路由】
 * 路徑: /notifications
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Notification } from '../types';
import { Bell, ArrowLeft, Check, CheckCheck } from 'lucide-react';
import { useNotifications } from '../context/NotificationContext';

export const Notifications: React.FC = () => {
    // 使用共享的 NotificationContext
    const { notifications, unreadCount, isLoading, markAllAsRead } = useNotifications();

    if (isLoading) {
        return (
            <div className="p-8 text-center text-slate-500">
                Loading notifications...
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* 頁面標題 */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link
                        to="/"
                        className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                        <ArrowLeft size={20} className="text-slate-500" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                            <Bell className="text-indigo-600" size={24} />
                            Notifications
                        </h1>
                        <p className="text-sm text-slate-500 mt-1">
                            {unreadCount > 0 ? `${unreadCount} unread notifications` : 'All caught up!'}
                        </p>
                    </div>
                </div>
                {unreadCount > 0 && (
                    <button
                        onClick={markAllAsRead}
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                    >
                        <CheckCheck size={18} />
                        Mark all as read
                    </button>
                )}
            </div>

            {/* 通知列表 */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                {notifications.length === 0 ? (
                    <div className="p-12 text-center">
                        <Bell className="mx-auto text-slate-300 mb-4" size={48} />
                        <p className="text-slate-500">No notifications yet</p>
                    </div>
                ) : (
                    <div className="divide-y divide-slate-100">
                        {notifications.map(n => {
                            const isClickable = Boolean(n.projectId);
                            return (
                                <div
                                    key={n.id}
                                    className={`p-5 flex items-start gap-4 transition-colors ${!n.read ? 'bg-indigo-50/30' : 'hover:bg-slate-50'
                                        }`}
                                >
                                    {/* 狀態指示點 */}
                                    <div className={`mt-1 w-2.5 h-2.5 rounded-full flex-shrink-0 ${n.type === 'success' ? 'bg-emerald-500' :
                                        n.type === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                                        }`}></div>

                                    <div className="flex-1 min-w-0">
                                        <p className={`text-sm text-slate-800 ${!n.read ? 'font-semibold' : ''}`}>
                                            {n.message}
                                        </p>
                                        <p className="text-xs text-slate-400 mt-1">{n.createdAt}</p>
                                        {n.projectName && (
                                            <p className="text-xs text-indigo-500 mt-1">
                                                Project: {n.projectName}
                                            </p>
                                        )}
                                    </div>

                                    {isClickable && (
                                        <Link
                                            to={`/projects/${n.projectId}`}
                                            className="px-3 py-1.5 text-xs font-medium text-indigo-600 hover:bg-indigo-100 rounded-lg transition-colors"
                                        >
                                            View Project
                                        </Link>
                                    )}

                                    {!n.read && (
                                        <div className="w-2 h-2 bg-indigo-500 rounded-full flex-shrink-0 mt-2"></div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};
