import {Award, BookOpen, Check, Flame, Lock, Zap} from "lucide-react";
import type {Profile} from "@/lib/api";

export function AchievementBadges({profile}: {profile: Profile}) {
  const milestones: Record<string, {value: number; target: number; unit: string; icon: typeof Flame; color: string}> = {
    Wildfire: {value: profile.streak, target: 3, unit: "days", icon: Flame, color: "orange"},
    Sage: {value: profile.total_xp, target: 100, unit: "XP", icon: Zap, color: "gold"},
    Trailblazer: {value: profile.completed_skills, target: 3, unit: "skills", icon: BookOpen, color: "blue"},
  };
  const earned = profile.achievements.filter(badge => badge.earned).length;

  return <section aria-labelledby="badges-heading" className="badge-section">
    <div className="badge-section-heading"><h2 id="badges-heading">Achievements</h2><span className="pill">{earned} / {profile.achievements.length} earned</span></div>
    <p className="muted badge-intro">Little milestones. Big reasons to keep learning.</p>
    <div className="badge-grid">{profile.achievements.map(badge => {
      const milestone = milestones[badge.title];
      const Icon = milestone?.icon ?? Award;
      const progress = milestone ? Math.min(milestone.target, Math.max(0, milestone.value)) : 0;
      return <article key={badge.title} className={`badge-card ${badge.earned ? "earned" : "locked"}`}>
        <div className={`badge-medal ${milestone?.color ?? "gold"}`} aria-hidden="true"><Icon size={38} strokeWidth={2.5}/><span className="badge-seal">{badge.earned ? <Check size={14}/> : <Lock size={14}/>}</span></div>
        <h3>{badge.title}</h3><p className="badge-description">{badge.description}</p>
        <span className={`badge-status ${badge.earned ? "earned" : ""}`}>{badge.earned ? <Check size={14}/> : <Lock size={14}/>} {badge.earned ? "Earned" : "Locked"}</span>
        {milestone && <div className="badge-progress"><div className="badge-progress-track" role="progressbar" aria-label={`${badge.title} progress`} aria-valuemin={0} aria-valuemax={milestone.target} aria-valuenow={progress} aria-valuetext={`${progress} of ${milestone.target} ${milestone.unit}`}><span style={{width: `${progress / milestone.target * 100}%`}}/></div><span>{progress} / {milestone.target} {milestone.unit}</span></div>}
        {badge.title === "Wildfire" && <p className="badge-note">Based on your current streak.</p>}
      </article>;
    })}</div>
  </section>;
}
