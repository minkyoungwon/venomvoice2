import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import Lottie from 'lottie-web';
import { create } from 'zustand';

// 상태 관리를 위한 Zustand 스토어
const useVoiceStore = create((set) => ({
  status: '대기 중', // '대기 중', '녹음 중', 'STT 대기', '요약 대기', 'TTS 대기', 'TTS 재생 중'
  setStatus: (status) => set({ status }),
}));

const VoiceInteraction = () => {
  const { status, setStatus } = useVoiceStore();
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [error, setError] = useState(null);
  
  const audioRef = useRef(null);
  const animationRef = useRef(null);
  const animationContainerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  
  // VAD 관련 변수
  const vadTimeoutRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  
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
    if (status === '녹음 중' || status === 'TTS 재생 중') {
      animationRef.current?.play();
    } else {
      animationRef.current?.stop();
    }
  }, [status]);
  
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
        if (status === 'TTS 재생 중' && audioRef.current) {
          audioRef.current.pause();
          setStatus('녹음 중');
          console.log('사용자 음성 감지: TTS 재생 중단');
        }
        
        // 타임아웃 재설정
        clearTimeout(vadTimeoutRef.current);
        vadTimeoutRef.current = setTimeout(() => {
          console.log('침묵 감지: 녹음 중지');
          if (status === '녹음 중') {
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
    try {
      setError(null);
      setStatus('녹음 중');
      
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
      setError('마이크 접근 오류: ' + err.message);
      setStatus('대기 중');
      console.error('녹음 시작 오류:', err);
    }
  };
  
  // 녹음 중지
  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsListening(false);
      setStatus('STT 대기');
      
      clearTimeout(vadTimeoutRef.current);
      
      // 스트림 트랙 중지
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };
  
  // 오디오 처리 (STT 및 응답 생성)
  const processAudio = async (audioBlob) => {
    try {
      setStatus('STT 대기');
      
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
      setTranscript(text);
      console.log('STT 결과:', text);
      
      // DeepSeek API 요청
      setStatus('요약 대기');
      const aiResponse = await axios.post('http://localhost:8000/api/chat', {
        message: text
      });
      
      const responseText = aiResponse.data.response;
      setResponse(responseText);
      console.log('AI 응답:', responseText);
      
      // TTS 요청
      setStatus('TTS 대기');
      const ttsResponse = await axios.post('http://localhost:8000/api/tts', {
        text: responseText,
        language: 'ko'
      }, {
        responseType: 'blob'
      });
      
      // 오디오 재생
      const audioUrl = URL.createObjectURL(new Blob([ttsResponse.data], { type: 'audio/wav' }));
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.onplay = () => setStatus('TTS 재생 중');
        audioRef.current.onended = () => setStatus('대기 중');
        audioRef.current.onerror = () => {
          setError('오디오 재생 오류');
          setStatus('대기 중');
        };
        audioRef.current.play();
      }
      
    } catch (err) {
      setError('처리 오류: ' + (err.response?.data?.detail || err.message));
      setStatus('대기 중');
      console.error('오디오 처리 오류:', err);
    }
  };

  return (
    <div className="voice-interaction-container">
      <h2>음성 대화 테스트</h2>
      
      <div className="status-indicator">
        현재 상태: <strong>{status}</strong>
      </div>
      
      <div 
        className="animation-container" 
        ref={animationContainerRef}
        style={{ width: '100px', height: '100px', margin: '20px auto' }}
      />
      
      <div className="controls">
        <button
          onClick={isListening ? stopRecording : startRecording}
          disabled={status === 'STT 대기' || status === '요약 대기' || status === 'TTS 대기'}
        >
          {isListening ? '녹음 중지' : '녹음 시작'}
        </button>
      </div>
      
      {error && (
        <div className="error-message" style={{ color: 'red', marginTop: '10px' }}>
          {error}
        </div>
      )}
      
      <div className="transcript" style={{ marginTop: '20px' }}>
        <h3>인식된 텍스트:</h3>
        <p>{transcript || '(아직 음성이 인식되지 않았습니다)'}</p>
      </div>
      
      <div className="response" style={{ marginTop: '20px' }}>
        <h3>AI 응답:</h3>
        <p>{response || '(아직 응답이 생성되지 않았습니다)'}</p>
      </div>
      
      <audio ref={audioRef} style={{ display: 'none' }} />
      
      <div className="instructions" style={{ marginTop: '20px', fontSize: '14px' }}>
        <p><strong>사용 방법:</strong></p>
        <ol>
          <li>'녹음 시작' 버튼을 클릭하여 말하기 시작하세요</li>
          <li>말을 멈추면 자동으로 녹음이 중지됩니다</li>
          <li>AI가 응답을 생성하고 음성으로 변환합니다</li>
          <li>AI가 말하는 도중에도 말하면 AI 음성이 중단되고 사용자 음성이 녹음됩니다</li>
        </ol>
      </div>
    </div>
  );
};

export default VoiceInteraction;