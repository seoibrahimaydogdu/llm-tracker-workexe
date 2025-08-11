const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_API_KEY = import.meta.env.VITE_SUPABASE_API_KEY;

export const trackUserVisit = () => {
  fetch(`${SUPABASE_URL}/rest/v1/user_visits`, {
    method: "POST",
    headers: {
      apikey: SUPABASE_API_KEY,
      Authorization: `Bearer ${SUPABASE_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      url: window.location.pathname,
      referrer: document.referrer,
      user_agent: navigator.userAgent,
      session_id: localStorage.getItem("session_id") || generateSessionId(),
      timestamp: new Date().toISOString()
    })
  });
};

const generateSessionId = () => {
  const sid = Math.random().toString(36).substring(2);
  localStorage.setItem("session_id", sid);
  return sid;
};