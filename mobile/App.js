import { useEffect, useState, useCallback } from "react";
import {
  SafeAreaView, ScrollView, View, Text, TouchableOpacity, Image,
  RefreshControl, Linking, StyleSheet, ActivityIndicator,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import { theme, SECTOR } from "./src/theme";
import { getLatestEdition } from "./src/api";
import { registerForPush } from "./src/notifications";

function verdictColor(v = "") {
  return theme.verdict[(v.split(/\s|—|-/)[0] || "").toUpperCase()] || theme.accent;
}

function Pill({ text, color }) {
  return (
    <View style={[styles.pill, { backgroundColor: color + "22" }]}>
      <Text style={{ color, fontWeight: "800", fontSize: 11 }}>{text}</Text>
    </View>
  );
}

function Section({ label, children }) {
  if (!children) return null;
  return (
    <View style={{ marginTop: 12 }}>
      <Text style={styles.sectionLabel}>{label}</Text>
      <Text style={styles.sectionBody}>{children}</Text>
    </View>
  );
}

function HeroImage({ s, sector }) {
  const placeholder = s.image_is_placeholder || !s.image_url || String(s.image_url).startsWith("data:");
  if (placeholder) {
    return (
      <View style={[styles.imgPlaceholder, { backgroundColor: (SECTOR[sector] || {}).color || "#334155" }]}>
        <Text style={styles.imgPlaceholderText}>{(SECTOR[sector] || {}).emoji} {sector}</Text>
      </View>
    );
  }
  return <Image source={{ uri: s.image_url }} style={styles.img} />;
}

function HeroCard({ s, idx, sector }) {
  const [open, setOpen] = useState(false);
  const cred = (s.credibility || "low").toLowerCase();
  return (
    <View style={styles.card}>
      <HeroImage s={s} sector={sector} />
      <View style={{ padding: 15 }}>
        <View style={styles.pillRow}>
          {s.verdict ? <Pill text={s.verdict} color={verdictColor(s.verdict)} /> : null}
          <Pill text={`${cred === "high" ? "✓ " : ""}${s.source_name || "source"} · ${cred}`} color={theme.cred[cred]} />
        </View>
        <Text style={styles.eyebrow}>STORY {idx}</Text>
        <Text style={styles.headline}>{s.headline}</Text>
        <Text style={styles.oneLiner}>🎬 {s.one_liner}</Text>
        <TouchableOpacity style={styles.deepBtn} onPress={() => setOpen((o) => !o)}>
          <Text style={styles.deepBtnText}>{open ? "▲ Hide deep dive" : "🔎 Deep Dive — full breakdown"}</Text>
        </TouchableOpacity>
        {open && (
          <View>
            <Section label="SOURCE LINKS">
              {(s.source_links || []).map((l) => (
                <Text key={l} style={styles.link} onPress={() => Linking.openURL(l)}>{l}{"\n"}</Text>
              ))}
            </Section>
            <Section label="THE STORY">{s.story}</Section>
            <Section label="THEIR FOUNDING STORY">{s.founding_story}</Section>
            <Section label="WHO SHOULD USE THIS">{s.who_should_use}</Section>
            <Section label="WHO SHOULD PURCHASE THIS">{s.who_should_buy}</Section>
            <Section label="FREE / BETTER ALTERNATIVES">{s.free_alternatives}</Section>
          </View>
        )}
      </View>
    </View>
  );
}

function SectorBlock({ sec }) {
  const meta = SECTOR[sec.sector] || { emoji: "•" };
  return (
    <View style={{ marginTop: 22 }}>
      <Text style={styles.sectorHead}>{meta.emoji} {sec.sector}
        <Text style={styles.sectorCount}>  · {sec.heroes.length} deep-dives</Text></Text>
      {sec.heroes.map((s, i) => <HeroCard key={s.id || i} s={s} idx={i + 1} sector={sec.sector} />)}
      {sec.other_news?.length ? (
        <View style={styles.otherBox}>
          <Text style={styles.otherTitle}>More in {sec.sector}</Text>
          {sec.other_news.map((o, i) => (
            <Text key={i} style={styles.otherItem} onPress={() => Linking.openURL((o.source_links || [])[0] || "")}>
              • {o.headline} <Text style={{ color: theme.accent }}>↗ {o.source_name}</Text>
            </Text>
          ))}
        </View>
      ) : null}
    </View>
  );
}

function AllNews({ edition, onBack }) {
  const order = (edition.sectors || []).map((s) => s.sector);
  const grouped = {};
  (edition.all_news || []).forEach((it) => {
    (grouped[it.sector] = grouped[it.sector] || []).push(it);
  });
  return (
    <ScrollView contentContainerStyle={{ padding: 14, paddingBottom: 60 }}>
      <TouchableOpacity onPress={onBack}><Text style={{ color: theme.accent, fontWeight: "700" }}>← Back to the edition</Text></TouchableOpacity>
      <Text style={styles.brand}>🔍 All News</Text>
      <Text style={styles.date}>{edition.edition_date} · {edition.all_news?.length} stories · ★ = deep-dive hero</Text>
      {order.map((sector) => (
        <View key={sector} style={{ marginTop: 18 }}>
          <Text style={styles.sectorHead}>{(SECTOR[sector] || {}).emoji} {sector}
            <Text style={styles.sectorCount}>  · {(grouped[sector] || []).length}</Text></Text>
          {(grouped[sector] || []).map((it, i) => (
            <Text key={i} style={styles.allNewsRow} onPress={() => Linking.openURL((it.source_links || [])[0] || "")}>
              <Text style={{ color: theme.accent }}>{it.kind === "hero" ? "★ " : "· "}</Text>
              {it.headline} <Text style={{ color: theme.muted }}>({it.source_name})</Text>
            </Text>
          ))}
        </View>
      ))}
    </ScrollView>
  );
}

export default function App() {
  const [edition, setEdition] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [screen, setScreen] = useState("feed");

  const load = useCallback(async () => {
    setEdition(await getLatestEdition());
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => { load(); registerForPush(); }, [load]);

  if (loading) {
    return (
      <SafeAreaView style={styles.screen}>
        <ActivityIndicator color={theme.accent} style={{ marginTop: 80 }} />
      </SafeAreaView>
    );
  }

  if (screen === "allnews") {
    return (
      <SafeAreaView style={styles.screen}>
        <StatusBar style="light" />
        <AllNews edition={edition} onBack={() => setScreen("feed")} />
      </SafeAreaView>
    );
  }

  const c = edition.counts || {};
  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="light" />
      <ScrollView
        contentContainerStyle={{ padding: 14, paddingBottom: 60 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor={theme.accent} />}
      >
        <Text style={styles.brand}>NO BS <Text style={{ color: theme.accent }}>·</Text> <Text style={styles.brandSub}>Should You Buy This?</Text></Text>
        <Text style={styles.date}>Daily AI Short · {edition.edition_date} · {c.heroes} deep-dives · {c.sectors} sectors</Text>

        <TouchableOpacity style={styles.allNewsBtn} onPress={() => setScreen("allnews")}>
          <Text style={styles.allNewsBtnText}>🔍 Deep Dive — All News ({c.all_news})</Text>
        </TouchableOpacity>

        {(edition.sectors || []).map((sec) => <SectorBlock key={sec.sector} sec={sec} />)}

        <Text style={styles.footer}>Sources on every item · not financial advice · pull to refresh</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  brand: { color: "#fff", fontSize: 24, fontWeight: "900", marginTop: 6 },
  brandSub: { color: theme.muted, fontSize: 15, fontWeight: "800" },
  date: { color: theme.muted, fontSize: 12, marginTop: 3, marginBottom: 12 },
  allNewsBtn: { backgroundColor: "#12233a", borderColor: "#234", borderWidth: 1, borderRadius: 10, padding: 12, alignItems: "center" },
  allNewsBtnText: { color: "#7cc4ff", fontWeight: "800", fontSize: 14 },
  sectorHead: { color: "#fff", fontSize: 19, fontWeight: "900", borderBottomColor: theme.border, borderBottomWidth: 2, paddingBottom: 8, marginBottom: 12 },
  sectorCount: { color: theme.muted, fontSize: 13, fontWeight: "700" },
  card: { backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 14, marginBottom: 14, overflow: "hidden" },
  img: { width: "100%", height: 180 },
  imgPlaceholder: { width: "100%", height: 120, justifyContent: "flex-end", padding: 14 },
  imgPlaceholderText: { color: "#0a0d11", fontWeight: "900", fontSize: 16, opacity: 0.85 },
  pillRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginBottom: 8 },
  pill: { paddingVertical: 4, paddingHorizontal: 10, borderRadius: 999 },
  eyebrow: { color: theme.muted, fontSize: 11, fontWeight: "700", letterSpacing: 1 },
  headline: { color: "#fff", fontSize: 17, fontWeight: "800", marginTop: 4, lineHeight: 23 },
  oneLiner: { color: "#cdd6df", fontSize: 14, marginTop: 6, lineHeight: 20 },
  deepBtn: { marginTop: 12, backgroundColor: "#0e1913", borderColor: "#1e3a2c", borderWidth: 1, borderRadius: 9, paddingVertical: 9, alignItems: "center" },
  deepBtnText: { color: theme.accent, fontWeight: "800", fontSize: 13 },
  sectionLabel: { color: theme.accent, fontSize: 11, fontWeight: "700", letterSpacing: 0.6 },
  sectionBody: { color: theme.text, fontSize: 14, lineHeight: 21, marginTop: 3 },
  link: { color: theme.accent, fontSize: 12 },
  otherBox: { backgroundColor: "#0e1319", borderColor: theme.border, borderWidth: 1, borderRadius: 12, padding: 14 },
  otherTitle: { color: theme.muted, fontWeight: "800", fontSize: 13, marginBottom: 8 },
  otherItem: { color: "#cdd6df", fontSize: 14, lineHeight: 21, marginBottom: 8 },
  allNewsRow: { color: theme.text, fontSize: 14, lineHeight: 21, marginBottom: 10, paddingBottom: 8, borderBottomColor: "#1c232b", borderBottomWidth: 1 },
  footer: { color: "#5a6672", fontSize: 12, textAlign: "center", marginTop: 26, lineHeight: 18 },
});
