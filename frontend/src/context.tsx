import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, tokenStore, type Amenity, type User } from "./api";

interface AppState {
  user: User | null;
  loading: boolean;
  amenities: Amenity[];
  amenityMap: Record<string, Amenity>;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    name: string,
    password: string,
    phone?: string,
  ) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [amenities, setAmenities] = useState<Amenity[]>([]);

  const loadSession = useCallback(async () => {
    if (!tokenStore.get()) {
      setLoading(false);
      return;
    }
    try {
      setUser(await api.me());
    } catch {
      tokenStore.clear();
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  // Каталог допов нужен на многих страницах — грузим один раз после входа.
  useEffect(() => {
    if (user) api.amenities().then(setAmenities).catch(() => {});
  }, [user]);

  const login = useCallback(async (email: string, password: string) => {
    await api.login(email, password);
    setUser(await api.me());
  }, []);

  const register = useCallback(
    async (email: string, name: string, password: string, phone?: string) => {
      await api.register(email, name, password, phone);
      await api.login(email, password);
      setUser(await api.me());
    },
    [],
  );

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    setUser(await api.me());
  }, []);

  const amenityMap = useMemo(
    () => Object.fromEntries(amenities.map((a) => [a.id, a])),
    [amenities],
  );

  const value: AppState = {
    user,
    loading,
    amenities,
    amenityMap,
    login,
    register,
    logout,
    refreshUser,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useApp(): AppState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
