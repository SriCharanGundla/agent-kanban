import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from "react";
import { authApi, setToken, clearToken, getToken } from "@/lib/api";
import type { User, UserCreate, UserLogin, UserUpdate } from "@/types";

// ============================================================================
// Types
// ============================================================================

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: UserLogin) => Promise<void>;
  register: (data: UserCreate) => Promise<void>;
  logout: () => void;
  updateProfile: (data: UserUpdate) => Promise<void>;
}

// ============================================================================
// Context
// ============================================================================

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ============================================================================
// Provider Props
// ============================================================================

interface AuthProviderProps {
  children: React.ReactNode;
}

// ============================================================================
// Provider Component
// ============================================================================

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = getToken();
      
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await authApi.me();
        setUser(currentUser);
      } catch (error) {
        console.error("Failed to fetch user:", error);
        // Clear invalid token
        clearToken();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  // Login function
  const login = useCallback(async (credentials: UserLogin): Promise<void> => {
    setIsLoading(true);
    try {
      const tokens = await authApi.login(credentials);
      setToken(tokens.access_token);
      
      // Fetch user data
      const currentUser = await authApi.me();
      setUser(currentUser);
    } catch (error) {
      setUser(null);
      clearToken();
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Register function
  const register = useCallback(async (data: UserCreate): Promise<void> => {
    setIsLoading(true);
    try {
      // Register user
      await authApi.register(data);
      
      // Try auto-login after registration
      try {
        await login({
          email: data.email,
          password: data.password,
        });
      } catch (loginError) {
        // Registration succeeded but auto-login failed
        // Throw a special error so UI can handle it
        const error = new Error("REGISTRATION_SUCCESS_LOGIN_FAILED");
        (error as Error & { originalError?: unknown }).originalError = loginError;
        throw error;
      }
    } catch (error) {
      setUser(null);
      clearToken();
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [login]);

  // Logout function
  const logout = useCallback((): void => {
    setUser(null);
    clearToken();
  }, []);

  // Update profile function
  const updateProfile = useCallback(async (data: UserUpdate): Promise<void> => {
    setIsLoading(true);
    try {
      const updatedUser = await authApi.updateProfile(data);
      setUser(updatedUser);
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Memoize context value to prevent unnecessary re-renders
  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      register,
      logout,
      updateProfile,
    }),
    [user, isLoading, login, register, logout, updateProfile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ============================================================================
// Hook
// ============================================================================

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  
  return context;
}
