# Extended incoming-PDF domain continuation

Updated: 2026-09-16
Job: [`6aaac4a45527934177eeadfd`](https://huggingface.co/jobs/rushilrawat/6aaac4a45527934177eeadfd)
Status: `COMPLETED`

Three 32,768-step seeds at learning rate `5e-5` cover every one of the 25,983
book-derived training segments. Selection uses all 615 PDF validation segments;
the 1,328 PDF test segments remain unopened.

| System | Validation CE | Accuracy |
| --- | ---: | ---: |
| Base IndicBERTv2 | 6.190638 | 25.1979% |
| Seed 17 | 4.574691 | 35.5761% |
| Seed 29 | 4.560908 | 35.4002% |
| Seed 43, selected | **4.524949** | **35.8399%** |
| Three-seed mean | **4.553516** | **35.6054%** |

This improves the shorter PDF-domain run's mean loss from 4.665097 to 4.553516
and mean accuracy from 33.9197% to 35.6054%. The job used 2,242.238 wall-clock
seconds, approximately **$0.4983** at $0.80/hour.
