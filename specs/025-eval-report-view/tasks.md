# Tasks: Eval Report View

**Feature**: `025-eval-report-view` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `web/main.py`: `GET /report`
- [x] T002 `frontend/src/lib/report.ts` + `components/app/report-view.tsx`
- [x] T003 `frontend/src/App.tsx`: Report tab
- [x] T004 [P] `tests/integration/test_report_api.py`
- [x] T005 `docs/architecture.md`; Agent Note
- [x] T006 `scripts/ci.sh --fast`; browser checkpoint; review; PR

## Dependencies

- T001 before T004.
- T002/T003 before T006.
- T006 last.
