from pathlib import Path

import click
import pytest


@click.command()
@click.argument("fixtures", nargs=-1, required=True)
@click.option(
    "--from-file",
    "-f",
    type=click.File("w"),
    help="Run the fixtures from within a file, inheriting the file's context.",
)
def run_fixtures(fixtures, from_file):
    """Create a temporary test that depends on each fixture, then run it.

    You can also run the fixtures from the context of a file, which is useful when testing fixtures
    that don't live at a global scope.

    Examples:
        python scripts/fixture_cli.py module_published_cv module_subscribe_satellite
        python scripts/fixture_cli.py module_lce --from-file tests/foreman/api/test_activationkey.py
    """
    fixture_string = ", ".join(filter(None, fixtures))
    test_template = f"def test_fake({fixture_string}):\n    assert True"
    if from_file:
        from_file = Path(from_file.name)
        # inject the test at the end of the file
        with from_file.open("a") as f:
            eof_pos = f.tell()
            f.write(f"\n\n{test_template}")
        pytest.main(["-qq", str(from_file.resolve()), "-k", "test_fake"])
        # remove the test from the file
        with from_file.open("r+") as f:
            f.seek(eof_pos)
            f.truncate()
    else:
        temp_file = Path("test_DELETEME.py")
        temp_file.write_text(test_template)
        pytest.main(["-qq", str(temp_file)])
        temp_file.unlink()


if __name__ == "__main__":
    run_fixtures()
