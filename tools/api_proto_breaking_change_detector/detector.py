from abc import ABC, abstractmethod
import tempfile
from rules_python.python.runfiles import runfiles
import subprocess
from shutil import copyfile
import os
import re


# generic breaking change detector for protos, extended by a wrapper class for a breaking change detector
class ProtoBreakingChangeDetector(ABC):
    # stateless
    @staticmethod
    @abstractmethod
    def is_breaking(path_to_before, path_to_after):
        pass


class ChangeDetectorError(Exception):
    pass


class ChangeDetectorInitializeError(ChangeDetectorError):
    pass


DEFAULT_PROTOLOCK_ARGS = ["--plugins="]


class ProtolockWrapper(ProtoBreakingChangeDetector):

    @staticmethod
    def _run_protolock(path_to_before, path_to_after, additional_args=None):
        # 1) copy start file into temp dir
        # 2) protolock init
        # 3) copy changed file into temp dir
        # 4) protolock commit
        # 5) check for differences (if changes are breaking, there should be none)

        if not os.path.isfile(path_to_before):
            raise ValueError(f"path_to_before {path_to_before} does not exist")

        if not os.path.isfile(path_to_after):
            raise ValueError(f"path_to_after {path_to_after} does not exist")

        temp_dir = tempfile.TemporaryDirectory()
        protolock_path = runfiles.Create().Rlocation(
            "com_github_nilslice_protolock/protolock_/protolock")
        protolock_args = DEFAULT_PROTOLOCK_ARGS + [
            f"--protoroot={temp_dir.name}", f"--lockdir={temp_dir.name}"
        ]
        if additional_args is not None:
            protolock_args.extend(additional_args)

        target = os.path.join(
            temp_dir.name, f"{os.path.basename(path_to_before).split('.')[0]}.proto")

        copyfile(path_to_before, target)

        # TODO: change this to use tools/run_command.py?
        initial_result = subprocess.run([protolock_path, "init", *protolock_args],
                                        capture_output=True)

        if len(initial_result.stdout) > 0 or len(initial_result.stderr) > 0:
            raise ChangeDetectorInitializeError("Unexpected error during init")

        lock_location = os.path.join(temp_dir.name, "proto.lock")
        with open(lock_location) as f:
            initial_lock = f.readlines()

        copyfile(path_to_after, target)

        # TODO: change this to use tools/run_command.py?
        final_result = subprocess.run([protolock_path, "commit", *protolock_args],
                                      capture_output=True)
        with open(lock_location) as f:
            final_lock = f.readlines()

        temp_dir.cleanup()

        return initial_result, final_result, initial_lock, final_lock

    @staticmethod
    def is_breaking(path_to_before, path_to_after, additional_args=None):
        _, final_result, _, _ = ProtolockWrapper._run_protolock(
            path_to_before, path_to_after, additional_args)
        # Ways protolock output could be indicative of a breaking change:
        # 1) stdout/stderr is nonempty
        # 2) stdout/stderr contains "CONFLICT"
        break_condition = lambda inp: len(inp) > 0 or bool(re.match(r"CONFLICT", inp))
        return break_condition(final_result.stdout.decode('utf-8')) or break_condition(
            final_result.stderr.decode('utf-8'))

    @staticmethod
    def lock_file_changed(path_to_before, path_to_after, additional_args=None):
        _, _, initial_lock, final_lock = ProtolockWrapper._run_protolock(
            path_to_before, path_to_after, additional_args)
        return any(before != after for before, after in zip(initial_lock, final_lock))
