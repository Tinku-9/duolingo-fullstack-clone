export function Mascot({small = false}: {small?: boolean}) {
  return <svg className={small ? "mascot small" : "mascot"} viewBox="0 0 160 170" role="img" aria-label="A cheerful green owl">
    <path d="M36 113 17 89Q10 76 23 75L43 81M124 113 143 89Q150 76 137 75L117 81" fill="#58cc02"/>
    <path d="M39 151 35 164 64 164 65 147M99 147 98 164 127 164 121 149" fill="#ff9600"/>
    <path d="M32 58 24 20 63 37Q80 31 97 37L136 20 128 58Q145 80 132 123Q121 154 80 154Q39 154 28 123Q15 80 32 58" fill="#58cc02"/>
    <path d="M45 107Q80 89 115 107L107 137Q80 156 53 137Z" fill="#89e219"/>
    <ellipse cx="57" cy="74" rx="24" ry="29" fill="white"/><ellipse cx="103" cy="74" rx="24" ry="29" fill="white"/>
    <ellipse cx="63" cy="78" rx="8" ry="12" fill="#333"/><ellipse cx="97" cy="78" rx="8" ry="12" fill="#333"/>
    <circle cx="66" cy="73" r="3" fill="white"/><circle cx="100" cy="73" r="3" fill="white"/>
    <path d="M66 100Q80 89 94 100L80 114Z" fill="#ffc800"/><path d="m75 111 5 6 5-6" fill="#ff9600"/>
  </svg>;
}
