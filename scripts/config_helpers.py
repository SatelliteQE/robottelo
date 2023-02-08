"""A series of commands to help with robottelo configuration"""
from pathlib import Path

import click
import deepdiff
import yaml
from logzero import logger


def merge_nested_dictionaries(original, new, overwrite=False):
    """Merge two dictionaries together, with the new dictionary taking precedence"""
    # iterate through all keys in the new dictionary
    for key, value in new.items():
        # if the key is not in the original, add it
        if key not in original:
            original[key] = value
        # if the key is in the original, and the value is a dictionary, recurse
        elif isinstance(value, dict):
            # use deepdiff to check if the dictionaries are the same
            if deepdiff.DeepDiff(original[key], value):
                original[key] = merge_nested_dictionaries(original[key], value, overwrite)
        elif original[key] == value:
            continue
        # if the key is in the original, and the value is a list, ask the user
        elif overwrite == "ask":
            choice_prompt = (
                f"The current value for {key} is {original[key]}.\n"
                "Please choose an option:\n"
                "1. Keep the current value\n"
                f"2. Overwrite the current value with {value}\n"
            )
            if isinstance(value, list):
                choice_prompt += "3. Merge the current value with {value}\n"
            user_choice = click.prompt(choice_prompt, type=int, default=1, show_default=True)
            if user_choice == 1:
                continue
            elif user_choice == 2:
                original[key] = value
            elif user_choice == 3 and isinstance(value, list):
                original[key] = original[key] + value
        elif overwrite:
            original[key] = value
    return original


def merge_yaml_files(original, new, overwrite=False):
    """Merge two yaml files together"""
    # load the original yaml file
    original_data = yaml.safe_load(original.read_text())
    new_data = yaml.safe_load(new.read_text())
    if original_data == new_data:
        return
    logger.warning(f"Merging {original} with {new}")
    merged_data = merge_nested_dictionaries(original_data, new_data, overwrite)
    original.write_text(yaml.safe_dump(merged_data))


@click.group()
def config():
    """Manage robottelo configuration"""
    pass


@config.command()
@click.option(
    "--from",
    "from_",
    type=click.Path(exists=True, file_okay=False),
    help="The path to the existing config directory",
)
def symlink(from_):
    """Symlink the config directory to the specified path"""
    from_ = Path(from_)
    # iterate through all files in the from_ directory
    for file in from_.glob("*"):
        # check if the file exists in the conf directory
        if not (real_name := Path(f"conf/{file.name}")).exists() and not real_name.is_symlink():
            # if not, symlink to the file in the from_ directory
            logger.warning(f"Symlinking {real_name} to {from_ / real_name}")
            real_name.symlink_to(from_ / real_name.name)


@config.command()
@click.option(
    "--from",
    "from_",
    type=click.Path(exists=True, file_okay=False),
    help="The path to the existing config directory",
)
@click.option(
    "--strategy",
    type=click.Choice(["ask", "overwrite", "preserve"]),
    help="The strategy to use when merging",
    default="ask",
)
def merge(from_, strategy):
    """Merge the config directory into the specified path"""
    from_ = Path(from_)
    # iterate through all files in the from_ directory
    for file in from_.glob("*"):
        if (real_name := Path(f"conf/{file.name}")).is_symlink():
            # file is a symlink. Ask user if they want to overwrite
            choice_prompt = (
                f"{real_name} is a symlink to {real_name.resolve()}\n"
                "Please choose an option:\n"
                "1. Keep the current symlink\n"
                f"2. Overwrite the current symlink with {file}\n"
            )
            user_choice = click.prompt(choice_prompt, type=int, default=1, show_default=True)
            if user_choice == 1:
                continue
            elif user_choice == 2:
                logger.warning(f"Overwriting {real_name} with {file}")
                real_name.unlink()
                real_name.write_text(file.read_text())
        # check if the file exists in the conf directory
        elif real_name.exists():
            # file exists and isn't a symlink, merge the files
            merge_yaml_files(real_name, file, strategy)
        else:
            # if not, copy the file to the conf directory
            logger.info(f"Copying {file} to {real_name}")
            real_name.write_text(file.read_text())


if __name__ == "__main__":
    config()
