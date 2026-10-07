"use client";

import Link from "next/link";
import {useCallback, useEffect, useState} from "react";
import {useRouter} from "next/navigation";
import {BookOpen, Check, ChevronRight, Flame, Gem, Heart, Home, Lock, Settings, Shield, Sparkles, Star, Trophy, User, X, Zap} from "lucide-react";
import {api, Attempt, Leaderboard, Learner, Profile, Skill, Unit} from "@/lib/api";
import {guestName, saveGuestName} from "@/lib/guest-name";
import {AchievementBadges} from "./achievement-badges";
import {ThemeToggle} from "./theme-toggle";
import {UnitGuide} from "./unit-guide";
import {Mascot} from "./mascot";
import {useDialogFocus} from "./use-dialog-focus";

const navigation = [{href: "/learn", name: "Learn", icon: Home}, {href: "/leaderboard", name: "Leaderboards", icon: Shield}, {href: "/profile", name: "Profile", icon: User}, {href: "/settings", name: "Settings", icon: Settings}];
export function Dashboard({page}: {page: "learn" | "leaderboard" | "profile" | "settings"}) {
  const router = useRouter();
  const [me, setMe] = useState<Learner | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [board, setBoard] = useState<Leaderboard | null>(null);
  const [active, setActive] = useState<Attempt | null>(null);
  const [selected, setSelected] = useState<Skill | null>(null);
  const [guideUnit, setGuideUnit] = useState<Unit | null>(null);
  const [heartModal, setHeartModal] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [nameMessage, setNameMessage] = useState("");
  const [nameError, setNameError] = useState("");
  useDialogFocus(heartModal, () => setHeartModal(false));
  const load = useCallback(async () => {
    setError("");
    try {
      const learner = await api<Learner>("/api/me");
      learner.display_name = guestName(learner.id, learner.display_name);
      setMe(learner); setDisplayName(learner.display_name);
      if (page === "learn") { const [path, attempt] = await Promise.all([api<{units: Unit[]}>(`/api/courses/${learner.course_id}/path`), api<Attempt | null>("/api/me/active-attempt")]); setUnits(path.units); setActive(attempt); }
      if (page === "leaderboard") {
        const ranking = await api<Leaderboard>("/api/leaderboard");
        setBoard({...ranking, entries: ranking.entries.map(entry => entry.is_you ? {...entry, name: learner.display_name} : entry)});
      }
      if (page === "profile") {
        const details = await api<Profile>("/api/me/profile");
        setProfile({...details, display_name: learner.display_name});
      }
    } catch (e) {setError((e as Error).message);}
  }, [page]);
  useEffect(() => {void load();}, [load]);
  async function start(lessonId: number) {
    setBusy(true); setError("");
    try {const attempt = await api<Attempt>(`/api/lessons/${lessonId}/attempts`, {method: "POST"}); router.push(`/lesson/${attempt.id}`);}
    catch (e) {setError((e as Error).message); setSelected(null); if (me?.hearts === 0) setHeartModal(true);}
    finally {setBusy(false);}
  }
  async function refill() {setBusy(true); try {setMe(await api<Learner>("/api/me/hearts/refill", {method: "POST"})); setHeartModal(false);} catch(e) {setError((e as Error).message);} finally {setBusy(false);}}

  function saveName(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!me) return;
    setNameMessage(""); setNameError("");
    try {
      const name = saveGuestName(me.id, displayName);
      setDisplayName(name); setMe({...me, display_name: name});
      setNameMessage("Your name has been saved.");
    } catch (e) {setNameError((e as Error).message);}
  }

  return <div className="app-shell">
    <aside className="sidebar"><Link className="wordmark" href="/learn">duolingo</Link><nav aria-label="Main navigation">{navigation.map(({href, name, icon: Icon}) => <Link key={href} href={href} className={`nav-item ${href === `/${page}` ? "selected" : ""}`}><Icon size={28}/><span>{name}</span></Link>)}</nav><div className="sidebar-note"><Mascot small/><p>A little learning.<br/>A lot of possibility.</p></div></aside>
    <div className="workspace"><header className="topbar"><span className="course-flag" title="Learning Spanish"><svg width="32" height="24" viewBox="0 0 32 24" role="img" aria-label="Spanish course"><defs><clipPath id="flag-round"><rect width="32" height="24" rx="5"/></clipPath></defs><g clipPath="url(#flag-round)"><path fill="#c8414b" d="M0 0h32v24H0z"/><path fill="#ffdc64" d="M0 6h32v12H0z"/><rect x="8" y="10" width="5" height="6" rx="1" fill="#c8414b"/><path stroke="#ffdc64" strokeWidth="1" d="M10.5 10v6M8 13h5"/><path fill="#c8414b" d="m7.5 9 1-2 2 1 2-1 1 2z"/></g></svg></span><span className="stat orange"><Flame fill="currentColor"/>{me?.streak ?? "—"}</span><span className="stat blue"><Gem/>{me?.gems ?? "—"}</span><span className="stat gold"><Zap fill="currentColor"/>{me?.total_xp ?? "—"}<span className="stat-label"> XP</span></span><button className="stat red heart-button" onClick={() => setHeartModal(true)} aria-label={`${me?.hearts ?? 0} hearts. Open refill`}><Heart fill="currentColor"/>{me?.hearts ?? "—"}</button></header>
    <div className="dashboard-columns"><main className={`main-content ${page !== "learn" ? "content-page" : ""}`}>
      {error && <div className="error-box" role="alert">{error}<button onClick={() => void load()}>Try again</button></div>}
      {!me && !error && <div className="loading">Getting your learning adventure ready…</div>}
      {page === "learn" && <>
        <div className="section-heading"><span>SECTION 1 · ROOKIE</span><BookOpen size={22}/></div>
        {active && <div className="resume-banner"><span>Your lesson is waiting for you.</span><Link href={`/lesson/${active.id}`}>Resume <ChevronRight size={16}/></Link></div>}
        {units.map((unit, unitIndex) => <section key={unit.id} className={`unit-section unit-color-${unitIndex % 3}`}><div className="unit-banner"><div><span>UNIT {unit.position}</span><h1>{unit.title}</h1><p>{unit.description}</p></div><button type="button" className="unit-guide-button" onClick={() => {setSelected(null); setGuideUnit(unit);}} aria-label={`Open guidebook for ${unit.title}`} aria-haspopup="dialog" title="Open unit guidebook"><BookOpen size={30}/></button></div>
          <div className="learning-path">{unit.skills.map((skill, skillIndex) => <div className="path-stop" style={{marginLeft: skillIndex % 2 === 0 ? -68 : 72}} key={skill.id}>
            {skill.state === "available" && <div className="start-bubble">START</div>}
            <button className={`path-node ${skill.state}`} onClick={() => {setError(""); setSelected(skill);}} aria-label={`${skill.title}: ${skill.state}, ${skill.completed_lessons} of ${skill.total_lessons} lessons completed`}><span className="node-ring" style={{background: `conic-gradient(var(--unit-color) ${skill.completed_lessons / skill.total_lessons * 360}deg, var(--border) 0)`}}/><span className="node-face">{skill.state === "locked" ? <Lock size={27}/> : skill.state === "completed" ? <Check size={34} strokeWidth={4}/> : skill.icon_key === "book" ? <BookOpen size={30}/> : <Star size={34} fill="currentColor"/>}</span></button><span className="node-label">{skill.title}</span>
            {selected?.id === skill.id && <div className="skill-popover"><button className="close-popover" onClick={() => setSelected(null)} aria-label="Close skill"><X size={17}/></button><h3>{skill.title}</h3><p>{skill.state === "locked" ? "Complete the earlier lessons to unlock this skill." : `${skill.completed_lessons} of ${skill.total_lessons} lessons completed`}</p>{skill.state !== "locked" && <button className="button primary" disabled={busy} onClick={() => void start(skill.lessons.find(x => x.state === "available")?.id ?? skill.lessons[0].id)}>{busy ? "Starting…" : skill.state === "completed" ? "Practice +20 XP" : "Start +20 XP"}</button>}</div>}
          </div>)}<div className="path-decoration"><Mascot small/><span>Keep going.<br/>You’ve got this!</span></div></div>
        </section>)}
      </>}
      {page === "leaderboard" && board && <><div className="page-hero"><Trophy className="gold" size={70}/><h1>Bronze League</h1><p>A little friendly competition goes a long way.</p><span className="pill">Week of {board.week_start}</span></div><div className="leaderboard-list">{board.entries.map(entry => <div key={entry.id} className={`leaderboard-row ${entry.is_you ? "you" : ""}`}><span className={`rank rank-${entry.rank}`}>{entry.rank}</span><span className={`avatar avatar-${entry.id % 4}`}>{entry.name[0]}</span><strong>{entry.name}{entry.is_you && <small> YOU</small>}</strong><span>{entry.xp} XP</span></div>)}</div><p className="muted centered">Your XP updates as you learn. Other learners are seeded demo profiles.</p></>}
      {page === "profile" && profile && <><div className="profile-header"><div className="profile-avatar">{profile.display_name[0]}</div><h1>{profile.display_name}</h1><p>Learning Spanish · One day at a time</p></div><h2>Statistics</h2><div className="stats-grid"><StatCard icon={<Flame className="orange"/>} value={profile.streak} label="Day streak"/><StatCard icon={<Zap className="gold"/>} value={profile.total_xp} label="Total XP"/><StatCard icon={<Check className="green"/>} value={profile.completed_skills} label="Skills completed"/><StatCard icon={<Shield className="blue"/>} value="Bronze" label="Current league"/></div><AchievementBadges profile={profile}/></>}
      {page === "settings" && <><h1>Settings</h1><p className="muted">Your learning space, your way.</p><div className="settings-card"><h2>Account</h2><p>You have your own guest profile in this browser. Your learning progress is saved automatically.</p><form className="name-form" onSubmit={saveName}><label htmlFor="display-name">Your name</label><input id="display-name" name="displayName" autoComplete="nickname" value={displayName} onChange={event => {setDisplayName(event.target.value); setNameMessage(""); setNameError("");}} required maxLength={50} disabled={!me} aria-describedby="name-help"/><p id="name-help">Your name is saved in this browser and appears on your profile and leaderboard. Clearing site data removes it.</p><button className="button primary" type="submit" disabled={!me || !displayName.trim()}>Save name</button><div aria-live="polite" className="name-status">{nameMessage}</div>{nameError && <div className="red" role="alert">{nameError}</div>}</form><ThemeToggle/><h2>Learning preferences</h2><p>Spanish · English interface · 40 XP daily goal</p><h2>Coming soon</h2><p>Notifications, additional languages, subscription purchases, and speech recognition.</p></div></>}
    </main><aside className="right-rail"><div className="rail-card super-card"><Sparkles className="purple"/><h2>Make every day count</h2><p>Small steps today. Big progress tomorrow.</p><Mascot/><Link className="button secondary" href="/profile">View your progress</Link></div><div className="rail-card"><div className="card-heading"><h2>Daily goal</h2><Zap className="gold"/></div><p>Earn {me?.daily_goal_xp ?? 40} XP today</p><div className="goal-track"><span style={{width: `${Math.min(100, (me?.daily_xp ?? 0) / (me?.daily_goal_xp ?? 40) * 100)}%`}}/></div><strong className="muted">{me?.daily_xp ?? 0} / {me?.daily_goal_xp ?? 40} XP</strong></div><div className="rail-card"><div className="card-heading"><h2>Bronze League</h2><Shield className="gold"/></div><p>Keep learning to climb the ranks.</p><Link className="text-link" href="/leaderboard">View leaderboard <ChevronRight size={17}/></Link></div><footer className="rail-footer">ABOUT · HELP · PRIVACY<br/>Independent assignment demo</footer></aside></div></div>
    {guideUnit && <UnitGuide unit={guideUnit} onClose={() => setGuideUnit(null)}/>}
    {heartModal && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="heart-title"><button className="modal-close" onClick={() => setHeartModal(false)} aria-label="Close"><X/></button><Heart size={64} className="red" fill="currentColor"/><h2 id="heart-title">Keep your heart in it</h2><p>You have {me?.hearts ?? 0} of 5 hearts. Mistakes use one heart.</p><p className="muted">Demo refill: restore your hearts for free.</p><button className="button primary" disabled={busy} onClick={() => void refill()}>{busy ? "Refilling…" : "Refill hearts"}</button></section></div>}
  </div>;
}

function StatCard({icon, value, label}: {icon: React.ReactNode; value: string | number; label: string}) {return <div className="stat-card">{icon}<div><strong>{value}</strong><span>{label}</span></div></div>;}
