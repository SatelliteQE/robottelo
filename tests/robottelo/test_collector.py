import ast
from copy import copy
import os
import re
import subprocess


class TestCollector:
    """
    Collect and run tests that reference a specific method.
    Also collect and run tests using fixtures that ref the method.

    Fixtures considered will be searched for in all of /robottelo/
    Cases collected will only be scoped by local directory below.
    Current Implementation is only able to identify Module-Scoped fixtures.
    
    Takes about 10-15 minutes to collect, most of the time is spent finding 
    nested fixtures in parent's directories (recursively).

    To shorten collection time, narrow the scope of fixtures using FIXTURE_DIR.
    """

    # Just collect the cases or run them?
    COLLECT_ONLY = True

    # Replace with specific method string to look for.
    # ie: 'cli_factory.setup_org_for_a_rh_repo'
    FIND_METHOD = 'cli_factory.setup_org_for_a_custom_repo'

    # Replace with full local path, to directory or .py file, to scope test cases for.
    TEST_DIR = '/Users/damoore/projects/robottelo/tests/foreman/cli/test_errata.py'
    # Optional: replace with a path to directory or .py file, for lesser scope of fixtures.
    FIXTURE_DIR = None

    def run_tests_relevant_to_method(self):
        parent_dir = copy(self.TEST_DIR)
        if not self.FIXTURE_DIR:
            # parent directory for fixtures ends with '/robottelo' (Default)
            while not parent_dir.endswith('/robottelo'):
                parent_dir = parent_dir[:-1]
        else:
            # Use optional fixture directory for different scope
            parent_dir = self.FIXTURE_DIR

        # all collected fixtures that are relevant
        # (ref the method, or ref another fixture that has method)
        fixtures = sorted(
            self.find_fixtures_calling_method(
                targets=[self.FIND_METHOD],  # Initialize with the method name as the first target
                path=parent_dir,
            )
        )
        # all collected cases that are relevant
        # (ref the method, or imports a relevant fixture)
        cases = sorted(
            self.find_tests_calling_method_or_fixtures(
                function_name=self.FIND_METHOD,
                fixtures=fixtures,
                path=self.TEST_DIR,
            )
        )

        subprocess = self.run_collected_tests_and_fixtures(
            cases, fixtures, collect_only=self.COLLECT_ONLY
        )
        if subprocess is not None:
            # Extract the number of tests collected from stdout
            tests_collected_match = re.search(r'(\d+) tests collected', subprocess['result'].stdout)
            tests_collected = int(tests_collected_match.group(1)) if tests_collected_match else None

            # Extract the error messages from stderr to count the failed tests
            error_matches = re.findall(r'ERROR: not found: (.+)', subprocess['result'].stderr)
            warnings_or_errors = len(error_matches)

            # Extract the number of tests run and summary
            tests_run_match = re.search(r'(\d+)\s+tests run', subprocess['result'].stdout)
            tests_run = int(tests_run_match.group(1)) if tests_run_match else None

            # Print the extracted values
            print(f'Tests Collected: {tests_collected}')
            print(f'Tests Run: {tests_run}')
            print(f'Tests Failed: {warnings_or_errors}')
        breakpoint()

    def run_collected_tests_and_fixtures(self, cases, fixtures, collect_only=True):
        """Run Pytest on the specific test cases, and others that use the fixtures."""
        if not cases:
            print("No test cases found to run.")
            return None

        pytest_cmd = ['pytest', '-q',]
        if collect_only:
            pytest_cmd.insert(1, '--collect-only')

        # Add collected test cases
        pytest_cmd.extend(f'{" ".join(cases)}')

        # If there are fixtures, include them using --uses-fixtures
        if fixtures:
            pytest_cmd.append(f'--uses-fixtures={",".join(fixtures)}')

        print(f'Running command: {" ".join(pytest_cmd)}')  # Debugging output

        # Execute the pytest command
        result = subprocess.run(pytest_cmd, capture_output=True, text=True)

        # Print pytest's output to the terminal

        return {'result': result, 'cmd': pytest_cmd}

    def is_fixture(self, node):
        """Check if the function is decorated with @pytest.fixture."""
        return any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "fixture"
            for decorator in node.decorator_list
        )

    def walk_nodes_and_check(self, targets, node):
        """Check a node's subnodes for any of the targets in the targets list."""
        # only consider fixtures or tests
        if self.is_fixture(node) or node.name.startswith('test_'):
            for subnode in ast.walk(node):
                # check if subnode(s) contain any matches to target names
                if any(_t in ast.unparse(subnode) for _t in targets):
                    return True
        return False

    def find_fixtures_calling_method(self, targets, path, processed_fixtures=None):
        """Recursively search for fixtures referencing the target method, collect all related fixtures."""
        if processed_fixtures is None:
            processed_fixtures = set()
        relevant_fixtures = set()

        def process_file_for_fixtures(filepath):
            """Parse a Python file and look for relevant fixtures."""
            with open(filepath, encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read(), filename=filepath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and self.is_fixture(node):
                            if self.walk_nodes_and_check(targets, node):
                                if node.name not in relevant_fixtures:
                                    relevant_fixtures.add(node.name)
                except (SyntaxError, UnicodeDecodeError):
                    pass  # Skip files that fail to parse

        # Process if path is to a single python file
        if os.path.isfile(path) and path.endswith(".py"):
            process_file_for_fixtures(path)
        # Otherwise, traverse the directories
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):  # Only consider Python files
                        process_file_for_fixtures(os.path.join(root, file))

        # Remove already processed fixtures to avoid infinite loops
        new_fixtures = relevant_fixtures - processed_fixtures
        processed_fixtures.update(new_fixtures)
        # Only recurse if we found new fixtures
        if new_fixtures:
            # recursively check for relevant fixtures that reference each other
            relevant_fixtures.update(
                self.find_fixtures_calling_method(
                    processed_fixtures=processed_fixtures,  # Pass down processed fixtures
                    targets=list(relevant_fixtures),
                    path=path,
                )
            )

        return relevant_fixtures

    def find_tests_calling_method_or_fixtures(self, function_name, fixtures, path):
        """Find tests that reference the function, either directly or indirectly through fixtures."""
        relevant_cases = set()
        targets = list({function_name} | set(fixtures))

        def process_file_for_cases(filepath):
            """Parse a Python file and look for relevant test functions."""
            with open(filepath, encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read(), filename=filepath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                            if self.walk_nodes_and_check(targets, node):
                                if node.name not in relevant_cases:
                                    relevant_cases.add(f'{filepath}::{node.name}')
                except (SyntaxError, UnicodeDecodeError):
                    pass  # Skip files that fail to parse

        # Process if path is to a single python file
        if os.path.isfile(path) and path.endswith(".py"):
            process_file_for_cases(path)
        # Otherwise, traverse the directories
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):  # Only consider Python files
                        process_file_for_cases(os.path.join(root, file))

        return relevant_cases


# Invoke the collector
collector = TestCollector()
collector.run_tests_relevant_to_method()
