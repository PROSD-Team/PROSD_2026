export interface UserSession {
  id: string;
  email: string;
}

const STORAGE_KEY = "prosd.user";

export const getStoredUser = (): UserSession | null => {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as UserSession;
    if (!parsed?.id || !parsed?.email) return null;
    return parsed;
  } catch {
    return null;
  }
};

export const setStoredUser = (user: UserSession) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
};

export const clearStoredUser = () => {
  localStorage.removeItem(STORAGE_KEY);
};
