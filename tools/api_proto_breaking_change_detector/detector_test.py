import os
import unittest

from detector import ProtolockWrapper, ChangeDetectorInitializeError


class ProtolockTests(unittest.TestCase):

    def run_protolock_test(self, testname, is_breaking, expects_changes, additional_args=None):
        # there's probably a better/safer way to navigate
        # but it seems like check_spelling_pedantic_test.py takes this approach as well
        tests_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "testdata",
            "api_proto_breaking_change_detector", "breaking" if is_breaking else "allowed")

        # check that test files exist
        current = os.path.join(tests_path, f"{testname}_current")
        changed = os.path.join(tests_path, f"{testname}_next")

        breaking_response = ProtolockWrapper.is_breaking(current, changed, additional_args)
        self.assertEqual(breaking_response, is_breaking)

        lock_file_changed_response = ProtolockWrapper.lock_file_changed(
            current, changed, additional_args)
        self.assertEqual(lock_file_changed_response, expects_changes)


class TestBreakingChanges(ProtolockTests):

    def test_change_field_id(self):
        self.run_protolock_test(
            self.test_change_field_id.__name__, is_breaking=True, expects_changes=False)

    def test_change_field_type(self):
        self.run_protolock_test(
            self.test_change_field_type.__name__, is_breaking=True, expects_changes=False)

    def test_change_field_plurality(self):
        self.run_protolock_test(
            self.test_change_field_plurality.__name__, is_breaking=True, expects_changes=False)

    def test_change_field_name(self):
        self.run_protolock_test(
            self.test_change_field_name.__name__, is_breaking=True, expects_changes=False)

    @unittest.skip("package name detection not yet added to Protolock (simply requires plugin)")
    def test_change_package_name(self):
        self.run_protolock_test(
            self.test_change_package_name.__name__, is_breaking=True, expects_changes=False)

    @unittest.skip(
        "oneof support not yet added to Protolock (requires Protolock changes AND plugin)")
    def test_change_field_from_oneof(self):
        self.run_protolock_test(
            self.test_change_field_from_oneof.__name__, is_breaking=True, expects_changes=False)

    @unittest.skip(
        "oneof support not yet added to Protolock (requires Protolock changes AND plugin)")
    def test_change_field_to_oneof(self):
        self.run_protolock_test(
            self.test_change_field_to_oneof.__name__, is_breaking=True, expects_changes=False)

    @unittest.skip("PGV field support not yet added to Protolock (simply requires plugin)")
    def test_change_pgv_field(self):
        self.run_protolock_test(
            self.test_change_pgv_field.__name__, is_breaking=True, expects_changes=False)

    @unittest.skip("PGV message option support not yet added to Protolock (simply requires plugin)")
    def test_change_pgv_message(self):
        self.run_protolock_test(
            self.test_change_pgv_message.__name__, is_breaking=True, expects_changes=False)

    @unittest.skip(
        "PGV oneof option support not yet added to Protolock (requires Protolock changes AND plugin)"
    )
    def test_change_pgv_oneof(self):
        self.run_protolock_test(
            self.test_change_pgv_oneof.__name__, is_breaking=True, expects_changes=False)


class TestAllowedChanges(ProtolockTests):

    def test_add_comment(self):
        self.run_protolock_test(
            self.test_add_comment.__name__, is_breaking=False, expects_changes=False)

    def test_add_field(self):
        self.run_protolock_test(
            self.test_add_field.__name__, is_breaking=False, expects_changes=True)

    def test_add_option(self):
        self.run_protolock_test(
            self.test_add_option.__name__, is_breaking=False, expects_changes=True)

    def test_add_enum_value(self):
        self.run_protolock_test(
            self.test_add_enum_value.__name__, is_breaking=False, expects_changes=True)

    def test_remove_and_reserve_field(self):
        self.run_protolock_test(
            self.test_remove_and_reserve_field.__name__, is_breaking=False, expects_changes=True)

    def test_force_breaking_change(self):
        self.run_protolock_test(
            self.test_force_breaking_change.__name__,
            is_breaking=False,
            expects_changes=True,
            additional_args=["--force"])


if __name__ == '__main__':
    unittest.main()
