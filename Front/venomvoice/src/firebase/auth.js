// Firebase 인증 함수
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signOut as firebaseSignOut,
  onAuthStateChanged
} from 'firebase/auth';
import { auth } from './config';

// 회원가입 함수
export const signUp = async (email, password) => {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    return { user: userCredential.user, error: null };
  } catch (error) {
    console.error('회원가입 오류:', error.message);
    return { user: null, error: error.message };
  }
};

// 로그인 함수
export const signIn = async (email, password) => {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    return { user: userCredential.user, error: null };
  } catch (error) {
    console.error('로그인 오류:', error.message);
    return { user: null, error: error.message };
  }
};

// 로그아웃 함수
export const signOut = async () => {
  try {
    await firebaseSignOut(auth);
    return { success: true, error: null };
  } catch (error) {
    console.error('로그아웃 오류:', error.message);
    return { success: false, error: error.message };
  }
};

// 인증 상태 변경 감지 설정
export const subscribeToAuthChanges = (callback) => {
  return onAuthStateChanged(auth, (user) => {
    callback(user);
  });
};
