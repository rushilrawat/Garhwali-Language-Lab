# Developer readiness

Status: **ready for exploratory use; not a validated model release**.

The [8 October GitHub CI run](https://github.com/rushilrawat/Garhwali-Language-Lab/actions/runs/37802743148)
passed 832 tests and the frozen release snapshot check. No full training run
or new bundle release is implied by that check.

The project has a fresh-clone setup, a CPU-first text training example, an ASR
training notebook, explicit dataset contracts, and repeatable development
metrics. Human transcript review is not required to run these tools. Until
review happens, describe every loss and ASR score as provisional evidence
against automatically screened text or upstream provider references.

## Five readiness steps

| Step | Current state | Evidence / remaining limit |
| --- | --- | --- |
| 1. Fresh-clone setup | Implemented | [Developer quick start](DEVELOPER_QUICKSTART.md) installs from `requirements-dev.txt`; training uses optional `requirements-training.txt`. |
| 2. End-to-end examples | Implemented | `examples/train_text_mlm.py` trains an MLM from the public Hub text view. The [ASR notebook](../notebooks/garhwali_asr_reference_kaggle.ipynb) fine-tunes Whisper from the private Kaggle audio package. |
| 3. Data contracts | Implemented | [Dataset schema](DATASET_SCHEMA.md) documents text/speech fields, joins, split rules, rights, and review state. |
| 4. Reproducible evaluation | Provisional path implemented | Text training records a seed, dataset revision, and development loss. ASR records the input manifest hash and base-model revision and computes validation WER/CER. Text development rows come from the same train view; VAANI references remain unreviewed. |
| 5. Release check | Smoke gate implemented; no tagged developer release | The repo suite covers the deterministic text split; CI compiles the text example, invokes `--help`, and parses the Kaggle notebook code cells. CI checks the integrity of the frozen v0.1.1 bundle with `--snapshot-only`. A separate full source-freshness check finds newer local generated artifacts, so it is not evidence for a new bundle release. Model weights are not cached and the optional training stack is incomplete here; full training and the private Kaggle notebook have not been rerun from a clean account environment. |

## Run it

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python examples/search_garhwali_lexicon.py "water" --limit 3
.venv/bin/python -m pip install -r requirements-training.txt
.venv/bin/python examples/train_text_mlm.py
```

The ASR example runs in Kaggle after attaching the private dataset
`rushilrawat1/garhwali-asr-reference-clips-v0-1`. It trains on 2,202 rows and
uses 373 validation references; CPU runs are slower. Test scoring is disabled
by default because that split has been consulted in prior project work.

## Interpretation limits

- The 1,841 text rows are existing Meta transcript values. They are
  automatically screened, have no native-speaker review, and form a small
  experimental profile.
- The 2,718 VAANI labels are upstream provider references, not adjudicated
  ground truth. Validation and test district coverage is uneven.
- A deterministic text development split measures training behavior only. It
  is not an independent evaluation set.
- Setup and CI smoke checks establish that the tools are discoverable and
  syntactically usable. They do not establish model quality, a successful
  clean-clone training run, or broad Garhwali coverage.

Human review can be added later to validate references and text, then the
evaluation gate can be upgraded without changing the dataset-loading API.
