import { createContext, useContext, useState, useEffect } from 'react';
import {
  loginUser,
  registerUser,
  logoutUser,
  getCurrentUser,
  setTokens,
  getToken,
  clearTokens,
} from '../services/api';

/**
 * @typedef {Object} AuthState
 * @property {Object|null}  user    - Current authenticated user profile.
 * @property {string|null}  token   - JWT access token (read from localStorage).
 * @property {boolean}      loading - True while the initial auth check runs.
 * @property {boolean}      isAuth  - Derived: true when both user and token exist.
 */

/**
 * @typedef {Object} AuthActions
 * @property {(email: string, password: string) => Promise<{success: boolean, error?: string}>} login
 * @property {(email: string, password: string, fullName: string) => Promise<{success: boolean, error?: string}>} register
 * @property {() => Promise<void>} logout
 * @property {() => Promise<void>} checkAuth
 */

/** @type {import('react').Context<AuthState & AuthActions>} */
const AuthContext = createContext(null);

/**
 * AuthProvider wraps the application and provides global
 * authentication state and actions via React Context.
 *
 * @param {Object} props
 * @param {import('react').ReactNode} props.children
 * @returns {JSX.Element}
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  /** Derived authentication flag. */
  const isAuth = !!user && !!token;

  /**
   * Validate the stored token on mount and hydrate user state.
   * Sets loading to false once complete regardless of outcome.
   */
  async function checkAuth() {
    try {
      const storedToken = getToken();
      if (!storedToken) {
        setLoading(false);
        return;
      }

      setToken(storedToken);
      const data = await getCurrentUser();
      setUser(data.user || data);
    } catch {
      clearTokens();
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }

  /**
   * Authenticate with email and password.
   * On success, persists tokens and sets user state.
   *
   * @param {string} email    - User email address.
   * @param {string} password - User password.
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  async function login(email, password) {
    try {
      const data = await loginUser(email, password);
      const accessToken = data.access_token || data.token;
      const refreshToken = data.refresh_token || '';

      setTokens(accessToken, refreshToken);
      setToken(accessToken);
      setUser(data.user || data);

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Login failed. Please try again.',
      };
    }
  }

  /**
   * Register a new account.
   * On success, persists tokens and sets user state.
   *
   * @param {string} email    - User email address.
   * @param {string} password - User password.
   * @param {string} fullName - User full name.
   * @returns {Promise<{success: boolean, error?: string}>}
   */
  async function register(email, password, fullName) {
    try {
      const data = await registerUser(email, password, fullName);
      const accessToken = data.access_token || data.token;
      const refreshToken = data.refresh_token || '';

      setTokens(accessToken, refreshToken);
      setToken(accessToken);
      setUser(data.user || data);

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Registration failed. Please try again.',
      };
    }
  }

  /**
   * Log out the current user.
   * Clears tokens and user state, then redirects to /login.
   */
  async function logout() {
    try {
      await logoutUser();
    } catch {
      // Silently ignore logout errors
    } finally {
      clearTokens();
      setUser(null);
      setToken(null);
      window.location.href = '/login';
    }
  }

  // Run auth check on initial mount
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    checkAuth();
  }, []);

  /** @type {AuthState & AuthActions} */
  const value = {
    user,
    token,
    loading,
    isAuth,
    login,
    register,
    logout,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Custom hook to consume the AuthContext.
 * Must be used within an AuthProvider.
 *
 * @returns {AuthState & AuthActions} Auth state and actions.
 * @throws {Error} If used outside of AuthProvider.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
