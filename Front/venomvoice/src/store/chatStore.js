// 채팅 상태 관리 스토어
import { create } from 'zustand';
import { 
  createConversation,
  updateConversation,
  getConversation,
  getUserConversations,
  deleteConversation
} from '../firebase/firestore';

const useChatStore = create((set, get) => ({
  // 상태
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  error: null,
  recordingState: 'idle', // 'idle', 'recording', 'processing'
  processingState: 'idle', // 'idle', 'stt', 'ai', 'tts'
  
  // 메시지 목록 초기화
  setMessages: (messages) => {
    set({ messages });
  },
  
  // 상태 설정
  setRecordingState: (state) => {
    set({ recordingState: state });
  },
  
  // 처리 상태 설정
  setProcessingState: (state) => {
    set({ processingState: state });
  },
  
  // 대화 목록 가져오기
  fetchConversations: async (userId) => {
    set({ isLoading: true, error: null });
    
    const { data, error } = await getUserConversations(userId);
    
    if (data) {
      set({ 
        conversations: data,
        isLoading: false,
        error: null
      });
      
      return { success: true, data };
    } else {
      set({ 
        isLoading: false,
        error
      });
      
      return { success: false, error };
    }
  },
  
  // 특정 대화 가져오기
  fetchConversation: async (conversationId) => {
    set({ isLoading: true, error: null });
    
    const { data, error } = await getConversation(conversationId);
    
    if (data) {
      set({ 
        currentConversation: data,
        messages: data.messages || [],
        isLoading: false,
        error: null
      });
      
      return { success: true, data };
    } else {
      set({ 
        isLoading: false,
        error
      });
      
      return { success: false, error };
    }
  },
  
  // 새 대화 생성
  createNewConversation: async (userId, title = '새 대화') => {
    set({ isLoading: true, error: null });
    
    const conversationData = {
      userId,
      title,
      messages: [],
      createdAt: new Date()
    };
    
    const { id, error } = await createConversation(conversationData);
    
    if (id) {
      const newConversation = { id, ...conversationData };
      
      set({ 
        currentConversation: newConversation,
        messages: [],
        isLoading: false,
        error: null
      });
      
      // 대화 목록 업데이트
      const { conversations } = get();
      set({ conversations: [newConversation, ...conversations] });
      
      return { success: true, conversationId: id };
    } else {
      set({ 
        isLoading: false,
        error
      });
      
      return { success: false, error };
    }
  },
  
  // 메시지 추가
  addMessage: async (message) => {
    const { currentConversation, messages } = get();
    
    if (!currentConversation) {
      return { success: false, error: '현재 대화가 없습니다.' };
    }
    
    // 메시지 형식 지정
    const newMessage = {
      id: Date.now().toString(),
      content: message.content,
      contentType: message.contentType || 'text',
      role: message.role,
      timestamp: new Date()
    };
    
    // 로컬 상태 업데이트
    const updatedMessages = [...messages, newMessage];
    set({ messages: updatedMessages });
    
    // Firestore 업데이트
    const { success, error } = await updateConversation(
      currentConversation.id, 
      { messages: updatedMessages }
    );
    
    if (!success) {
      set({ error });
      return { success: false, error };
    }
    
    return { success: true };
  },
  
  // 대화 제목 변경
  updateConversationTitle: async (title) => {
    const { currentConversation } = get();
    
    if (!currentConversation) {
      return { success: false, error: '현재 대화가 없습니다.' };
    }
    
    // Firestore 업데이트
    const { success, error } = await updateConversation(
      currentConversation.id, 
      { title }
    );
    
    if (success) {
      // 로컬 상태 업데이트
      const updatedConversation = { ...currentConversation, title };
      set({ currentConversation: updatedConversation });
      
      // 대화 목록 업데이트
      const { conversations } = get();
      const updatedConversations = conversations.map(conv => 
        conv.id === currentConversation.id ? updatedConversation : conv
      );
      
      set({ conversations: updatedConversations });
      
      return { success: true };
    } else {
      set({ error });
      return { success: false, error };
    }
  },
  
  // 대화 삭제
  deleteCurrentConversation: async () => {
    const { currentConversation } = get();
    
    if (!currentConversation) {
      return { success: false, error: '현재 대화가 없습니다.' };
    }
    
    // Firestore에서 삭제
    const { success, error } = await deleteConversation(currentConversation.id);
    
    if (success) {
      // 로컬 상태 업데이트
      const { conversations } = get();
      const updatedConversations = conversations.filter(
        conv => conv.id !== currentConversation.id
      );
      
      set({ 
        conversations: updatedConversations,
        currentConversation: null,
        messages: []
      });
      
      return { success: true };
    } else {
      set({ error });
      return { success: false, error };
    }
  },
  
  // 상태 초기화
  resetState: () => {
    set({
      currentConversation: null,
      messages: [],
      isLoading: false,
      error: null,
      recordingState: 'idle',
      processingState: 'idle'
    });
  }
}));

export default useChatStore;
