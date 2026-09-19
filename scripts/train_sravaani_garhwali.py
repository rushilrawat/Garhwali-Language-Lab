#!/usr/bin/env python3
"""Plan or run decoder-only SraVaani adaptation on strict Garhwali references."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tarfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/model_ready/sravaani_finetune'
PACKAGE_REPORT = DATA / 'report.json'
CHECKPOINT = ROOT / '.cache/sravaani-finetune/SraVaani-nemo-checkpoint.nemo'
OUTPUT = ROOT / 'models/sravaani-garhwali-decoder-pilot-v0.1.nemo'
EXPERIMENTS = ROOT / 'models/sravaani-garhwali-decoder-pilot-v0.1'
PLAN_OUTPUT = ROOT / 'data/processed/evaluation/asr/sravaani_finetune/plan.json'
TRAINING_REPOSITORY = 'https://github.com/ARTPARK-Speech-Models/SraVaani'
TRAINING_REVISION = '11026fa0f97386ae05270872d899800151b2a8ef'
OFFICIAL_CHECKPOINT_URL = (
    'https://drive.usercontent.google.com/download?'
    'id=1v5VaYibAaDSFuWvROsPbCzeG3iM6VbxY&export=download&confirm=t'
)
OFFICIAL_CHECKPOINT_BYTES = 1_796_208_640
OFFICIAL_CHECKPOINT_SHA256 = 'cb206f88afbe179d10229a8002e92c74789eed77557ef38a33533e26b69067af'
CLOUD_HARDWARE = 'l4x1'
CLOUD_HOURLY_USD = 0.80
CLOUD_TIMEOUT_HOURS = 6

BATCH_SIZE = 4
ACCUMULATE_GRAD_BATCHES = 8
EPOCHS = 2
LEARNING_RATE = 1e-4
MIN_LEARNING_RATE = 1e-6
WARMUP_STEPS = 10
WEIGHT_DECAY = 1e-3


def compute_optimizer_steps(records, batch_size, accumulate_grad_batches, epochs):
    microbatches = math.ceil(records / batch_size)
    return math.ceil(microbatches / accumulate_grad_batches) * epochs


def build_training_plan(package):
    if package.get('package_status') != 'ready_for_nemo_cuda_training':
        raise ValueError('SraVaani NeMo data package is not ready')
    if any(package['leakage'].values()):
        raise ValueError('SraVaani NeMo data package has split leakage')
    if not package.get('test_split_held_out_from_training'):
        raise ValueError('SraVaani test split is not held out')
    train = package['splits']['train']
    validation = package['splits']['validation']
    test = package['splits']['test']
    return {
        'run_id': 'garhwali-sravaani-decoder-only-adaptation-pilot-v0.1',
        'model_id': 'ARTPARK-IISc/SraVaani-1.0',
        'training_repository': TRAINING_REPOSITORY,
        'training_repository_revision': TRAINING_REVISION,
        'adaptation_scope': 'decoder_and_joint_only_encoder_frozen',
        'training_records': train['records'],
        'training_audio_hours': train['duration_seconds'] / 3600,
        'validation_records': validation['records'],
        'validation_audio_hours': validation['duration_seconds'] / 3600,
        'held_out_test_records': test['records'],
        'held_out_test_audio_hours': test['duration_seconds'] / 3600,
        'batch_size': BATCH_SIZE,
        'accumulate_grad_batches': ACCUMULATE_GRAD_BATCHES,
        'effective_batch_size': BATCH_SIZE * ACCUMULATE_GRAD_BATCHES,
        'epochs': EPOCHS,
        'optimizer_steps': compute_optimizer_steps(
            train['records'], BATCH_SIZE, ACCUMULATE_GRAD_BATCHES, EPOCHS
        ),
        'optimizer': 'AdamW',
        'learning_rate': LEARNING_RATE,
        'weight_decay': WEIGHT_DECAY,
        'scheduler': 'CosineAnnealing',
        'warmup_steps': WARMUP_STEPS,
        'minimum_learning_rate': MIN_LEARNING_RATE,
        'gradient_clip': 1.0,
        'selection_metric': 'validation_wer',
        'final_test_policy': 'run_once_after_validation_selection',
        'machine_labels_used': False,
        'base_checkpoint': {
            'url': OFFICIAL_CHECKPOINT_URL,
            'bytes': OFFICIAL_CHECKPOINT_BYTES,
            'sha256': OFFICIAL_CHECKPOINT_SHA256,
            'availability': 'official_direct_download',
            'local_copy_required': False,
        },
        'cloud_job': {
            'hardware': CLOUD_HARDWARE,
            'gpu_memory_gb': 24,
            'timeout_hours': CLOUD_TIMEOUT_HOURS,
            'hourly_compute_cost_usd': CLOUD_HOURLY_USD,
            'maximum_compute_cost_usd': round(
                CLOUD_HOURLY_USD * CLOUD_TIMEOUT_HOURS, 2
            ),
            'billing_status': 'positive_huggingface_credit_required',
        },
    }


def external_dependency_status(checkpoint, cuda_available):
    missing = []
    if not Path(checkpoint).is_file():
        missing.append('sravaani_nemo_checkpoint')
    if not cuda_available:
        missing.append('cuda_capable_nvidia_gpu')
    return {
        'status': 'ready' if not missing else 'blocked_external_dependencies',
        'missing': missing,
    }


def cuda_available():
    try:
        import torch
    except ImportError:
        return False
    return torch.cuda.is_available()


def write_plan(plan, output=PLAN_OUTPUT):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def validate_checkpoint_file(
    checkpoint,
    expected_bytes=OFFICIAL_CHECKPOINT_BYTES,
    expected_sha256=OFFICIAL_CHECKPOINT_SHA256,
):
    checkpoint = Path(checkpoint)
    if not checkpoint.is_file():
        raise ValueError('SraVaani NeMo checkpoint is missing')
    size = checkpoint.stat().st_size
    if expected_bytes is not None and size != expected_bytes:
        raise ValueError(
            f'SraVaani NeMo checkpoint size is {size}; expected {expected_bytes}'
        )
    digest = sha256_file(checkpoint)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(
            f'SraVaani NeMo checkpoint SHA-256 is {digest}; '
            f'expected {expected_sha256}'
        )
    if not tarfile.is_tarfile(checkpoint):
        raise ValueError('SraVaani NeMo checkpoint is not a readable tar archive')
    return {
        'path': str(checkpoint), 'bytes': size, 'sha256': digest,
        'tar_valid': True,
    }


def download_checkpoint(
    checkpoint=CHECKPOINT,
    url=OFFICIAL_CHECKPOINT_URL,
    expected_bytes=OFFICIAL_CHECKPOINT_BYTES,
    expected_sha256=OFFICIAL_CHECKPOINT_SHA256,
):
    checkpoint = Path(checkpoint)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    partial = checkpoint.with_suffix(checkpoint.suffix + '.partial')
    try:
        with urllib.request.urlopen(url, timeout=120) as response, partial.open('wb') as target:
            while chunk := response.read(8 * 1024 * 1024):
                target.write(chunk)
        validation = validate_checkpoint_file(
            partial, expected_bytes, expected_sha256
        )
        partial.replace(checkpoint)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return {**validation, 'path': str(checkpoint), 'source_url': url}


def execute_training(
    plan,
    checkpoint=CHECKPOINT,
    data=DATA,
    output=OUTPUT,
    experiments=EXPERIMENTS,
):
    checkpoint = Path(checkpoint)
    validate_checkpoint_file(checkpoint)
    if not cuda_available():
        raise RuntimeError('SraVaani fine-tuning requires a CUDA-capable NVIDIA GPU')

    import lightning.pytorch as pl
    from nemo.collections.asr.models import EncDecHybridRNNTCTCBPEModel
    from nemo.utils.exp_manager import exp_manager
    from omegaconf import OmegaConf, open_dict

    data = Path(data)
    output = Path(output)
    experiments = Path(experiments)
    model = EncDecHybridRNNTCTCBPEModel.restore_from(str(checkpoint))
    model.encoder.freeze()
    with open_dict(model.cfg):
        model.cfg.train_ds.manifest_filepath = str(data / 'train/shard_0000.json')
        model.cfg.train_ds.tarred_audio_filepaths = str(data / 'train/shard_0000.tar')
        model.cfg.train_ds.is_tarred = True
        model.cfg.train_ds.shuffle_n = 2048
        model.cfg.train_ds.batch_size = BATCH_SIZE
        model.cfg.train_ds.num_workers = 1
        model.cfg.train_ds.pin_memory = True

        model.cfg.validation_ds.manifest_filepath = str(
            data / 'validation/shard_0000.json'
        )
        model.cfg.validation_ds.tarred_audio_filepaths = str(
            data / 'validation/shard_0000.tar'
        )
        model.cfg.validation_ds.is_tarred = True
        model.cfg.validation_ds.batch_size = BATCH_SIZE
        model.cfg.validation_ds.num_workers = 1

        model.cfg.optim.lr = LEARNING_RATE
        model.cfg.optim.name = 'adamw'
        model.cfg.optim.weight_decay = WEIGHT_DECAY
        model.cfg.optim.sched = OmegaConf.create({
            'name': 'CosineAnnealing',
            'warmup_steps': WARMUP_STEPS,
            'max_steps': plan['optimizer_steps'],
            'min_lr': MIN_LEARNING_RATE,
        })

    model.setup_training_data(model.cfg.train_ds)
    model.setup_validation_data(model.cfg.validation_ds)
    model.setup_optimization(model.cfg.optim)
    trainer = pl.Trainer(
        devices=1,
        accelerator='gpu',
        max_epochs=EPOCHS,
        accumulate_grad_batches=ACCUMULATE_GRAD_BATCHES,
        gradient_clip_val=1.0,
        val_check_interval=1.0,
        log_every_n_steps=10,
        logger=False,
        enable_checkpointing=False,
    )
    exp_manager(trainer, {
        'exp_dir': str(experiments),
        'name': 'training',
        'create_tensorboard_logger': True,
        'create_checkpoint_callback': True,
        'checkpoint_callback_params': {
            'monitor': 'val_wer',
            'mode': 'min',
            'save_top_k': 3,
        },
    })
    trainer.fit(model)
    output.parent.mkdir(parents=True, exist_ok=True)
    model.save_to(str(output))
    return {
        **plan,
        'status': 'training_completed',
        'output_checkpoint': str(output),
        'global_step': trainer.global_step,
    }


def run(
    package_report=PACKAGE_REPORT,
    checkpoint=CHECKPOINT,
    execute=False,
    data=DATA,
    output=OUTPUT,
    experiments=EXPERIMENTS,
    plan_output=PLAN_OUTPUT,
    download_checkpoint_requested=False,
):
    package = json.loads(Path(package_report).read_text(encoding='utf-8'))
    plan = build_training_plan(package)
    if download_checkpoint_requested:
        if Path(checkpoint).is_file():
            validate_checkpoint_file(checkpoint)
        else:
            download_checkpoint(checkpoint)
    dependencies = external_dependency_status(checkpoint, cuda_available())
    result = {**plan, 'external_dependencies': dependencies}
    if execute:
        if dependencies['status'] != 'ready':
            raise RuntimeError(
                'Missing SraVaani training dependencies: '
                + ', '.join(dependencies['missing'])
            )
        result = execute_training(plan, checkpoint, data, output, experiments)
    write_plan(result, plan_output)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package-report', type=Path, default=PACKAGE_REPORT)
    parser.add_argument('--checkpoint', type=Path, default=CHECKPOINT)
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--experiments', type=Path, default=EXPERIMENTS)
    parser.add_argument('--plan-output', type=Path, default=PLAN_OUTPUT)
    parser.add_argument('--download-checkpoint', action='store_true')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    print(json.dumps(
        run(
            args.package_report,
            args.checkpoint,
            args.execute,
            args.data,
            args.output,
            args.experiments,
            args.plan_output,
            args.download_checkpoint,
        ),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))


if __name__ == '__main__':
    main()
