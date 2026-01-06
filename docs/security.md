# Security Considerations

FastWorker is designed for **trusted environments** and does not include built-in authentication or encryption. This document outlines security considerations and recommendations for production use.

---

## Overview

FastWorker prioritizes simplicity and performance over security features. This means:

- No built-in authentication
- No built-in encryption
- No access control
- Pickle serialization (insecure by design)

**FastWorker should only be deployed on trusted networks.**

---

## Authentication

### Current State

FastWorker does **NOT** provide:

| Component | Authentication |
|-----------|---------------|
| Task submission | None |
| Result queries | None |
| Management GUI | None |
| Worker registration | None |

### Implications

- Anyone with network access can submit tasks to your workers
- Anyone with network access can query task results
- Anyone with network access can view/manage via the GUI
- Any subworker can register and process tasks

### Recommendations

1. **Network isolation**: Run FastWorker on internal/VPN networks only
2. **Firewall rules**: Restrict access to control plane ports (5550-5559)
3. **Reverse proxy**: Place GUI behind authenticated reverse proxy (nginx, Apache)
4. **Network segmentation**: Isolate FastWorker from public networks

---

## Serialization Security

### The Pickle Problem

FastWorker supports two serialization formats:

| Format | Security | Recommendation |
|--------|----------|----------------|
| JSON | Safe | Default, recommended |
| Pickle | **NOT secure** | Use only on trusted networks |

### Why Pickle is Dangerous

The Python `pickle` module is **not secure**. From the official documentation:

> "The pickle module is not secure. Only unpickle data you trust. It is possible to construct malicious pickle data which will execute arbitrary code during unpickling."

### Attack Vector

```
# Malicious task data (example)
malicious_data = b"\x80\x03c__main__\n malicious_class\nq\x00..."  # Executes code!
```

If an attacker can submit Pickle-serialized tasks, they can execute arbitrary code on your workers.

### Recommendations

1. **Use JSON serialization** (default):
   ```python
   # Default - safe
   client = Client()  # Uses JSON
   ```

2. **Avoid Pickle**:
   ```python
   # NOT recommended - insecure
   client = Client(serialization_format=SerializationFormat.PICKLE)
   ```

3. **Set environment variable**:
   ```bash
   # Force JSON even if env var tries to set Pickle
   export FASTWORKER_SERIALIZATION_FORMAT=JSON
   ```

4. **Runtime warnings**: FastWorker now emits `SecurityWarning` when Pickle is used.

---

## Network Security

### Ports Used

| Port | Purpose |
|------|---------|
| 5550 | Discovery broadcast |
| 5555 | Critical priority tasks |
| 5556 | High priority tasks |
| 5557 | Normal priority tasks |
| 5558 | Low priority tasks |
| 5559 | Result queries |
| 8080 | Management GUI (configurable) |

### Recommendations

1. **Firewall rules**:
   ```bash
   # iptables example - allow only internal network
   iptables -A INPUT -s 10.0.0.0/8 -p tcp --dport 5550:5559 -j ACCEPT
   iptables -A INPUT -p tcp --dport 5550:5559 -j DROP
   ```

2. **Bind to localhost** (for development):
   ```bash
   fastworker control-plane --gui-host 127.0.0.1
   ```

3. **Use VPN** for remote worker connections

4. **Network segmentation**: Place FastWorker in isolated VLAN/subnet

---

## GUI Security

The management GUI has no built-in authentication.

### Current State

- No login required
- No access control
- No audit logging

### Recommendations

1. **Don't expose to internet**: Bind to 127.0.0.1 or internal network only
2. **Use reverse proxy with auth**:
   ```nginx
   location /fastworker/ {
       auth_basic "Admin Area";
       auth_basic_user_file /etc/nginx/.htpasswd;
       proxy_pass http://127.0.0.1:8080;
   }
   ```
3. **Disable GUI in production** if not needed:
   ```bash
   fastworker control-plane --no-gui
   ```

---

## Worker Security

### Subworker Registration

Subworkers register without authentication. Any Python process can register as a subworker.

### Recommendations

1. **Network isolation**: Only allow subworkers from trusted networks
2. **Validate worker identity** at application level if needed
3. **Monitor worker registrations**: Log and alert on unexpected workers

---

## Environment Variables

FastWorker uses environment variables for configuration. Ensure these are properly secured:

| Variable | Sensitivity | Recommendation |
|----------|-------------|----------------|
| FASTWORKER_DISCOVERY_ADDRESS | Low | Network address |
| FASTWORKER_SERIALIZATION_FORMAT | Medium | Affects security |
| FASTWORKER_TIMEOUT | Low | Integer value |
| FASTWORKER_RETRIES | Low | Integer value |

---

## Production Checklist

- [ ] FastWorker on isolated/trusted network
- [ ] Firewall rules configured
- [ ] JSON serialization (default)
- [ ] GUI behind authentication or disabled
- [ ] No public internet exposure
- [ ] Monitoring for unexpected workers
- [ ] Workers on trusted network only
- [ ] Regular security updates

---

## Alternatives for Secure Deployments

If you need built-in security features, consider:

1. **Add authentication layer**: Implement custom auth in your tasks
2. **Use TLS**: Terminate TLS at reverse proxy
3. **VPN**: Run FastWorker over VPN
4. **Alternative systems**: RabbitMQ, Kafka with SASL auth, AWS SQS

---

## Summary

FastWorker is **not secure by default**. It is designed for:

- Development environments
- Internal/trusted networks
- Simple deployments where network security is handled externally

If your security requirements include authentication, encryption, or access control, FastWorker may not be the right choice without additional security measures.

---

## See Also

- [Limitations](limitations.md) - Scope and constraints
- [Configuration](configuration.md) - Configuration options
- [CLI Reference](api.md) - Command-line interface
