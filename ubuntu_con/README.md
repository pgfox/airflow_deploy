# Ubuntu SSH Container

This directory defines a minimal Ubuntu 22.04 container with OpenSSH server enabled so you can SSH into it from the host.

## Build and run

```bash
cd ubuntu_con
# Build the image and run the container in the foreground
docker compose up --build
```

To run detached:
```bash
docker compose up --build -d
```

The container exposes SSH on host port `2222`, mapped to container port `22`. Default credentials:
- **User:** `ubuntu`
- **Password:** `ubuntu`

Once the container is running, connect via:
```bash
ssh ubuntu@localhost -p 2222
```
You will land in a regular shell with password-based login enabled. The `ubuntu` user has passwordless sudo privileges for administrative commands.

## Notes

- Change the password immediately for anything beyond local testing (`passwd`).
- Adjust the exposed port in `docker-compose.yaml` if `2222` conflicts with another service.
- Includes the `psql` client (`postgresql-client`) so you can reach the shared Postgres instance directly.
- Extend the `Dockerfile` with additional packages or SSH keys as needed.
