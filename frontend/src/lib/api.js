const BASE = "/api";

export async function getEphemeris(month, day) {
  const res = await fetch(`${BASE}/ephemeris/${month}/${day}`);
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}

export async function searchEphemeris(query) {
  const res = await fetch(`${BASE}/ephemeris/search?query=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}