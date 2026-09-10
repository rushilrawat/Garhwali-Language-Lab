"""Checkpointed orchestration for the deterministic Garhwali ingestion pipeline."""

import argparse
import json
import operator
from pathlib import Path
from typing import Annotated, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

import collect_online
import dedup_report
import verify_ingestion


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / 'data' / 'cache' / 'ingestion-graph.sqlite'


class IngestionState(TypedDict, total=False):
    wave: str
    completed_steps: Annotated[list[str], operator.add]
    status: str


def wave_actions(wave):
    actions = {
        'fourth': ('fourth_wave_acquire', 'fourth_wave_extract'),
        'fifth': ('fifth_wave_acquire', 'fifth_wave_extract'),
        'sixth': ('sixth_wave_acquire', 'sixth_wave_extract'),
        'seventh': ('seventh_wave_acquire', 'seventh_wave_extract'),
        'eighth': ('eighth_wave_acquire', 'eighth_wave_extract'),
        'ninth': ('ninth_wave_acquire', 'ninth_wave_extract'),
    }
    try:
        return actions[wave]
    except KeyError as exc:
        raise ValueError(f'Unknown ingestion wave: {wave}') from exc


def retryable_acquisition_error(error):
    if not isinstance(error, RuntimeError):
        return False
    message = str(error).lower()
    return any(marker in message for marker in (
        'http 429', 'http 500', 'http 502', 'http 503', 'http 504',
        'timed out', 'timeout', 'temporarily unavailable', 'connection reset',
    ))


def default_acquire(wave):
    acquire_action, _ = wave_actions(wave)
    getattr(collect_online, acquire_action)()


def default_extract(wave):
    _, extract_action = wave_actions(wave)
    getattr(collect_online, extract_action)()


def build_ingestion_graph(*, acquire=default_acquire, extract=default_extract,
                          dedup=dedup_report.main, verify=verify_ingestion.main,
                          checkpointer=None):
    def acquire_node(state):
        acquire(state['wave'])
        return {'completed_steps': ['acquire'], 'status': 'acquired'}

    def extract_node(state):
        extract(state['wave'])
        return {'completed_steps': ['extract'], 'status': 'extracted'}

    def dedup_node(_state):
        dedup()
        return {'completed_steps': ['dedup'], 'status': 'deduplicated'}

    def verify_node(_state):
        verify()
        return {'completed_steps': ['verify'], 'status': 'complete'}

    builder = StateGraph(IngestionState)
    builder.add_node('acquire', acquire_node, retry_policy=RetryPolicy(
        max_attempts=4, initial_interval=2.0, backoff_factor=2.0,
        max_interval=30.0, jitter=True, retry_on=retryable_acquisition_error))
    builder.add_node('extract', extract_node)
    builder.add_node('dedup', dedup_node)
    builder.add_node('verify', verify_node)
    builder.add_edge(START, 'acquire')
    builder.add_edge('acquire', 'extract')
    builder.add_edge('extract', 'dedup')
    builder.add_edge('dedup', 'verify')
    builder.add_edge('verify', END)
    return builder.compile(checkpointer=checkpointer)


def run_graph(command, wave, run_id, db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    config = {'configurable': {'thread_id': run_id}}
    with SqliteSaver.from_conn_string(str(db_path)) as saver:
        graph = build_ingestion_graph(checkpointer=saver)
        if command == 'status':
            state = graph.get_state(config)
            return dict(state.values) if state.values else {'status': 'not_started'}
        if command == 'resume':
            return graph.invoke(None, config)
        return graph.invoke({'wave': wave, 'completed_steps': [], 'status': 'started'}, config)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'resume', 'status'])
    parser.add_argument('--wave', choices=['fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth'])
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    if args.command == 'run' and not args.wave:
        parser.error('--wave is required for run')
    result = run_graph(args.command, args.wave, args.run_id, args.db)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
