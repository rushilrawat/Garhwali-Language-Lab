---
annotations_creators:
- expert-annotated
language:
- anp
- awa
- ben
- bgc
- bhb
- bhd
- bho
- bjj
- bns
- bra
- gbm
- guj
- hne
- kfg
- kfy
- mag
- mar
- mup
- noe
- pan
- raj
license: cc-by-sa-4.0
multilinguality: monolingual
task_categories:
- text-classification
task_ids:
- language-identification
dataset_info:
  features:
  - name: text
    dtype: string
  - name: label
    dtype: string
  splits:
  - name: train
    num_bytes: 3285103
    num_examples: 2138
  - name: test
    num_bytes: 1711841
    num_examples: 1152
  download_size: 1794208
  dataset_size: 4996944
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: test
    path: data/test-*
tags:
- mteb
- text
---
<!-- adapted from https://github.com/huggingface/huggingface_hub/blob/v0.30.2/src/huggingface_hub/templates/datasetcard_template.md -->

<div align="center" style="padding: 40px 20px; background-color: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05); max-width: 600px; margin: 0 auto;">
  <h1 style="font-size: 3.5rem; color: #1a1a1a; margin: 0 0 20px 0; letter-spacing: 2px; font-weight: 700;">HinDialectClassification</h1>
  <div style="font-size: 1.5rem; color: #4a4a4a; margin-bottom: 5px; font-weight: 300;">An <a href="https://github.com/embeddings-benchmark/mteb" style="color: #2c5282; font-weight: 600; text-decoration: none;" onmouseover="this.style.textDecoration='underline'" onmouseout="this.style.textDecoration='none'">MTEB</a> dataset</div>
  <div style="font-size: 0.9rem; color: #2c5282; margin-top: 10px;">Massive Text Embedding Benchmark</div>
</div>

HinDialect: 26 Hindi-related languages and dialects of the Indic Continuum in North India

|               |                                             |
|---------------|---------------------------------------------|
| Task category | t2c                              |
| Domains       | Social, Spoken, Written                               |
| Reference     | https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-4839 |


## How to evaluate on this task

You can evaluate an embedding model on this dataset using the following code:

```python
import mteb

task = mteb.get_tasks(["HinDialectClassification"])
evaluator = mteb.MTEB(task)

model = mteb.get_model(YOUR_MODEL)
evaluator.run(model)
```

