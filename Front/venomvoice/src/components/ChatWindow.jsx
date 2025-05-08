import { useEffect, useState, useRef } from 'react';
import useChatStore from '../store/chatStore.js';
import useAuthStore from '../store/authStore.js';
import { getDeepSeekResponse, getDeepSeekApiKey } from '../api/deepseekService.js';

const ChatWindow = () => {
  // 상태 관리
  const [isInitialized, setIsInitialized] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const messagesEndRef = useRef(null);
  
  // 인증 및 채팅 스토어
  const { user } = useAuthStore();
  const { 
    conversations,
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
        console.log('대화 목록 초기화 시작');
        // 사용자의 모든 대화 목록 가져오기
        const { success, data } = await fetchConversations(user.uid);
        console.log('대화 목록 가져오기 결과:', success, data);
        
        // 대화가 있으면 첫 번째 대화 선택
        if (success && data && data.length > 0) {
          console.log('기존 대화 선택:', data[0].id);
          const convResult = await fetchConversation(data[0].id);
          console.log('대화 가져오기 결과:', convResult);
        } else {
          // 대화가 없으면 새 대화 생성
          console.log('새 대화 생성 중');
          await createNewConversation(user.uid);
        }
        
        setIsInitialized(true);
      };
      
      initializeChat();
    }
  }, [user, isInitialized, fetchConversations, fetchConversation, createNewConversation]);

  // 스크롤을 최신 메시지로 이동
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // 대화 선택 처리
  const handleConversationSelect = async (conversationId) => {
    if (isProcessing) return;
    
    await fetchConversation(conversationId);
    setSelectedConversation(conversationId);
  };

  // 메시지 전송 및 DeepSeek API 호출
  const sendMessage = async (messageText) => {
    if (!currentConversation || !messageText.trim() || isProcessing) return;
    
    setIsProcessing(true);
    
    // 사용자 메시지 저장
    const userMessage = {
      content: messageText,
      role: "user",
    };
    
    await addMessage(userMessage);
    
    try {
      // DeepSeek API 호출
      const apiKey = getDeepSeekApiKey();
      
      if (!apiKey) {
        throw new Error('DeepSeek API 키가 설정되지 않았습니다.');
      }
      
      const response = await getDeepSeekResponse(messageText, messages, apiKey);
      
      if (response.success) {
        // 챗봇 응답 저장
        const botResponse = {
          content: response.content,
          role: "assistant",
        };
        
        await addMessage(botResponse);
      } else {
        // 에러 메시지 표시
        const errorResponse = {
          content: `죄송합니다, 응답을 생성하는 중 오류가 발생했습니다: ${response.error}`,
          role: "assistant",
        };
        
        await addMessage(errorResponse);
      }
    } catch (error) {
      console.error('메시지 전송 오류:', error);
      
      // 에러 메시지 표시
      const errorResponse = {
        content: `죄송합니다, 예상치 못한 오류가 발생했습니다: ${error.message}`,
        role: "assistant",
      };
      
      await addMessage(errorResponse);
    } finally {
      setIsProcessing(false);
      setInputMessage('');
    }
  };
  
  // 입력 처리
  const handleInputChange = (e) => {
    setInputMessage(e.target.value);
  };
  
  // 메시지 제출 처리
  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputMessage);
  };
  
  // 새 대화 시작
  const startNewConversation = async () => {
    if (isProcessing || !user) return;
    
    const { success, conversationId } = await createNewConversation(user.uid);
    
    if (success) {
      // 환영 메시지 전송
      sendMessage("안녕하세요! 어떻게 도와드릴까요?");
    }
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
    <div className="chat-container">
      {/* 대화 목록 사이드바 */}
      <div className="conversations-sidebar">
        <div className="new-chat-button-container">
          <button 
            className="new-chat-button" 
            onClick={startNewConversation}
            disabled={isProcessing}
          >
            새 대화 시작
          </button>
        </div>
        
        <div className="conversations-list">
          <h3>대화 목록</h3>
          {conversations.length === 0 ? (
            <div className="no-conversations">
              대화 내역이 없습니다.
            </div>
          ) : (
            <ul>
              {conversations.map((conv) => (
                <li 
                  key={conv.id} 
                  className={`conversation-item ${currentConversation?.id === conv.id ? 'active' : ''}`}
                  onClick={() => handleConversationSelect(conv.id)}
                >
                  <div className="conversation-title">
                    {conv.title || '새 대화'}
                  </div>
                  <div className="conversation-date">
                    {conv.createdAt && conv.createdAt.toDate ? 
                      new Date(conv.createdAt.toDate()).toLocaleDateString() : 
                      new Date().toLocaleDateString()}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      
      {/* 채팅 창 */}
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
            <>
              {messages.map((message) => (
                <div 
                  key={message.id} 
                  className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
                >
                  <div className="message-content">
                    {message.content}
                  </div>
                  <div className="message-timestamp">
                    {message.timestamp && message.timestamp.toDate ? 
                      new Date(message.timestamp.toDate()).toLocaleTimeString() : 
                      new Date().toLocaleTimeString()}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
        
        <div className="chat-input-container">
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              value={inputMessage}
              onChange={handleInputChange}
              placeholder="메시지를 입력하세요..."
              disabled={isProcessing}
              className="chat-input"
            />
            <button 
              type="submit" 
              disabled={isProcessing || !inputMessage.trim()}
              className="send-button"
            >
              {isProcessing ? '처리 중...' : '전송'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
