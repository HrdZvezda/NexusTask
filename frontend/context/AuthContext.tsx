/**
 * ============================================
 * AuthContext.tsx - 認證狀態管理
 * ============================================
 * 
 * 【這個檔案的作用】
 * 管理整個應用程式的「登入狀態」。
 * 讓所有頁面都能知道：
 * - 目前是誰登入了？
 * - 是否正在載入中？
 * - 如何執行登入、登出、註冊等操作？
 * 
 * 【什麼是 Context？】
 * React Context 是一種「全域狀態管理」的方式。
 * 
 * 想像一下：你有一個大家庭（整個應用程式），
 * 家裡有一個公告欄（Context），
 * 任何人（任何組件）都可以看到公告欄上的訊息。
 * 
 * 不用 Context 的話，你要把訊息一層一層傳下去：
 * 爺爺 → 爸爸 → 你 → 弟弟（很麻煩！）
 * 
 * 用了 Context 之後：
 * 任何人直接看公告欄就好（方便！）
 * 
 * 【串接流程】
 * 
 * App.tsx
 *    │
 *    └─ AuthProvider (提供認證狀態)
 *          │
 *          ├─ Layout.tsx (可以用 useAuth() 取得狀態)
 *          │     │
 *          │     └─ 顯示使用者名稱、頭像
 *          │
 *          ├─ Login.tsx (可以用 useAuth() 執行登入)
 *          │
 *          ├─ Dashboard.tsx (可以用 useAuth() 知道誰登入)
 *          │
 *          └─ ... 其他所有頁面
 * 
 * 【和後端的關係】
 * 這個檔案會呼叫 apiService.ts 的 authService 來和後端溝通
 * AuthContext → apiService.ts → 後端 auth.py
 */

// ============================================
// 導入需要的模組
// ============================================

// React 核心功能
import React, { createContext, useContext, useState, useEffect } from 'react';

// 使用者類型定義（從 types.ts 導入）
import { User } from '../types';

// 認證相關的 API 服務（從 apiService.ts 導入）
// 這是和後端溝通的橋樑
import { authService } from '../services/apiService';

// ============================================
// 類型定義
// ============================================

/**
 * 定義 AuthContext 提供的內容
 * 
 * 這就是「公告欄上會有什麼資訊」
 */
interface AuthContextType {
  user: User | null;  // 目前登入的使用者，null 表示沒有人登入
  
  /**
   * 登入函數
   * @param email - 電子郵件
   * @param pass - 密碼
   * 
   * 【串接】→ authService.login() → POST /auth/login → 後端 auth.py login()
   */
  login: (email: string, pass: string) => Promise<void>;
  
  /**
   * 註冊函數
   * @param name - 使用者名稱
   * @param email - 電子郵件
   * @param pass - 密碼
   * @param department - 部門
   * 
   * 【串接】→ authService.register() → POST /auth/register → 後端 auth.py register()
   */
  register: (name: string, email: string, pass: string, department: string) => Promise<void>;
  
  /**
   * 登出函數
   * 
   * 【串接】→ authService.logout() → POST /auth/logout → 後端 auth.py logout()
   */
  logout: () => void;
  
  /**
   * 更新個人資料函數
   * @param data - 要更新的資料
   * 
   * 【串接】→ authService.updateProfile() → PATCH /auth/me → 後端 auth.py update_me()
   */
  updateProfile: (data: Partial<User>) => Promise<void>;
  
  loading: boolean;   // 是否正在載入中（檢查登入狀態時為 true）
}

// ============================================
// 建立 Context
// ============================================

