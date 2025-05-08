// Firestore 데이터베이스 함수
import { 
  collection,
  doc,
  setDoc,
  getDoc,
  getDocs,
  addDoc,
  updateDoc,
  deleteDoc,
  query,
  where,
  orderBy,
  limit,
} from 'firebase/firestore';
import { firestore } from './config';

// 사용자 프로필 생성/업데이트
export const createOrUpdateUser = async (userId, userData) => {
  try {
    const userRef = doc(firestore, 'users', userId);
    await setDoc(userRef, userData, { merge: true });
    return { success: true, error: null };
  } catch (error) {
    console.error('사용자 정보 저장 오류:', error.message);
    return { success: false, error: error.message };
  }
};

// 사용자 정보 가져오기
export const getUserProfile = async (userId) => {
  try {
    const userRef = doc(firestore, 'users', userId);
    const userSnap = await getDoc(userRef);
    
    if (userSnap.exists()) {
      return { data: userSnap.data(), error: null };
    } else {
      return { data: null, error: '사용자를 찾을 수 없습니다.' };
    }
  } catch (error) {
    console.error('사용자 정보 조회 오류:', error.message);
    return { data: null, error: error.message };
  }
};

// 대화 목록 가져오기
export const getUserConversations = async (userId) => {
  try {
    console.log('사용자 대화 목록 조회 시작:', userId);
    const q = query(
      collection(firestore, 'conversations'),
      where('userId', '==', userId),
      orderBy('createdAt', 'desc')
    );
    
    console.log('쉷업한 쿼리:', q);
    const querySnapshot = await getDocs(q);
    console.log('쿼리 결과 크기:', querySnapshot.size);
    
    const conversations = [];
    
    querySnapshot.forEach((doc) => {
      const data = doc.data();
      console.log('가져온 대화 데이터:', doc.id, data);
      conversations.push({
        id: doc.id,
        ...data
      });
    });
    
    console.log('최종 대화 목록:', conversations.length);
    return { data: conversations, error: null };
  } catch (error) {
    console.error('대화 목록 조회 오류:', error.message);
    return { data: [], error: error.message };
  }
};

// 새 대화 생성
export const createConversation = async (conversationData) => {
  try {
    const docRef = await addDoc(collection(firestore, 'conversations'), {
      ...conversationData,
      createdAt: new Date(),
    });
    
    return { id: docRef.id, error: null };
  } catch (error) {
    console.error('대화 생성 오류:', error.message);
    return { id: null, error: error.message };
  }
};

// 대화 내용 업데이트 (메시지 추가)
export const updateConversation = async (conversationId, updatedData) => {
  try {
    const conversationRef = doc(firestore, 'conversations', conversationId);
    await updateDoc(conversationRef, updatedData);
    
    return { success: true, error: null };
  } catch (error) {
    console.error('대화 업데이트 오류:', error.message);
    return { success: false, error: error.message };
  }
};

// 대화 삭제
export const deleteConversation = async (conversationId) => {
  try {
    await deleteDoc(doc(firestore, 'conversations', conversationId));
    return { success: true, error: null };
  } catch (error) {
    console.error('대화 삭제 오류:', error.message);
    return { success: false, error: error.message };
  }
};

// 대화 정보 가져오기
export const getConversation = async (conversationId) => {
  try {
    console.log('대화 가져오기 시작:', conversationId);
    const conversationRef = doc(firestore, 'conversations', conversationId);
    const conversationSnap = await getDoc(conversationRef);
    
    if (conversationSnap.exists()) {
      const data = conversationSnap.data();
      console.log('가져온 대화 데이터:', data);
      console.log('대화 메시지 수:', data.messages ? data.messages.length : 0);
      
      // 메시지 에 아무것도 없는 경우 빈 배열로 초기화
      const formattedData = {
        id: conversationSnap.id,
        ...data,
        messages: data.messages || []
      };
      
      return { data: formattedData, error: null };
    } else {
      console.log('대화를 찾을 수 없음:', conversationId);
      return { data: null, error: '대화를 찾을 수 없습니다.' };
    }
  } catch (error) {
    console.error('대화 조회 오류:', error.message);
    return { data: null, error: error.message };
  }
};
