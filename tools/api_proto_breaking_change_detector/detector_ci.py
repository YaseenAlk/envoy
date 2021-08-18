#!/usr/bin/env python

import argparse
import sys
from pathlib import Path
from detector import BufWrapper
from detector_errors import ChangeDetectorError
from buf_utils import make_lock, pull_buf_deps

API_DIR = Path("api").resolve()
LOCK_FILE_DIR = Path(API_DIR, "proto_snapshot.bin").resolve()
CONFIG_FILE_LOC = Path(API_DIR, "buf.yaml")
BUF_PATH = "buf"  # TODO: figure out where to find buf


def update_lock_file():
    """Returns True if there was a failure"""
    if not (LOCK_FILE_DIR.exists() and LOCK_FILE_DIR.is_file()):
        raise ChangeDetectorError(f'Expected lock file at {LOCK_FILE_DIR} but did not find one')

    detector = BufWrapper(
        LOCK_FILE_DIR, API_DIR, buf_path=BUF_PATH, config_file_loc=CONFIG_FILE_LOC)
    detector.update_lock_file(force=True)
    return False


def detect_breaking_changes():
    """Returns True if there was a failure"""
    if not (LOCK_FILE_DIR.exists() and LOCK_FILE_DIR.is_file()):
        raise ChangeDetectorError(f'Expected lock file at {LOCK_FILE_DIR} but did not find one')

    detector = BufWrapper(
        LOCK_FILE_DIR, API_DIR, buf_path=BUF_PATH, config_file_loc=CONFIG_FILE_LOC)
    detector.run_detector()
    breaking = detector.is_breaking()

    if breaking:
        print('Breaking changes detected in api protobufs:')
        for i, breaking_change in enumerate(detector.get_breaking_changes()):
            print(f'\t{i}: {breaking_change}')
        print(
            "ERROR: non-backwards-compatible changes detected in api protobufs. If intentional, run 'tools/api_proto_breaking_change_detector/detector_ci.sh fix' to update lock file"
        )
    return breaking


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Tool to detect breaking changes in api protobufs.')
    parser.add_argument(
        'action',
        choices=['check', 'fix'],
        default='check',
        help='Enforce backwards compatibility in api protobufs.')
    args = parser.parse_args()

    exit_status = 0
    if args.action == 'check':
        exit_status &= detect_breaking_changes()
    elif args.action == 'fix':
        exit_status &= update_lock_file()

    sys.exit(exit_status)
