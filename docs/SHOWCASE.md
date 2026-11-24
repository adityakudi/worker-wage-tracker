# Frontend showcase — 24 November 2026

The frontend now has a cinematic charcoal/amber landing page and a responsive interactive design preview. Original visual direction uses abstract structural beams and a wage-record motif, inspired by the presentation approach of the supplied UNSTABLE FORGE reference. No third-party artwork, video or copy was reused.

## How to explore

Run the existing frontend dev command. The landing page opens at `/`; choose Explore the demo for the sample workspace or Open workspace for the original API-connected screens. Direct links `/#demo` and `/#live` also work. Production API calls require VITE_API_BASE_URL; local requests continue to use the existing Vite proxy.

The sample workspace includes overview, worksite cards, searchable workers, details, local attendance toggles, illustrative payments and working sample CSV export. Sample wages reconcile to earnings of INR 13,925, payments/advances of INR 9,900 and an outstanding balance of INR 4,025.

These are design-preview interactions. They do not establish completion of persistent attendance, payment, reporting or dispute features. The API-connected signup/login and worksite flows remain separate; production backend deployment and database integration are still pending.

## Verification

- Vite production build passed.
- Browser checked landing, demo navigation, worker search and detail view, attendance toggle, payments, reports and CSV download.
- Searching Sunita returns only that worker; membership/site labels use stable sample records after filtering.
- Keyboard Escape closes the sample worker detail modal.
- CSS includes mobile layouts and reduced-motion preferences. Small-screen viewport testing is still pending.
- The showcase video uses captured frontend screens, animated title/caption treatments and an original synthesized ambient bed. It is a design showcase rather than a complete end-to-end product demo.
