# Text release quality audit

**Grain:** one exact-unique text segment per split row

**Records:** 151,690

## Split and integrity checks

| Check | Count | Status |
| --- | ---: | --- |
| empty_text | 0 | pass |
| duplicate_segment_ids_within_splits | 0 | pass |
| train_validation_overlap | 0 | pass |
| train_test_overlap | 0 | pass |
| validation_test_overlap | 0 | pass |
| missing_source_id | 0 | pass |
| missing_rights_status | 0 | pass |

## Coverage

- Incoming-PDF segments: **27,907**
- Distinct source identifiers: **61**
- Character length: median **60**, p95 **259**, maximum **8,665**

No record was changed or removed. Model-backed semantic and language/noise audits remain additive review evidence.
