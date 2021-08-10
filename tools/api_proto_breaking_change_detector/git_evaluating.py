"""
Check out api folder from commit <SHA1>:
    git restore -s <SHA1> -- ../../api

Remove untracked files when switching commits:
    git clean -fd ../../api

Get commit history of api folder:
    git log main --pretty=format:"%H"  -- ../../api
    * important to do this on the main branch so that it only includes fast-forward commits on the api folder 
    * --pretty flag formats the output; %H limits it to just the full length commit hash
    * sorted from newest -> oldest

Get first commit of api folder:
    git log main --pretty=format:"%H"  -- ../../api | tail -n 1

Number of commits on api folder:
    git log main --pretty=format:"%H"  -- ../../api | wc -l | awk '{ print $1 }'

Get commit message from commit hash:
    git log -n 1 --pretty=format:"%s\n%b" <SHA1>

Note: I run this script in the envoy root directory.
"""

import subprocess
from pathlib import Path
from datetime import datetime

BUF_YAML_CONTENT = """version: v1beta1
deps:
{0}
build:
  roots:
    - api
{2}
breaking:
  use:
{1}
"""

# key=starting commit, val = list of deps
BUF_DEPS = {}
# commit 0
BUF_DEPS["1fdb6386c4bb42748530d7a9bf58ded644d77749"] = [
    "buf.build/beta/googleapis",
    "buf.build/beta/opencensus",
    "buf.build/beta/prometheus:4eb826fd93f74bb994a08a9e7653e0d1",
    "buf.build/beta/opentelemetry",
    "buf.build/beta/gogo",
    "buf.build/beta/udpa",
]
# commit 422
BUF_DEPS["5cb222964fb691d8cb6cb0f6dd8fdd7b5dbdbb61"] = [
    "buf.build/beta/googleapis",
    "buf.build/beta/opencensus",
    "buf.build/beta/prometheus:4eb826fd93f74bb994a08a9e7653e0d1",
    "buf.build/beta/opentelemetry",
    "buf.build/beta/gogo",
]
# commit 477
BUF_DEPS["350a35f2ac685c4958934466a90b40f876968f99"] = BUF_DEPS[
    "1fdb6386c4bb42748530d7a9bf58ded644d77749"]
# commit 686
BUF_DEPS["297f7a73b3f93bccf8af73c0a555ae52bce6cecb"] = BUF_DEPS[
    "1fdb6386c4bb42748530d7a9bf58ded644d77749"]
# commit 698
BUF_DEPS["8d99679bb28ef50a7f04d62a5903bbefd8ff603a"] = BUF_DEPS[
    "1fdb6386c4bb42748530d7a9bf58ded644d77749"]
# commit 826
BUF_DEPS["961acf13e62d50cc785307b88cc63c61d61f93a3"] = BUF_DEPS[
    "1fdb6386c4bb42748530d7a9bf58ded644d77749"]
# commit 827
BUF_DEPS["c6232b702e1bfa2185041883666a5add2965d9e1"] = BUF_DEPS[
    "1fdb6386c4bb42748530d7a9bf58ded644d77749"]
# commit 957
BUF_DEPS["99471fd8f4ef7406f50cf41cf1cfa22bbdfeacc7"] = BUF_DEPS[
    "1fdb6386c4bb42748530d7a9bf58ded644d77749"]
# commit 1136
BUF_DEPS["8c4a3c77a7de016a118aacc4cea933951b85e589"] = BUF_DEPS[
    "1fdb6386c4bb42748530d7a9bf58ded644d77749"]
# commit 1371
BUF_DEPS["c1bc5e78fa68b86236c8d6237e2db15ce1743459"] = [
    "buf.build/beta/googleapis",
    "buf.build/beta/opencensus",
    "buf.build/beta/prometheus",
    "buf.build/beta/opentelemetry",
    "buf.build/beta/gogo",
    "buf.build/beta/udpa",
]
# commit 1411
BUF_DEPS["40ed33327c23a9e4e88aec448694eb1d03098efd"] = [
    "buf.build/beta/googleapis",
    "buf.build/beta/opencensus",
    "buf.build/beta/prometheus",
    "buf.build/beta/opentelemetry",
    "buf.build/beta/gogo",
    "buf.build/beta/xds",
]

