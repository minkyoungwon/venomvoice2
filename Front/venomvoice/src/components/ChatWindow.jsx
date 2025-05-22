import { useEffect, useState, useRef } from 'react';
import useChatStore from '../store/chatStore.js';
import useAuthStore from '../store/authStore.js';
import { getDeepSeekResponse, getDeepSeekApiKey } from '../api/deepseekService.js';
import axios from 'axios';
import Lottie from 'lottie-web';

const ChatWindow = () => {
  // 기존 상태 관리
  const [isInitialized, setIsInitialized] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const messagesEndRef = useRef(null);
  
  // 음성 관련 상태
  const [isListening, setIsListening] = useState(false);
  const [conversationStatus, setConversationStatus] = useState('대기 중'); // '대기 중', '녹음 중', 'STT 처리 중', 'AI 응답 생성 중', 'TTS 재생 중'
  
  // 음성 관련 참조 변수
  const audioRef = useRef(null);
  const animationRef = useRef(null);
  const animationContainerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  
  // VAD 관련 변수
  const vadTimeoutRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  
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
  
  // Lottie 애니메이션 초기화
  useEffect(() => {
    if (animationContainerRef.current) {
      animationRef.current = Lottie.loadAnimation({
        container: animationContainerRef.current,
        renderer: 'svg',
        loop: true,
        autoplay: false,
        path: '/assets/voice-animation.json', // Lottie JSON 파일 경로
      });
      
      return () => animationRef.current?.destroy();
    }
  }, []);
  
  // 상태에 따른 애니메이션 제어
  useEffect(() => {
    if (conversationStatus === '녹음 중' || conversationStatus === 'TTS 재생 중') {
      animationRef.current?.play();
    } else {
      animationRef.current?.stop();
    }
  }, [conversationStatus]);

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

  // 오디오 컨텍스트 초기화
  const initAudioContext = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
    }
  };
  
  // VAD (Voice Activity Detection) 설정
  const setupVAD = (stream) => {
    initAudioContext();
    
    const source = audioContextRef.current.createMediaStreamSource(stream);
    source.connect(analyserRef.current);
    
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const checkAudioLevel = () => {
      if (!isListening) return;
      
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((acc, val) => acc + val, 0) / bufferLength;
      
      // 음성 감지 임계값 (조정 필요)
      if (average > 20) {
        console.log('음성 감지! 평균 레벨:', average);
        
        // TTS 재생 중이라면 일시 정지
        if (conversationStatus === 'TTS 재생 중' && audioRef.current) {
          audioRef.current.pause();
          setConversationStatus('녹음 중');
          console.log('사용자 음성 감지: TTS 재생 중단');
        }
        
        // 타임아웃 재설정
        clearTimeout(vadTimeoutRef.current);
        vadTimeoutRef.current = setTimeout(() => {
          console.log('침묵 감지: 녹음 중지');
          if (conversationStatus === '녹음 중') {
            stopRecording();
          }
        }, 1500); // 1.5초 침묵 후 녹음 중지
      }
      
      requestAnimationFrame(checkAudioLevel);
    };
    
    checkAudioLevel();
  };
  
  // 녹음 시작
  const startRecording = async () => {
    if (!currentConversation) return;
    
    try {
      setConversationStatus('녹음 중');
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setupVAD(stream);
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processAudio(audioBlob);
      };
      
      mediaRecorder.start();
      setIsListening(true);
      
      // 30초 후 자동 중지
      setTimeout(() => {
        if (mediaRecorderRef.current?.state === 'recording') {
          stopRecording();
        }
      }, 30000);
      
    } catch (err) {
      console.error('녹음 시작 오류:', err);
      setConversationStatus('대기 중');
    }
  };
  
  // 녹음 중지
  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsListening(false);
      setConversationStatus('STT 처리 중');
      
      clearTimeout(vadTimeoutRef.current);
      
      // 스트림 트랙 중지
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };
  
  // 오디오 처리 (STT 및 응답 생성)
  const processAudio = async (audioBlob) => {
    try {
      setConversationStatus('STT 처리 중');
      setIsProcessing(true);
      
      // 오디오 파일 생성
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      
      // STT 요청
      const sttResponse = await axios.post('http://localhost:8000/api/stt', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const text = sttResponse.data.text;
      console.log('STT 결과:', text);
      
      // 사용자 메시지 저장
      const userMessage = {
        content: text,
        role: "user",
      };
      
      await addMessage(userMessage);
      
      // DeepSeek API 요청
      setConversationStatus('AI 응답 생성 중');
      
      const apiKey = getDeepSeekApiKey();
      
      if (!apiKey) {
        throw new Error('DeepSeek API 키가 설정되지 않았습니다.');
      }
      
      const response = await getDeepSeekResponse(text, messages, apiKey);
      
      let botResponse;
      if (response.success) {
        // 챗봇 응답 저장
        botResponse = {
          content: response.content,
          role: "assistant",
        };
      } else {
        // 에러 메시지 표시
        botResponse = {
          content: `죄송합니다, 응답을 생성하는 중 오류가 발생했습니다: ${response.error}`,
          role: "assistant",
        };
      }
      
      await addMessage(botResponse);
      
      // TTS 요청
      setConversationStatus('TTS 생성 중');
      
      const ttsResponse = await axios.post('http://localhost:8000/api/tts', {
        text: botResponse.content,
        language: 'ko'
      }, {
        responseType: 'blob'
      });
      
      // 오디오 재생
      const audioUrl = URL.createObjectURL(new Blob([ttsResponse.data], { type: 'audio/wav' }));
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.onplay = () => setConversationStatus('TTS 재생 중');
        audioRef.current.onended = () => setConversationStatus('대기 중');
        audioRef.current.onerror = () => setConversationStatus('대기 중');
        audioRef.current.play();
      }
      
    } catch (err) {
      console.error('오디오 처리 오류:', err);
      setConversationStatus('대기 중');
    } finally {
      setIsProcessing(false);
    }
  };

  // 대화 선택 처리
  const handleConversationSelect = async (conversationId) => {
    if (isProcessing) return;
    
    await fetchConversation(conversationId);
    setSelectedConversation(conversationId);
  };

  // 메시지 전송 및 DeepSeek API 호출 (텍스트 입력용)
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
      
      let botResponse;
      if (response.success) {
        // 챗봇 응답 저장
        botResponse = {
          content: response.content,
          role: "assistant",
        };
      } else {
        // 에러 메시지 표시
        botResponse = {
          content: `죄송합니다, 응답을 생성하는 중 오류가 발생했습니다: ${response.error}`,
          role: "assistant",
        };
      }
      
      await addMessage(botResponse);
      
      // TTS 요청
      const ttsResponse = await axios.post('http://localhost:8000/api/tts', {
        text: botResponse.content,
        language: 'ko'
      }, {
        responseType: 'blob'
      });
      
      // 오디오 재생
      const audioUrl = URL.createObjectURL(new Blob([ttsResponse.data], { type: 'audio/wav' }));
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.onplay = () => setConversationStatus('TTS 재생 중');
        audioRef.current.onended = () => setConversationStatus('대기 중');
        audioRef.current.play();
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
          <div className="status-indicator">
            {conversationStatus}
          </div>
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
        
        {/* 음성 애니메이션 영역 */}
        <div 
          className="animation-container" 
          ref={animationContainerRef}
          style={{ 
            width: '100px', 
            height: '100px', 
            margin: '10px auto',
            display: isListening || conversationStatus === 'TTS 재생 중' ? 'block' : 'none'
          }}
        />
        
        {/* 오디오 플레이어 (숨김) */}
        <audio ref={audioRef} style={{ display: 'none' }} />
        
        {/* 입력 영역 */}
        <div className="chat-input-container">
          <div className="voice-controls">
            <button 
              className={`voice-button ${isListening ? 'recording' : ''}`}
              onClick={isListening ? stopRecording : startRecording}
              disabled={conversationStatus !== '대기 중' && conversationStatus !== '녹음 중'}
            >
              {isListening ? '종료' : '음성'}
            </button>
          </div>
          
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              value={inputMessage}
              onChange={handleInputChange}
              placeholder="메시지를 입력하세요..."
              disabled={isProcessing || isListening}
              className="chat-input"
            />
            <button 
              type="submit" 
              disabled={isProcessing || !inputMessage.trim() || isListening}
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