import { useAuthContext } from '../context/AuthContext';

/**
 * Custom hook for accessing authentication state and actions.
 * Must be used within an AuthProvider.
 *
 * @returns {{ user: Object|null, isAuth: boolean, loading: boolean, login: Function, register: Function, logout: Function }}
 */
export function useAuth() {
  const context = useAuthContext();
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
