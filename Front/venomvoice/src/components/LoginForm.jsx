import { useState } from 'react';
import useAuthStore from '../store/authStore.js';

const LoginForm = () => {
  // 상태 관리
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // 인증 스토어에서 필요한 함수 가져오기
  const { signIn, signUp, isLoading, error } = useAuthStore();

  // 폼 제출 처리
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!email || !password) {
      setErrorMessage('이메일과 비밀번호를 모두, 입력해주세요.');
      return;
    }

    try {
      let result;
      
      if (isSignUp) {
        // 회원가입 처리
        result = await signUp(email, password);
      } else {
        // 로그인 처리
        result = await signIn(email, password);
      }

      if (!result.success) {
        setErrorMessage(result.error || '인증에 실패했습니다.');
      }
    } catch (err) {
      setErrorMessage('처리 중 오류가 발생했습니다: ' + err.message);
    }
  };

  return (
    <div className="login-form">
      <h2>{isSignUp ? '회원가입' : '로그인'}</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="email">이메일</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="이메일 주소를 입력하세요"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">비밀번호</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="비밀번호를 입력하세요"
            required
          />
        </div>
        
        {(errorMessage || error) && (
          <div className="error-message">
            {errorMessage || error}
          </div>
        )}
        
        <button type="submit" disabled={isLoading}>
          {isLoading ? '처리 중...' : isSignUp ? '가입하기' : '로그인'}
        </button>
      </form>
      
      <div className="form-switch">
        <button onClick={() => setIsSignUp(!isSignUp)}>
          {isSignUp ? '이미 계정이 있으신가요? 로그인하기' : '계정이 없으신가요? 회원가입하기'}
        </button>
      </div>
    </div>
  );
};

export default LoginForm;
