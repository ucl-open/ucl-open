"""End-to-end tests for the copier project template.

These tests generate a new project from `template/`, deploy it with the template's
deploy script for the current platform, and run the generated scripts, in the same
order as a new user would. Deploying needs network access to resolve the generated
project's dependencies, and the same tools as the deploy script: git, uv, the .NET SDK,
and PowerShell (Windows PowerShell on Windows, or PowerShell 7 and bash elsewhere).

Run only these tests with `pytest -m template`, or skip them with `pytest -m "not template"`.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import copier
import pytest

pytestmark = pytest.mark.template

WINDOWS = sys.platform == "win32"
if WINDOWS:
    DEPLOY_COMMAND = ["cmd", "/c", str(Path("scripts") / "deploy.cmd")]
    DEPLOY_TOOLS = ("powershell", "git", "uv", "dotnet")
    VENV_PYTHON = Path(".venv") / "Scripts" / "python.exe"
else:
    DEPLOY_COMMAND = ["bash", str(Path("scripts") / "deploy.sh")]
    DEPLOY_TOOLS = ("bash", "pwsh", "git", "uv", "dotnet")
    VENV_PYTHON = Path(".venv") / "bin" / "python"

requires_deploy_tools = pytest.mark.skipif(
    any(shutil.which(tool) is None for tool in DEPLOY_TOOLS),
    reason=f"the template deploy script requires {', '.join(DEPLOY_TOOLS)}",
)

TEMPLATE_ROOT = Path(__file__).parents[2] / "template"
EXAMPLES = sorted(
    path.name.removesuffix(".jinja")
    for path in (TEMPLATE_ROOT / "template" / "examples").glob("*.py.jinja")
)

ANSWERS = {
    "project_name": "test-rig",
    "author_name": "Test Author",
    "author_email": "test.author@example.com",
    "prefix": "ucl-open",
}
PYTHON_FOLDER_NAME = "ucl_open_test_rig"
PYTHON_PACKAGE_NAME = "ucl-open-test-rig"
PYTHON_CLASS_PREFIX = "UclOpenTestRig"
CSHARP_NAMESPACE = "UclOpenTestRig"

DEPLOY_TIMEOUT = 1800
SCRIPT_TIMEOUT = 600


def run(args: list[str], cwd: Path, timeout: float = SCRIPT_TIMEOUT) -> subprocess.CompletedProcess[str]:
    """Runs a command in the generated project, isolated from the virtual environment running the tests."""
    env = {key: value for key, value in os.environ.items() if key not in ("VIRTUAL_ENV", "PYTHONPATH")}
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def describe(result: subprocess.CompletedProcess[str]) -> str:
    return (
        f"exit code {result.returncode}\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )


def assert_success(result: subprocess.CompletedProcess[str]) -> None:
    if result.returncode != 0:
        pytest.fail(f"{' '.join(result.args)} failed with {describe(result)}", pytrace=False)


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generates a new project from the template."""
    destination = tmp_path_factory.mktemp("template") / ANSWERS["project_name"]
    copier.run_copy(str(TEMPLATE_ROOT), destination, data=ANSWERS, defaults=True, quiet=True)
    return destination


@pytest.fixture(scope="module")
def deploy_result(project: Path) -> subprocess.CompletedProcess[str]:
    """Initializes a git repository in the generated project and runs the deploy script."""
    initialized = run(["git", "init", "-b", "main"], project)
    assert_success(initialized)
    return run(DEPLOY_COMMAND, project, timeout=DEPLOY_TIMEOUT)


@pytest.fixture(scope="module")
def deployed_project(project: Path, deploy_result: subprocess.CompletedProcess[str]) -> Path:
    """The generated project, after a successful deployment."""
    if deploy_result.returncode != 0 or not (project / VENV_PYTHON).exists():
        pytest.fail(f"the template was not deployed, see test_deploy\n{describe(deploy_result)}")
    return project


