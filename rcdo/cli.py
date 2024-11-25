import click
from rcdo.remote_worker import RemoteWorker


@click.group()
@click.pass_context
@click.argument(
    "remote_host",
)
@click.argument(
    "cmd",
)
@click.option(
    "-i",
    "--input",
    "inp",
    type=str,
    default="__NONE__",
    help="Remote file(s) to grab.",
)
@click.option(
    "-o",
    "--output",
    type=str,
    default="__NONE__",
    help="Local file(s) to create.",
)
@click.option(
    "--ssh-config",
    "ssh_config",
    type=str,
    default="~/.ssh/config",
    show_default=True,
    help="Path to SSH config file.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Print out diagnostic information.",
)
def cli(ctx: click.Context, remote_host, cmd, inp, output, ssh_config, verbose):
    """Run a local command `cmd` on a remote machine.

    `remote_host` can be a single or multi-step hop, e.g.,

        user@hostname:password
        user1@hostname1:password+user2@hostname2:password+...
    """
    ctx.obj = {
        "worker": RemoteWorker(
            remote_host=remote_host,
            cmd=cmd,
            input_spec=None if inp == "__NONE__" else inp,
            output_spec=None if output == "__NONE__" else output,
            ssh_config=ssh_config,
            verbose=verbose,
        ),
        "verbose": verbose,
    }


@cli.command()
@click.pass_context
def local(ctx: click.Context):
    """The command is from your local machine."""
    try:
        ctx.obj["worker"].run_local()
    except Exception as e:
        print(f"PROGRAM ERROR: {e}")
    finally:
        ctx.obj["worker"].cleanup()
    ctx.obj["worker"].cleanup()


@cli.command()
@click.pass_context
def remote(ctx: click.Context):
    """The command is from the remote machine."""
    try:
        ctx.obj["worker"].run_remote()
    except Exception as e:
        print(f"PROGRAM ERROR: {e}")
    finally:
        ctx.obj["worker"].cleanup()
    ctx.obj["worker"].cleanup()


def main():
    cli()


if __name__ == "__main__":
    main()
