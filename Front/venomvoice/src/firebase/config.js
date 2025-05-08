// Firebase 설정 파일
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

// Firebase 환경 변수를 통한 설정
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
};

// Firebase 초기화
const app = initializeApp(firebaseConfig);

// 환경 변수 디버깅 (개발 모드에서만)
if (import.meta.env.DEV) {
  console.log('Firebase 설정:', {
    apiKeyExists: !!import.meta.env.VITE_FIREBASE_API_KEY,
    authDomainExists: !!import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectIdExists: !!import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucketExists: !!import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderIdExists: !!import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appIdExists: !!import.meta.env.VITE_FIREBASE_APP_ID,
    measurementIdExists: !!import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
  });
}

// Firebase 서비스 내보내기
export const auth = getAuth(app);
export const firestore = getFirestore(app);
export default app;
