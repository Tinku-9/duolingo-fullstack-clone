const keyFor = (userId: number) => `duolingo.guest-name.v1.${userId}`;

export function guestName(userId: number, fallback: string): string {
  try {
    return localStorage.getItem(keyFor(userId)) || fallback;
  } catch {
    return fallback;
  }
}

export function saveGuestName(userId: number, value: string): string {
  const name = value.trim();
  if (!name || name.length > 50) throw new Error("Enter a name between 1 and 50 characters.");
  try {
    localStorage.setItem(keyFor(userId), name);
  } catch {
    throw new Error("Your browser could not save the name. Enable site storage and try again.");
  }
  return name;
}
