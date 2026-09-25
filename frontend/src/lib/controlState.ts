/* Component registry: freetheplatform/frontend/registry/src/lib/controlState.ts
   Copied, not imported, and kept identical to allbikes' and freethedesk's. */

/**
 * The interaction states every control family shares: the focus ring, and the
 * two reasons a control can be disabled.
 *
 * splitcart arrived with five spellings of the focus ring, all inherited
 * unmodified from the shadcn scaffold -- `ring-[3px]`, `ring-2`,
 * `ring-4`, `outline-1` drawn beside a ring, and a global `outline-ring/50`
 * reset -- and two controls, the text input and the navigation-menu trigger,
 * that removed the browser's own ring and put nothing back at all. Naming the
 * states once is what stops the sixth spelling appearing.
 *
 * Text controls keep their own focus treatment: a control that owns a border
 * says "focus" by moving that border, and a filled box has no border to move.
 */

/**
 * The ring for a control that is a box rather than a border: buttons, links
 * styled as buttons, tabs, a menu trigger.
 *
 * An outline rather than a `box-shadow`, so it cannot collide with a
 * component's own shadow and cannot be clipped by a rounded background. Drawn
 * only for `:focus-visible`, so a mouse click on a button does not paint it.
 */
export const focusRingClassName =
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]';

/**
 * The same outline drawn *inside* the element, for a focusable table row.
 *
 * A row is as wide as the table and butts up against its neighbours, so an
 * outline offset outwards paints over the rows above and below it. Negative
 * offset keeps it on the row it belongs to.
 */
export const focusRowClassName =
  'focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[var(--focus-ring)]';

/**
 * The ring for a control that owns a border: a text input, a textarea, a
 * select trigger.
 *
 * A control with a border says "focus" by moving that border, and fills the
 * space just outside it with a soft ring -- `--ring-field`, whose exact size
 * and strength is each site's own. An outline here would draw a second hard
 * edge a few pixels outside the first, which reads as two borders rather than
 * as one focused control.
 *
 * `shadow-focus` rather than `ring-*`: Tailwind's ring utilities compose into
 * the same `box-shadow` slot as a component's own shadow, so a shadowed input
 * loses one or the other. This is a single named shadow token, applied on
 * `:focus-visible` only.
 */
export const focusFieldClassName =
  'focus-visible:border-focus-ring focus-visible:shadow-focus focus-visible:outline-none';

/**
 * Disabled because the application is working: a submit that has been pressed,
 * a form mid-flight. The pointer says "wait", and the control stays legible
 * because the label it carries ("Confirming…") is the status.
 */
export const disabledBusyClassName = 'disabled:cursor-wait disabled:opacity-55';

/**
 * Disabled because the control is not available yet: nothing selected, no next
 * page to go to. The pointer says "not allowed", and the control fades further
 * back than a busy one because it is not part of what the user is doing.
 */
export const disabledUnavailableClassName = 'disabled:cursor-not-allowed disabled:opacity-45';
