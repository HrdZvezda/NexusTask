/**
 * ============================================
 * Register.tsx - 註冊頁面
 * ============================================
 * 
 * 【這個頁面的作用】
 * 讓新使用者建立帳號
 * 
 * 【頁面結構】
 * - 姓名輸入
 * - Email 輸入
 * - 部門選擇（下拉選單）
 * - 密碼輸入
 * - 確認密碼
 * - 註冊按鈕
 * - 登入連結
 * 
 * 【路由】
 * 路徑: /register
 * 
 * 【API 串接】
 * authService.register(name, email, password, department)
 * → POST /auth/register
 * → 後端 auth.py register()
 * → 然後自動登入
 */

// ============================================
// 導入 React 和相關模組
// ============================================

import React, { useState } from 'react';

// React Router
import { useNavigate, Link } from 'react-router-dom';

// 認證 Context
import { useAuth } from '../context/AuthContext';

// Lucide 圖示
import { Lock, Mail, User, Briefcase, AlertCircle } from 'lucide-react';

// ============================================
// 常數定義
// ============================================

/**
 * 可選的部門列表
 * 用於下拉選單
 */
const DEPARTMENTS = [
  'Engineering',
  'Design',
  'Product Management',
  'Marketing',
  'Sales',
  'Human Resources',
  'Finance',
  'Operations',
  'Other'
];

// ============================================
// Register 組件
// ============================================

export const Register: React.FC = () => {
  // ============================================
  // 狀態管理
  // ============================================
  
  // 表單欄位
  const [name, setName] = useState('');              // 姓名
  const [email, setEmail] = useState('');            // Email
  const [department, setDepartment] = useState('');  // 部門
  const [password, setPassword] = useState('');      // 密碼
  const [confirmPassword, setConfirmPassword] = useState('');  // 確認密碼
  
  // 錯誤和載入狀態
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // 從 AuthContext 取得 register 函數
  const { register } = useAuth();
  
  // React Router 的導航函數
  const navigate = useNavigate();

  // ============================================
  // 表單提交處理
  // ============================================
  
  /**
   * 處理註冊表單提交
   * 
   * @param e - 表單提交事件
   * 
   * 【流程】
   * 1. 驗證密碼是否相符
   * 2. 驗證密碼長度
   * 3. 呼叫 register 函數
   * 4. 成功：自動登入並跳轉到首頁
   * 5. 失敗：顯示錯誤訊息
   * 
   * 【API 呼叫】
   * register(name, email, password, department)
   * → AuthContext 的 register 函數
   * → apiService.ts 的 authService.register()
   * → POST /auth/register
   * → 後端 auth.py register()
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // 驗證：密碼和確認密碼必須相同
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // 驗證：密碼至少 4 個字元
    if (password.length < 4) {
      setError("Password must be at least 4 characters");
      return;
    }

    setIsLoading(true);
    try {
      // 呼叫註冊函數
      // 如果沒有選擇部門，預設為 'General'
      await register(name, email, password, department || 'General');
      
      // 註冊成功（同時也會自動登入），跳轉到首頁
      navigate('/');
    } catch (err: any) {
      // 顯示錯誤訊息
      setError(err.message || 'Failed to create account');
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================
  // 渲染 UI
  // ============================================
  
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-slate-100">
        
        {/* ========== Logo 和標題 ========== */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center text-white mx-auto mb-4 text-xl font-bold">
            N
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Create Account</h1>
          <p className="text-slate-500 mt-2">Join NexusTeam</p>
        </div>

        {/* ========== 註冊表單 ========== */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          {/* 錯誤訊息 */}
          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm text-center flex items-center justify-center gap-2">
              <AlertCircle size={16} /> {error}
            </div>
          )}

          {/* 姓名輸入框 */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                placeholder="John Doe"
                required
              />
            </div>
          </div>

          {/* Email 輸入框 */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          {/* 部門選擇下拉選單 */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700">Department</label>
            <div className="relative">
              <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all appearance-none bg-white text-slate-700"
                required
              >
                <option value="" disabled>Select Department</option>
                {DEPARTMENTS.map(dept => (
                  <option key={dept} value={dept}>{dept}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 密碼輸入框 */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                placeholder="Create a password"
                required
              />
            </div>
          </div>

          {/* 確認密碼輸入框 */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-slate-700">Confirm Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                placeholder="Confirm password"
                required
              />
            </div>
          </div>

          {/* 註冊按鈕 */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-indigo-600 text-white py-2.5 rounded-lg font-medium hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-500/20 transition-all disabled:opacity-70 disabled:cursor-not-allowed mt-2"
          >
            {isLoading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>

        {/* ========== 登入連結 ========== */}
        <div className="mt-8 text-center border-t border-slate-100 pt-6">
          <p className="text-sm text-slate-500 mb-2">Already have an account?</p>
          <Link to="/login" className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};
