import { useEffect, useState } from 'react';
import './App.css';
import LoginForm from './components/LoginForm';
import ChatWindow from './components/ChatWindow';
import useAuthStore from './store/authStore.js';

function App() {
  const [unsubscribe, setUnsubscribe] = useState(null);
  
  // 인증 상태 가져오기
  const { isAuthenticated, isLoading, user, initialize } = useAuthStore();

  // 컴포넌트 마운트 시 인증 상태 구독
  useEffect(() => {
    const authUnsubscribe = initialize();
    setUnsubscribe(() => authUnsubscribe);
    
    // 컴포넌트 언마운트 시 구독 해제
    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [initialize]);

  // 로딩 중 화면
  if (isLoading) {
    return (
      <div className="app loading">
        <div className="loading-container">
          <h2>로딩 중...</h2>
          <p>Firebase 연결을 확인하고 있습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Venom Voice</h1>
        {isAuthenticated && user && (
          <div className="user-info">
            <span>{user.email}</span>
            <button onClick={() => useAuthStore.getState().signOut()}>
              로그아웃
            </button>
          </div>
        )}
      </header>
      
      <main className="app-main">
        {isAuthenticated ? (
          <div className="authenticated-content">
            <aside className="app-sidebar">
              <div className="firebase-test-panel">
                <h3>Firebase 연결 상태</h3>
                <div className="status-item">
                  <span className="status-label">인증:</span>
                  <span className="status-value success">연결됨</span>
                </div>
                <div className="status-item">
                  <span className="status-label">사용자 ID:</span>
                  <span className="status-value">{user.uid}</span>
                </div>
                <div className="status-item">
                  <span className="status-label">이메일:</span>
                  <span className="status-value">{user.email}</span>
                </div>
              </div>
            </aside>
            
            <section className="app-content">
              <ChatWindow />
            </section>
          </div>
        ) : (
          <div className="login-container">
            <LoginForm />
          </div>
        )}
      </main>
      
      <footer className="app-footer">
        <p>Venom Voice - Firebase 연동 테스트</p>
      </footer>
    </div>
  );
}

export default App;
