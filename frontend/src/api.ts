// Единая точка общения с backend. Токен храним в localStorage.
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const TOKEN_KEY = "aispace_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export type Role = "user" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  phone: string | null;
  role: Role;
  is_active: boolean;
  created_at: string;
  telegram_linked?: boolean;
}

export type TransferStatus = "pending" | "accepted" | "rejected" | "cancelled";

export interface Transfer {
  id: number;
  status: TransferStatus;
  created_at: string;
  resolved_at: string | null;
  room_name: string;
  booking: {
    id: number;
    title: string;
    room_id: number;
    start_time: string;
    end_time: string;
  };
  from_user: { id: number; full_name: string; email: string };
  to_user: { id: number; full_name: string; email: string };
  new_title: string | null;
  new_comment: string | null;
  new_amenities: string[] | null;
  new_start_time: string | null;
  new_end_time: string | null;
}

export interface AdminUser extends User {
  bookings_count: number;
}

export interface Room {
  id: number;
  name: string;
  capacity: number;
  description: string | null;
  is_active: boolean;
}

export interface Amenity {
  id: string;
  label: string;
  icon: string;
}

export interface Booking {
  id: number;
  room_id: number;
  user_id: number;
  title: string;
  comment: string | null;
  amenities: string[];
  start_time: string;
  end_time: string;
  created_at: string;
}

export interface AdminBooking {
  id: number;
  title: string;
  comment: string | null;
  amenities: string[];
  start_time: string;
  end_time: string;
  created_at: string;
  room_id: number;
  room_name: string;
  user: { id: number; full_name: string; email: string };
}

export interface NameCount {
  label: string;
  count: number;
}
export interface DayCount {
  date: string;
  count: number;
}
export interface Analytics {
  total_bookings: number;
  upcoming_bookings: number;
  active_rooms: number;
  total_users: number;
  total_hours: number;
  per_room: NameCount[];
  per_day: DayCount[];
  top_users: NameCount[];
  amenities: NameCount[];
}

export interface BookingDraft {
  room_id: number | null;
  room_name: string | null;
  title: string | null;
  start_time: string | null;
  end_time: string | null;
  missing: string[];
  clarification: string | null;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail[0]?.msg ?? detail;
    } catch {
      /* тело не JSON */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

function jsonBody(data: unknown, method = "POST"): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  };
}

export const api = {
  register: (
    email: string,
    full_name: string,
    password: string,
    phone?: string,
  ) =>
    request<User>(
      "/auth/register",
      jsonBody({ email, full_name, password, phone: phone || null }),
    ),

  updateMe: (patch: { full_name?: string; phone?: string | null }) =>
    request<User>("/auth/me", jsonBody(patch, "PATCH")),

  telegramCode: () => request<{ code: string }>("/auth/me/telegram-code", { method: "POST" }),

  transfers: () =>
    request<{ incoming: Transfer[]; outgoing: Transfer[] }>("/transfers"),

  requestTransfer: (payload: {
    booking_id: number;
    new_title?: string | null;
    new_comment?: string | null;
    new_amenities?: string[] | null;
    new_start_time?: string | null;
    new_end_time?: string | null;
  }) => request<Transfer>("/transfers", jsonBody(payload)),

  resolveTransfer: (id: number, action: "accept" | "reject" | "cancel") =>
    request<Transfer>(`/transfers/${id}/${action}`, { method: "POST" }),

  login: async (email: string, password: string) => {
    const form = new URLSearchParams({ username: email, password });
    const data = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    tokenStore.set(data.access_token);
  },

  me: () => request<User>("/auth/me"),

  // --- Комнаты ---
  rooms: (includeInactive = false) =>
    request<Room[]>(`/rooms${includeInactive ? "?include_inactive=true" : ""}`),

  createRoom: (r: { name: string; capacity: number; description?: string | null }) =>
    request<Room>("/rooms", jsonBody(r)),

  updateRoom: (
    id: number,
    r: Partial<Pick<Room, "name" | "capacity" | "description" | "is_active">>,
  ) => request<Room>(`/rooms/${id}`, jsonBody(r, "PATCH")),

  archiveRoom: (id: number) => request<Room>(`/rooms/${id}`, { method: "DELETE" }),

  // --- Допы ---
  amenities: () => request<Amenity[]>("/amenities"),

  // --- Пользователи (админ) ---
  users: () => request<AdminUser[]>("/users"),

  updateUser: (id: number, patch: { role?: Role; is_active?: boolean }) =>
    request<AdminUser>(`/users/${id}`, jsonBody(patch, "PATCH")),

  // --- Брони ---
  bookings: (params: { room_id?: number; date_from?: string; date_to?: string }) => {
    const q = new URLSearchParams();
    if (params.room_id != null) q.set("room_id", String(params.room_id));
    if (params.date_from) q.set("date_from", params.date_from);
    if (params.date_to) q.set("date_to", params.date_to);
    return request<Booking[]>(`/bookings?${q.toString()}`);
  },

  myBookings: () => request<Booking[]>("/bookings/my"),

  adminBookings: (params: {
    room_id?: number;
    date_from?: string;
    date_to?: string;
  }) => {
    const q = new URLSearchParams();
    if (params.room_id != null) q.set("room_id", String(params.room_id));
    if (params.date_from) q.set("date_from", params.date_from);
    if (params.date_to) q.set("date_to", params.date_to);
    return request<AdminBooking[]>(`/bookings/all?${q.toString()}`);
  },

  analytics: () => request<Analytics>("/analytics"),

  createBooking: (b: {
    room_id: number;
    title: string;
    comment?: string | null;
    amenities?: string[];
    start_time: string;
    end_time: string;
  }) => request<Booking>("/bookings", jsonBody(b)),

  cancelBooking: (id: number) =>
    request<void>(`/bookings/${id}`, { method: "DELETE" }),

  parseNL: (text: string) => request<BookingDraft>("/nl/parse", jsonBody({ text })),
};
