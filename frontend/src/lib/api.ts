export type Learner = { id: number; display_name: string; hearts: number; gems: number; streak: number; total_xp: number; daily_xp: number; weekly_xp: number; daily_goal_xp: number; course_id: number; timezone: string };
export type Lesson = {id: number; title: string; state: "completed" | "available" | "locked"; xp_reward: number};
export type Skill = {id: number; title: string; icon_key: string; state: Lesson["state"]; completed_lessons: number; total_lessons: number; lessons: Lesson[]};
export type Unit = {id: number; title: string; description: string; position: number; skills: Skill[]};
export type Item = {id: string; text: string};
export type Exercise = {id: number; type: "multiple_choice" | "word_bank" | "match_pairs" | "fill_blank" | "type_answer"; prompt: string; payload: {sentence?: string; hint?: string; options?: Item[]; tokens?: Item[]; left?: Item[]; right?: Item[]}};
export type Attempt = {id: string; lesson_id: number; status: "active" | "completed" | "failed" | "abandoned"; answered: number; total: number; hearts: number; accuracy: number; awarded_xp: number; exercise: Exercise | null};
export type Answer = {option_id?: string; token_ids?: string[]; pairs?: Record<string,string>; text?: string};
export type Feedback = {correct: boolean; correction: string; attempt: Attempt};
export type Profile = Learner & {completed_skills: number; achievements: {title: string; description: string; earned: boolean}[]};
export type Leaderboard = {league: string; week_start: string; entries: {id: number; name: string; xp: number; rank: number; is_you: boolean}[]};

const tokenKey = "duolingo.guest-token.v1";
let pendingToken: Promise<string> | undefined;

async function guestToken(base: string): Promise<string> {
  if (typeof window === "undefined") throw new Error("Guest profiles require a browser.");
  const obtain = async () => {
    const stored = localStorage.getItem(tokenKey);
    if (stored) return stored;
    const response = await fetch(`${base}/api/guests`, {method: "POST", cache: "no-store"});
    if (!response.ok) throw new Error("Could not create your guest profile. Please try again.");
    const {token} = await response.json() as {token: string};
    localStorage.setItem(tokenKey, token);
    return token;
  };
  // Serialize first visits across tabs as well as concurrent dashboard requests.
  pendingToken ??= (async (): Promise<string> => {
    return navigator.locks ? await navigator.locks.request(tokenKey, obtain) : await obtain();
  })();
  try { return await pendingToken; }
  finally { pendingToken = undefined; }
}

export async function api<T>(path: string, options?: {method?: string; body?: unknown}): Promise<T> {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  let response: Response;
  try {
    const token = await guestToken(base);
    response = await fetch(`${base}${path}`, {method: options?.method || "GET", headers: {"Authorization": `Bearer ${token}`, ...(options?.body ? {"Content-Type": "application/json"} : {})}, body: options?.body ? JSON.stringify(options.body) : undefined, cache: "no-store"});
  } catch {
    throw new Error("We couldn't reach the learning server. Check that the backend is running and try again.");
  }
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(typeof error?.detail === "string" ? error.detail : "Something went wrong. Please try again.");
  }
  return response.json();
}
