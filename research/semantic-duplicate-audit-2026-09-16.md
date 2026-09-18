# Semantic duplicate and split-leakage audit

Job: [`6aaafaf85527934177eeba25`](https://huggingface.co/jobs/rushilrawat/6aaafaf85527934177eeba25)
Status: `COMPLETED`

The multilingual embedding audit examined all **114,082** text segments and
found **29,903** candidate pairs at cosine similarity 0.92 or higher. **2,839**
pairs cross split boundaries and therefore require resolution before a frozen
benchmark release. These are semantic candidates rather than confirmed copies;
no record was deleted or changed automatically.

The complete candidate file and source provenance are stored under
`data/processed/evaluation/data_quality/semantic_duplicates_v0_1/cloud_output/`.
