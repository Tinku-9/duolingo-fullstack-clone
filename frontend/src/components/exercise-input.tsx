"use client";
import {useState} from "react";
import {Check, MessageCircle} from "lucide-react";
import {Answer, Exercise} from "@/lib/api";
import {Mascot} from "./mascot";

export function ExerciseInput({exercise, value, onChange, disabled}: {exercise: Exercise; value: Answer; onChange: (value: Answer) => void; disabled: boolean}) {
  const [left, setLeft] = useState<string | null>(null);
  const payload = exercise.payload;
  const selected = value.token_ids ?? [];
  const pairs = value.pairs ?? {};
  return <div className="exercise-input"><h1>{exercise.prompt}</h1>
    {payload.sentence && <div className="sentence-row"><Mascot small/><div className="speech-bubble"><MessageCircle size={22}/><span>{payload.sentence}</span></div></div>}
    {exercise.type === "multiple_choice" && <div className="choice-list">{payload.options?.map((option, i) => <button key={option.id} disabled={disabled} className={`choice ${value.option_id === option.id ? "chosen" : ""}`} onClick={() => onChange({option_id: option.id})}><span className="choice-number">{i + 1}</span>{option.text}{value.option_id === option.id && <Check size={20}/>}</button>)}</div>}
    {exercise.type === "word_bank" && <><div className="word-answer" aria-label="Your selected words">{selected.map(id => <button disabled={disabled} className="word-token" key={id} onClick={() => onChange({token_ids: selected.filter(x => x !== id)})}>{payload.tokens?.find(t => t.id === id)?.text}</button>)}{!selected.length && <span className="muted">Tap the words to build your answer</span>}</div><div className="word-bank">{payload.tokens?.map(token => <button key={token.id} className={`word-token ${selected.includes(token.id) ? "used" : ""}`} disabled={disabled || selected.includes(token.id)} onClick={() => onChange({token_ids: [...selected, token.id]})}>{token.text}</button>)}</div></>}
    {exercise.type === "match_pairs" && <><p className="muted exercise-instructions">Choose a word on the left, then its translation on the right. Tap a paired word to undo.</p><div className="match-grid"><div>{payload.left?.map(item => <button key={item.id} disabled={disabled} className={`match-item ${left === item.id ? "chosen" : ""} ${pairs[item.id] ? "paired" : ""}`} onClick={() => {if (pairs[item.id]) {const copy = {...pairs}; delete copy[item.id]; onChange({pairs: copy});} setLeft(item.id);}}>{item.text}{pairs[item.id] && <span className="pair-index">{(payload.left?.findIndex(x => x.id === item.id) ?? 0) + 1}</span>}</button>)}</div><div>{payload.right?.map(item => {const partner = Object.keys(pairs).find(key => pairs[key] === item.id); return <button key={item.id} disabled={disabled || (!left && !partner)} className={`match-item ${partner ? "paired" : ""}`} onClick={() => {const copy = {...pairs}; if (partner) delete copy[partner]; if (left) copy[left] = item.id; onChange({pairs: copy}); setLeft(null);}}>{item.text}{partner && <span className="pair-index">{(payload.left?.findIndex(x => x.id === partner) ?? 0) + 1}</span>}</button>;})}</div></div></>}
    {(exercise.type === "fill_blank" || exercise.type === "type_answer") && <div className="text-answer"><label htmlFor="lesson-answer">{payload.hint || "Your English translation"}</label><textarea id="lesson-answer" autoFocus disabled={disabled} rows={3} value={value.text ?? ""} onChange={e => onChange({text: e.target.value})} placeholder="Type your answer here…" autoComplete="off" spellCheck={false}/>{exercise.type === "fill_blank" && <div className="accent-buttons">{["á", "é", "í", "ó", "ú", "ñ", "ü"].map(char => <button key={char} disabled={disabled} onClick={() => onChange({text: (value.text ?? "") + char})}>{char}</button>)}</div>}</div>}
  </div>;
}

export function answerReady(exercise: Exercise, value: Answer) {
  if (exercise.type === "multiple_choice") return Boolean(value.option_id);
  if (exercise.type === "word_bank") return Boolean(value.token_ids?.length);
  if (exercise.type === "match_pairs") return Object.keys(value.pairs ?? {}).length === exercise.payload.left?.length;
  return Boolean(value.text?.trim());
}
