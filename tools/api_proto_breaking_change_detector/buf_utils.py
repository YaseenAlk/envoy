from pathlib import Path
from tools.run_command import run_command
from detector_errors import ChangeDetectorInitializeError

# TODO decide to use this or delete it
BUF_YAML_CONTENT = """version: v1beta1
deps:
    - buf.build/beta/googleapis
    - buf.build/beta/opencensus
    - buf.build/beta/prometheus
    - buf.build/beta/opentelemetry
    - buf.build/beta/gogo
    - buf.build/beta/xds
build:
  roots:
    - .
breaking:
  ignore_unstable_packages: true
  use:
    - FIELD_SAME_ONEOF
    - FIELD_SAME_JSON_NAME
    - FIELD_SAME_NAME
    - FIELD_SAME_TYPE
    - FIELD_SAME_LABEL
    - FILE_SAME_PACKAGE
    - FIELD_NO_DELETE_UNLESS_NUMBER_RESERVED
    - FIELD_NO_DELETE_UNLESS_NAME_RESERVED
"""

def make_lock(buf_path, target_path, lock_file_path, additional_args=None):
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
        #raise ChangeDetectorInitializeError(
        raise Exception(
            f"Unexpected error during init:\n\tExit Status Code: {initial_code}\n\tstdout: {initial_out}\n\t stderr: {initial_err}\n"
        )
    return initial_code, initial_out, initial_err


def check_breaking(buf_path, target_path, lock_file_path, additional_args=None):
    yaml_file_loc = Path(".", "tools", "api_proto_breaking_change_detector", "buf.yaml")
    buf_args = [
            "--path",
            # buf requires relative pathing for roots
            str(Path(target_path).relative_to(Path(".").absolute())),
            "--config",
            str(yaml_file_loc),
    ]
    buf_args.extend(additional_args or [])

    final_code, final_out, final_err = run_command(
            ' '.join([buf_path, f"breaking --against {lock_file_path}", *buf_args]))
    final_out, final_err = ''.join(final_out), ''.join(final_err)
    return final_code, final_out, final_err

