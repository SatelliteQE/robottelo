from pathlib import Path

import click
import pytest


def fixture_to_test(fixture_name):
    """Convert a fixture name to a test name.

    Basic Example: fixture_to_test("module_published_cv")
    Returns: "def test_run_module_published_cv(module_published_cv):\n    assert True"

    Parametrized Example: fixture_to_test("sat_azure:sat,puppet_sat")
    Returns: "@pytest.mark.parametrize('sat_azure', ['sat', 'puppet_sat'], indirect=True)"
             "\ndef test_run_sat_azure(sat_azure):\n    assert True"
    """
    if ":" not in fixture_name:
        return f"def test_runfake_{fixture_name}({fixture_name}):\n    assert True"

    fixture_name, params = fixture_name.split(":")
    params = params.split(",")
    return (
        f"@pytest.mark.parametrize('{fixture_name}', {params}, indirect=True)\n"
        f"def test_runfake_{fixture_name}({fixture_name}):\n    assert True"
    )


@click.command()
@click.argument("fixtures", nargs=-1, required=True)
@click.option(
    "--from-file",
    type=click.File("w"),
    help="Run the fixtures from within a file, inheriting the file's context.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Toggle verbose mode (default is quiet).",
)
@click.option(
    "--xdist-workers",
    "-n",
    type=int,
    default=1,
    help="Run the tests in parallel with xdist.",
)
def run_fixtures(fixtures, from_file, verbose, xdist_workers):
    """Create a temporary test that depends on each fixture, then run it.

    You can also run the fixtures from the context of a file, which is useful when testing fixtures
    that don't live at a global scope.

    Indirectly parametrized fixtures are also possible with this syntax: fixture_name:param1,param2,param3

    Examples:
        python scripts/fixture_cli.py module_published_cv module_subscribe_satellite
        python scripts/fixture_cli.py module_lce --from-file tests/foreman/api/test_activationkey.py
        python scripts/fixture_cli.py sat_azure:sat,puppet_sat
    """
    verbosity = "-v" if verbose else "-qq"
    xdist_workers = str(xdist_workers)  # pytest expects a string
    generated_tests = "import pytest\n\n" + "\n\n".join(map(fixture_to_test, fixtures))
    if from_file:
        from_file = Path(from_file.name)
        # inject the test at the end of the file
        with from_file.open("a") as f:
            eof_pos = f.tell()
            f.write(f"\n\n{generated_tests}")
        pytest.main(
            [verbosity, "-n", xdist_workers, str(from_file.resolve()), "-k", "test_runfake_"]
        )
        # remove the test from the file
        with from_file.open("r+") as f:
            f.seek(eof_pos)
            f.truncate()
    else:
        temp_file = Path("test_DELETEME.py")
        temp_file.write_text(generated_tests)
        pytest.main([verbosity, "-n", xdist_workers, str(temp_file)])
        temp_file.unlink()


if __name__ == "__main__":
    run_fixtures()
