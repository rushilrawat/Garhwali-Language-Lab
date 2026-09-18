# Balanced general/book IndicBERTv2 continuation

Updated: 2026-09-16
Job: [`6aaacf0d5527934177eeb02d`](https://huggingface.co/jobs/rushilrawat/6aaacf0d5527934177eeb02d)
Status: `COMPLETED`

Three 16,384-step seeds trained on a deterministic 50/50 mixture of 25,983
incoming-book segments and 25,983 general Garhwali segments. Selection used 256
general validation segments; all 615 PDF validation segments were scored as a
secondary domain. No test records were uploaded.

| System | General CE | General accuracy | PDF CE | PDF accuracy |
| --- | ---: | ---: | ---: | ---: |
| Base | 6.729359 | 22.3796% | 6.075329 | 24.4733% |
| Seed 17 | 5.322512 | **26.1568%** | **4.670685** | 32.2725% |
| Seed 29, CE-selected | **5.308042** | 25.6846% | 4.689353 | 32.2277% |
| Seed 43 | 5.319200 | 25.5902% | 4.697330 | **32.3622%** |

All seeds improve both domains. The job used 1,339.228 wall-clock seconds,
approximately **$0.2976** at $0.80/hour.
