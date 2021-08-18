from pathlib import Path
from tools.run_command import run_command
from detector_errors import ChangeDetectorInitializeError
import os

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


def _generate_buf_args(target_path, config_file_loc, additional_args):
    buf_args = [
        "--path",
        # buf requires relative pathing for roots
        str(Path(target_path).relative_to(Path(".").absolute())),
    ]

    if config_file_loc:
        buf_args.extend(["--config", str(config_file_loc)])

    buf_args.extend(additional_args or [])

    return buf_args


def pull_buf_deps(buf_path, target_path, config_file_loc=None, additional_args=None):
    # TODO: reconsider if this cd is necessary
    if config_file_loc:
        os.chdir(Path(config_file_loc).parent)

    buf_args = _generate_buf_args(target_path, config_file_loc, additional_args)

    update_code, _, update_err = run_command(f'{buf_path} mod update')
    # for some reason buf prints out the "downloading..." lines on stderr
    if update_code != 0:
        raise ChangeDetectorInitializeError(
            f'Error running `buf mod update`: exit status code {update_code} | stderr: {update_err}'
        )

    build_code, build_out, build_err = run_command(' '.join([f'{buf_path} build', *buf_args]))
    build_out, build_err = ''.join(build_out), ''.join(build_err)
    if build_code != 0:
        raise ChangeDetectorInitializeError(
            f'Error running `buf build` after updating deps: exit status code {build_code} | stdout: {build_out} | stderr: {build_err}'
        )


def make_lock(buf_path, target_path, lock_file_path, config_file_loc=None, additional_args=None):
    buf_args = _generate_buf_args(target_path, config_file_loc, additional_args)

    initial_code, initial_out, initial_err = run_command(
        ' '.join([buf_path, f"build -o {lock_file_path}", *buf_args]))
    initial_out, initial_err = ''.join(initial_out), ''.join(initial_err)

    if initial_code != 0 or len(initial_out) > 0 or len(initial_err) > 0:
        raise ChangeDetectorInitializeError(
            f"Unexpected error during init:\n\tExit Status Code: {initial_code}\n\tstdout: {initial_out}\n\t stderr: {initial_err}\n"
        )
    return initial_code, initial_out, initial_err


def check_breaking(
        buf_path, target_path, lock_file_path, config_file_loc=None, additional_args=None):
    buf_args = _generate_buf_args(target_path, config_file_loc, additional_args)

    final_code, final_out, final_err = run_command(
        ' '.join([buf_path, f"breaking --against {lock_file_path}", *buf_args]))
    return final_code, final_out, final_err
