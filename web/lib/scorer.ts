/**
 * Heuristic salience scorer — ported from Python openconch/scorer.py.
 * Scores text for importance on a 0-1 scale.
 */

const ENTITY_PATTERNS = [
  /\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b/g,       // Proper nouns
  /\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b/g,        // Dates
  /\b\d+(?:\.\d+)?%\b/g,                         // Percentages
  /\$\d+(?:,\d{3})*(?:\.\d{2})?\b/g,            // Dollar amounts
  /\b\d{3,}\b/g,                                  // Large numbers
  /\b[A-Z]{2,}\b/g,                               // Acronyms
];

const SALIENCE_KEYWORDS = new Set([
  "always", "never", "prefer", "hate", "love", "allergic",
  "birthday", "password", "address", "phone", "email",
  "deadline", "meeting", "appointment", "important", "critical",
  "remember", "don't forget", "key", "essential", "must",
  "favorite", "dislike", "need", "want", "require",
]);

export function scoreSalience(text: string, existingMemories?: string[]): number {
  const scores: number[] = [];

  // Entity density
  let entityCount = 0;
  for (const pattern of ENTITY_PATTERNS) {
    const matches = text.match(pattern);
    entityCount += matches ? matches.length : 0;
  }
  const wordCount = Math.max(text.split(/\s+/).length, 1);
  const entityScore = Math.min(1.0, entityCount / Math.max(wordCount * 0.1, 1));
  scores.push(entityScore * 0.3);

  // Keyword salience
  const textLower = text.toLowerCase();
  let keywordHits = 0;
  for (const kw of SALIENCE_KEYWORDS) {
    if (textLower.includes(kw)) keywordHits++;
  }
  const keywordScore = Math.min(1.0, keywordHits / 3.0);
  scores.push(keywordScore * 0.3);

  // Specificity
  const specificity = Math.min(1.0, text.length / 200.0);
  scores.push(specificity * 0.2);

  // Novelty
  if (existingMemories && existingMemories.length > 0) {
    const novelty = computeNovelty(text, existingMemories);
    scores.push(novelty * 0.2);
  } else {
    scores.push(0.15);
  }

  return Math.min(1.0, scores.reduce((a, b) => a + b, 0));
}

function computeNovelty(text: string, existing: string[]): number {
  const textWords = new Set(text.toLowerCase().split(/\s+/));
  if (textWords.size === 0) return 0;

  let maxOverlap = 0;
  const recent = existing.slice(-50);

  for (const mem of recent) {
    const memWords = new Set(mem.toLowerCase().split(/\s+/));
    if (memWords.size === 0) continue;

    const union = new Set([...textWords, ...memWords]);
    let intersection = 0;
    for (const w of textWords) {
      if (memWords.has(w)) intersection++;
    }

    const overlap = intersection / union.size;
    maxOverlap = Math.max(maxOverlap, overlap);
  }

  return 1.0 - maxOverlap;
}
