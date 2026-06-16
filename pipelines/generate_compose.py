#!/usr/bin/env python3
"""Genera docker-compose.yml a partir de config/workers.yml."""

import sys
import yaml

RABBITMQ_HEALTHCHECK = {
    "test": ["CMD-SHELL", "nc -z localhost 5672 || exit 1"],
    "interval": "5s",
    "timeout": "5s",
    "retries": 20,
    "start_period": "60s",
}


def build_infrastructure(config: dict) -> dict:
    services = {}
    for name, cfg in config.get("infrastructure", {}).items():
        services[name] = {
            "build": "./rabbitmq",
            "ports": cfg.get("ports", []),
            "healthcheck": RABBITMQ_HEALTHCHECK,
            "volumes": [
                "rabbitmq_data:/var/lib/rabbitmq",
            ],
        }
    return services


def build_workers(config: dict, infra_names: list[str]) -> dict:
    services = {}
    depends_on = {name: {"condition": "service_healthy"} for name in infra_names}

    for name, cfg in config.get("workers", {}).items():
        environment = {"QUEUE_IN": cfg["queue_in"]}
        if cfg.get("queue_out"):
            environment["QUEUE_OUT"] = cfg["queue_out"]

        networks = ["default"]
        if not cfg.get("queue_out"):
            networks.append("backend")

        service = {
            "build": f"./workers/{name}",
            "volumes": [
                "./common:/app/common:ro",
                "./cache:/app/cache",
            ],
            "env_file": ".env",
            "environment": environment,
            "depends_on": depends_on,
            "deploy": {"replicas": cfg["replicas"]},
            "restart": "on-failure",
            "networks": networks,
        }

        if "mem_limit" in cfg:
            service["mem_limit"] = cfg["mem_limit"]

        services[name] = service

    return services


def build_producer(infra_names: list[str]) -> dict:
    depends_on = {name: {"condition": "service_healthy"} for name in infra_names}
    return {
        "producer": {
            "build": "./producer",
            "volumes": ["./common:/app/common:ro"],
            "env_file": ".env",
            "depends_on": depends_on,
            "profiles": ["producer"],
        }
    }


def generate(config_path: str, output_path: str):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    infra = build_infrastructure(config)
    infra_names = list(infra.keys())
    workers = build_workers(config, infra_names)
    producer = build_producer(infra_names)

    compose = {
        "services": {
            **infra,
            **workers,
            **producer,
        },
        "networks": {
            "default": {
                "name": "pipelines_internal",
                "driver": "bridge",
            },
            "backend": {
                "name": "funes_backend_network",
                "external": True,
            },
        },
        "volumes": {
            "rabbitmq_data": None,
        },
    }

    with open(output_path, "w") as f:
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False)

    n_workers = len(workers)
    total_replicas = sum(cfg["replicas"] for cfg in config.get("workers", {}).values())
    print(f"✓ {output_path} generado")
    print(f"  infra:    {infra_names}")
    print(
        f"  workers:  {list(workers.keys())} ({n_workers} tipos, {total_replicas} réplicas)"
    )


if __name__ == "__main__":
    config = sys.argv[1] if len(sys.argv) > 1 else "config/workers.yml"
    output = sys.argv[2] if len(sys.argv) > 2 else "docker-compose.yml"
    generate(config, output)
