/**
 * The JSON body an unsuccessful API response carries, when it carries one.
 *
 * Django REST Framework answers with `detail` for its own errors and this
 * project's views answer with `error` or `message`; field-level validation
 * errors arrive as arbitrary extra keys, which is what the index signature is
 * for. Values are `unknown` because a field error is a string in some views
 * and a list of strings in others, and pretending otherwise is how a `.join`
 * ends up called on a string.
 */
export type ApiErrorBody = {
  detail?: string;
  error?: string;
  message?: string;
  [field: string]: unknown;
};
