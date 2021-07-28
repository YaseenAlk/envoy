from pathlib import Path
import unittest

from detector import BufWrapper, ChangeDetectorInitializeError


class BufTests(unittest.TestCase):

    def run_buf_test(self, testname, is_breaking, expects_changes, additional_args=None):
        tests_path = Path(
            Path(__file__).absolute().parent.parent, "testdata",
            "api_proto_breaking_change_detector", "breaking" if is_breaking else "allowed")

        current = Path(tests_path, f"{testname}_current")
        changed = Path(tests_path, f"{testname}_next")

        breaking_response = BufWrapper.is_breaking(current, changed, additional_args)
        self.assertEqual(breaking_response, is_breaking)

        lock_file_changed_response = BufWrapper.lock_file_changed(current, changed, additional_args)
        self.assertEqual(lock_file_changed_response, expects_changes)


class TestBreakingChanges(BufTests):

    def test_change_field_id(self):
        self.run_buf_test(
            self.test_change_field_id.__name__, is_breaking=True, expects_changes=False)

    def test_change_field_type(self):
        self.run_buf_test(
            self.test_change_field_type.__name__, is_breaking=True, expects_changes=False)

    def test_change_field_plurality(self):
        self.run_buf_test(
            self.test_change_field_plurality.__name__, is_breaking=True, expects_changes=False)

    def test_change_field_name(self):
        self.run_buf_test(
            self.test_change_field_name.__name__, is_breaking=True, expects_changes=False)

    def test_change_package_name(self):
        self.run_buf_test(
            self.test_change_package_name.__name__, is_breaking=True, expects_changes=False)

    def test_change_field_from_oneof(self):
        self.run_buf_test(
            self.test_change_field_from_oneof.__name__, is_breaking=True, expects_changes=False)

    def test_change_field_to_oneof(self):
        self.run_buf_test(
            self.test_change_field_to_oneof.__name__, is_breaking=True, expects_changes=False)

    @unittest.skip("PGV field support not yet added to buf")
    def test_change_pgv_field(self):
        self.run_buf_test(
            self.test_change_pgv_field.__name__, is_breaking=True, expects_changes=False)

    @unittest.skip("PGV message option support not yet added to buf")
    def test_change_pgv_message(self):
        self.run_buf_test(
            self.test_change_pgv_message.__name__, is_breaking=True, expects_changes=False)

    @unittest.skip("PGV oneof option support not yet added to buf")
    def test_change_pgv_oneof(self):
        self.run_buf_test(
            self.test_change_pgv_oneof.__name__, is_breaking=True, expects_changes=False)


class TestAllowedChanges(BufTests):

    def test_add_comment(self):
        self.run_buf_test(self.test_add_comment.__name__, is_breaking=False, expects_changes=True)

    def test_add_field(self):
        self.run_buf_test(self.test_add_field.__name__, is_breaking=False, expects_changes=True)

    def test_add_option(self):
        self.run_buf_test(self.test_add_option.__name__, is_breaking=False, expects_changes=True)

    def test_add_enum_value(self):
        self.run_buf_test(
            self.test_add_enum_value.__name__, is_breaking=False, expects_changes=True)

    def test_remove_and_reserve_field(self):
        self.run_buf_test(
            self.test_remove_and_reserve_field.__name__, is_breaking=False, expects_changes=True)

    # copied from protolock tests but might remove
    # It doesn't make sense to evaluate 'forcing' a breaking change in buf because by default,
    # buf lets you re-build without checking for breaking changes
    # Buf does not require forcing breaking changes into the lock file like protolock does
    @unittest.skip("'forcing' a breaking change does not make sense for buf")
    def test_force_breaking_change(self):
        self.run_buf_test(
            self.test_force_breaking_change.__name__,
            is_breaking=False,
            expects_changes=True,
            additional_args=["--force"])


if __name__ == '__main__':
    unittest.main()
