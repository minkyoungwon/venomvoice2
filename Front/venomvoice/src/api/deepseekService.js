// DeepSeek API 서비스
// src/api/deepseekService.js

// DeepSeek API 요청을 위한 기본 설정
const DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions';  // 실제 API URL로 변경 필요
const DEEPSEEK_MODEL = 'deepseek-chat';  // 실제 모델명으로 변경 필요

/**
 * DeepSeek API를 호출하여 텍스트 응답을 생성합니다.
 * @param {string} prompt - 사용자 입력 메시지
 * @param {Array} history - 이전 대화 내역 (선택적)
 * @param {string} apiKey - DeepSeek API 키
 * @returns {Promise<Object>} - 응답 객체
 */
export const getDeepSeekResponse = async (prompt, history = [], apiKey) => {
  try {
    // API 키 확인
    if (!apiKey) {
      throw new Error('DeepSeek API 키가 제공되지 않았습니다.');
    }
    
    // 대화 형식으로 메시지 구성
    const messages = [...formatChatHistory(history), {
      role: 'user',
      content: prompt
    }];
    
    // API 요청 설정
    const response = await fetch(DEEPSEEK_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: DEEPSEEK_MODEL,
        messages: messages,
        temperature: 0.7,
        max_tokens: 500
      })
    });
    
    // 응답 확인
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`DeepSeek API 오류: ${errorData.error?.message || response.statusText}`);
    }
    
    // 응답 데이터 파싱
    const data = await response.json();
    
    return {
      success: true,
      content: data.choices[0].message.content,
      data: data
    };
  } catch (error) {
    console.error('DeepSeek API 호출 실패:', error);
    return {
      success: false,
      error: error.message,
      content: null,
      data: null
    };
  }
};

/**
 * 채팅 히스토리를 DeepSeek API 형식에 맞게 변환합니다.
 * @param {Array} messages - 메시지 배열
 * @returns {Array} - 변환된 메시지 배열
 */
const formatChatHistory = (messages) => {
  if (!messages || messages.length === 0) return [];
  
  // 최근 10개 메시지만 사용 (컨텍스트 제한을 위해)
  const recentMessages = messages.slice(-10);
  
  // DeepSeek API 형식에 맞게 변환
  return recentMessages.map(msg => ({
    role: msg.role === 'user' ? 'user' : 'assistant',
    content: msg.content
  }));
};

/**
 * 환경 변수에서 DeepSeek API 키를 가져옵니다.
 * 프로덕션에서는 안전한 방법으로 API 키를 관리해야 합니다.
 * @returns {string} API 키
 */
export const getDeepSeekApiKey = () => {
  // 실제 환경에서는 서버 사이드에서 안전하게 관리되어야 함
  return import.meta.env.VITE_DEEPSEEK_API_KEY;
};
