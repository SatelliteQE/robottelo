"""A series of commands to help with robottelo configuration"""
from pathlib import Path

import click
from logzero import logger


@click.group()
def config():
    """Manage robottelo configuration"""
    pass


@config.command("symlink")
@click.option(
    "--from",
    "from_",
    type=click.Path(exists=True, file_okay=False),
    help="The path to the existing config directory",
)
def symlink(from_):
    """Symlink the config directory to the specified path"""
    from_ = Path(from_)
    # iterate through all template files in the conf directory
    for template in Path("conf/").glob("*.template"):
        # check if non-template file exists
        if not (real_name := Path(f"conf/{template.stem}")).exists():
            # if not, symlink to the file in the from_ directory
            link_path = from_ / real_name.name
            if not link_path.exists():
                logger.error(f"Could not find {link_path}")
                continue
            logger.warning(f"Symlinking {real_name} to {from_ / real_name}")
            real_name.symlink_to(from_ / real_name.name)
        else:
            logger.info(f"Skipping {real_name} because it already exists")


if __name__ == "__main__":
    config()
