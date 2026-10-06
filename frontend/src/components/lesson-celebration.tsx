export function LessonCelebration() {
  return <div className="lesson-confetti" aria-hidden="true">{Array.from({length: 24}, (_, index) => <i key={index} style={{left: `${4 + (index * 19) % 92}%`, background: ["#58cc02", "#1cb0f6", "#ffc800", "#ff9600"][index % 4], animationDelay: `${(index % 6) * 0.12}s`, transform: `rotate(${index * 37}deg)`}}/>)}</div>;
}
