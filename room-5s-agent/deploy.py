import click
import os
from google.agents.cli._project import read_project_config, resolve_gcp_project
from google.agents.cli.deploy.agent_runtime import deploy_agent_runtime

@click.command()
@click.option("--project", default=None, help="GCP project ID.")
@click.option("--region", default=None, help="GCP region.")
@click.option("--update-env-vars", default=None, help="Comma-separated KEY=VALUE env vars.")
@click.option("--secrets", default=None, help="Comma-separated ENV=SECRET or ENV=SECRET:VERSION pairs.")
@click.option("--service-account", default=None, help="Service account email.")
@click.option("--agent-identity", is_flag=True, default=False, help="Enable agent identity.")
@click.option("--no-wait", is_flag=True, default=False, help="Start the deployment and return immediately.")
@click.option("--no-confirm-project", is_flag=True, default=False, help="Skip project confirmation prompt (ignored, kept for compatibility).")
@click.option("--min-instances", default=0, type=int, help="Minimum number of instances.")
@click.option("--max-instances", default=2, type=int, help="Maximum number of instances.")
@click.option("--cpu", default="1", help="CPU allocation (e.g. '1', '2').")
@click.option("--memory", default="2Gi", help="Memory allocation (e.g. '512Mi', '2Gi').")
def main(project, region, update_env_vars, secrets, service_account, agent_identity, no_wait, no_confirm_project, min_instances, max_instances, cpu, memory):
    cfg = read_project_config()
    project = project or os.environ.get("GOOGLE_CLOUD_PROJECT") or resolve_gcp_project()
    region = region or cfg.region or "asia-northeast1"
    
    deploy_agent_runtime(
        cfg=cfg,
        display_name="room-5s-agent",
        project=project,
        location=region,
        set_env_vars=update_env_vars,
        set_secrets=secrets,
        service_account=service_account,
        agent_identity=agent_identity,
        no_wait=no_wait,
        min_instances=min_instances,
        max_instances=max_instances,
        cpu=cpu,
        memory=memory,
    )

if __name__ == "__main__":
    main()
