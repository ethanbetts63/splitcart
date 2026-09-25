/**
 * A request body this app hands to `JSON.stringify`.
 *
 * Deliberately `unknown` per value rather than `any`: the client serialises
 * whatever it is given and never reads into it, so the useful guarantee is
 * "an object", not the shape of its fields. A caller that needs field-level
 * typing passes a named type, which is assignable to this.
 */
export type JsonBody = Record<string, unknown>;
