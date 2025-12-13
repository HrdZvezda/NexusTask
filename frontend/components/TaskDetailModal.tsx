/**
 * ============================================
 * TaskDetailModal.tsx - 任務詳情彈窗組件
 * ============================================
 * 
 * 【這個組件的作用】
 * 顯示任務的詳細資訊，並提供編輯功能，包括：
 * - 查看任務的標題、描述、狀態、優先級
 * - 修改負責人（Assignee）
 * - 修改截止日期（Due Date）
 * - 編輯備註（Notes）
 * - 查看和新增評論（Comments）
 * 
 * 【彈窗結構圖】
 * ┌────────────────────────────────────────┐
 * │ Header                              X │
 * │ [Priority] [Status]                   │
 * │ Task Title                            │
 * ├────────────────────────────────────────┤
 * │ Description                           │
 * │ ......                                │
 * │                                       │
 * │ 👤 Assignee: [Dropdown]               │
 * │ 📅 Due Date: [Date Picker]            │
 * ├────────────────────────────────────────┤
 * │ 📝 Notes                              │
 * │ [Click to edit notes...]              │
 * ├────────────────────────────────────────┤
 * │ 💬 Comments (3)                       │
 * │ ┌──────────────────────────────────┐  │
 * │ │ User1: Comment content...        │  │
 * │ └──────────────────────────────────┘  │
 * │ ┌──────────────────────────────────┐  │
 * │ │ User2: Another comment...        │  │
 * │ └──────────────────────────────────┘  │
 * ├────────────────────────────────────────┤
 * │ 👤 [Write a comment...        ] [Send]│
 * └────────────────────────────────────────┘
 * 
 * 【在哪裡被使用？】
 * - ProjectDetail.tsx：點擊任務卡片時開啟
 * 
 * 【API 串接】
 * - taskService.getComments() → 取得評論列表
 * - taskService.updateTask() → 更新任務（負責人、日期、備註）
 * - taskService.addComment() → 新增評論
 * - taskService.updateComment() → 編輯評論
 */

// ============================================
// 導入 React 和相關模組
// ============================================

import React, { useState, useEffect, useRef } from 'react';

// 類型定義
import { Task, Comment, User, TaskPriority, Attachment } from '../types';

// API 服務
import { taskService, attachmentService } from '../services/apiService';

// Lucide 圖示
import { 
  X,                    // 關閉圖示
  User as UserIcon,     // 使用者圖示（重新命名避免和類型衝突）
  Calendar,             // 日曆圖示
  FileText,             // 文件圖示（用於備註）
  MessageSquare,        // 訊息圖示（用於評論）
  Send,                 // 發送圖示
  Check,                // 勾選圖示
  Paperclip,            // 附件圖示
  Upload,               // 上傳圖示
  Download,             // 下載圖示
  Trash2                // 刪除圖示
} from 'lucide-react';

// 輔助函數
import { getPriorityColor } from '../utils/helpers';

// ============================================
// 組件 Props 介面
// ============================================

/**
 * TaskDetailModal 組件的 Props
 * 
 * @property task - 要顯示的任務資料
 * @property currentUser - 目前登入的使用者（用於判斷是否可以編輯評論）
 * @property projectMembers - 專案成員列表（用於負責人下拉選單）
 * @property onClose - 關閉彈窗的回調函數
 * @property onUpdateTask - 任務更新後的回調函數（通知父組件更新資料）
 */
interface TaskDetailModalProps {
  task: Task;
  currentUser: User | null;
  projectMembers: User[];
  onClose: () => void;
  onUpdateTask: (task: Task) => void;
}

// ============================================
// TaskDetailModal 組件
// ============================================

