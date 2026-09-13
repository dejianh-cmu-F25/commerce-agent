# Tasks: Data Quality

**Feature**: `027-data-quality` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `app/data/quality.py` (clean_text, parse_price, parse_stock, parse_tags, normalize_product, normalize_order)
- [x] T002 `app/core/settings.py` + `config/settings.yaml` + `.env.example`: `data.quality`
- [x] T003 `app/adapters/storefront_sqlite.py`: apply normalizers (repair/strict)
- [x] T004 `scripts/repair_storefront.py`
- [x] T005 `evals/data_quality_set.py` + `evals/data_quality.py`; `scripts/ci.sh`
- [x] T006 `evals/report.py`: render the data-quality section
- [x] T007 [P] `tests/unit/test_data_quality.py`, `tests/integration/test_storefront_dirty.py`
- [x] T008 Agent Note; change log entry
- [x] T009 `make ci-fast`; PR

## Dependencies

- T001 before T003/T004/T007.
- T005 before T006/T009.
- T009 last.
