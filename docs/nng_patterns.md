# NNG Patterns Used

FastQueue leverages several nng patterns to provide robust, brokerless task queue functionality.

## Surveyor/Respondent Pattern

### Usage
- **Task Distribution**: Distributing tasks from clients to workers
- **Load Balancing**: Automatic load balancing among available workers
- **Result Collection**: Collecting results from workers

### Implementation
```python
# Client side (Surveyor)
surveyor = pynng.Surveyor0(listen="tcp://127.0.0.1:5555")

# Worker side (Respondent)
respondent = pynng.Respondent0(dial="tcp://127.0.0.1:5555")
```

### Benefits
- All respondents can reply to a survey
- Built-in timeout handling
- Automatic retry mechanisms
- Load distribution across multiple respondents

## Bus Pattern

### Usage
- **Service Discovery**: Automatic discovery of workers and clients
- **Peer Communication**: Communication between all peers in the network
- **Presence Announcements**: Workers announce their presence to the network

### Implementation
```python
# Worker discovery bus
bus = pynng.Bus0(listen="tcp://127.0.0.1:5550")

# Client discovery bus
bus = pynng.Bus0(dial="tcp://127.0.0.1:5550")
```

### Benefits
- All peers can send and receive messages
- Automatic peer discovery
- No central coordination point
- Lightweight and efficient

## Req/Rep Pattern

### Usage
- **Synchronous Communication**: Synchronous request-response communication
- **Reliable Delivery**: Guaranteed message delivery
- **Task Submission**: Direct task submission to specific workers

### Implementation
```python
# Client side (Requester)
req = pynng.Req0(dial="tcp://127.0.0.1:5555")

# Worker side (Replier)
rep = pynng.Rep0(listen="tcp://127.0.0.1:5555")
```

### Benefits
- Guaranteed message delivery
- Built-in retry mechanisms
- Automatic connection management
- Timeout handling

## Pattern Combinations

### Priority-Based Task Routing

FastQueue uses multiple Surveyor/Respondent pairs for different priority levels:

```python
# Critical priority tasks
critical_surveyor = pynng.Surveyor0(listen="tcp://127.0.0.1:5555_critical")
critical_respondent = pynng.Respondent0(dial="tcp://127.0.0.1:5555_critical")

# High priority tasks
high_surveyor = pynng.Surveyor0(listen="tcp://127.0.0.1:5555_high")
high_respondent = pynng.Respondent0(dial="tcp://127.0.0.1:5555_high")

# Normal priority tasks
normal_surveyor = pynng.Surveyor0(listen="tcp://127.0.0.1:5555_normal")
normal_respondent = pynng.Respondent0(dial="tcp://127.0.0.1:5555_normal")

# Low priority tasks
low_surveyor = pynng.Surveyor0(listen="tcp://127.0.0.1:5555_low")
low_respondent = pynng.Respondent0(dial="tcp://127.0.0.1:5555_low")
```

### Service Discovery Network

All peers connect to the discovery network:

```python
# Worker discovery
worker_bus = pynng.Bus0(listen="tcp://127.0.0.1:5550")

# Client discovery
client_bus = pynng.Bus0(dial="tcp://127.0.0.1:5550")
```

## NNG Configuration Options

### Resilience Settings

```python
socket = pynng.Req0(
    # Connection resilience
    reconnect_time_min=100,    # 100ms min reconnect time
    reconnect_time_max=5000,   # 5s max reconnect time
    
    # Retry settings
    retry_send_wait=1000,      # 1s between send retries
    retry_recv_wait=1000,      # 1s between receive retries
    
    # Timeout settings
    send_timeout=30000,        # 30s send timeout
    recv_timeout=30000,        # 30s receive timeout
)
```

### Polyamorous Mode

```python
# Connect to multiple workers
socket = pynng.Req0(
    polyamorous=True,  # Enable polyamorous mode
)
```

## Benefits of NNG Patterns

### 1. Built-in Reliability
- Automatic reconnection
- Built-in retry mechanisms
- Timeout handling
- Error recovery

### 2. Scalability
- Automatic load balancing
- Dynamic peer discovery
- Horizontal scaling
- No single points of failure

### 3. Performance
- Lightweight messaging
- Efficient memory usage
- Low latency
- High throughput

### 4. Flexibility
- Multiple communication patterns
- Configurable behavior
- Cross-language support
- Extensible architecture

## Comparison with Traditional Message Brokers

| Feature | FastQueue (NNG) | Traditional Brokers |
|---------|----------------|-------------------|
| Broker Required | No | Yes |
| Single Point of Failure | No | Yes |
| Auto-discovery | Yes | No (manual config) |
| Load Balancing | Built-in | Requires configuration |
| Retry Mechanisms | Built-in | Varies by broker |
| Language Support | Multiple | Varies by broker |

The use of NNG patterns makes FastQueue inherently more robust and easier to deploy than traditional message broker-based solutions.