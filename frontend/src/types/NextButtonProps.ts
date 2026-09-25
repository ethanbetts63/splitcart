/**
 * Where the "Next" button is drawn. Two values, because there are two places
 * it appears and they are different things rather than two sizes of one thing:
 * `inline` is the button at the end of the cart dialog, sitting in the flow
 * after the item list; `floating` is the persistent call to action pinned to
 * the corner of the browsing pages once the cart has something in it.
 *
 * This replaced an open `className` passthrough that the floating call site
 * used to reposition, resize and re-radius the button from the outside — the
 * shape `component-registry.md` REG-6 calls drift wearing a prop's clothes.
 * The two appearances are now named here, so adding a third is a decision
 * made in this file rather than a class string invented at a call site.
 */
export type NextButtonPlacement = 'inline' | 'floating';

export interface NextButtonProps {
  onAfterNavigate?: () => void;
  placement?: NextButtonPlacement;
}
