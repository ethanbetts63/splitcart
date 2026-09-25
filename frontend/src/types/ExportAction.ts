/**
 * Which export is in flight, so the button that started it can show a spinner
 * and the other one stays clickable. `null` when nothing is running.
 */
export type ExportAction = {
  type: 'email' | 'download';
  plan: string;
};
