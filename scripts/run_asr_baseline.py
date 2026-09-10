#!/usr/bin/env python3
"""Run a small Whisper baseline and measure Garhwali WER/CER."""
import argparse
import json
import sys
import wave
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from asr_metrics import score


def read_audio(path):
    with wave.open(str(path), 'rb') as source:
        if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, 16000):
            raise ValueError(f'expected mono 16-bit 16kHz PCM: {path}')
        samples = array('h'); samples.frombytes(source.readframes(source.getnframes()))
        if sys.byteorder != 'little': samples.byteswap()
    import numpy as np
    return np.asarray(samples, dtype=np.float32) / 32768.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='openai/whisper-tiny')
    parser.add_argument('--limit', type=int, default=12)
    args = parser.parse_args()
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    processor = WhisperProcessor.from_pretrained(args.model)
    model = WhisperForConditionalGeneration.from_pretrained(args.model)
    model.eval()
    rows=[]
    source=ROOT/'data/processed/model_ready/cleaned/audio_transcripts.jsonl'
    with source.open(encoding='utf-8') as handle:
        candidates=[json.loads(line) for line in handle if json.loads(line).get('split')=='validation']
    candidates.sort(key=lambda row: row['audio_sha256'])
    totals={'word_errors':0,'reference_words':0,'character_errors':0,'reference_characters':0}
    for row in candidates[:args.limit]:
        audio=read_audio(ROOT/row['local_audio_path'])
        inputs=processor(audio, sampling_rate=16000, return_tensors='pt')
        generated=model.generate(inputs.input_features, language='hi', task='transcribe', max_new_tokens=128)
        prediction=processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
        metrics=score(row['asr_target_clean'], prediction)
        for key in totals: totals[key]+=metrics[key]
        rows.append({'audio_sha256':row['audio_sha256'],'local_audio_path':row['local_audio_path'],
                     'reference':row['asr_target_clean'],'prediction':prediction,**metrics})
        print(f"{len(rows)}/{args.limit} WER={metrics['wer']:.3f}", flush=True)
    out=ROOT/'data/processed/evaluation/asr'; out.mkdir(parents=True,exist_ok=True)
    (out/'baseline_predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    report={'model':args.model,'language_prompt':'hi','records':len(rows),**totals,
            'wer':totals['word_errors']/max(1,totals['reference_words']),
            'cer':totals['character_errors']/max(1,totals['reference_characters'])}
    (out/'baseline_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
