/* Component registry: freetheplatform/frontend/registry/src/lib/controlState.ts
   Copied, not imported. Edit the registry and re-sync; a deliberate local
   change here must be marked. See _docs/component-registry.md. */

/** Shared interaction states: the three focus treatments, and the two reasons a control is disabled. */

/** Focus ring for a box (button, link-as-button, menu toggle). An outline, so it cannot collide with the component's own shadow; `:focus-visible` only. */
export const focusRingClassName =
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]';

/** The same outline inset, for a focusable table row; an outward offset would paint over neighbouring rows. */
export const focusRowClassName =
  'focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[var(--focus-ring)]';

/**
 * Focus for a control that owns a border (input, textarea, select): the border moves and `--ring-field` fills the gap.
 * `shadow-focus` rather than `ring-*`, which shares the `box-shadow` slot with the component's own shadow.
 */
export const focusFieldClassName =
  'focus-visible:border-focus-ring focus-visible:shadow-focus focus-visible:outline-none';

/** Disabled because the app is working (a submitted form): the pointer says "wait". */
export const disabledBusyClassName = 'disabled:cursor-wait disabled:opacity-55';

/** Disabled because the control is not available yet (terms unaccepted, nothing selected): the pointer says "not allowed". */
export const disabledUnavailableClassName = 'disabled:cursor-not-allowed disabled:opacity-45';
