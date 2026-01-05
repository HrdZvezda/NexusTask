/**
 * ============================================
 * Login.tsx - 登入頁面
 * ============================================
 * 
 * 【這個頁面的作用】
 * 讓使用者輸入帳號密碼登入系統
 * 
 * 【頁面結構圖】
 * ┌────────────────────────────────────────┐
 * │                                        │
 * │            [N] Logo                    │
 * │          Welcome Back                  │
 * │    Sign in to continue to NexusTeam    │
 * │                                        │
 * │  ┌──────────────────────────────────┐  │
 * │  │ 📧 Email                         │  │
 * │  │ you@example.com                  │  │
 * │  └──────────────────────────────────┘  │
 * │                                        │
 * │  ┌──────────────────────────────────┐  │
 * │  │ 🔒 Password                      │  │
 * │  │ ••••••••                         │  │
 * │  └──────────────────────────────────┘  │
 * │                                        │
 * │  [         Sign In          ]          │
 * │                                        │
 * │  Don't have an account?                │
 * │  Create an account                     │
 * │                                        │
 * │  Demo: demo@test.com / demo            │
 * └────────────────────────────────────────┘
 * 
 * 【路由】
 * 路徑: /login
 * 
 * 【API 串接】
 * authService.login(email, password)
 * → POST /auth/login
 * → 後端 auth.py login()
 */

// ============================================
// 導入 React 和相關模組
// ============================================

import React, { useState } from 'react';

// React Router
// useNavigate: 程式化導航（登入成功後跳轉到首頁）
// Link: 建立連結（跳轉到註冊頁面）
import { useNavigate, Link } from 'react-router-dom';

// 認證 Context
import { useAuth } from '../context/AuthContext';

// Lucide 圖示
import { Lock, Mail } from 'lucide-react';

// ============================================
// Login 組件
// ============================================

export const Login: React.FC = () => {
  // ============================================
  // 狀態管理
  // ============================================

  // 表單欄位狀態
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // 錯誤訊息
  const [error, setError] = useState('');

  // 載入狀態（防止重複提交）
  const [isLoading, setIsLoading] = useState(false);

  // 從 AuthContext 取得 login 函數
  const { login } = useAuth();

  // React Router 的導航函數
  const navigate = useNavigate();

  // ============================================
  // 表單提交處理
  // ============================================

  /**
   * 處理登入表單提交
   * 
   * @param e - 表單提交事件
   * 
   * 【流程】
   * 1. 阻止表單預設行為（頁面刷新）
   * 2. 清除之前的錯誤訊息
   * 3. 設定載入狀態
   * 4. 呼叫 login 函數（來自 AuthContext）
   * 5. 成功：跳轉到首頁
   * 6. 失敗：顯示錯誤訊息
   * 
   * 【API 呼叫】
   * login(email, password)
   * → AuthContext 的 login 函數
   * → apiService.ts 的 authService.login()
   * → POST /auth/login
   * → 後端 auth.py login()
   */
  const handleSubmit = async (e: React.FormEvent) => {
    // 阻止表單預設的頁面刷新行為
    e.preventDefault();

    // 清除之前的錯誤訊息
    setError('');

    // 設定載入狀態（按鈕會顯示「Signing in...」）
    setIsLoading(true);

    try {
      // 呼叫 login 函數
      // 這個函數來自 AuthContext，會：
      // 1. 呼叫後端 API
      // 2. 儲存 token 到 localStorage
      // 3. 更新全域的 user 狀態
      await login(email, password);

      // 登入成功，跳轉到首頁
      navigate('/');
    } catch (err) {
      // 登入失敗，顯示錯誤訊息
      setError('Invalid email or password');
    } finally {
      // 不管成功或失敗，都結束載入狀態
      setIsLoading(false);
    }
  };

  // ============================================
  // 渲染 UI
  // ============================================

  return (
    // 全螢幕置中的容器
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">

      {/* 登入卡片 */}
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-slate-100">

        {/* ========== Logo 和標題 ========== */}
        <div className="text-center mb-8">
          {/* Logo */}
          <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center text-white mx-auto mb-4 text-xl font-bold">
            N
          </div>
          {/* 標題 */}
          <h1 className="text-2xl font-bold text-slate-900">Welcome</h1>
          <p className="text-slate-500 mt-2">Sign in to continue to NexusTeam</p>
        </div>

        {/* ========== 登入表單 ========== */}
        <form onSubmit={handleSubmit} className="space-y-6">

          {/* 錯誤訊息 */}
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm text-center">
              {error}
            </div>
          )}

          {/* Email 輸入框 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Email</label>
            <div className="relative">
              {/* 左側圖示 */}
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              {/* 輸入框 */}
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          {/* Password 輸入框 */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Password</label>
            <div className="relative">
              {/* 左側圖示 */}
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              {/* 輸入框 */}
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          {/* 登入按鈕 */}
          <button
            type="submit"
            disabled={isLoading}  // 載入中時禁用按鈕
            className="w-full bg-indigo-600 text-white py-2.5 rounded-lg font-medium hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-500/20 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {/* 根據載入狀態顯示不同文字 */}
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* ========== 註冊連結 ========== */}
        <div className="mt-8 text-center border-t border-slate-100 pt-6">
          <p className="text-sm text-slate-500 mb-2">Don't have an account?</p>
          <Link
            to="/register"
            className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 hover:underline"
          >
            Create an account
          </Link>
        </div>

        {/* ========== 測試帳號提示 ========== */}
        <div className="mt-6 text-center text-xs text-slate-400">
          <p>Demo Account: howard@test.com / password</p>
        </div>
      </div>
    </div>
  );
};
