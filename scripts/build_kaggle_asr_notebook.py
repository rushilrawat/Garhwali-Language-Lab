"""Write a reproducible Kaggle notebook for the reference-only VAANI ASR split."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks/garhwali_asr_reference_kaggle.ipynb"


def markdown(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text.splitlines(keepends=True)}


cells = [
    markdown("""# Garhwali ASR baseline: existing VAANI reference labels

This is a reproducibility run, not new corpus data. Input is a private Kaggle copy of 2,718 existing CC BY 4.0 ARTPARK-IISc/VAANI clips and provider reference transcripts, matching the Hugging Face `asr_reference` v0.2 view. The splits are speaker disjoint: 2,202 train / 373 validation / 143 test. The 716 records added to the earlier Kaggle input already existed upstream. No machine drafts are training targets, and the references have not been adjudicated by a native speaker. We initialize from `openai/whisper-tiny`, run one epoch, then report validation and exploratory test WER/CER. The test set has been consulted during development, so its score is not a blind benchmark. This notebook does not publish the model automatically.

Source: https://huggingface.co/datasets/ARTPARK-IISc/Vaani
"""),
    code("""import csv, json, os, random, re, unicodedata, wave, zipfile
from pathlib import Path
from collections import Counter
import numpy as np
import torch

SEED = 17
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
ROOT = Path('/kaggle/input')
manifests = list(ROOT.rglob('manifest.csv'))
if manifests:
    DATA = manifests[0].parent
else:
    zips = list(ROOT.rglob('garhwali-asr-reference-v0.2.zip'))
    if len(zips) == 1:
        DATA = Path('/kaggle/working/reference_input')
        DATA.mkdir(exist_ok=True)
        with zipfile.ZipFile(zips[0]) as archive: archive.extractall(DATA)
    else:
        import kagglehub
        DATA = Path(kagglehub.dataset_download('rushilrawat1/garhwali-asr-reference-clips-v0-1'))
with (DATA / 'manifest.csv').open(encoding='utf-8', newline='') as stream:
    rows = list(csv.DictReader(stream))
splits = {s: [r for r in rows if r['split'] == s] for s in ('train','validation','test')}
assert {s: len(v) for s,v in splits.items()} == {'train':2202,'validation':373,'test':143}
assert len({r['audio_sha256'] for r in rows}) == len(rows)
assert all((DATA / r['audio_file']).is_file() for r in rows)
print('Input:',DATA,'rows:',{s:len(v) for s,v in splits.items()},'device:',torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')
"""),
    code("""from transformers import WhisperProcessor, WhisperForConditionalGeneration

MODEL_ID = 'openai/whisper-tiny'
processor = WhisperProcessor.from_pretrained(MODEL_ID)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_ID)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
model.config.use_cache = False
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)

def read_wav(row):
    with wave.open(str(DATA / row['audio_file']), 'rb') as stream:
        assert stream.getframerate() == 16000 and stream.getnchannels() == 1 and stream.getsampwidth() == 2
        audio = np.frombuffer(stream.readframes(stream.getnframes()), dtype='<i2').astype(np.float32)/32768.0
    return audio

def features_and_labels(row):
    features = processor(read_wav(row), sampling_rate=16000, return_tensors='pt').input_features.to(device)
    labels = processor.tokenizer(row['transcript'], return_tensors='pt').input_ids.to(device)
    return features, labels

order = list(splits['train']); random.shuffle(order)
model.train(); losses=[]
for step, row in enumerate(order, 1):
    features, labels = features_and_labels(row)
    optimizer.zero_grad(set_to_none=True)
    loss = model(input_features=features, labels=labels).loss
    loss.backward(); optimizer.step()
    losses.append(float(loss.detach().cpu()))
    if step == 1 or step % 100 == 0:
        print(f'step {step}/{len(order)} loss {losses[-1]:.4f}', flush=True)
OUT = Path('/kaggle/working/garhwali-whisper-tiny-reference-v0.2')
OUT.mkdir(exist_ok=True)
model.save_pretrained(OUT); processor.save_pretrained(OUT)
print('Training complete; mean loss',sum(losses)/len(losses))
"""),
    code("""def normalize(text):
    text = unicodedata.normalize('NFKC', text).casefold()
    text = ''.join(ch if (ch.isspace() or unicodedata.category(ch)[0] in ('L','M','N')) else ' ' for ch in text)
    return ' '.join(text.split())

def edit_distance(a,b):
    previous = list(range(len(b)+1))
    for i,x in enumerate(a,1):
        current=[i]+[0]*len(b)
        for j,y in enumerate(b,1): current[j]=min(current[j-1]+1,previous[j]+1,previous[j-1]+(x!=y))
        previous=current
    return previous[-1]

def score(split):
    model.eval(); totals=Counter(); predictions=[]
    with torch.no_grad():
        for row in splits[split]:
            features=processor(read_wav(row),sampling_rate=16000,return_tensors='pt').input_features.to(device)
            tokens=model.generate(features,language='hi',task='transcribe',max_length=128)
            hypothesis=processor.batch_decode(tokens,skip_special_tokens=True)[0].strip()
            reference=row['transcript']
            ref,hyp=normalize(reference),normalize(hypothesis)
            totals['word_errors']+=edit_distance(ref.split(),hyp.split()); totals['reference_words']+=len(ref.split())
            totals['character_errors']+=edit_distance(list(ref.replace(' ','')),list(hyp.replace(' ','')))
            totals['reference_characters']+=len(ref.replace(' ','')); totals['rows']+=1
            predictions.append({'audio_sha256':row['audio_sha256'],'split':split,'reference':reference,'hypothesis':hypothesis})
    result=dict(totals); result['wer']=totals['word_errors']/max(1,totals['reference_words']); result['cer']=totals['character_errors']/max(1,totals['reference_characters'])
    with (OUT / f'{split}_predictions.jsonl').open('w',encoding='utf-8') as stream:
        for item in predictions: stream.write(json.dumps(item,ensure_ascii=False)+'\\n')
    return result

report={'model_source':MODEL_ID,'seed':SEED,'train_rows':len(order),'mean_training_loss':sum(losses)/len(losses),'validation':score('validation'),'test':score('test'),'source':'ARTPARK-IISc/Vaani','license':'CC-BY-4.0','note':'Existing reference labels only; no new examples'}
(OUT/'run_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
"""),
]

notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
print(OUT)
