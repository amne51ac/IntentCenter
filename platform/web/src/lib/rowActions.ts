/** Use when the REST API does not expose this operation for the resource yet. */
export function notifyActionUnavailable(action: string) {
  window.alert(
    `${action} is not wired in the API for this object type yet. Use bulk tools or the REST API where available.`,
  );
}
