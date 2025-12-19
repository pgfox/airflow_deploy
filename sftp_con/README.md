# SFTP Container

Simple SFTP service that joins the shared `shared_infra_net` network so other stacks in this repo can reach it (`sftp-server:22`). It exposes port `2299` on the host, allowing you to push and pull files via any SFTP client.

## Layout

- `docker-compose.yaml` – defines the SFTP service using the `atmoz/sftp` image
- `data/` – bind-mounted to `/home/ubuntu/upload` for persistent storage

## Usage

```bash
cd sftp_con
docker compose up -d
```

This starts a single SFTP user:

- **Username:** `ubuntu`
- **Password:** `ubuntu`
- **Upload directory:** `/home/ubuntu/upload` (mapped to `./data`)

From the host you can push files with the native `sftp` client:

```bash
sftp -P 2299 ubuntu@localhost
put /path/to/local/file.txt
```

Files uploaded through SFTP appear in the local `data/` folder. To tear everything down (data is retained):

```bash
docker compose down
```

Remove the data by deleting the `data/` folder manually if desired.
