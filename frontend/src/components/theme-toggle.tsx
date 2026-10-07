"use client";

import {useEffect, useState} from "react";
import {Moon, Sun} from "lucide-react";

const themeKey = "duolingo.theme.v1";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);
  const [ready, setReady] = useState(false);
  const [message, setMessage] = useState("");
  useEffect(() => {
    setDark(document.documentElement.dataset.theme === "dark");
    setReady(true);
  }, []);

  function toggle() {
    const next = !dark;
    document.documentElement.dataset.theme = next ? "dark" : "light";
    setDark(next);
    try {
      localStorage.setItem(themeKey, next ? "dark" : "light");
      setMessage("");
    } catch {
      setMessage("Theme changed for now. Your browser could not save the preference.");
    }
  }

  return <div className="theme-settings"><h2>Appearance</h2><div className="theme-row"><div><strong id="theme-label">Dark mode</strong><p id="theme-help">Choose a darker look for your learning space.</p></div><button type="button" className="theme-toggle" role="switch" aria-checked={dark} aria-labelledby="theme-label" aria-describedby="theme-help" disabled={!ready} onClick={toggle}>{dark ? <Moon size={20}/> : <Sun size={20}/>}<span>{dark ? "On" : "Off"}</span></button></div><div className="muted theme-message" role="status">{message}</div></div>;
}
