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

from pathlib import Path
from typing import List

from buf_utils import check_breaking, make_lock, pull_buf_deps
from detector_errors import ChangeDetectorError


class ProtoBreakingChangeDetector(object):
    """Abstract breaking change detector interface"""

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
        """Return a list of strings containing breaking changes output by the tool"""
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


class BufWrapper(ProtoBreakingChangeDetector):
    """Breaking change detector implemented with buf"""

    def __init__(
            self,
            path_to_changed_dir: str,
            additional_args: List[str] = None,
            buf_path: str = None,
            config_file_loc: str = None,
            path_to_lock_file: str = None,
            git_ref: str = None,
            git_path: str = None) -> None:
        """Initialize the configuration of buf

        This function sets up any necessary config without actually
        running buf against any proto files.

        BufWrapper takes a path to a directory containing proto files
        as input, and it checks if these proto files break any changes
        from a given initial state.

        The initial state can be input in 2 different ways: as a lock
        file, or as a git ref. In the lock file mode, __init__ expects
        an absolute path to a lock file. In the git mode, __init__
        expects a git ref string, as well as an absolute path to a .git
        file for the repository. Note that exactly one mode must be used
        for the initial state.

        Args:
            path_to_changed_dir {str} -- absolute path to a directory containing proto files in the after state
            buf_path {str} -- path to the buf binary (default: "buf")
            additional_args {List[str]} -- additional arguments passed into the buf binary invocations
            config_file_loc {str} -- absolute path to buf.yaml configuration file (if not provided, uses default buf configuration)
            
            If using lock file mode:
                path_to_lock_file {str} -- absolute path to the lock file representing the initial state (must be provided if using lock file mode)
            If using git ref mode:
                git_ref {str} -- git reference to use for the initial state of the protos (typically a commit hash) (must be provided if using git mode)
                git_path {str} -- absolute path to .git file for the repository of interest (must be provided if using git mode)
        """
        if path_to_lock_file and not Path(path_to_lock_file).is_file():
            raise ValueError(f"path_to_lock_file {path_to_lock_file} is not a file path")

        if not Path(path_to_changed_dir).is_dir():
            raise ValueError(f"path_to_changed_dir {path_to_changed_dir} is not a valid directory")

        if Path.cwd() not in Path(path_to_changed_dir).parents:
            raise ValueError(
                f"path_to_changed_dir {path_to_changed_dir} must be a subdirectory of the cwd ({ Path.cwd() })"
            )

        if bool(path_to_lock_file) == bool(git_ref):
            raise ValueError("Expecting either a path to a lock file or a git ref, but not both")
        if bool(git_ref) != bool(git_path):
            raise ChangeDetectorError(
                "If using git mode, expecting a git ref and a path to .git file")

        self._path_to_changed_dir = path_to_changed_dir
        self._additional_args = additional_args
        self._final_lock = None
        self._buf_path = buf_path or "buf"
        self._config_file_loc = config_file_loc
        self._path_to_lock_file = path_to_lock_file
        self._git_ref = git_ref
        self._git_path = git_path

        if self._path_to_lock_file:
            locktype = Path(self._path_to_lock_file).suffix
            self._is_lock_text_file = locktype == '.json'

        pull_buf_deps(
            self._buf_path,
            self._path_to_changed_dir,
            config_file_loc=self._config_file_loc,
            additional_args=self._additional_args)

    def run_detector(self) -> None:
        if self._path_to_lock_file:
            if self._is_lock_text_file:
                with open(self._path_to_lock_file, mode='r') as f:
                    self._initial_lock = f.readlines()
            else:
                with open(self._path_to_lock_file, mode='rb') as f:
                    self._initial_lock = f.read()

        self._final_result = check_breaking(
            self._buf_path,
            self._path_to_changed_dir,
            config_file_loc=self._config_file_loc,
            additional_args=self._additional_args,
            lock_file_path=self._path_to_lock_file,
            git_ref=self._git_ref,
            git_path=self._git_path)

    def update_lock_file(self, force=False):
        if not self._path_to_lock_file:
            raise ChangeDetectorError(
                "update_lock_file invoked while detector is being run in git mode")

        if not force and self.is_breaking():
            return

        make_lock(
            self._buf_path,
            self._path_to_changed_dir,
            self._path_to_lock_file,
            config_file_loc=self._config_file_loc,
            additional_args=self._additional_args)
        if self._is_lock_text_file:
            with open(self._path_to_lock_file, mode='r') as f:
                self._final_lock = f.readlines()
        else:
            with open(self._path_to_lock_file, mode='rb') as f:
                self._final_lock = f.read()

    def is_breaking(self) -> bool:
        final_code, final_out, final_err = self._final_result
        final_out, final_err = '\n'.join(final_out), '\n'.join(final_err)

        if final_err != "":
            raise ChangeDetectorError(f"Error from buf: {final_err}")

        if final_code != 0:
            return True
        if final_out != "":
            return True
        return False

    def get_breaking_changes(self) -> List[str]:
        _, final_out, _ = self._final_result
        return filter(lambda x: len(x) > 0, final_out) if self.is_breaking() else []

    def lock_file_changed(self) -> bool:
        if not self._path_to_lock_file:
            raise ChangeDetectorError(
                "lock_file_changed invoked while detector is being run in git mode")

        if not self._final_lock:
            return False
        if not self._is_lock_text_file:
            return self._initial_lock != self._final_lock
        else:
            return any(
                before != after for before, after in zip(self._initial_lock, self._final_lock))
