/**
 * ============================================
 * QueryProvider.tsx - React Query Provider
 * ============================================
 * 
 * 提供 React Query 的設定和 Context
 */

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// 建立 QueryClient 實例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 資料過期時間（預設 5 分鐘）
      staleTime: 5 * 60 * 1000,
      
      // 快取保留時間（預設 30 分鐘）
      gcTime: 30 * 60 * 1000,
      
      // 失敗時重試次數
      retry: 1,
      
      // 重試延遲
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      
      // 當視窗重新取得焦點時重新取得資料
      refetchOnWindowFocus: true,
      
      // 當重新連接網路時重新取得資料
      refetchOnReconnect: true,
    },
    mutations: {
      // 失敗時重試次數
      retry: 1,
    },
  },
});

interface QueryProviderProps {
  children: React.ReactNode;
}

/**
 * QueryProvider 組件
 * 
 * 使用方式：
 * 在 App.tsx 中包住整個應用程式：
 * ```tsx
 * <QueryProvider>
 *   <App />
 * </QueryProvider>
 * ```
 */
export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

/**
 * 取得 QueryClient 實例
 * 用於在 Provider 外部操作快取
 */
export function getQueryClient() {
  return queryClient;
}

