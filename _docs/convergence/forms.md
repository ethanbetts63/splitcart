# Convergence plan — forms

**Type:** closed record. Non-normative. The binding rules are
[`forms-standard.md`](../../../freetheplatform/_docs/forms-standard.md)
(FORMS-1..11).

The conversion landed on 2026-09-25 and the session-dependent half on
2026-10-13, with [`auth-migration.md`](auth-migration.md). Five Track B forms,
five schemas, and `npm run check:forms` and `check:form-contract` holding them.
Verdicts are in
[`../../../freetheplatform/_docs/conformance/splitcart.md`](../../../freetheplatform/_docs/conformance/splitcart.md).

- **Bounds are the shared table.** `freetheplatform.security.bounds` on the
  Django side and `@freetheplatform/web-security` on the frontend; the local
  mirrors and their pinning test are gone. FORMS-8 is the package's own test.
- **FORMS-9..11 hold.** `lib/serverApi.ts` is the one reader of
  `DJANGO_API_URL`, and its `serverApiFetch` forwards the two session cookies
  and nothing else. Login, signup and both password-reset forms are Server
  Actions over it.
- **The cart rename stays a client action.** It goes through `CartContext`,
  which owns the cart's state and updates it from the answer, over the
  browser's own same-origin session.
- **The engines are registry copies,** `serializer-contract.mjs` included: it is
  scoped to splitcart in the sync because no other repo holds its forms to its
  serializers this way. The reset-password form is the one Track B form outside
  it, for the reason `scripts/check-form-contract.mjs` gives.
