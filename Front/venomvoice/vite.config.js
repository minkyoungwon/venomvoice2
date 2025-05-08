import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // env 변수 로드
  const env = loadEnv(mode, process.cwd());
  
  return {
    plugins: [react()],
    // 개발 서버 설정
    server: {
      // 개발 시 자동으로 브라우저 열기
      open: true,
      // 호스트 설정
      host: true,
    },
    // 환경 변수 설정
    define: {
      '__APP_ENV__': JSON.stringify(env.APP_ENV),
    },
  }
})
