/**
 * Turn plain inventory object references in assistant text into Markdown links
 * so ChatMarkdown can render them with in-app navigation.
 *
 * - Fenced ``` blocks and inline `code` spans are not modified.
 * - `/o/ResourceType/<uuid>` → [path](path) for the router
 * - `ResourceType/<uuid>` (PascalCase) → [Type](/o/Type/u) when not part of an `/o/Type/uuid` path
 */

const UUID =
  "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}";

/** /o/Type/<uuid> not already the URL in [text](url) */
const BARE_INVENTORY_PATH = new RegExp(
  `(?<!\\]\\()(/o/[A-Za-z][A-Za-z0-9_]*/${UUID})`,
  "g",
);

/**
 * Type/uuid: require start of "Type" to not be immediately after `/` (excludes the Type segment in /o/Type/…).
 * JS: fixed 1-char lookbehind: not `\/` from …/o/ or …/c/
 */
const TYPE_SLASH_UUID = new RegExp(`(?<![/])\\b([A-Z][A-Za-z0-9_]*)/(${UUID})\\b`, "g");

function linkifySegment(s: string): string {
  let t = s.replace(BARE_INVENTORY_PATH, (_m, p: string) => `[${p}](${p})`);
  t = t.replace(TYPE_SLASH_UUID, (_full, resType: string, id: string) => {
    const path = `/o/${encodeURIComponent(resType)}/${id}`;
    return `[${resType}](${path})`;
  });
  return t;
}

export function linkifyInventoryReferences(text: string): string {
  if (!text) {
    return text;
  }
  return text
    .split(/(```[\s\S]*?```)/g)
    .map((block, i) => {
      if (i % 2 === 1) {
        return block;
      }
      return block
        .split(/(`[^`]+`)/g)
        .map((part, j) => (j % 2 === 1 ? part : linkifySegment(part)))
        .join("");
    })
    .join("");
}
