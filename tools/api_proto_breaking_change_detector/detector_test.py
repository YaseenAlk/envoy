""" Proto Breaking Change Detector Test Suite

This script evaluates breaking change detectors (e.g. buf) against
different protobuf file changes to ensure proper and consistent behavior
in `allowed`and `breaking` circumstances. Although the dependency likely
already tests for these circumstances, these specify Envoy's requirements
and ensure that tool behavior is consistent across dependency updates.
"""

from pathlib import Path
import unittest

from detector import BufWrapper, BUF_STATE_FILE, ChangeDetectorInitializeError

import tempfile
from rules_python.python.runfiles import runfiles
from tools.run_command import run_command
from shutil import copyfile
import os


class BreakingChangeDetectorTests(object):
    detector_type = None

    def run_detector_test(self, testname, is_breaking, expects_changes, additional_args=None):
        """Runs a test case for an arbitrary breaking change detector type"""

        buf_config_loc = Path(".", "tools", "api_proto_breaking_change_detector")

        tests_path = Path(
            Path(__file__).absolute().parent.parent, "testdata",
            "api_proto_breaking_change_detector", "breaking" if is_breaking else "allowed")

        current = Path(tests_path, f"{testname}_current")
        changed = Path(tests_path, f"{testname}_next")

        # buf requires protobuf files to be in a subdirectory of the yaml file
        with tempfile.TemporaryDirectory(prefix=str(Path(".").absolute()) + os.sep) as temp_dir:
            target = Path(temp_dir, f"{testname}.proto")
            copyfile(current, target)

            buf_path = runfiles.Create().Rlocation("com_github_bufbuild_buf/bin/buf")
            yaml_file_loc = Path(".", "tools", "api_proto_breaking_change_detector", "buf.yaml")
            buf_args = [
                "--path",
                # buf requires relative pathing for roots
                str(target.relative_to(Path(".").absolute())),
                "--config",
                str(yaml_file_loc),
            ]
            buf_args.extend(additional_args or [])
            lock_location = Path(temp_dir, BUF_STATE_FILE)

            initial_code, initial_out, initial_err = run_command(
                ' '.join([buf_path, f"build -o {lock_location}", *buf_args]))
            initial_out, initial_err = ''.join(initial_out), ''.join(initial_err)

            if initial_code != 0 or len(initial_out) > 0 or len(initial_err) > 0:
                raise ChangeDetectorInitializeError(
                    f"Unexpected error during init:\n\tExit Status Code: {initial_code}\n\tstdout: {initial_out}\n\t stderr: {initial_err}\n"
                )

            copyfile(changed, target)

            detector_obj = self.detector_type(lock_location, temp_dir, additional_args)
            detector_obj.run_detector()

            breaking_response = detector_obj.is_breaking()
            self.assertEqual(breaking_response, is_breaking)

            lock_file_changed_response = detector_obj.lock_file_changed()
            self.assertEqual(lock_file_changed_response, expects_changes)


class TestBreakingChanges(BreakingChangeDetectorTests):

    def run_breaking_test(self, testname):
        self.run_detector_test(testname, is_breaking=True, expects_changes=False)

    def test_change_field_id(self):
        self.run_breaking_test(self.test_change_field_id.__name__)

    def test_change_field_type(self):
        self.run_breaking_test(self.test_change_field_type.__name__)

    def test_change_field_plurality(self):
        self.run_breaking_test(self.test_change_field_plurality.__name__)

    def test_change_field_name(self):
        self.run_breaking_test(self.test_change_field_name.__name__)

    def test_change_package_name(self):
        self.run_breaking_test(self.test_change_package_name.__name__)

    def test_change_field_from_oneof(self):
        self.run_breaking_test(self.test_change_field_from_oneof.__name__)

    def test_change_field_to_oneof(self):
        self.run_breaking_test(self.test_change_field_to_oneof.__name__)

    def test_change_pgv_field(self):
        self.run_breaking_test(self.test_change_pgv_field.__name__)

    def test_change_pgv_message(self):
        self.run_breaking_test(self.test_change_pgv_message.__name__)

    def test_change_pgv_oneof(self):
        self.run_breaking_test(self.test_change_pgv_oneof.__name__)


class TestAllowedChanges(BreakingChangeDetectorTests):

    def run_allowed_test(self, testname):
        self.run_detector_test(testname, is_breaking=False, expects_changes=True)

    def test_add_comment(self):
        self.run_allowed_test(self.test_add_comment.__name__)

    def test_add_field(self):
        self.run_allowed_test(self.test_add_field.__name__)

    def test_add_option(self):
        self.run_allowed_test(self.test_add_option.__name__)

    def test_add_enum_value(self):
        self.run_allowed_test(self.test_add_enum_value.__name__)

    def test_remove_and_reserve_field(self):
        self.run_allowed_test(self.test_remove_and_reserve_field.__name__)


class BufTests(TestAllowedChanges, TestBreakingChanges, unittest.TestCase):
    detector_type = BufWrapper

    @unittest.skip("PGV field support not yet added to buf")
    def test_change_pgv_field(self):
        pass

    @unittest.skip("PGV message option support not yet added to buf")
    def test_change_pgv_message(self):
        pass

    @unittest.skip("PGV oneof option support not yet added to buf")
    def test_change_pgv_oneof(self):
        pass


if __name__ == '__main__':
    unittest.main()
