import click
from rich import print
from rich_click import RichGroup

from sector import configuration, github, logger


@click.group(cls=RichGroup)
@click.option("--debug", is_flag=True, help="Enable debug logs.")
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    logger.configure(debug)
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    if debug:
        print("Debug mode is ON")


@cli.command()
@click.option(
    "--owner",
    default="kuadrant",
    help="Set the owner/org used in GitHub",
    show_default=True,
    type=str,
)
@click.option(
    "-p",
    "--project",
    multiple=True,
    default=(
        "authorino",
        "authorino-operator",
        "dns-operator",
        "kuadrant-console-plugin",
        "kuadrantctl",
        "kuadrant-operator",
        "limitador",
        "limitador-operator",
        "wasm-shim",
    ),
    help="Look up information for a project. This can be used multiple times."
    "When used with `--detailed` adding `@<tag>` list details all the way back to that release"
    "Accepted formats <project> | <project>@<tag>",
    show_default=True,
)
@click.option(
    "--sort",
    "_sort",
    default="time",
    type=click.Choice(["time", "name"], case_sensitive=False),
    show_choices=True,
    show_default=True,
    help="Changet the order in which the list is ordered.",
)
@click.option(
    "--detailed",
    is_flag=True,
    help="Display more details about the projects. "
    "This requires a number of calls to the github api and can be very slow.",
)
def info(owner: str, project: tuple[str], _sort: str, detailed: bool) -> None:
    """
    List the information about the different projects.
    GITHUB_TOKEN is a required envoriment variable
    """
    log = logger.get_logger("cli")
    log.info("Running 'sector info'")
    log.debug(f"{locals()=}")
    try:
        _project = [github.Repo(p) for p in project]
        github.info(owner, _project, log, _sort, detailed)
    except ValueError as e:
        log.exception(e)
        print(e)


@cli.command()
@click.option(
    "--owner",
    default="kuadrant",
    help="Set the owner/org used in GitHub",
    show_default=True,
    type=str,
)
@click.option(
    "-p",
    "--project",
    "project",
    default="kuadrant-operator",
    help="Set the project at the top of the chain."
    "This project needs to have a `release.yaml` in the root of the project",
    show_default=True,
    type=str,
)
@click.option(
    "-c",
    "--configuration-file",
    "config_path",
    default="./config.toml",
    help="Set the path to a configuration file which is needed for mapper some elements within the setup",
    show_default=True,
    type=str,
)
def result(owner: str, project: str, config_path: str) -> None:
    """
    Get the break down of what is new in the project and its dependencies.
    This includes fetching the release.yaml file for the latest kuadrant-operator release.
    GITHUB_TOKEN is a required environment variable.
    """
    log = logger.get_logger("cli")
    log.info("Running 'sector result'")
    log.debug(f"{locals()=}")

    try:
        _config = configuration.load(config_path)
        github.result(owner, project, log, _config)

    except ValueError as e:
        log.exception(e)
        print(f"[bold red]Error:[/bold red] {e}")
    except Exception as e:
        log.exception(e)
        print(f"[bold red]Unexpected error:[/bold red] {e}")


if __name__ == "__main__":
    cli()
