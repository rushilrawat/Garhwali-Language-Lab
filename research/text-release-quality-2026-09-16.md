# Text release quality audit

> Historical snapshot from 2026-09-16 (114,082 segments). The current package
> has 114,064 prepared segments; see [`finalreport.md`](../finalreport.md) for
> current release status.

**Grain:** one exact-unique text segment per split row

**Records:** 114,082

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

- Incoming-PDF segments: **27,926**
- Distinct source identifiers: **53**
- Character length: median **56**, p95 **209**, maximum **2,193**

No record was changed or removed. Model-backed semantic and language/noise audits remain additive review evidence.
