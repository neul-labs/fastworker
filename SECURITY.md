# Security Policy

## Reporting a Vulnerability

Please report security vulnerabilities to **me@dipankar.name**. Expect an initial response within 48 hours.

## Serialization Safety

FastWorker supports both JSON and PICKLE serialization formats:

- **JSON** (default): Safe for untrusted networks. Use this unless you have a specific reason not to.
- **PICKLE**: Not secure — can execute arbitrary code during deserialization. Only use on fully trusted networks.

The PICKLE path emits a `RuntimeWarning` at runtime. Never expose a FastWorker instance using PICKLE serialization to untrusted networks.

## GUI Authentication

The management GUI supports API key authentication via the `FASTWORKER_GUI_API_KEY` environment variable. When set, all write endpoints (`POST`) require a `Authorization: Bearer <key>` header. Without this key, the GUI is accessible without authentication — only bind it to `127.0.0.1` (the default) in shared environments.

## Network Exposure

- All NNG sockets default to `tcp://127.0.0.1` — localhost only
- Binding to `0.0.0.0` exposes the control plane and workers to the network
- There is no built-in TLS/encryption for NNG sockets
- Use a VPN, SSH tunnel, or firewall rules when deploying across machines
