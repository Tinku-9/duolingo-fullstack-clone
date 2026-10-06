"use client";
import {useEffect, useRef} from "react";

export function useDialogFocus(open: boolean, onClose: () => void) {
  const close = useRef(onClose);
  useEffect(() => {close.current = onClose;}, [onClose]);
  useEffect(() => {
    if (!open) return;
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]');
    if (!dialog) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const focusable = () => Array.from(dialog.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), [tabindex="0"]'));
    focusable()[0]?.focus();
    function key(event: KeyboardEvent) {
      if (event.key === "Escape") {event.preventDefault(); close.current();}
      if (event.key !== "Tab") return;
      const elements = focusable();
      const first = elements[0], last = elements[elements.length - 1];
      if (!first) {event.preventDefault(); return;}
      if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last.focus();}
      else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first.focus();}
    }
    document.addEventListener("keydown", key);
    return () => {document.removeEventListener("keydown", key); document.body.style.overflow = overflow; previous?.focus();};
  }, [open]);
}
