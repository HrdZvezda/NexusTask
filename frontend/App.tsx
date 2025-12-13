/**
 * ============================================
 * App.tsx - 應用程式的根組件（入口點）
 * ============================================
 * 
 * 【這個檔案的作用】
 * 這是整個前端應用程式的「總指揮」，負責：
 * 1. 設定路由（決定網址對應到哪個頁面）
 * 2. 設定認證保護（某些頁面需要登入才能看）
 * 3. 包裝整個應用程式的狀態管理
 * 
 * 【應用程式的架構圖】
 * 
 * index.tsx (程式進入點)
 *     │
 *     └─ App.tsx (你現在在這裡)
 *           │
 *           └─ AuthProvider (認證狀態管理)
 *                 │
 *                 └─ Router (路由管理)
 *                       │
 *                       ├─ /login → Login.tsx (登入頁，不需登入)
 *                       │
 *                       ├─ /register → Register.tsx (註冊頁，不需登入)
 *                       │
 *                       └─ ProtectedRoute (需要登入的頁面)
 *                             │
 *                             └─ Layout.tsx (共用的頁面框架)
 *                                   │
 *                                   ├─ / → Dashboard.tsx (儀表板)
 *                                   │
 *                                   ├─ /projects → Projects.tsx (專案列表)
 *                                   │
 *                                   ├─ /projects/:id → ProjectDetail.tsx (專案詳情)
 *                                   │
 *                                   ├─ /tasks/my → MyTasks.tsx (我的任務)
 *                                   │
 *                                   └─ /settings → Settings.tsx (設定)
 * 
 * 【路由是什麼？】
 * 路由就是「網址」和「頁面」的對應關係。
 * 例如：
 * - 使用者輸入 http://localhost:3000/#/projects
 * - 路由系統看到 /projects
 * - 顯示 Projects.tsx 這個頁面
 */

// ============================================
// 導入需要的模組
// ============================================

import React from 'react';

// 從 react-router-dom 導入路由相關組件
// HashRouter: 使用 # 符號的路由（如 http://localhost:3000/#/projects）
// Routes: 路由的容器，包住所有的 Route
// Route: 定義單一個路由（網址 → 頁面）
// Navigate: 用來重新導向到其他頁面
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// 導入認證相關的 Context 和 Hook
import { AuthProvider, useAuth } from './context/AuthContext';

// 導入通知狀態 Context
import { NotificationProvider } from './context/NotificationContext';

// 導入 React Query Provider（伺服器狀態管理）
import { QueryProvider } from './providers/QueryProvider';

// 導入共用的佈局組件（側邊欄、頂部導航等）
import { Layout } from './components/Layout';

// 導入各個頁面組件
import { Login } from './pages/Login';           // 登入頁
import { Register } from './pages/Register';     // 註冊頁
import { Dashboard } from './pages/Dashboard';   // 儀表板（首頁）
import { Projects } from './pages/Projects';     // 專案列表頁
import { ProjectDetail } from './pages/ProjectDetail';  // 專案詳情頁
import { MyTasks } from './pages/MyTasks';       // 我的任務頁
import { Settings } from './pages/Settings';     // 設定頁
import { Notifications } from './pages/Notifications';  // 通知頁

// ============================================
// ProtectedRoute 組件 - 路由保護
// ============================================

/**
 * ProtectedRoute - 受保護的路由組件
 * 
 * 【這個組件的作用】
 * 檢查使用者是否已登入：
 * - 已登入 → 顯示頁面內容
 * - 未登入 → 重新導向到登入頁
 * 
 * 這就像是一個「守衛」，只讓有登入的人進入某些頁面。
 * 
 * @param children - 被保護的頁面內容
 * 
 * 【使用方式】
 * <ProtectedRoute>
 *   <Dashboard />
 * </ProtectedRoute>
 * 
 * 這樣 Dashboard 就只有登入的使用者才能看到
 */
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // 使用 useAuth Hook 取得認證狀態
  // user: 目前登入的使用者（null 表示沒登入）
  // loading: 是否正在檢查登入狀態
  const { user, loading } = useAuth();

  // 情況 1: 正在載入中（檢查是否有之前的登入狀態）
  // 顯示載入畫面，避免畫面閃爍
  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-slate-50 text-indigo-600">
        Loading NexusTeam...
      </div>
    );
  }

  // 情況 2: 沒有登入
  // 使用 Navigate 組件重新導向到登入頁面
  // to="/login" 表示導向到 /login 這個路徑
  if (!user) {
    return <Navigate to="/login" />;
  }

  // 情況 3: 已經登入
  // 用 Layout 組件包住子內容，提供側邊欄、頂部導航等共用元素
  // {children} 是傳入的頁面內容（如 Dashboard）
  return <Layout>{children}</Layout>;
};

