"use client";

import {BookOpen, X} from "lucide-react";
import {Unit} from "@/lib/api";
import {PronunciationButton} from "./pronunciation-button";
import {useDialogFocus} from "./use-dialog-focus";

// Curated study notes for the three units in the seeded Spanish course.
const guides: Record<number, {words: [string, string][]; examples: [string, string][]; tip: string}> = {
  1: {
    words: [["hola", "hello"], ["adi?s", "goodbye"], ["s?", "yes"], ["no", "no"], ["gracias", "thank you"], ["por favor", "please"]],
    examples: [["Hola, buenos d?as", "Hello, good morning"], ["S?, por favor", "Yes, please"]],
    tip: "Keep the accent in s? when you mean yes. Say gracias to thank someone and por favor when making a polite request.",
  },
  2: {
    words: [["agua", "water"], ["pan", "bread"], ["leche", "milk"], ["caf?", "coffee"], ["quiero", "I want"]],
    examples: [["Quiero agua", "I want water"], ["Quiero caf?", "I want coffee"]],
    tip: "Use quiero followed by a drink or food to say what you want. Add por favor to make your request polite.",
  },
  3: {
    words: [["madre", "mother"], ["padre", "father"], ["amigo", "friend"], ["hermana", "sister"], ["mi", "my"]],
    examples: [["Mi madre", "My mother"], ["Mi hermana", "My sister"]],
    tip: "Put mi before a singular family word to say my: mi madre, mi padre, or mi hermana.",
  },
};

export function UnitGuide({unit, onClose}: {unit: Unit; onClose: () => void}) {
  useDialogFocus(true, onClose);
  const guide = guides[unit.position];
  return <div className="modal-backdrop"><section className="modal unit-guide" role="dialog" aria-modal="true" aria-labelledby="unit-guide-title">
    <header className="unit-guide-header"><div><span className="muted">UNIT {unit.position} GUIDEBOOK</span><h2 id="unit-guide-title"><BookOpen size={24}/>{unit.title}</h2></div><button type="button" className="icon-button" onClick={onClose} aria-label="Close guidebook"><X size={24}/></button></header>
    <p>{unit.description}</p>
    {guide ? <>
      <h3>Key vocabulary</h3>
      <table className="guide-vocabulary"><thead><tr><th scope="col">Spanish</th><th scope="col">English</th></tr></thead><tbody>{guide.words.map(([spanish, english]) => <tr key={spanish}><td lang="es">{spanish}</td><td>{english}</td></tr>)}</tbody></table>
      <h3>Useful phrases</h3>
      {guide.examples.map(([spanish, english]) => <div className="guide-example" key={spanish}><strong lang="es">{spanish}</strong><p>{english}</p><PronunciationButton text={spanish}/></div>)}
      <div className="guide-tip"><h3>Remember</h3><p>{guide.tip}</p></div>
    </> : <><h3>What you will learn</h3><ul>{unit.skills.map(skill => <li key={skill.id}>{skill.title}</li>)}</ul></>}
    <button type="button" className="button primary" onClick={onClose}>Back to learning</button>
  </section></div>;
}
