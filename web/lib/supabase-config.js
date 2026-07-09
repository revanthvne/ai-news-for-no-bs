// Supabase connection for the web app.
// URL + anon key are PUBLIC by design (the anon key ships to the browser and is
// protected by row-level security), so they're safe as baked-in defaults — this
// lets the site read from Supabase with no env-var setup. Environment variables
// still override them if set. The SERVICE key is secret and is NEVER hardcoded.
export const SUPABASE_URL =
  process.env.NEXT_PUBLIC_SUPABASE_URL || "https://zdycrjreufxzrrnqiyul.supabase.co";

export const SUPABASE_ANON =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpkeWNyanJldWZ4enJybnFpeXVsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MTY1NDYsImV4cCI6MjA5OTA5MjU0Nn0.WSQt4NEz_Fvamnw4PcgVIFM8SofeCTt4I2CxasQN_bU";

// Secret — only present when the env var is set (used by /approve). Never a literal.
export const SUPABASE_SERVICE = process.env.SUPABASE_SERVICE_KEY || "";
