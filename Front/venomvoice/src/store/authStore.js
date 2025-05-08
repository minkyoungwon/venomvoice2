// Auth 상태 관리 스토어
import { create } from 'zustand';
import { subscribeToAuthChanges, signIn, signUp, signOut } from '../firebase/auth';
import { createOrUpdateUser, getUserProfile } from '../firebase/firestore';

const useAuthStore = create((set, get) => ({
  // 상태
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  
  // 초기화 함수
  initialize: () => {
    const unsubscribe = subscribeToAuthChanges(async (user) => {
      if (user) {
        // 인증된 사용자가 있으면 프로필 정보 가져오기
        const { data } = await getUserProfile(user.uid);
        set({ 
          user: { ...user, profile: data || {} },
          isAuthenticated: true,
          isLoading: false,
          error: null 
        });
      } else {
        set({ 
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null 
        });
      }
    });
    
    // 클린업 함수 반환 (컴포넌트 언마운트 시 실행)
    return unsubscribe;
  },
  
  // 회원가입
  signUp: async (email, password, profileData = {}) => {
    set({ isLoading: true, error: null });
    
    const { user, error } = await signUp(email, password);
    
    if (user) {
      // 사용자 프로필 생성
      await createOrUpdateUser(user.uid, {
        email: user.email,
        createdAt: new Date(),
        ...profileData
      });
      
      set({ 
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null 
      });
      
      return { success: true };
    } else {
      set({ 
        isLoading: false,
        error 
      });
      
      return { success: false, error };
    }
  },
  
  // 로그인
  signIn: async (email, password) => {
    set({ isLoading: true, error: null });
    
    const { user, error } = await signIn(email, password);
    
    if (user) {
      const { data } = await getUserProfile(user.uid);
      
      set({ 
        user: { ...user, profile: data || {} },
        isAuthenticated: true,
        isLoading: false,
        error: null 
      });
      
      return { success: true };
    } else {
      set({ 
        isLoading: false,
        error 
      });
      
      return { success: false, error };
    }
  },
  
  // 로그아웃
  signOut: async () => {
    set({ isLoading: true, error: null });
    
    const { success, error } = await signOut();
    
    if (success) {
      set({ 
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null 
      });
      
      return { success: true };
    } else {
      set({ 
        isLoading: false,
        error 
      });
      
      return { success: false, error };
    }
  },
  
  // 사용자 정보 업데이트
  updateUserProfile: async (profileData) => {
    const { user } = get();
    
    if (!user) {
      return { success: false, error: '로그인이 필요합니다.' };
    }
    
    const { success, error } = await createOrUpdateUser(user.uid, profileData);
    
    if (success) {
      const { data } = await getUserProfile(user.uid);
      
      set({ 
        user: { ...user, profile: data || {} }
      });
      
      return { success: true };
    } else {
      return { success: false, error };
    }
  }
}));

export default useAuthStore;
