const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path) {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`Error ${res.status} en ${path}`);
  }
  return res.json();
}

export async function fetchStats() {
  return request("/stats");
}

export async function fetchStudents() {
  return request("/students");
}

export async function fetchStudent(code) {
  return request(`/students/${encodeURIComponent(code)}`);
}

export async function fetchWeaknesses() {
  return request("/weaknesses");
}

export async function fetchTopicWeakness() {
  return request("/topic-weakness");
}

export async function fetchExperiments() {
  return request("/experiments");
}

export async function fetchHealth() {
  return request("/health");
}

export function telegramDeepLink(botUsername, startParam = "UEBOL-3A") {
  const bot = botUsername || import.meta.env.VITE_TELEGRAM_BOT || "YachayBot";
  return `https://t.me/${bot}?start=${encodeURIComponent(startParam)}`;
}

export { API_URL };
