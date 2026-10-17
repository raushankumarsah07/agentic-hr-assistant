const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
async function request(path, options) {
  let response;
  try {
    response = await fetch(`${API}${path}`, options);
  } catch {
    throw new Error(`Backend is offline. Start FastAPI at ${API}.`);
  }
  if (!response.ok) {
    let detail = "";
    try { detail = (await response.json()).detail || ""; } catch {}
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json();
}
export async function sendMessage(payload) {
  return request("/api/chat", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
}
export async function getThread(id) {
  try { return await request(`/api/threads/${id}`); } catch { return null; }
}
export async function getSlots() {
  return request("/api/slots");
}
export async function checkHealth() { return request("/api/health"); }
