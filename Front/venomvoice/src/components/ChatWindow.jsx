import { useEffect, useState } from 'react';
import useChatStore from '../store/chatStore.js';
import useAuthStore from '../store/authStore.js';

const ChatWindow = () => {
  // 상태 관리
  const [isInitialized, setIsInitialized] = useState(false);
  
  // 인증 및 채팅 스토어
  const { user } = useAuthStore();
  const { 
    currentConversation, 
    messages, 
    createNewConversation, 
    fetchConversations,
    fetchConversation,
    addMessage,
    isLoading 
  } = useChatStore();

  // 컴포넌트 마운트 시 대화 목록 가져오기
  useEffect(() => {
    if (user && !isInitialized) {
      const initializeChat = async () => {
        // 사용자의 모든 대화 목록 가져오기
        const { success, data } = await fetchConversations(user.uid);
        
        // 대화가 있으면 첫 번째 대화 선택
        if (success && data && data.length > 0) {
          await fetchConversation(data[0].id);
        } else {
          // 대화가 없으면 새 대화 생성
          await createNewConversation(user.uid);
        }
        
        setIsInitialized(true);
      };
      
      initializeChat();
    }
  }, [user, isInitialized, fetchConversations, fetchConversation, createNewConversation]);

  // Firebase 연결 테스트를 위한 메시지 전송 (임시)
  const sendTestMessage = async () => {
    if (!currentConversation) return;
    
    const testMessage = {
      content: "안녕하세요! 테스트 메시지입니다.",
      role: "user",
    };
    
    await addMessage(testMessage);
    
    // 챗봇 응답 (시뮬레이션)
    setTimeout(async () => {
      const botResponse = {
        content: "테스트 응답입니다. Firebase 연결이 정상적으로 작동 중입니다.",
        role: "assistant",
      };
      
      await addMessage(botResponse);
    }, 1000);
  };

  // 대화가 로드되지 않은 경우
  if (!currentConversation) {
    return (
      <div className="chat-window">
        <div className="loading-message">
          {isLoading ? '대화를 불러오는 중...' : '대화를 시작해보세요.'}
        </div>
      </div>
    );
  }

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h3>{currentConversation.title || '새 대화'}</h3>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <p>새로운 대화를 시작해보세요!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div 
              key={message.id} 
              className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
            >
              <div className="message-content">
                {message.content}
              </div>
              <div className="message-timestamp">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
      </div>
      
      <div className="chat-controls">
        <button 
          className="test-button" 
          onClick={sendTestMessage}
          disabled={isLoading}
        >
          테스트 메시지 전송
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
