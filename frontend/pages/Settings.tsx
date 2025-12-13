/**
 * ============================================
 * Settings.tsx - 帳號設定頁面
 * ============================================
 * 
 * 【這個頁面的作用】
 * 讓使用者管理自己的帳號設定，包括：
 * - 修改顯示名稱
 * - 修改部門
 * - 修改密碼
 * 
 * 【頁面結構】
 * ┌────────────────────────────────────────┐
 * │ ← Back                                │
 * │ Account Settings                      │
 * │                                        │
 * │ ┌────────────────────────────────────┐│
 * │ │ [Avatar] User Name                 ││
 * │ │          ADMIN • Engineering       ││
 * │ ├────────────────────────────────────┤│
 * │ │ Display Name                       ││
 * │ │ [👤 _______________]               ││
 * │ │                                    ││
 * │ │ Department                         ││
 * │ │ [💼 _______________]               ││
 * │ │                                    ││
 * │ │ Email Address                      ││
 * │ │ [📧 user@email.com] (disabled)     ││
 * │ ├────────────────────────────────────┤│
 * │ │ 🛡️ Change Password    [Save Changes]│
 * │ └────────────────────────────────────┘│
 * └────────────────────────────────────────┘
 * 
 * 【路由】
 * 路徑: /settings
 * 
 * 【API 串接】
 * - authService.updateProfile() → 更新個人資料
 * - authService.changePassword() → 修改密碼
 */

// ============================================
// 導入 React 和相關模組
// ============================================

import React, { useState } from 'react';

// React Router
import { useNavigate } from 'react-router-dom';

// 認證相關
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/apiService';

// Lucide 圖示
import { 
  User,           // 使用者圖示
  Mail,           // 郵件圖示
  Shield,         // 安全圖示
  Save,           // 儲存圖示
  Briefcase,      // 公事包圖示
  X,              // 關閉圖示
  AlertCircle,    // 警告圖示
  CheckCircle2,   // 成功圖示
  ArrowLeft       // 返回箭頭
} from 'lucide-react';

// ============================================
// 常數定義
// ============================================

/**
 * 可選的部門列表
 * 用於自動完成建議
 */
const DEPARTMENTS = [
  'Engineering',
  'Design',
  'Product Management',
  'Marketing',
  'Sales',
  'Human Resources',
  'Finance',
  'Legal',
  'Operations',
  'Customer Support',
  'Data Science',
  'Quality Assurance'
];

// ============================================
// Settings 組件
// ============================================

