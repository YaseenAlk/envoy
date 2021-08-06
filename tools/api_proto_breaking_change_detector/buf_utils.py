from rules_python.python.runfiles import runfiles
from pathlib import Path
from tools.run_command import run_command
from detector import ChangeDetectorInitializeError


def make_lock(target_path, lock_file_path, additional_args=None):
    buf_path = runfiles.Create().Rlocation("com_github_bufbuild_buf/bin/buf")
    yaml_file_loc = Path(".", "tools", "api_proto_breaking_change_detector", "buf.yaml")
    buf_args = [
        "--path",
        # buf requires relative pathing for roots
        str(Path(target_path).relative_to(Path(".").absolute())),
        "--config",
        str(yaml_file_loc),
    ]
    buf_args.extend(additional_args or [])

    initial_code, initial_out, initial_err = run_command(
        ' '.join([buf_path, f"build -o {lock_file_path}", *buf_args]))
    initial_out, initial_err = ''.join(initial_out), ''.join(initial_err)

    if initial_code != 0 or len(initial_out) > 0 or len(initial_err) > 0:
        raise ChangeDetectorInitializeError(
            f"Unexpected error during init:\n\tExit Status Code: {initial_code}\n\tstdout: {initial_out}\n\t stderr: {initial_err}\n"
        )
    return initial_code, initial_out, initial_err


def check_breaking():
    pass
