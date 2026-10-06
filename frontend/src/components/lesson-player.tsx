"use client";
import {useCallback, useEffect, useState} from "react";
import {useRouter} from "next/navigation";
import {Check, Flame, Heart, RotateCcw, Trophy, X, Zap} from "lucide-react";
import {Answer, api, Attempt, Feedback, Learner} from "@/lib/api";
import {answerReady, ExerciseInput} from "./exercise-input";
import {LessonCelebration} from "./lesson-celebration";
import {Mascot} from "./mascot";
import {useDialogFocus} from "./use-dialog-focus";

export function LessonPlayer({id}: {id: string}) {
  const router = useRouter();
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [answer, setAnswer] = useState<Answer>({});
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [learner, setLearner] = useState<Learner | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [celebrate, setCelebrate] = useState(false);
  const [exit, setExit] = useState(false);
  useDialogFocus(exit, () => setExit(false));
  const load = useCallback(async () => {try {setError(""); setAttempt(await api<Attempt>(`/api/attempts/${id}`));} catch(e) {setError((e as Error).message);}}, [id]);
  useEffect(() => {void load();}, [load]);

  async function submit() {
    if (!attempt?.exercise || busy || feedback || !answerReady(attempt.exercise, answer)) return;
    setBusy(true); setError("");
    try {setFeedback(await api<Feedback>(`/api/attempts/${id}/answers`, {method: "POST", body: {exercise_id: attempt.exercise.id, answer}}));}
    catch(e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  async function finish() {
    setBusy(true); setError("");
    try {const result = await api<{attempt: Attempt; learner: Learner}>(`/api/attempts/${id}/complete`, {method: "POST"}); setAttempt(result.attempt); setLearner(result.learner); setFeedback(null); setCelebrate(true);}
    catch(e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  async function next() {
    if (!feedback) return;
    setAttempt(feedback.attempt); setFeedback(null); setAnswer({});
    if (feedback.attempt.status === "active" && feedback.attempt.answered === feedback.attempt.total) await finish();
  }
  async function abandon() {
    setBusy(true); try {await api(`/api/attempts/${id}/abandon`, {method: "POST"}); router.push("/learn");}
    catch(e) {setError((e as Error).message); setExit(false);} finally {setBusy(false);}
  }
  async function refill() {
    setBusy(true); try {await api("/api/me/hearts/refill", {method: "POST"}); router.push("/learn");} catch(e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  useEffect(() => {
    function key(event: KeyboardEvent) {
      if (event.key === "Enter" && !event.shiftKey && !busy && !exit && attempt?.status === "active") {
        if (event.target instanceof HTMLButtonElement) return;
        event.preventDefault();
        if (feedback) void next(); else if (attempt.exercise && answerReady(attempt.exercise, answer)) void submit();
      }
    }
    window.addEventListener("keydown", key); return () => window.removeEventListener("keydown", key);
  });

  const current = feedback?.attempt ?? attempt;
  return <div className="lesson-shell"><header className="lesson-header"><button className="icon-button" onClick={() => attempt?.status === "active" ? setExit(true) : router.push("/learn")} aria-label="Exit lesson"><X size={30}/></button><div className="lesson-progress" role="progressbar" aria-label="Lesson progress" aria-valuenow={current?.answered ?? 0} aria-valuemin={0} aria-valuemax={current?.total ?? 5}><span style={{width: `${(current?.answered ?? 0) / (current?.total ?? 5) * 100}%`}}/></div><span className="stat red"><Heart fill="currentColor"/>{current?.hearts ?? "—"}</span></header>
    {error && <div className="lesson-error error-box" role="alert">{error}{!attempt && <button onClick={() => void load()}>Try again</button>}</div>}
    {!attempt && !error && <div className="loading">Your lesson is loading…</div>}
    {attempt?.status === "active" && attempt.exercise && <main className="lesson-main"><ExerciseInput key={attempt.exercise.id} exercise={attempt.exercise} value={answer} onChange={setAnswer} disabled={busy || Boolean(feedback)}/></main>}
    {attempt?.status === "active" && !attempt.exercise && !feedback && <main className="lesson-main end-summary"><Mascot/><h1>You reached the finish line!</h1><p>Collect your XP and save your progress.</p><button className="button primary" disabled={busy} onClick={() => void finish()}>Collect XP</button></main>}
    {attempt?.status === "completed" && <main className="end-summary">{celebrate && <LessonCelebration/>}<div className="celebration"><Mascot/><span>✦</span><span>✦</span></div><h1>Lesson complete!</h1><p>One step closer. Keep that momentum going!</p><div className="completion-stats"><div className="completion-card xp"><Zap/><span>Total XP</span><strong>+{attempt.awarded_xp}</strong></div><div className="completion-card accuracy"><Trophy/><span>Accuracy</span><strong>{attempt.accuracy}%</strong></div><div className="completion-card streak"><Flame/><span>Day streak</span><strong>{learner?.streak ?? "✓"}</strong></div></div>{learner && <p className="daily-summary">{learner.daily_xp >= learner.daily_goal_xp ? "Daily goal reached!" : "Daily goal:"} {learner.daily_xp} / {learner.daily_goal_xp} XP {learner.daily_xp >= learner.daily_goal_xp ? "🎉" : ""}</p>}<button className="button primary wide" onClick={() => router.push("/learn")}>Continue</button></main>}
    {attempt?.status === "failed" && <main className="end-summary"><Heart size={90} fill="currentColor" className="red"/><h1>Time for a fresh start</h1><p>You’re out of hearts. Refill and give this lesson another try.</p><p className="muted">This attempt earned no XP. Your earlier progress is saved.</p><button className="button primary wide" disabled={busy} onClick={() => void refill()}><RotateCcw size={19}/> Refill hearts · Demo</button><button className="text-link" onClick={() => router.push("/learn")}>Back to learning path</button></main>}
    {attempt?.status === "abandoned" && <main className="end-summary"><Mascot/><h1>Ready when you are</h1><p>This lesson was ended. Start a fresh lesson from your path.</p><button className="button primary" onClick={() => router.push("/learn")}>Back to path</button></main>}
    {attempt?.status === "active" && attempt.exercise && <footer className={`lesson-footer ${feedback ? feedback.correct ? "correct" : "incorrect" : ""}`}><div className="feedback-inner"><div className="feedback-copy" aria-live="polite">{feedback ? <><div className="feedback-icon">{feedback.correct ? <Check size={35}/> : <X size={35}/>}</div><div><h2>{feedback.correct ? "Nicely done!" : "Good effort!"}</h2><p>{feedback.correct ? "You’re making progress." : `Correct answer: ${feedback.correction}`}</p></div></> : <span className="muted keyboard-hint">Press Enter to check your answer</span>}</div><button className={`button ${feedback && !feedback.correct ? "danger" : "primary"}`} disabled={busy || (!feedback && !answerReady(attempt.exercise, answer))} onClick={() => feedback ? void next() : void submit()}>{busy ? "Saving…" : feedback ? "Continue" : "Check"}</button></div></footer>}
    {exit && <div className="modal-backdrop"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="exit-title"><Mascot small/><h2 id="exit-title">Wait, don’t give up!</h2><p>If you exit now, you won’t earn XP for this lesson. Hearts already used stay used.</p><button className="button primary" onClick={() => setExit(false)}>Keep learning</button><button className="button secondary" disabled={busy} onClick={() => void abandon()}>Exit lesson</button></section></div>}
  </div>;
}