export const Settings: React.FC = () => {
  // ============================================
  // 從 Context 和 Router 取得資料
  // ============================================
  
  // 從 AuthContext 取得使用者資料和更新函數
  const { user, updateProfile } = useAuth();
  
  // 導航函數
  const navigate = useNavigate();
  
  // ============================================
  // 個人資料表單狀態
  // ============================================
  
  // 顯示名稱（初始值為目前使用者的名稱）
  const [name, setName] = useState(user?.name || '');
  
  // 部門
  const [department, setDepartment] = useState(user?.department || '');
  
  // 儲存中狀態
  const [isSaving, setIsSaving] = useState(false);
  
  // 部門自動完成的顯示狀態
  const [showDeptSuggestions, setShowDeptSuggestions] = useState(false);

  // ============================================
  // 修改密碼彈窗狀態
  // ============================================
  
  // 彈窗開關
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  
  // 密碼欄位
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // 密碼修改的錯誤和成功訊息
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  
  // 密碼修改中狀態
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // ============================================
  // 個人資料表單處理
  // ============================================
  
  /**
   * 處理個人資料更新
   * 
   * @param e - 表單提交事件
   * 
   * 【API 呼叫】
   * updateProfile({ name, department })
   * → AuthContext 的 updateProfile 函數
   * → apiService.ts 的 authService.updateProfile()
   * → PATCH /auth/me
   * → 後端 auth.py update_me()
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    
    // 呼叫更新函數
    await updateProfile({ name, department });
    
    // 短暫延遲後重設儲存狀態，讓使用者看到「Saving...」
    setTimeout(() => setIsSaving(false), 500);
  };

  // ============================================
  // 修改密碼處理
  // ============================================
  
  /**
   * 處理密碼修改
   * 
   * @param e - 表單提交事件
   * 
   * 【流程】
   * 1. 驗證新密碼和確認密碼是否相符
   * 2. 驗證密碼長度
   * 3. 呼叫 API 修改密碼
   * 4. 成功：顯示成功訊息，關閉彈窗
   * 5. 失敗：顯示錯誤訊息
   * 
   * 【API 呼叫】
   * authService.changePassword(currentPassword, newPassword)
   * → POST /auth/change-password
   * → 後端 auth.py change_password()
   */
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');
    
    // 驗證：新密碼和確認密碼必須相同
    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }
    
    // 驗證：密碼至少 4 個字元
    if (newPassword.length < 4) {
      setPasswordError("Password must be at least 4 characters.");
      return;
    }

    setIsChangingPassword(true);
    try {
      // 呼叫 API 修改密碼
      await authService.changePassword(currentPassword, newPassword);
      
      // 顯示成功訊息
      setPasswordSuccess("Password updated successfully!");
      
      // 1.5 秒後關閉彈窗並重設表單
      setTimeout(() => {
        setIsPasswordModalOpen(false);
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setPasswordSuccess('');
      }, 1500);
    } catch (err: any) {
      // 顯示錯誤訊息
      setPasswordError(err.message || "Failed to change password.");
    } finally {
      setIsChangingPassword(false);
    }
  };

  /**
   * 過濾部門列表（用於自動完成）
   */
  const filteredDepartments = DEPARTMENTS.filter(d => 
    d.toLowerCase().includes(department.toLowerCase())
  );

  // ============================================
  // 渲染 UI
  // ============================================
  
  return (
    <div className="max-w-2xl mx-auto">
      {/* 返回按鈕 */}
      <button 
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-slate-500 hover:text-slate-800 mb-4 transition-colors text-sm font-medium"
      >
        <ArrowLeft size={16} /> Back
      </button>
      
      {/* 頁面標題 */}
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Account Settings</h1>

      {/* ========================================
          設定表單卡片
      ======================================== */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 md:p-8">
        
        {/* 使用者資訊區塊 */}
        <div className="flex items-center gap-6 mb-8">
          <img 
            src={user?.avatar} 
            alt="Avatar" 
            className="w-20 h-20 rounded-full bg-slate-100 object-cover" 
          />
          <div>
            <h2 className="text-lg font-bold text-slate-900">{user?.name}</h2>
            <p className="text-slate-500 text-sm">
              {user?.role.toUpperCase()} • {user?.department || 'NexusTeam'}
            </p>
          </div>
        </div>

        {/* 個人資料表單 */}
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* 顯示名稱 */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Display Name
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
          </div>

          {/* 部門（有自動完成功能）*/}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Department
            </label>
            <div className="relative">
              <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="text" 
                value={department}
                onChange={(e) => {
                  setDepartment(e.target.value);
                  setShowDeptSuggestions(true);
                }}
                onFocus={() => setShowDeptSuggestions(true)}
                placeholder="e.g., Engineering, Design"
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
              />
              
              {/* 自動完成下拉選單 */}
              {showDeptSuggestions && (
                <>
                  {/* 點擊外部關閉 */}
                  <div 
                    className="fixed inset-0 z-10" 
                    onClick={() => setShowDeptSuggestions(false)}
                  ></div>
                  <div className="absolute top-full left-0 mt-1 w-full bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-20 max-h-48 overflow-y-auto">
                    {filteredDepartments.length > 0 ? (
                      filteredDepartments.map((dept) => (
                        <button
                          key={dept}
                          type="button"
                          onClick={() => {
                            setDepartment(dept);
                            setShowDeptSuggestions(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 transition-colors"
                        >
                          {dept}
                        </button>
                      ))
                    ) : (
                      <div className="px-4 py-2 text-sm text-slate-400 italic">
                        No matching departments
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Email（不可修改）*/}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Email Address
            </label>
            <div className="relative opacity-60">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input 
                type="email" 
                value={user?.email}
                disabled
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg bg-slate-50 cursor-not-allowed"
              />
            </div>
            <p className="text-xs text-slate-400 mt-1">Contact admin to change email.</p>
          </div>

          {/* 底部操作區 */}
          <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
            {/* 修改密碼按鈕 */}
            <button 
              type="button" 
              onClick={() => setIsPasswordModalOpen(true)}
              className="text-indigo-600 text-sm font-medium hover:underline flex items-center gap-2"
            >
              <Shield size={16} /> Change Password
            </button>
            
            {/* 儲存按鈕 */}
            <button 
              type="submit" 
              disabled={isSaving}
              className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 flex items-center gap-2 disabled:opacity-70"
            >
              <Save size={18} />
              {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>

      {/* ========================================
          修改密碼彈窗
      ======================================== */}
      {isPasswordModalOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm" 
          onClick={() => setIsPasswordModalOpen(false)}
        >
          <div 
            className="bg-white rounded-xl w-full max-w-md shadow-2xl" 
            onClick={e => e.stopPropagation()}
          >
            {/* 彈窗標題 */}
            <div className="p-6 border-b border-slate-100 flex justify-between items-center">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Shield size={20} className="text-indigo-600" /> Change Password
              </h2>
              <button 
                onClick={() => setIsPasswordModalOpen(false)} 
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={20} />
              </button>
            </div>
            
            {/* 密碼表單 */}
            <form onSubmit={handleChangePassword} className="p-6 space-y-4">
              {/* 錯誤訊息 */}
              {passwordError && (
                <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg flex items-center gap-2">
                  <AlertCircle size={16} /> {passwordError}
                </div>
              )}
              
              {/* 成功訊息 */}
              {passwordSuccess && (
                <div className="bg-emerald-50 text-emerald-600 text-sm p-3 rounded-lg flex items-center gap-2">
                  <CheckCircle2 size={16} /> {passwordSuccess}
                </div>
              )}

              {/* 目前密碼 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Current Password
                </label>
                <input 
                  type="password" 
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                />
                <p className="text-xs text-slate-400 mt-1">(Demo: use 'demo')</p>
              </div>

              {/* 新密碼 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  New Password
                </label>
                <input 
                  type="password" 
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              {/* 確認新密碼 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Confirm New Password
                </label>
                <input 
                  type="password" 
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              {/* 按鈕 */}
              <div className="pt-4 flex justify-end gap-3 mt-2">
                <button 
                  type="button" 
                  onClick={() => setIsPasswordModalOpen(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-lg font-medium text-sm"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={isChangingPassword || !!passwordSuccess}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium text-sm shadow-sm disabled:opacity-50"
                >
                  {isChangingPassword ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
