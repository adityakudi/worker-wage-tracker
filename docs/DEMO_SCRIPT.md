# Two-minute progress demonstration

Capture target: 26 November 2026. This is a demonstration of the implemented subset, not an end-to-end attendance/payroll/dispute product launch.

The reproducible `scripts/capture_demo.py` drives Chromium against the actual production container and disposable PostgreSQL. All accounts and worksite names are synthetic fixtures. Captions are added for explanation; API responses and application screens are not mocked. The video is silent and captioned.

| Approximate time | Actual flow and message |
|---|---|
| 00:00–00:12 | Landing page. Explain the daily-wage record problem and the partial-build status. |
| 00:12–00:25 | Open the live workspace. Explain authenticated forms versus the sample-data showcase. |
| 00:25–00:38 | Create a contractor account through the real signup form; show its empty API-backed worksite list. |
| 00:38–00:52 | Create a synthetic Jaipur worksite and verify it appears. |
| 00:52–01:06 | Search and open details; explain ownership checks. |
| 01:06–01:22 | Edit the name, sign out, then log in and retrieve the saved record. |
| 01:22–01:36 | Delete the eligible unassigned record and check that an unauthenticated API request returns 401. |
| 01:36–01:48 | Register a worker through the UI. Show the honest worker placeholder rather than a fabricated wage screen. |
| 01:48–02:00 | Explain remaining attendance, ledger, disputes, relationship UI and deployment work. |

The workflow checks browser assertions, collects page errors, records six PNG screenshots, converts the browser recording to a 120-second H.264 MP4, and verifies duration with ffprobe. Evidence is committed only after the workflow's API tests, container checks, browser assertions and video-duration check pass. Downloadable workflow artifacts provide an additional copy.

The first proof is a successful workflow run, not the existence of this script. If capture fails, do not list generated files as verified deliverables. The full-product demo requirement stays open until the missing flows are implemented and demonstrated.
