import React, { useState, useRef } from 'react';
import axios from 'axios';

const TTSTest = () => {
  const [text, setText] = useState('안녕하세요, Zonos TTS 테스트입니다.');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const audioRef = useRef(null);

  const handleTestTTS = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('http://localhost:8000/api/tts', {
        text,
        language: 'ko'
      }, {
        responseType: 'blob'
      });
      
      // Blob URL 생성
      const audioBlob = new Blob([response.data], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // 오디오 엘리먼트 업데이트 및 재생
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
      }
      
      console.log('TTS 성공!');
    } catch (err) {
      setError('TTS 처리 중 오류가 발생했습니다: ' + (err.response?.data?.detail || err.message));
      console.error('TTS 오류:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="tts-test-container">
      <h2>Zonos TTS 테스트</h2>
      
      <div className="input-group">
        <textarea 
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="TTS로 변환할 텍스트를 입력하세요"
          rows={4}
          style={{ width: '100%', marginBottom: '10px' }}
        />
      </div>
      
      <button 
        onClick={handleTestTTS}
        disabled={isLoading || !text.trim()}
      >
        {isLoading ? '처리 중...' : 'TTS 테스트'}
      </button>
      
      {error && (
        <div className="error-message" style={{ color: 'red', marginTop: '10px' }}>
          {error}
        </div>
      )}
      
      <div className="audio-player" style={{ marginTop: '20px' }}>
        <audio ref={audioRef} controls />
      </div>
      
      <div className="instructions" style={{ marginTop: '20px', fontSize: '14px' }}>
        <p><strong>테스트 방법:</strong></p>
        <ol>
          <li>텍스트를 입력하세요 (기본 텍스트가 제공됩니다)</li>
          <li>'TTS 테스트' 버튼을 클릭하세요</li>
          <li>변환된 음성이 자동으로 재생됩니다</li>
          <li>긴 텍스트의 경우 자동으로 분할 처리됩니다</li>
        </ol>
      </div>
    </div>
  );
};

export default TTSTest;