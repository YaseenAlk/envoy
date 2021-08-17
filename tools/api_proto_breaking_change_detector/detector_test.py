""" Proto Breaking Change Detector Test Suite

This script evaluates breaking change detectors (e.g. buf) against
different protobuf file changes to ensure proper and consistent behavior
in `allowed`and `breaking` circumstances. Although the dependency likely
already tests for these circumstances, these specify Envoy's requirements
and ensure that tool behavior is consistent across dependency updates.
"""

from pathlib import Path
import unittest

from detector import BufWrapper, BUF_STATE_FILE
from detector_errors import ChangeDetectorInitializeError

import tempfile
from rules_python.python.runfiles import runfiles
from tools.run_command import run_command
from shutil import copyfile
import os
from buf_utils import make_lock, check_breaking
from typing import Tuple


class BreakingChangeDetectorTests(object):
    detector_type = None

    def initialize_test(self, testname, current_file, changed_file, additional_args=None):
        """Initializes a test case by creating a lock file

        Arguments:
            testname {str} -- name of the test case, must match testdata file name
            current_file {str} -- absolute path to the .proto file in the "before" state
            changed_file {str} -- absolute path to the .proto file in the "after" state
        
        Returns #TODO documentation?
        """
        pass

    def create_detector(self, lock_location, changed_directory, additional_args=None):
        pass

    def run_detector_test(self, testname, is_breaking, expects_changes, additional_args=None):
        """Runs a test case for an arbitrary breaking change detector type"""
        tests_path = Path(
            Path(__file__).absolute().parent.parent, "testdata",
            "api_proto_breaking_change_detector", "breaking" if is_breaking else "allowed")

        current = Path(tests_path, f"{testname}_current")
        changed = Path(tests_path, f"{testname}_next")

        # buf requires protobuf files to be in a subdirectory of the yaml file
        with tempfile.TemporaryDirectory(prefix=str(Path(".").absolute()) + os.sep) as temp_dir:
            lock_location, changed_dir = self.initialize_test(
                testname, temp_dir, current, changed, additional_args)

            detector_obj = self.create_detector(lock_location, changed_dir, additional_args)
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

    def initialize_test(
            self, testname, target_path, current_file, changed_file, additional_args=None):
        target = Path(target_path, f"{testname}.proto")
        copyfile(current_file, target)
        lock_location = Path(target_path, BUF_STATE_FILE)

        make_lock(runfiles.Create().Rlocation("com_github_bufbuild_buf/bin/buf"), 
            target_path, lock_location, additional_args)

        copyfile(changed_file, target)

        return lock_location, target_path
    
    def create_detector(self, lock_location, changed_directory, additional_args=None):
        return BufWrapper(lock_location, changed_directory, additional_args=additional_args, buf_path=runfiles.Create().Rlocation("com_github_bufbuild_buf/bin/buf"))

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
