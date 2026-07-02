// Fetches the latest edition from the deployed web app's static JSON
// (public/editions/latest.json). Falls back to the bundled edition so the
// app always shows content, even offline or before you set apiBase.
import Constants from "expo-constants";
import bundled from "../assets/latest.json";

const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE ||
  Constants.expoConfig?.extra?.apiBase ||
  "";

export async function getLatestEdition() {
  if (API_BASE && !API_BASE.includes("YOUR-WEB-APP")) {
    try {
      const res = await fetch(`${API_BASE}/editions/latest.json`, {
        headers: { "cache-control": "no-cache" },
      });
      if (res.ok) return await res.json();
    } catch {
      // fall through to bundled
    }
  }
  return bundled;
}
