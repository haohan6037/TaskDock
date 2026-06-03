# Project Memory: OpenClaw Brain

## Goal

Build a host-based OpenClaw Brain system.

## Core principles

- OpenClaw should run on the host machine.
- Docker containers should be workers.
- Workers should be lightweight HTTP services.
- Workers should be stateless by default.
- Memory should be external and retrieved on demand.
- The Brain should route tasks, verify results, and save useful task history.
