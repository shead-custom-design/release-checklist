import argparse
import os
import subprocess
import sys

import blessings

__version__ = "0.2.0"

parser = argparse.ArgumentParser(description="Simplifies releasing a Python package.")
parser.add_argument("--dry-run", action="store_true", help="Don't actually make changes.")
parser.add_argument("--editor", default="vi", help="Text editor. Default: %(default)s")
parser.add_argument("name", help="Project name.")
parser.add_argument("pypi", help="PyPI name.")
parser.add_argument("repo", help="Repository <org>/<repo> identifier.")
parser.add_argument("module", help="Python module name.")
parser.add_argument("version", help="Package release version.")
parser.add_argument("nextversion", help="Next package version after release.")

def prompt(term, message, commands=[], cwd=None):
    print(term.bold_white(message))
    if cwd is not None:
        print("  " + term.red(" ".join(["pushd", cwd])))
    for command in commands:
        command = [f"\"{item}\"" if " " in item else item for item in command]
        print("  " + term.red(" ".join(command)))
    if cwd is not None:
        print("  " + term.red(" ".join(["popd"])))

    try:
        command = input("skip/quit/<enter>: ")
        if command == "":
            return True
        if command == "skip":
            return False
        if command == "quit":
            print()
            exit(0)
    except KeyboardInterrupt:
        print()
        exit(0)


def run(arguments, commands, cwd=None):
    if not arguments.dry_run:
        if cwd is not None:
            oldcwd = os.getcwd()
            os.chdir(cwd)
        for command in commands:
            subprocess.check_call(command)
        if cwd is not None:
            os.chdir(oldcwd)

def main():
    arguments = parser.parse_args()
    term = blessings.Terminal()

    commands = [[arguments.editor, f"{arguments.module}/__init__.py"], ["pip", "install", "-e", "."]]
    if prompt(term, f"Set {arguments.module}.__version__ to \"{arguments.version}\":", commands):
        run(arguments, commands)

    commands = [[arguments.editor, "docs/release-notes.rst"]]
    if prompt(term, "Update release notes:", commands):
        run(arguments, commands)

    commands = [[sys.executable, "regression.py"]]
    if prompt(term, "Run regression to ensure all tests pass:", commands):
        run(arguments, commands)

    commands = [["make", "clean"], ["make", "html"]]
    if prompt(term, "Rebuild documentation from scratch:", commands, cwd="docs"):
        run(arguments, commands, cwd="docs")

    commands = [[arguments.editor, "pyproject.toml"]]
    if prompt(term, "Update the classifiers and descriptions in pyproject.toml:", commands):
        run(arguments, commands)

    commands = [["git", "commit", "-a", "-m", f"{arguments.name} version {arguments.version}"]]
    if prompt(term, "Commit the release changes:", commands):
        run(arguments, commands)

    commands = [["git", "push"]]
    if prompt(term, "Push the release commit:", commands):
        run(arguments, commands)

    commands = [["git", "tag", "-a", f"v{arguments.version}", "-m", f"{arguments.name} version {arguments.version}"]]
    if prompt(term, "Tag the release commit:", commands):
        run(arguments, commands)

    commands = [["git", "push", "origin", f"v{arguments.version}"]]
    if prompt(term, "Push the release tag:", commands):
        run(arguments, commands)

    commands = [[arguments.editor, "docs/release-notes.rst"]]
    if prompt(term, f"Create release \"{arguments.name} {arguments.version}\" in Github:", commands):
        run(arguments, commands)

    commands = [["rm", "-rf", "dist"], ["flit", "build"]]
    if prompt(term, "Build the new source release:", commands):
        run(arguments, commands)

    commands = [["flit", "publish"]]
    if prompt(term, "Upload the source release to PyPi:", commands):
        run(arguments, commands)

    commands = [[arguments.editor, f"{arguments.module}/__init__.py"], ["pip", "install", "-e", "."]]
    if prompt(term, f"Bump {arguments.module}.__version__ to \"{arguments.nextversion}\":", commands):
        run(arguments, commands)

    commands = [["git", "commit", "-a", "-m", "Bump version number."]]
    if prompt(term, "Commit the development changes:", commands):
        run(arguments, commands)

    commands = [["git", "push"]]
    if prompt(term, "Push the development commit:", commands):
        run(arguments, commands)

    commands = [[arguments.editor, "docs/release-notes.rst"]]
    if prompt(term, f"Post details to https://github.com/{arguments.repo}/discussions", commands):
        run(arguments, commands)

    prompt(term, "Remove any features that were deprecated in the new release:")

    commands = [["git", "commit", "-a", "-m", "Remove deprecated code."]]
    if prompt(term, "Commit the deprecation changes:", commands):
        run(arguments, commands)

    commands = [["git", "push"]]
    if prompt(term, "Push the deprecation commit:", commands):
        run(arguments, commands)