export const TaskDetailModal: React.FC<TaskDetailModalProps> = ({ 
  task, 
  currentUser, 
  projectMembers, 
  onClose, 
  onUpdateTask 
}) => {
  // ============================================
  // 狀態管理
  // ============================================
  
  // 評論相關狀態
  const [comments, setComments] = useState<Comment[]>([]);        // 評論列表
  const [newComment, setNewComment] = useState('');               // 新評論輸入框的值
  const [isSendingComment, setIsSendingComment] = useState(false);// 是否正在發送評論
  
  // 備註編輯狀態
  const [isEditingNotes, setIsEditingNotes] = useState(false);    // 是否正在編輯備註
  const [noteContent, setNoteContent] = useState(task.notes || '');// 備註內容

  // 負責人編輯狀態
  const [editAssigneeSearch, setEditAssigneeSearch] = useState('');     // 負責人搜尋關鍵字
  const [isEditAssigneeOpen, setIsEditAssigneeOpen] = useState(false);  // 是否顯示負責人下拉選單

  // 評論編輯狀態
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null);  // 正在編輯的評論 ID
  const [editingCommentContent, setEditingCommentContent] = useState('');         // 編輯中的評論內容

  // 附件相關狀態
  const [attachments, setAttachments] = useState<Attachment[]>(task.attachments || []);  // 附件列表
  const [isUploading, setIsUploading] = useState(false);                      // 是否正在上傳
  const fileInputRef = useRef<HTMLInputElement>(null);                        // 檔案輸入框 ref

  // 評論列表底部的 ref，用於自動滾動到最新評論
  const commentsEndRef = useRef<HTMLDivElement>(null);

  // ============================================
  // 副作用：載入評論
  // ============================================
  
  /**
   * 當任務 ID 改變時，載入該任務的評論與附件
   * 
   * 【API 呼叫】
   * taskService.getComments(taskId) → 取得評論
   * attachmentService.getTaskAttachments(taskId) → 取得附件
   */
  useEffect(() => {
    // 載入評論
    taskService.getComments(task.id).then(setComments);
    setNoteContent(task.notes || '');
    
    // 初始化負責人顯示名稱
    const assignee = projectMembers.find(m => m.id === task.assigneeId);
    setEditAssigneeSearch(assignee ? assignee.name : 'Unassigned');

    // 載入附件
    attachmentService.getTaskAttachments(task.id).then(setAttachments).catch(console.error);
  }, [task.id, task.projectId, projectMembers, task.assigneeId, task.notes]);

  // ============================================
  // 備註相關函數
  // ============================================
  
  /**
   * 儲存備註
   * 
   * 【API 呼叫】
   * taskService.updateTask(taskId, { notes: content })
   * → PATCH /tasks/{taskId}
   * → 後端 tasks.py update_task()
   */
  const handleSaveNotes = async () => {
    try {
      // 呼叫 API 更新備註
      const updatedTask = await taskService.updateTask(task.id, { notes: noteContent });
      // 通知父組件更新資料
      onUpdateTask(updatedTask);
      // 結束編輯模式
      setIsEditingNotes(false);
    } catch (error) {
      console.error("Failed to update notes", error);
    }
  };

  // ============================================
  // 負責人相關函數
  // ============================================
  
  /**
   * 更新任務負責人
   * 
   * @param assigneeId - 新負責人的 ID（空字串表示取消指派）
   * 
   * 【API 呼叫】
   * taskService.updateTask(taskId, { assigneeId })
   * → PATCH /tasks/{taskId}
   * → 後端 tasks.py update_task()
   */
  const handleUpdateAssignee = async (assigneeId: string) => {
    try {
      const updatedTask = await taskService.updateTask(task.id, { assigneeId });
      onUpdateTask(updatedTask);
      setIsEditAssigneeOpen(false);
      
      // 更新顯示名稱
      const assignee = projectMembers.find(m => m.id === assigneeId);
      setEditAssigneeSearch(assignee ? assignee.name : 'Unassigned');
    } catch (error) {
      console.error("Failed to update assignee", error);
    }
  };

  // ============================================
  // 截止日期相關函數
  // ============================================
  
  /**
   * 更新任務截止日期
   * 
   * @param date - 新的截止日期（YYYY-MM-DD 格式）
   * 
   * 【API 呼叫】
   * taskService.updateTask(taskId, { dueDate: date })
   * → PATCH /tasks/{taskId}
   * → 後端 tasks.py update_task()
   */
  const handleUpdateDueDate = async (date: string) => {
    try {
      const updatedTask = await taskService.updateTask(task.id, { dueDate: date });
      onUpdateTask(updatedTask);
    } catch (error) {
      console.error("Failed to update due date", error);
    }
  };

  // ============================================
  // 評論相關函數
  // ============================================
  
  /**
   * 新增評論
   * 
   * @param e - 表單提交事件
   * 
   * 【API 呼叫】
   * taskService.addComment(taskId, content, userId, userName)
   * → POST /tasks/{taskId}/comments
   * → 後端 tasks.py create_task_comment()
   */
  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();  // 阻止表單預設的頁面刷新行為
    
    // 驗證：評論不能為空，且必須有登入使用者
    if (!newComment.trim() || !currentUser) return;

    setIsSendingComment(true);
    try {
      // 呼叫 API 新增評論
      const comment = await taskService.addComment(
        task.id, 
        newComment, 
        currentUser.id, 
        currentUser.name
      );
      
      // 把新評論加到列表中
      setComments(prev => [...prev, comment]);
      // 清空輸入框
      setNewComment('');
      
      // 更新父組件中的評論數量（不需要重新載入整個任務）
      onUpdateTask({ ...task, commentsCount: (task.commentsCount || 0) + 1 });
      
      // 自動滾動到最新評論
      setTimeout(() => {
        commentsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (error) {
      console.error("Failed to add comment", error);
    } finally {
      setIsSendingComment(false);
    }
  };

  /**
   * 編輯現有評論
   * 
   * 【API 呼叫】
   * taskService.updateComment(commentId, content)
   * → PATCH /comments/{commentId}
   * → 後端 tasks.py update_comment()
   */
  const handleEditComment = async () => {
    if (!editingCommentId) return;
    try {
      const updated = await taskService.updateComment(editingCommentId, editingCommentContent);
      // 更新列表中的評論
      setComments(prev => prev.map(c => c.id === editingCommentId ? updated : c));
      // 結束編輯模式
      setEditingCommentId(null);
      setEditingCommentContent('');
    } catch (e) {
      console.error(e);
    }
  };

  // ============================================
  // 附件相關函數
  // ============================================

  /**
   * 上傳附件
   */
  const handleUploadAttachment = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const attachment = await attachmentService.uploadAttachment(task.id, file);
      setAttachments(prev => [attachment, ...prev]);
    } catch (error) {
      console.error('Failed to upload attachment:', error);
      alert(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  /**
   * 下載附件
   */
  const handleDownloadAttachment = async (attachment: Attachment) => {
    try {
      await attachmentService.downloadAttachment(attachment.id, attachment.originalFilename);
    } catch (error) {
      console.error('Failed to download attachment:', error);
    }
  };

  /**
   * 刪除附件
   */
  const handleDeleteAttachment = async (attachmentId: string) => {
    if (!confirm('確定要刪除此附件嗎？')) return;
    try {
      await attachmentService.deleteAttachment(attachmentId);
      setAttachments(prev => prev.filter(a => a.id !== attachmentId));
    } catch (error) {
      console.error('Failed to delete attachment:', error);
    }
  };

  /**
   * 格式化檔案大小
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  /**
   * 過濾成員列表（用於負責人搜尋）
   * 
   * @returns 符合搜尋條件的成員列表
   */
  const getFilteredMembers = () => {
    if (!editAssigneeSearch) return projectMembers;
    return projectMembers.filter(m => 
      m.name.toLowerCase().includes(editAssigneeSearch.toLowerCase()) || 
      m.email.toLowerCase().includes(editAssigneeSearch.toLowerCase())
    );
  };

  // ============================================
  // 渲染 UI
  // ============================================
  
  return (
    // 背景遮罩：點擊會關閉彈窗
    <div 
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm" 
      onClick={onClose}
    >
      {/* 彈窗主體：停止事件冒泡，避免點擊內容時關閉 */}
      <div 
        className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl" 
        onClick={e => e.stopPropagation()}
      >
        {/* ========================================
            Header 區塊
            顯示優先級、狀態、標題和關閉按鈕
        ======================================== */}
        <div className="p-6 border-b border-slate-100 flex justify-between items-start">
          <div className="flex-1 pr-4">
            {/* 優先級和狀態標籤 */}
            <div className="flex items-center gap-3 mb-2">
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getPriorityColor(task.priority)}`}>
                {task.priority}
              </span>
              <span className="text-xs text-slate-400 uppercase tracking-wider">
                {task.status.replace('_', ' ')}
              </span>
            </div>
            {/* 任務標題 */}
            <h2 className="text-xl font-bold text-slate-900">{task.title}</h2>
          </div>
          {/* 關閉按鈕 */}
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1">
            <X size={24} />
          </button>
        </div>

        {/* ========================================
            Body 區塊
            可滾動的內容區域
        ======================================== */}
        <div className="flex-1 overflow-y-auto p-6">
          
          {/* 描述區塊 */}
          <div className="mb-8">
            <h3 className="text-sm font-semibold text-slate-900 mb-2">Description</h3>
            <p className="text-slate-600 text-sm leading-relaxed whitespace-pre-line">
              {task.description}
            </p>
            
            {/* 負責人和截止日期 */}
            <div className="mt-6 flex flex-wrap items-center gap-6 text-sm text-slate-500">
              
              {/* ========== 負責人選擇器 ========== */}
              <div className="flex items-center gap-2">
                <UserIcon size={16} />
                <span className="whitespace-nowrap">Assignee:</span>
                <div className="relative">
                  {/* 負責人輸入框（可搜尋） */}
                  <input 
                    type="text"
                    value={editAssigneeSearch}
                    onChange={(e) => {
                      setEditAssigneeSearch(e.target.value);
                      setIsEditAssigneeOpen(true);
                    }}
                    onFocus={() => {
                      setIsEditAssigneeOpen(true);
                      setEditAssigneeSearch(''); 
                    }}
                    className="border-b border-slate-200 pb-0.5 font-medium text-slate-800 focus:outline-none focus:border-indigo-500 text-sm bg-transparent min-w-[120px]"
                  />
                  
                  {/* 負責人下拉選單 */}
                  {isEditAssigneeOpen && (
                    <>
                      {/* 點擊外部關閉的遮罩 */}
                      <div 
                        className="fixed inset-0 z-20" 
                        onClick={() => {
                          setIsEditAssigneeOpen(false);
                          // 重設顯示名稱
                          const m = projectMembers.find(u => u.id === task.assigneeId);
                          setEditAssigneeSearch(m ? m.name : 'Unassigned');
                        }}
                      ></div>
                      
                      {/* 下拉選單內容 */}
                      <div className="absolute top-full left-0 mt-1 w-56 bg-white rounded-lg shadow-xl border border-slate-100 py-1 z-30 max-h-48 overflow-auto">
                        {/* 取消指派選項 */}
                        <button 
                          onClick={() => handleUpdateAssignee('')} 
                          className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700"
                        >
                          Unassigned
                        </button>
                        
                        {/* 成員列表 */}
                        {getFilteredMembers().map(m => (
                          <button 
                            key={m.id} 
                            onClick={() => handleUpdateAssignee(m.id)} 
                            className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 text-slate-700 flex items-center gap-2"
                          >
                            <img src={m.avatar} alt="" className="w-5 h-5 rounded-full" />
                            <span className="truncate">{m.name}</span>
                            {/* 顯示勾選標記表示目前選中 */}
                            {task.assigneeId === m.id && (
                              <Check size={14} className="text-indigo-600 ml-auto" />
                            )}
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* ========== 截止日期選擇器 ========== */}
              <div className="flex items-center gap-2">
                <Calendar size={16} />
                <span className="whitespace-nowrap">Due Date:</span>
                <input 
                  type="date"
                  className="bg-transparent border-b border-slate-200 pb-0.5 font-medium text-slate-800 focus:outline-none focus:border-indigo-500 text-sm cursor-pointer hover:bg-slate-50"
                  value={task.dueDate || ''}
                  onChange={(e) => handleUpdateDueDate(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* ========== 附件區塊 ========== */}
          <div className="mb-8 border-t border-slate-100 pt-6">
            <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Paperclip size={16} /> Attachments ({attachments.length})
            </h3>
            
            {/* 上傳按鈕 */}
            <div className="mb-3">
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleUploadAttachment}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-slate-100 text-slate-700 rounded hover:bg-slate-200 disabled:opacity-50"
              >
                <Upload size={14} />
                {isUploading ? 'Uploading...' : 'Upload File'}
              </button>
              <p className="text-xs text-slate-400 mt-1">Max 10MB. Supports images, PDFs, documents, etc.</p>
            </div>
            
            {/* 附件列表 */}
            <div className="space-y-2">
              {attachments.map(attachment => (
                <div 
                  key={attachment.id}
                  className="flex items-center gap-3 p-2 rounded-lg bg-slate-50 hover:bg-slate-100 group"
                >
                  {/* 檔案圖示 */}
                  <div className="w-8 h-8 rounded bg-indigo-100 flex items-center justify-center text-indigo-600">
                    <Paperclip size={14} />
                  </div>
                  
                  {/* 檔案資訊 */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800 truncate">
                      {attachment.originalFilename}
                    </p>
                    <p className="text-xs text-slate-400">
                      {formatFileSize(attachment.fileSize)}
                    </p>
                  </div>
                  
                  {/* 操作按鈕 */}
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleDownloadAttachment(attachment)}
                      className="p-1 text-slate-400 hover:text-indigo-600"
                      title="Download"
                    >
                      <Download size={14} />
                    </button>
                    {currentUser?.id === attachment.uploadedBy && (
                      <button
                        onClick={() => handleDeleteAttachment(attachment.id)}
                        className="p-1 text-slate-400 hover:text-red-600"
                        title="Delete"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
              
              {attachments.length === 0 && (
                <p className="text-sm text-slate-400 italic">No attachments yet</p>
              )}
            </div>
          </div>

          {/* ========== 備註區塊 ========== */}
          <div className="mb-8 border-t border-slate-100 pt-6">
            <h3 className="text-sm font-semibold text-slate-900 mb-2 flex items-center gap-2">
              <FileText size={16} /> Notes
            </h3>
            
            {/* 編輯模式 vs 顯示模式 */}
            {isEditingNotes ? (
              // 編輯模式：顯示文字輸入框
              <div className="bg-slate-50 rounded-lg p-2 border border-slate-200">
                <textarea
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  className="w-full bg-transparent border-none p-2 text-sm text-slate-800 focus:ring-0 resize-y min-h-[100px] outline-none"
                  placeholder="Add unstructured notes..."
                  autoFocus
                />
                <div className="flex justify-end gap-2 mt-2 px-2 pb-1">
                  {/* 取消按鈕 */}
                  <button 
                    onClick={() => { 
                      setNoteContent(task.notes || ''); 
                      setIsEditingNotes(false); 
                    }} 
                    className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-200/50 rounded"
                  >
                    Cancel
                  </button>
                  {/* 儲存按鈕 */}
                  <button 
                    onClick={handleSaveNotes} 
                    className="px-3 py-1.5 text-xs font-medium bg-indigo-600 text-white hover:bg-indigo-700 rounded shadow-sm"
                  >
                    Save Notes
                  </button>
                </div>
              </div>
            ) : (
              // 顯示模式：點擊進入編輯
              <div 
                onClick={() => setIsEditingNotes(true)} 
                className="text-sm text-slate-600 p-3 rounded-lg hover:bg-slate-50 border border-transparent hover:border-slate-200 cursor-text min-h-[60px] whitespace-pre-wrap"
              >
                {noteContent ? noteContent : (
                  <span className="text-slate-400 italic">Click to add notes...</span>
                )}
              </div>
            )}
          </div>

          {/* ========== 評論區塊 ========== */}
          <div className="border-t border-slate-100 pt-6">
            <h3 className="text-sm font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <MessageSquare size={16} /> Comments ({comments.length})
            </h3>
            
            {/* 評論列表 */}
            <div className="space-y-4 mb-6">
              {comments.map(comment => (
                <div key={comment.id} className="flex gap-3 group">
                  {/* 使用者頭像（首字母） */}
                  <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 text-xs font-bold flex-shrink-0">
                    {comment.userName.charAt(0)}
                  </div>
                  
                  {/* 評論內容 */}
                  <div className={`flex-1 rounded-lg p-3 relative ${
                    editingCommentId === comment.id 
                      ? 'bg-white ring-2 ring-indigo-500 shadow-sm' 
                      : 'bg-slate-50'
                  }`}>
                    {/* 評論標題列 */}
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-slate-900">
                        {comment.userName}
                      </span>
                      <div className="flex items-center gap-2 text-[10px] text-slate-400">
                        <span>{new Date(comment.createdAt).toLocaleDateString()}</span>
                        {/* 只有自己的評論才能編輯 */}
                        {currentUser?.id === comment.userId && !editingCommentId && (
                          <button 
                            onClick={() => { 
                              setEditingCommentId(comment.id); 
                              setEditingCommentContent(comment.content); 
                            }} 
                            className="text-indigo-600 hover:underline"
                          >
                            Edit
                          </button>
                        )}
                      </div>
                    </div>
                    
                    {/* 評論內容：編輯模式 vs 顯示模式 */}
                    {editingCommentId === comment.id ? (
                      <div className="mt-2">
                        <textarea 
                          value={editingCommentContent} 
                          onChange={e => setEditingCommentContent(e.target.value)} 
                          className="w-full text-sm border-0 bg-transparent p-0 focus:ring-0 outline-none resize-none text-slate-800" 
                          rows={3} 
                          autoFocus 
                        />
                        <div className="flex gap-2 mt-2 justify-end">
                          <button 
                            onClick={() => setEditingCommentId(null)} 
                            className="text-xs text-slate-600 px-3 py-1"
                          >
                            Cancel
                          </button>
                          <button 
                            onClick={handleEditComment} 
                            className="text-xs bg-indigo-600 text-white px-3 py-1 rounded"
                          >
                            Save
                          </button>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-slate-700 whitespace-pre-wrap">
                        {comment.content}
                      </p>
                    )}
                  </div>
                </div>
              ))}
              
              {/* 自動滾動的定位點 */}
              <div ref={commentsEndRef} />
            </div>
          </div>
        </div>

        {/* ========================================
            Footer 區塊
            新增評論的輸入框
        ======================================== */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50 rounded-b-xl">
          <form onSubmit={handleAddComment} className="flex gap-3">
            {/* 目前使用者頭像 */}
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
              {currentUser?.name.charAt(0) || 'U'}
            </div>
            
            {/* 評論輸入框 */}
            <div className="flex-1 relative">
              <input 
                type="text" 
                value={newComment} 
                onChange={e => setNewComment(e.target.value)} 
                placeholder="Write a comment..." 
                className="w-full border border-slate-300 rounded-lg pl-4 pr-12 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none text-sm" 
              />
              {/* 發送按鈕 */}
              <button 
                type="submit" 
                disabled={!newComment.trim() || isSendingComment} 
                className="absolute right-2 top-1/2 -translate-y-1/2 text-indigo-600 hover:text-indigo-800 disabled:opacity-50 p-1"
              >
                <Send size={18} />
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
