"""NNG patterns implementation for FastQueue."""
import pynng
import asyncio
from typing import Optional, List, Callable
from enum import Enum

class PatternType(Enum):
    """NNG pattern types."""
    REQ_REP = "req_rep"
    PUB_SUB = "pub_sub"
    SURVEYOR_RESPONDENT = "surveyor_respondent"
    BUS = "bus"
    PAIR = "pair"

class ReqRepPattern:
    """Request/Reply pattern for reliable delivery."""
    
    def __init__(self, address: str, is_server: bool = False):
        self.address = address
        self.is_server = is_server
        self.socket = None
    
    async def start(self):
        """Start the socket."""
        if self.is_server:
            self.socket = pynng.Rep0(listen=self.address)
        else:
            self.socket = pynng.Req0(dial=self.address)
    
    async def send(self, data: bytes):
        """Send data."""
        await self.socket.asend(data)
    
    async def recv(self) -> bytes:
        """Receive data."""
        return await self.socket.arecv()
    
    def close(self):
        """Close the socket."""
        if self.socket:
            self.socket.close()

class PubSubPattern:
    """Publish/Subscribe pattern for priority queues."""
    
    def __init__(self, address: str, is_publisher: bool = False, subscribe_topic: bytes = b''):
        self.address = address
        self.is_publisher = is_publisher
        self.subscribe_topic = subscribe_topic
        self.socket = None
    
    async def start(self):
        """Start the socket."""
        if self.is_publisher:
            self.socket = pynng.Pub0(listen=self.address)
        else:
            self.socket = pynng.Sub0(dial=self.address)
            if self.subscribe_topic:
                self.socket.subscribe(self.subscribe_topic)
    
    async def send(self, data: bytes):
        """Send data (publishers only)."""
        if not self.is_publisher:
            raise RuntimeError("Only publishers can send data")
        await self.socket.asend(data)
    
    async def recv(self) -> bytes:
        """Receive data (subscribers only)."""
        if self.is_publisher:
            raise RuntimeError("Only subscribers can receive data")
        return await self.socket.arecv()
    
    def close(self):
        """Close the socket."""
        if self.socket:
            self.socket.close()

class SurveyorRespondentPattern:
    """Surveyor/Respondent pattern for load balancing."""
    
    def __init__(self, address: str, is_surveyor: bool = False):
        self.address = address
        self.is_surveyor = is_surveyor
        self.socket = None
    
    async def start(self):
        """Start the socket."""
        if self.is_surveyor:
            self.socket = pynng.Surveyor0(listen=self.address)
        else:
            self.socket = pynng.Respondent0(dial=self.address)
    
    async def send(self, data: bytes):
        """Send data."""
        await self.socket.asend(data)
    
    async def recv(self) -> bytes:
        """Receive data."""
        return await self.socket.arecv()
    
    def close(self):
        """Close the socket."""
        if self.socket:
            self.socket.close()

class BusPattern:
    """Bus pattern for service discovery."""
    
    def __init__(self, address: str, listen: bool = False):
        self.address = address
        self.listen = listen
        self.socket = None
    
    async def start(self):
        """Start the socket."""
        if self.listen:
            self.socket = pynng.Bus0(listen=self.address)
        else:
            self.socket = pynng.Bus0(dial=self.address)
    
    async def send(self, data: bytes):
        """Send data."""
        await self.socket.asend(data)
    
    async def recv(self) -> bytes:
        """Receive data."""
        return await self.socket.arecv()
    
    def close(self):
        """Close the socket."""
        if self.socket:
            self.socket.close()

class PairPattern:
    """Pair pattern for reliable delivery."""
    
    def __init__(self, address: str, is_server: bool = False):
        self.address = address
        self.is_server = is_server
        self.socket = None
    
    async def start(self):
        """Start the socket."""
        if self.is_server:
            self.socket = pynng.Pair0(listen=self.address)
        else:
            self.socket = pynng.Pair0(dial=self.address)
    
    async def send(self, data: bytes):
        """Send data."""
        await self.socket.asend(data)
    
    async def recv(self) -> bytes:
        """Receive data."""
        return await self.socket.arecv()
    
    def close(self):
        """Close the socket."""
        if self.socket:
            self.socket.close()