BUF_RULES = [
    "FIELD_SAME_ONEOF",
    "FIELD_SAME_JSON_NAME",
    "FIELD_SAME_NAME",
    "FIELD_SAME_TYPE",
    "FIELD_SAME_LABEL",
    "FILE_SAME_PACKAGE",

    # needed for allowing removal/reserving of fields
    "FIELD_NO_DELETE_UNLESS_NUMBER_RESERVED",
    "FIELD_NO_DELETE_UNLESS_NAME_RESERVED",
]
BUF_EXCLUDES = {
    # commit 0
    "1fdb6386c4bb42748530d7a9bf58ded644d77749": ["api/udpa/"],
    # commit 422
    "5cb222964fb691d8cb6cb0f6dd8fdd7b5dbdbb61": ["api/udpa/"],
    # commit 477
    "350a35f2ac685c4958934466a90b40f876968f99": ["api/udpa/"],
    # commit 686
    "297f7a73b3f93bccf8af73c0a555ae52bce6cecb": ["api/udpa/"],
    # commit 698
    "8d99679bb28ef50a7f04d62a5903bbefd8ff603a": ["api/udpa/"],
    # commit 826
    "961acf13e62d50cc785307b88cc63c61d61f93a3": ["api/udpa/"],
    # commit 827
    "c6232b702e1bfa2185041883666a5add2965d9e1": ["api/udpa/"],
    # commit 957
    "99471fd8f4ef7406f50cf41cf1cfa22bbdfeacc7": ["api/udpa/"],
    # commit 1136
    "8c4a3c77a7de016a118aacc4cea933951b85e589": ["api/udpa/"],
    # commit 1371
    "c1bc5e78fa68b86236c8d6237e2db15ce1743459": [],
    # commit 1411
    "40ed33327c23a9e4e88aec448694eb1d03098efd": [],
}

API_PATH = Path(Path(__file__).parent, '../../api')
BUF_PATH = "buf"  # this would change e.g. if we bazelify this script
# only builds successfully from commit c1bc5e78fa68b86236c8d6237e2db15ce1743459 onward
STARTING_COMMIT = "8c4a3c77a7de016a118aacc4cea933951b85e589"
STARTING_COMMIT_NUM = 1136


def formatted_yaml_list(items, num_indents=2):
    return "\n".join("  " * num_indents + "- " + x for x in items)


def format_excludes(items):
    return "" if len(items) == 0 else "  excludes:\n" + formatted_yaml_list(items)


def run_cmd(*args):
    clean = subprocess.run(args, capture_output=True)
    code, out, err = clean.returncode, clean.stdout.decode('utf-8'), clean.stderr.decode('utf-8')
    return code, out, err


def update_buf_deps(i, comm):
    if comm not in BUF_DEPS:
        return
    print(f"Changing buf.yaml for commit #{i} : {comm}")
    content = BUF_YAML_CONTENT.format(
        formatted_yaml_list(BUF_DEPS[comm]), formatted_yaml_list(BUF_RULES),
        format_excludes(BUF_EXCLUDES[comm]))
    with open(Path(".", "buf.yaml"), "w") as file:
        file.write(content)

    with open(Path(".", f"buf-{i}-{comm}.yaml"), "w") as file:
        file.write(content)

    ucode, uout, uerr = run_cmd(BUF_PATH, "mod", "update")
    if ucode != 0 or len(uerr) > 0:
        raise Exception(
            "Error running `buf mod update` | status code:", ucode, "| stdout:", uout, "| stderr:",
            uerr)
    bcode, bout, berr = run_cmd(BUF_PATH, "build")
    if bcode != 0 or len(berr) > 0:
        # note: this might just fail because the commit you're looking at can't be built.
        # only invoke this function on commits that can build (e.g. use cycle_and_build() to see when they start being successful)
        raise Exception(
            "Error running `buf build` | status code:", bcode, "| stdout:", bout, "| stderr:", berr)


def get_commits_on_api():
    _, stdout, _ = run_cmd("git", 'log', 'main', '--pretty=format:"%H"', '--', API_PATH)
    commits = [x.strip('"') for x in stdout.split('\n')]
    # order is given to us from newest to oldest; reverse s.t. oldest commit is at index 0
    commits.reverse()
    return commits


def get_commits(start):
    commits = get_commits_on_api()
    subset = commits[commits.index(start):] if start in commits else commits
    return subset


