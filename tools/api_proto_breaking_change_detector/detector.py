""" Protocol Buffer Breaking Change Detector

This tool is used to detect "breaking changes" in protobuf files, to
ensure proper backwards-compatibility in protobuf API updates. The tool
can check for breaking changes of a single API by taking 2 .proto file
paths as input (before and after) and outputting a bool `is_breaking`.

The breaking change detector creates a temporary directory, copies in
each file to compute a protobuf "state", computes a diff of the "before"
and "after" states, and runs the diff against a set of rules to determine
if there was a breaking change.

The tool is currently implemented with buf (https://buf.build/)
"""

from tools.run_command import run_command
from buf_utils import check_breaking, make_lock
from shutil import copyfile
from pathlib import Path
import os
from typing import List


class ProtoBreakingChangeDetector(object):
    """Abstract breaking change detector interface"""

    def __init__(self, path_to_lock_file: str, path_to_changed_dir: str) -> None:
        """Initialize the configuration of the breaking change detector

        This function sets up any necessary config without actually
        running the detector against any proto files.

        #TODO change description
        Takes in a single protobuf as 2 files, in a ``before`` state
        and an ``after`` state, and checks if the ``after`` state
        violates any breaking change rules.

        Args:
            path_to_lock_file {str} -- #TODO change description
            path_to_changed_dir {str} -- #TODO change description
        """
        pass

    def run_detector(self) -> None:
        """Run the breaking change detector to detect rule violations

        This method should populate the detector's internal data such
        that `is_breaking` and `lock_file_changed` do not require any
        additional invocations to the breaking change detector.
        """
        pass

    def is_breaking(self) -> bool:
        """Return True if breaking changes were detected in the given protos"""
        pass

    def get_breaking_changes(self) -> List[str]:
        pass

    def lock_file_changed(self) -> bool:
        """Return True if the detector state file changed after being run

        This function assumes that the detector uses a lock file to
        compare "before" and "after" states of protobufs, which is
        admittedly an implementation detail. It is mostly used for
        testing, to ensure that the breaking change detector is
        checking all of the protobuf features we are interested in.
        """
        pass


BUF_STATE_FILE = "tmp.json"


class BufWrapper(ProtoBreakingChangeDetector):
    """Breaking change detector implemented with buf"""

    def __init__(
            self,
            path_to_lock_file: str,
            path_to_changed_dir: str,
            additional_args: List[str] = None,
            buf_path: str = None,
            config_file_loc: str = None) -> None:
        if not Path(path_to_lock_file).is_file():
            raise ValueError(f"path_to_lock_file {path_to_lock_file} is not a file path")

        if not Path(path_to_changed_dir).is_dir():
            raise ValueError(f"path_to_changed_dir {path_to_changed_dir} is not a valid directory")

        if Path(".").absolute() not in Path(path_to_changed_dir).parents:
            raise ValueError(
                f"path_to_changed_dir {path_to_changed_dir} must be a subdirectory of the cwd ({ Path('.').absolute() })"
            )

        self._path_to_lock_file = path_to_lock_file
        self._path_to_changed_dir = path_to_changed_dir
        self._additional_args = additional_args
        self.final_lock = None
        self._buf_path = buf_path or "buf"
        self._config_file_loc = config_file_loc

    def run_detector(self) -> None:
        with open(self._path_to_lock_file) as f:
            initial_lock = f.readlines()

        final_code, final_out, final_err = check_breaking(
            self._buf_path, self._path_to_changed_dir, self._path_to_lock_file,
            self._config_file_loc, self._additional_args)
        compressed_out, compressed_err = '\n'.join(final_out), '\n'.join(final_err)

        new_lock_location = Path(self._path_to_changed_dir, BUF_STATE_FILE)
        if len(compressed_out) == len(compressed_err) == final_code == 0:
            make_lock(
                self._buf_path,
                self._path_to_changed_dir,
                new_lock_location,
                config_file_loc=self._config_file_loc,
                additional_args=self._additional_args)
            with open(new_lock_location, "r") as f:
                self.final_lock = f.readlines()

        self.final_result = final_code, final_out, final_err
        self.initial_lock = initial_lock

    def update_lock_file(self):
        make_lock(
            self._buf_path,
            self._path_to_changed_dir,
            self._path_to_lock_file,
            config_file_loc=self._config_file_loc,
            additional_args=self._additional_args)

    def is_breaking(self) -> bool:
        final_code, final_out, final_err = self.final_result
        final_out, final_err = '\n'.join(final_out), '\n'.join(final_err)

        if final_code != 0:
            return True
        if final_out != "" or "Failure" in final_out:
            return True
        if final_err != "" or "Failure" in final_err:
            return True
        return False

    def get_breaking_changes(self) -> List[str]:
        _, final_out, _ = self.final_result
        return final_out if self.is_breaking() else []

    def lock_file_changed(self) -> bool:
        return self.final_lock is not None and any(
            before != after for before, after in zip(self.initial_lock, self.final_lock))
