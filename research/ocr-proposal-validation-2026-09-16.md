# OCR and spelling proposal validation

Job: [`6aab10f2f76d6a098a711bfe`](https://huggingface.co/jobs/rushilrawat/6aab10f2f76d6a098a711bfe)
Status: `COMPLETED`

The pinned masked-language model compared original and proposed forms for all
**10,856** records carrying spelling candidates. The first deterministic mask
seed supports 2,431 proposals, rejects 3,079, and leaves 5,346 inconclusive.
These are confidence-labelled review signals only: originals remain intact and
native review is required before any correction.

The run used 278.731 wall-clock seconds, approximately **$0.0619** at
$0.80/hour. A three-seed robustness run follows because one mask pattern is not
strong enough for final correction decisions.

## Three-seed consensus

Job [`6aab13d0f76d6a098a711c37`](https://huggingface.co/jobs/rushilrawat/6aab13d0f76d6a098a711c37)
repeated the comparison with mask seeds 17, 29, and 43. Consensus supports
**1,781** proposals, rejects **2,448**, and leaves **6,627** inconclusive. The
stricter multi-seed result supersedes the single-seed decision for review
ordering. It used 715.300 wall-clock seconds, approximately **$0.1590**.

## PDF-adapted OCR subset

Job [`6aab19235527934177eebf31`](https://huggingface.co/jobs/rushilrawat/6aab19235527934177eebf31)
used the validation-selected seed-43 adapter from the extended incoming-book
continuation. Among **1,894** OCR-source records with spelling candidates,
three-seed consensus supports **103**, rejects **491**, and leaves **1,300**
inconclusive. The much smaller supported set is the safest machine-prioritized
queue for native review; it is not an automatically corrected corpus. The job
used 207.457 wall-clock seconds, approximately **$0.0461**.