def checkout_commit(i, comm):
    ccode, cout, cerr = run_cmd("git", "clean", "-fd", API_PATH)
    clean_output = ccode, cout, cerr
    failed_clean = ccode != 0 or len(cerr) != 0
    if failed_clean:
        print(f'--- error cleaning during commit #{i}: {comm} ---')
        print('ccode', ccode)
        print('cout', cout)
        print('cerr', cerr)
    tcode, tout, terr = run_cmd("git", "restore", "-s", comm, "--", API_PATH)
    try_checkout_output = tcode, tout, terr
    failed_checkout = tcode != 0 or len(terr) != 0
    if failed_checkout:
        print(f'--- error checking out during commit #{i}: {comm} ---')
        print('tcode', tcode)
        print('tout', tout)
        print('terr', terr)
    return clean_output, try_checkout_output


def cycle_checkout(commits, action):
    for i, comm in enumerate(commits):
        clean_output, try_checkout_output = checkout_commit(i, comm)
        action(i, comm, clean_output, try_checkout_output)


def cycle_and_build():
    folder_output = Path(".", datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p"))
    folder_output.mkdir()

    def build(i, comm, clean_output, try_checkout_output):
        ccode, _, cerr = clean_output
        tcode, _, terr = try_checkout_output
        failed_clean = ccode != 0 or len(cerr) != 0
        failed_checkout = tcode != 0 or len(terr) != 0
        if failed_clean or failed_checkout:
            print(f'skipping commit {i} ({comm}) because it failed')
            return

        update_buf_deps(i, comm)

        bcode, bout, berr = run_cmd(
            BUF_PATH, "build", "-o", Path(folder_output, f"test-{i}-{comm}.json"))
        if bcode != 0 or len(berr) > 0:
            print(f'error building commit #{i} ({comm})')
            with open(Path(folder_output, f"{i}-{comm}"), "w") as file:
                file.write(
                    '\n'.join(["status code",
                               str(bcode), "", "stdout", bout, "", "stderr", berr]))

    subset = get_commits(STARTING_COMMIT)
    cycle_checkout(subset, build)


def cycle_and_check_breaking():
    folder_output = Path(".", datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p"))
    folder_output.mkdir()
    lock_file_name = "lock-{0}-{1}.json"  # lock-index-commit_hash

    def get_lock_file(i, comm):
        return Path(folder_output, lock_file_name.format(i, comm))

    def check_breaking(starting_comm):
        current_lock_commit = [starting_comm]

        def helper(i, comm, clean_output, try_checkout_output):
            nonlocal current_lock_commit

            ccode, _, cerr = clean_output
            tcode, _, terr = try_checkout_output
            failed_clean = ccode != 0 or len(cerr) != 0
            failed_checkout = tcode != 0 or len(terr) != 0
            if failed_clean or failed_checkout:
                print(f'skipping commit {i} ({comm}) because it failed')
                return

            update_buf_deps(i, comm)

            # check for breaking change
            br_code, br_out, br_err = run_cmd(
                BUF_PATH, "breaking", "--against",
                get_lock_file(len(current_lock_commit) - 1, current_lock_commit[-1]))
            if br_code != 0 or len(br_out) != 0 or len(br_err) > 0:
                print(
                    f"error (or breaking change) detected between {current_lock_commit[-1]} -> {comm} (index {i})"
                )

                # get commit message for that hash
                _, commitmsg, _ = run_cmd("git", "log", "-n", "1", '--pretty=format:"%s\n%b"', comm)

                with open(Path(folder_output, f"{i+1}-{comm}"), "w") as file:
                    file.write(
                        '\n'.join([
                            "commit", commitmsg, "", "status code",
                            str(br_code), "", "stdout", br_out, "", "stderr", br_err
                        ]))

            # create lock file for this commit
            # assumes this commit _can_ successfully build,
            # which should be true for commits starting at STARTING_COMMIT
            run_cmd(BUF_PATH, "build", "-o", get_lock_file(i + 1, comm))
            current_lock_commit.append(comm)

        return helper

    commits = get_commits(STARTING_COMMIT)

    # make initial lock file
    start_comm = commits[0]
    checkout_commit(0, start_comm)
    update_buf_deps(0, start_comm)
    icode, _, ierr = run_cmd(BUF_PATH, "build", "-o", get_lock_file(0, start_comm))
    if icode != 0 or len(ierr) > 0:
        # Make sure that STARTING_COMMIT and all subsequent commits can be built in buf!
        print("failed initial lock creation: status code:", icode, "stderr:", ierr)
        print("aborting")
        return

    cycle_checkout(commits[1:], check_breaking(start_comm))


#cycle_and_build()
#cycle_and_check_breaking()