<!-- Datasets want link to arxiv in readme to autolink dataset with paper -->
To learn more about how to run models on `mteb` task check out the [GitHub repitory](https://github.com/embeddings-benchmark/mteb). 

## Citation

If you use this dataset, please cite the dataset as well as [mteb](https://github.com/embeddings-benchmark/mteb), as this dataset likely includes additional processing as a part of the [MMTEB Contribution](https://github.com/embeddings-benchmark/mteb/tree/main/docs/mmteb).

```bibtex

@misc{11234/1-4839,
  author = {Bafna, Niyati and {\v Z}abokrtsk{\'y}, Zden{\v e}k and Espa{\~n}a-Bonet, Cristina and van Genabith, Josef and Kumar, Lalit "Samyak Lalit" and Suman, Sharda and Shivay, Rahul},
  copyright = {Creative Commons - Attribution-{NonCommercial}-{ShareAlike} 4.0 International ({CC} {BY}-{NC}-{SA} 4.0)},
  note = {{LINDAT}/{CLARIAH}-{CZ} digital library at the Institute of Formal and Applied Linguistics ({{\'U}FAL}), Faculty of Mathematics and Physics, Charles University},
  title = {{HinDialect} 1.1: 26 Hindi-related languages and dialects of the Indic Continuum in North India},
  url = {http://hdl.handle.net/11234/1-4839},
  year = {2022},
}


@article{enevoldsen2025mmtebmassivemultilingualtext,
  title={MMTEB: Massive Multilingual Text Embedding Benchmark},
  author={Kenneth Enevoldsen and Isaac Chung and Imene Kerboua and Márton Kardos and Ashwin Mathur and David Stap and Jay Gala and Wissam Siblini and Dominik Krzemiński and Genta Indra Winata and Saba Sturua and Saiteja Utpala and Mathieu Ciancone and Marion Schaeffer and Gabriel Sequeira and Diganta Misra and Shreeya Dhakal and Jonathan Rystrøm and Roman Solomatin and Ömer Çağatan and Akash Kundu and Martin Bernstorff and Shitao Xiao and Akshita Sukhlecha and Bhavish Pahwa and Rafał Poświata and Kranthi Kiran GV and Shawon Ashraf and Daniel Auras and Björn Plüster and Jan Philipp Harries and Loïc Magne and Isabelle Mohr and Mariya Hendriksen and Dawei Zhu and Hippolyte Gisserot-Boukhlef and Tom Aarsen and Jan Kostkan and Konrad Wojtasik and Taemin Lee and Marek Šuppa and Crystina Zhang and Roberta Rocca and Mohammed Hamdy and Andrianos Michail and John Yang and Manuel Faysse and Aleksei Vatolin and Nandan Thakur and Manan Dey and Dipam Vasani and Pranjal Chitale and Simone Tedeschi and Nguyen Tai and Artem Snegirev and Michael Günther and Mengzhou Xia and Weijia Shi and Xing Han Lù and Jordan Clive and Gayatri Krishnakumar and Anna Maksimova and Silvan Wehrli and Maria Tikhonova and Henil Panchal and Aleksandr Abramov and Malte Ostendorff and Zheng Liu and Simon Clematide and Lester James Miranda and Alena Fenogenova and Guangyu Song and Ruqiya Bin Safi and Wen-Ding Li and Alessia Borghini and Federico Cassano and Hongjin Su and Jimmy Lin and Howard Yen and Lasse Hansen and Sara Hooker and Chenghao Xiao and Vaibhav Adlakha and Orion Weller and Siva Reddy and Niklas Muennighoff},
  publisher = {arXiv},
  journal={arXiv preprint arXiv:2502.13595},
  year={2025},
  url={https://arxiv.org/abs/2502.13595},
  doi = {10.48550/arXiv.2502.13595},
}

@article{muennighoff2022mteb,
  author = {Muennighoff, Niklas and Tazi, Nouamane and Magne, Lo{\"\i}c and Reimers, Nils},
  title = {MTEB: Massive Text Embedding Benchmark},
  publisher = {arXiv},
  journal={arXiv preprint arXiv:2210.07316},
  year = {2022}
  url = {https://arxiv.org/abs/2210.07316},
  doi = {10.48550/ARXIV.2210.07316},
}
```

# Dataset Statistics
<details>
  <summary> Dataset Statistics</summary>

The following code contains the descriptive statistics from the task. These can also be obtained using:

```python
import mteb

task = mteb.get_task("HinDialectClassification")

desc_stats = task.metadata.descriptive_stats
```

```json
{
    "test": {
        "num_samples": 1152,
        "number_of_characters": 672566,
        "number_texts_intersect_with_train": 23,
        "min_text_length": 28,
        "average_text_length": 583.8246527777778,
        "max_text_length": 5970,
        "unique_text": 1144,
        "unique_labels": 21,
        "labels": {
            "bundeli-bns": {
                "count": 114
            },
            "bhojpuri-bho": {
                "count": 46
            },
            "panjabi-pan": {
                "count": 264
            },
            "bhadrawahi-bhd": {
                "count": 3
            },
            "korku-kfq": {
                "count": 62
            },
            "awadhi-awa": {
                "count": 16
            },
            "nimadi-noe": {
                "count": 55
            },
            "haryanvi-bgc": {
                "count": 194
            },
            "chhattisgarhi-hne": {
                "count": 32
            },
            "rajasthani-raj": {
                "count": 24
            },
            "magahi-mag": {
                "count": 119
            },
            "malvi-mup": {
                "count": 45
            },
            "angika-anp": {
                "count": 34
            },
            "braj-bra": {
                "count": 29
            },
            "bhili-bhb": {
                "count": 54
            },
            "kumaoni-kfy": {
                "count": 3
            },
            "garhwali-gbm": {
                "count": 45
            },
            "gujarati-guj": {
                "count": 5
            },
            "bengali-ben": {
                "count": 4
            },
            "kanauji-bjj": {
                "count": 2
            },
            "marathi-mar": {
                "count": 2
            }
        }
    },
    "train": {
        "num_samples": 2138,
        "number_of_characters": 1289774,
        "number_texts_intersect_with_train": null,
        "min_text_length": 33,
        "average_text_length": 603.2619270346117,
        "max_text_length": 15395,
        "unique_text": 2108,
        "unique_labels": 21,
        "labels": {
            "haryanvi-bgc": {
                "count": 360
            },
            "angika-anp": {
                "count": 62
            },
            "garhwali-gbm": {
                "count": 83
            },
            "malvi-mup": {
                "count": 84
            },
            "bhili-bhb": {
                "count": 101
            },
            "magahi-mag": {
                "count": 221
            },
            "braj-bra": {
                "count": 54
            },
            "panjabi-pan": {
                "count": 490
            },
            "nimadi-noe": {
                "count": 102
            },
            "bundeli-bns": {
                "count": 212
            },
            "awadhi-awa": {
                "count": 31
            },
            "korku-kfq": {
                "count": 115
            },
            "bhojpuri-bho": {
                "count": 85
            },
            "chhattisgarhi-hne": {
                "count": 60
            },
            "rajasthani-raj": {
                "count": 43
            },
            "bhadrawahi-bhd": {
                "count": 5
            },
            "gujarati-guj": {
                "count": 9
            },
            "bengali-ben": {
                "count": 8
            },
            "kumaoni-kfy": {
                "count": 6
            },
            "marathi-mar": {
                "count": 3
            },
            "kanauji-bjj": {
                "count": 4
            }
        }
    }
}
```

</details>

---
*This dataset card was automatically generated using [MTEB](https://github.com/embeddings-benchmark/mteb)*