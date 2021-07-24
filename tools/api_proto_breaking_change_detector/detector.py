from abc import ABC, abstractmethod
import tempfile
from rules_python.python.runfiles import runfiles
from tools.run_command import run_command
from shutil import copyfile
import re
from pathlib import Path


# generic breaking change detector for protos, extended by a wrapper class for a breaking change detector
class ProtoBreakingChangeDetector(ABC):
    # stateless
    @staticmethod
    def is_breaking(path_to_before, path_to_after):
        pass

    @staticmethod
    def lock_file_changed(path_to_before, path_to_after):
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

        if not Path(path_to_before).is_file():
            raise ValueError(f"path_to_before {path_to_before} does not exist")

        if not Path(path_to_after).is_file():
            raise ValueError(f"path_to_after {path_to_after} does not exist")

        temp_dir = tempfile.TemporaryDirectory()
        protolock_path = runfiles.Create().Rlocation(
            "com_github_nilslice_protolock/protolock_/protolock")
        protolock_args = DEFAULT_PROTOLOCK_ARGS + [
            f"--protoroot={temp_dir.name}", f"--lockdir={temp_dir.name}"
        ]
        if additional_args is not None:
            protolock_args.extend(additional_args)

        target = Path(temp_dir.name, f"{Path(path_to_before).stem}.proto")

        copyfile(path_to_before, target)

        initial_code, initial_out, initial_err = run_command(
            ' '.join([protolock_path, "init", *protolock_args]))
        initial_out, initial_err = ''.join(initial_out), ''.join(initial_err)

        if len(initial_out) > 0 or len(initial_err) > 0:
            raise ChangeDetectorInitializeError("Unexpected error during init")

        lock_location = Path(temp_dir.name, "proto.lock")
        with open(lock_location) as f:
            initial_lock = f.readlines()

        copyfile(path_to_after, target)

        final_code, final_out, final_err = run_command(
            ' '.join([protolock_path, "commit", *protolock_args]))
        final_out, final_err = ''.join(final_out), ''.join(final_err)
        with open(lock_location) as f:
            final_lock = f.readlines()

        temp_dir.cleanup()

        return (initial_code, initial_out,
                initial_err), (final_code, final_out, final_err), initial_lock, final_lock

    @staticmethod
    def is_breaking(path_to_before, path_to_after, additional_args=None):
        _, final_result, _, _ = ProtolockWrapper._run_protolock(
            path_to_before, path_to_after, additional_args)

        _, final_out, final_err = final_result

        # Ways protolock output could be indicative of a breaking change:
        # 1) stdout/stderr is nonempty
        # 2) stdout/stderr contains "CONFLICT"
        break_condition = lambda inp: len(inp) > 0 or bool(re.match(r"CONFLICT", inp))
        return break_condition(final_out) or break_condition(final_err)

    @staticmethod
    def lock_file_changed(path_to_before, path_to_after, additional_args=None):
        _, _, initial_lock, final_lock = ProtolockWrapper._run_protolock(
            path_to_before, path_to_after, additional_args)
        return any(before != after for before, after in zip(initial_lock, final_lock))