/**
 * 建立 AuthContext
 * 
 * createContext() 建立一個新的 Context
 * undefined 是預設值，表示還沒有提供任何值
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ============================================
// AuthProvider 組件
// ============================================

/**
 * AuthProvider - 認證狀態提供者
 * 
 * 這個組件會包住整個應用程式（在 App.tsx 中）
 * 它負責：
 * 1. 管理登入狀態
 * 2. 提供登入、登出等函數給子組件使用
 * 
 * @param children - 被包住的子組件（整個應用程式）
 * 
 * 【使用方式】在 App.tsx 中：
 * <AuthProvider>
 *   <整個應用程式 />
 * </AuthProvider>
 */
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // ============================================
  // 狀態定義
  // ============================================
  
  /**
   * user 狀態：儲存目前登入的使用者資料
   * - 有值：表示有人登入
   * - null：表示沒有人登入
   * 
   * useState 是 React Hook，用來建立可變的狀態
   * useState<User | null>(null) 表示：
   * - 類型是 User 或 null
   * - 初始值是 null
   */
  const [user, setUser] = useState<User | null>(null);
  
  /**
   * loading 狀態：是否正在檢查登入狀態
   * - true：正在檢查（顯示載入畫面）
   * - false：檢查完畢
   * 
   * 初始值是 true，因為一開始要檢查是否已經登入
   */
  const [loading, setLoading] = useState(true);

  // ============================================
  // 初始化：檢查現有的登入狀態
  // ============================================
  
  /**
   * useEffect 是 React Hook，用來執行「副作用」
   * 副作用 = 和外部世界互動的事情（讀取 localStorage、呼叫 API 等）
   * 
   * useEffect(() => { ... }, []) 
   * 第二個參數是空陣列 []，表示「只在組件載入時執行一次」
   * 
   * 【執行時機】
   * 當使用者打開網頁時，這段程式碼會自動執行
   * 檢查是否之前已經登入過（有沒有存 token）
   */
  useEffect(() => {
    /**
     * 初始化認證狀態
     * 
     * 這是一個非同步函數（async），因為要等待 API 回應
     */
    const initAuth = async () => {
      try {
        // 步驟 1: 從 localStorage 讀取之前存的使用者資料和 token
        // localStorage 是瀏覽器提供的儲存空間，關閉瀏覽器後資料還在
        const storedUser = localStorage.getItem('nexus_user');
        const accessToken = localStorage.getItem('nexus_access_token');
        
        // 步驟 2: 如果有存過資料和 token，表示之前有登入過
        if (storedUser && accessToken) {
          try {
            // 嘗試和後端確認 token 是否還有效
            // 如果有效，後端會回傳最新的使用者資料
            // 【API 呼叫】GET /auth/me → 後端 auth.py get_me()
            const freshUser = await authService.getCurrentUser();
            
            // 更新狀態為最新的使用者資料
            setUser(freshUser);
            // 同時更新 localStorage 中的資料
            localStorage.setItem('nexus_user', JSON.stringify(freshUser));
          } catch {
            // 如果 API 失敗（例如 token 過期），就用本地存的資料
            // JSON.parse() 把 JSON 字串轉回物件
            setUser(JSON.parse(storedUser));
          }
        }
        // 如果沒有存過資料，user 維持 null（沒有登入）
        
      } catch (e) {
        // 發生錯誤時，印出錯誤訊息
        console.error(e);
        // 清除所有可能損壞的資料
        localStorage.removeItem('nexus_user');
        localStorage.removeItem('nexus_access_token');
        localStorage.removeItem('nexus_refresh_token');
      } finally {
        // finally 區塊「一定會執行」，不管成功或失敗
        // 設定 loading 為 false，表示檢查完畢
        setLoading(false);
      }
    };
    
    // 執行初始化函數
    initAuth();
  }, []);  // 空陣列表示只執行一次

  // ============================================
  // 登入函數
  // ============================================
  
  /**
   * 處理使用者登入
   * 
   * @param email - 使用者輸入的電子郵件
   * @param pass - 使用者輸入的密碼
   * 
   * 【串接流程】
   * Login.tsx 的表單 → 這個 login 函數 → authService.login() 
   * → POST /auth/login → 後端 auth.py login()
   */
  const login = async (email: string, pass: string) => {
    // 呼叫 API 服務的登入函數
    // await 會等待 API 回應
    const loggedInUser = await authService.login(email, pass);
    
    // 更新狀態：現在有使用者登入了
    setUser(loggedInUser);
    
    // 把使用者資料存到 localStorage
    // JSON.stringify() 把物件轉成 JSON 字串
    localStorage.setItem('nexus_user', JSON.stringify(loggedInUser));
  };

  // ============================================
  // 註冊函數
  // ============================================
  
  /**
   * 處理使用者註冊
   * 
   * @param name - 使用者名稱
   * @param email - 電子郵件
   * @param pass - 密碼
   * @param department - 部門
   * 
   * 【串接流程】
   * Register.tsx 的表單 → 這個 register 函數 → authService.register()
   * → POST /auth/register → 後端 auth.py register()
   * → 然後自動登入
   */
  const register = async (name: string, email: string, pass: string, department: string) => {
    // 呼叫 API 服務的註冊函數
    // 註冊成功後會自動登入，回傳登入後的使用者資料
    const registeredUser = await authService.register(name, email, pass, department);
    
    // 更新狀態
    setUser(registeredUser);
    
    // 存到 localStorage
    localStorage.setItem('nexus_user', JSON.stringify(registeredUser));
  };

  // ============================================
  // 登出函數
  // ============================================
  
  /**
   * 處理使用者登出
   * 
   * 【串接流程】
   * Layout.tsx 的登出按鈕 → 這個 logout 函數 → authService.logout()
   * → POST /auth/logout → 後端 auth.py logout()
   */
  const logout = async () => {
    try {
      // 通知後端使用者要登出
      await authService.logout();
    } catch {
      // 即使 API 呼叫失敗，我們還是要清除本地狀態
      // 這樣使用者就算後端有問題也能登出
    }
    
    // 清除狀態：沒有人登入了
    setUser(null);
    
    // 清除 localStorage 中所有認證相關的資料
    localStorage.removeItem('nexus_user');
    localStorage.removeItem('nexus_access_token');
    localStorage.removeItem('nexus_refresh_token');
  };

  // ============================================
  // 更新個人資料函數
  // ============================================
  
  /**
   * 更新使用者的個人資料
   * 
   * @param data - 要更新的資料（可以只更新部分欄位）
   * 
   * 【串接流程】
   * Settings.tsx 的表單 → 這個 updateProfile 函數 → authService.updateProfile()
   * → PATCH /auth/me → 後端 auth.py update_me()
   */
  const updateProfile = async (data: Partial<User>) => {
    // 呼叫 API 更新資料，回傳更新後的使用者資料
    const updatedUser = await authService.updateProfile(data);
    
    // 更新狀態
    setUser(updatedUser);
    
    // 更新 localStorage
    localStorage.setItem('nexus_user', JSON.stringify(updatedUser));
  };

  // ============================================
  // 提供 Context 給子組件
  // ============================================
  
  /**
   * 使用 Context.Provider 把值提供給所有子組件
   * 
   * value={{ ... }} 是要提供的值，包含：
   * - user: 目前登入的使用者
   * - login: 登入函數
   * - register: 註冊函數
   * - logout: 登出函數
   * - updateProfile: 更新個人資料函數
   * - loading: 是否正在載入
   * 
   * {children} 是被包住的子組件（整個應用程式）
   */
  return (
    <AuthContext.Provider value={{ user, login, register, logout, updateProfile, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// ============================================
// useAuth Hook
// ============================================

/**
 * useAuth - 自訂 Hook，讓任何組件都能輕鬆存取認證狀態
 * 
 * 【什麼是 Hook？】
 * Hook 是一種特殊的函數，讓你可以在函數組件中使用 React 的功能
 * 自訂 Hook 的名稱必須以 use 開頭
 * 
 * 【使用方式】
 * 在任何組件中：
 * 
 * import { useAuth } from '../context/AuthContext';
 * 
 * function MyComponent() {
 *   const { user, login, logout } = useAuth();
 *   
 *   // 現在可以使用 user, login, logout 了！
 *   if (user) {
 *     return <div>歡迎，{user.name}！</div>;
 *   }
 * }
 * 
 * @returns AuthContext 的值（user, login, logout 等）
 * @throws 如果不在 AuthProvider 內使用會拋出錯誤
 */
export const useAuth = () => {
  // useContext 讀取 Context 的值
  const context = useContext(AuthContext);
  
  // 如果 context 是 undefined，表示沒有被 AuthProvider 包住
  // 這是一個使用錯誤，所以拋出錯誤提醒開發者
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  
  // 回傳 context，讓使用者可以存取 user, login, logout 等
  return context;
};
