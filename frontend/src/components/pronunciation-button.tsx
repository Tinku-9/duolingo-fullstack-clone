"use client";

import {useEffect, useRef, useState} from "react";
import {Square, Volume2} from "lucide-react";

export function PronunciationButton({text}: {text: string}) {
  const [supported, setSupported] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState("");
  const utterance = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    setSupported("speechSynthesis" in window && "SpeechSynthesisUtterance" in window);
    return () => {
      if (utterance.current) {
        utterance.current.onend = null;
        utterance.current.onerror = null;
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  function listen() {
    const synth = window.speechSynthesis;
    if (speaking) {
      if (utterance.current) {utterance.current.onend = null; utterance.current.onerror = null;}
      synth.cancel();
      utterance.current = null;
      setSpeaking(false);
      return;
    }
    setError("");
    synth.cancel();
    const audio = new SpeechSynthesisUtterance(text);
    audio.lang = "es-ES";
    audio.rate = 0.85;
    const voices = synth.getVoices();
    const voice = voices.find(v => v.lang.toLowerCase() === "es-es")
      ?? voices.find(v => v.lang.toLowerCase().startsWith("es"));
    if (voice) audio.voice = voice;
    audio.onend = () => {
      if (utterance.current !== audio) return;
      setSpeaking(false); utterance.current = null;
    };
    audio.onerror = event => {
      if (utterance.current !== audio) return;
      setSpeaking(false); utterance.current = null;
      if (event.error !== "canceled" && event.error !== "interrupted") {
        setError("Audio is unavailable. You can continue the exercise.");
      }
    };
    utterance.current = audio;
    setSpeaking(true);
    try {synth.speak(audio);}
    catch {
      utterance.current = null; setSpeaking(false);
      setError("Audio is unavailable. You can continue the exercise.");
    }
  }

  if (!supported) return null;
  return <div className="pronunciation"><button type="button" className="pronunciation-button" onClick={listen} aria-label={speaking ? "Stop pronunciation" : "Listen to Spanish pronunciation"}>{speaking ? <Square size={18}/> : <Volume2 size={20}/>}<span>{speaking ? "Stop" : "Listen"}</span></button>{error && <p className="muted" role="status">{error}</p>}</div>;
}