// ============================================
// App 主組件
// ============================================

/**
 * App - 應用程式的根組件
 * 
 * 【組件的結構】
 * 
 * <AuthProvider>           ← 提供認證狀態給所有子組件
 *   <Router>               ← 提供路由功能
 *     <Routes>             ← 路由的容器
 *       <Route ... />      ← 各個頁面的路由定義
 *     </Routes>
 *   </Router>
 * </AuthProvider>
 */
const App: React.FC = () => {
  return (
    // QueryProvider 提供 React Query 的快取和狀態管理
    <QueryProvider>
      {/* AuthProvider 包住整個應用程式
          這樣所有組件都可以使用 useAuth() 來存取認證狀態 */}
      <AuthProvider>
        {/* 
        Router (HashRouter) 提供路由功能
        
        【為什麼用 HashRouter？】
        HashRouter 使用 # 符號來處理路由，例如：
        http://localhost:3000/#/projects
        
        好處是：
        1. 不需要後端設定，所有路由都由前端處理
        2. 靜態網頁伺服器也能使用
        3. 重新整理頁面不會出現 404 錯誤
      */}
        <Router>
          {/* NotificationProvider 提供通知狀態管理，確保 Dashboard 和 Notifications 頁面同步 */}
          <NotificationProvider>
            {/* Routes 是所有 Route 的容器 */}
            <Routes>
              {/* 
            ============================================
            公開路由（不需要登入就能存取）
            ============================================
          */}

              {/* 
            登入頁面
            路徑: /login
            組件: Login
            
            當使用者訪問 http://localhost:3000/#/login 時，
            顯示 Login 組件
          */}
              <Route path="/login" element={<Login />} />

              {/* 
            註冊頁面
            路徑: /register
            組件: Register
          */}
              <Route path="/register" element={<Register />} />

              {/* 
            ============================================
            受保護的路由（需要登入才能存取）
            ============================================
          */}

              {/* 
            首頁（儀表板）
            路徑: /
            組件: Dashboard
            
            被 ProtectedRoute 包住，所以需要登入才能看到
            如果沒登入，會被導向到 /login
          */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />

              {/* 
            專案列表頁
            路徑: /projects
            組件: Projects
          */}
              <Route
                path="/projects"
                element={
                  <ProtectedRoute>
                    <Projects />
                  </ProtectedRoute>
                }
              />

              {/* 
            專案詳情頁
            路徑: /projects/:projectId
            組件: ProjectDetail
            
            :projectId 是動態參數，表示這個位置可以是任何值
            例如：/projects/123 中的 123 就是 projectId
            
            在 ProjectDetail 組件中可以用 useParams() 取得這個值
          */}
              <Route
                path="/projects/:projectId"
                element={
                  <ProtectedRoute>
                    <ProjectDetail />
                  </ProtectedRoute>
                }
              />

              {/* 
            我的任務頁
            路徑: /tasks/my
            組件: MyTasks
          */}
              <Route
                path="/tasks/my"
                element={
                  <ProtectedRoute>
                    <MyTasks />
                  </ProtectedRoute>
                }
              />

              {/* 
            設定頁
            路徑: /settings
            組件: Settings
          */}
              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <Settings />
                  </ProtectedRoute>
                }
              />

              {/* 
            通知頁
            路徑: /notifications
            組件: Notifications
          */}
              <Route
                path="/notifications"
                element={
                  <ProtectedRoute>
                    <Notifications />
                  </ProtectedRoute>
                }
              />

              {/* 
            萬用路由（處理所有不存在的路徑）
            路徑: *（星號表示匹配所有路徑）
            
            如果使用者輸入了不存在的網址（例如 /xyz），
            會被重新導向到首頁 /
          */}
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </NotificationProvider>
        </Router>
      </AuthProvider>
    </QueryProvider>
  );
};

// 導出 App 組件，讓 index.tsx 可以導入並渲染
export default App;
