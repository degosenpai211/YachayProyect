const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, options);
  if (!res.ok) {
    throw new Error(`Error ${res.status} en ${path}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export async function fetchStats() {
  return request("/stats");
}

export async function fetchStudents(course) {
  const q = course ? `?course=${encodeURIComponent(course)}` : "";
  return request(`/students${q}`);
}

export async function fetchStudent(code) {
  return request(`/students/${encodeURIComponent(code)}`);
}

export async function fetchWeaknesses(course) {
  const q = course ? `?course=${encodeURIComponent(course)}` : "";
  return request(`/weaknesses${q}`);
}

export async function fetchTopicWeakness() {
  return request("/topic-weakness");
}

export async function fetchExperiments(course) {
  const q = course ? `?course=${encodeURIComponent(course)}` : "";
  return request(`/experiments${q}`);
}

export async function resolveWeakness(id) {
  return request(`/weaknesses/${id}/resolve`, { method: "POST" });
}

export async function updateExperiment(id, body) {
  return request(`/experiments/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function fetchHealth() {
  return request("/health");
}

export function telegramDeepLink(botUsername, startParam = "UEBOL-3A-12") {
  const bot = botUsername || import.meta.env.VITE_TELEGRAM_BOT || "YachayBot";
  return `https://t.me/${bot}?start=${encodeURIComponent(startParam)}`;
}

export { API_URL };
