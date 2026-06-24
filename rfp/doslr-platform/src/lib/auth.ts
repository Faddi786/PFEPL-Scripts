const AUTH_KEY = "doslr_auth_session";

export function loginSession(userId: string) {
  sessionStorage.setItem(
    AUTH_KEY,
    JSON.stringify({
      userId,
      loggedInAt: new Date().toISOString(),
    }),
  );
}

export function logoutSession() {
  sessionStorage.removeItem(AUTH_KEY);
}

export function isAuthenticated() {
  return Boolean(sessionStorage.getItem(AUTH_KEY));
}

export function getAuthUser() {
  const raw = sessionStorage.getItem(AUTH_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as { userId: string; loggedInAt: string };
  } catch {
    return null;
  }
}