def test_copy(project: Path):
    expected = [
        ".copier-answers.yml",
        "pyproject.toml",
        "scripts/deploy.cmd",
        "scripts/deploy.ps1",
        "scripts/deploy.sh",
        "src/main.bonsai",
        "src/Extensions.csproj",
        f"src/{PYTHON_FOLDER_NAME}/__init__.py",
        f"src/{PYTHON_FOLDER_NAME}/regenerate.py",
        f"src/{PYTHON_FOLDER_NAME}/rig.py",
        f"src/{PYTHON_FOLDER_NAME}/task.py",
        *(f"examples/{example}" for example in EXAMPLES),
    ]
    missing = [path for path in expected if not (project / path).is_file()]
    assert not missing, f"missing files in generated project: {missing}"

    unrendered = [str(path.relative_to(project)) for path in project.rglob("*") if path.suffix == ".jinja"]
    assert not unrendered, f"template files were not rendered: {unrendered}"

    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert f'name = "{PYTHON_PACKAGE_NAME}"' in pyproject
    assert ANSWERS["author_name"] in pyproject
    assert ANSWERS["author_email"] in pyproject
    assert (
        f"class {PYTHON_CLASS_PREFIX}Rig(" in (project / "src" / PYTHON_FOLDER_NAME / "rig.py").read_text()
    )

    answers = (project / ".copier-answers.yml").read_text(encoding="utf-8")
    for key, value in ANSWERS.items():
        assert f"{key}: {value}" in answers


@requires_deploy_tools
def test_deploy(project: Path, deploy_result: subprocess.CompletedProcess[str]):
    assert_success(deploy_result)

    # The deploy script does not stop on failing commands, so check what it produced
    python = project / VENV_PYTHON
    assert python.exists(), f"the Python environment was not created\n{describe(deploy_result)}"
    imports = f"import sys, ucl_open, {PYTHON_FOLDER_NAME}.rig, {PYTHON_FOLDER_NAME}.task"
    check = run([str(python), "-c", f"{imports}; print(sys.version_info[:2])"], project)
    assert_success(check)
    assert check.stdout.strip() == "(3, 11)", (
        "the environment does not use the Python version required by the template"
    )

    schema_file = project / "src" / "DataSchemas" / f"{PYTHON_FOLDER_NAME}.json"
    assert schema_file.is_file(), f"the JSON schema was not generated\n{describe(deploy_result)}"
    definitions = json.loads(schema_file.read_text(encoding="utf-8")).get("$defs", {})
    for model in (f"{PYTHON_CLASS_PREFIX}Rig", f"{PYTHON_CLASS_PREFIX}TaskLogic", "ExperimentSession"):
        assert model in definitions, f"the JSON schema does not define {model}"

    generated = project / "src" / "Extensions" / f"{CSHARP_NAMESPACE}.Generated.cs"
    assert generated.is_file(), f"the C# classes were not generated\n{describe(deploy_result)}"


@requires_deploy_tools
def test_regenerate(deployed_project: Path):
    schema_file = deployed_project / "src" / "DataSchemas" / f"{PYTHON_FOLDER_NAME}.json"
    generated = deployed_project / "src" / "Extensions" / f"{CSHARP_NAMESPACE}.Generated.cs"
    schema_file.unlink(missing_ok=True)
    generated.unlink(missing_ok=True)

    result = run(["uv", "run", "regenerate-schemas"], deployed_project)
    assert_success(result)
    assert schema_file.is_file(), f"the JSON schema was not regenerated\n{describe(result)}"
    json.loads(schema_file.read_text(encoding="utf-8"))
    assert generated.is_file(), f"the C# classes were not regenerated\n{describe(result)}"


@requires_deploy_tools
@pytest.mark.parametrize("example", EXAMPLES)
def test_example(deployed_project: Path, example: str):
    output_dir = deployed_project / "local"
    shutil.rmtree(output_dir, ignore_errors=True)

    result = run(["uv", "run", "python", str(Path("examples") / example)], deployed_project)
    assert_success(result)

    outputs = sorted(output_dir.glob("*.json"))
    assert outputs, f"{example} did not write a JSON configuration file to {output_dir}\n{describe(result)}"
    for output in outputs:
        json.loads(output.read_text(encoding="utf-8"))
