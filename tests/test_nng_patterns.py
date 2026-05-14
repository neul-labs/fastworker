"""Tests for NNG communication patterns."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastworker.patterns.nng_patterns import (
    ReqRepPattern,
    BusPattern,
    PairPattern,
    SurveyorRespondentPattern,
)


# --- ReqRepPattern ---

def test_reqrep_server_uses_rep0():
    with patch("fastworker.patterns.nng_patterns.pynng.Rep0") as MockRep, \
         patch("fastworker.patterns.nng_patterns.pynng.Req0") as MockReq:
        p = ReqRepPattern("tcp://127.0.0.1:5555", is_server=True)
        assert p.is_server is True
        assert not MockReq.called


def test_reqrep_client_uses_req0():
    with patch("fastworker.patterns.nng_patterns.pynng.Req0") as MockReq, \
         patch("fastworker.patterns.nng_patterns.pynng.Rep0") as MockRep:
        p = ReqRepPattern("tcp://127.0.0.1:5555", is_server=False)
        assert p.is_server is False
        assert not MockRep.called


def test_reqrep_close_when_no_socket():
    p = ReqRepPattern("tcp://127.0.0.1:5555", is_server=True)
    p.socket = None
    p.close()  # should not raise


# --- BusPattern ---

def test_bus_listen_uses_bus0():
    with patch("fastworker.patterns.nng_patterns.pynng.Bus0") as MockBus:
        p = BusPattern("tcp://127.0.0.1:5550", listen=True)
        assert p.listen is True


def test_bus_dial_uses_bus0():
    with patch("fastworker.patterns.nng_patterns.pynng.Bus0") as MockBus:
        p = BusPattern("tcp://127.0.0.1:5550", listen=False)
        assert p.listen is False


# --- PairPattern ---

def test_pair_server_uses_pair0():
    with patch("fastworker.patterns.nng_patterns.pynng.Pair0") as MockPair:
        p = PairPattern("tcp://127.0.0.1:5555", is_server=True)
        assert p.is_server is True


def test_pair_client_uses_pair0():
    with patch("fastworker.patterns.nng_patterns.pynng.Pair0") as MockPair:
        p = PairPattern("tcp://127.0.0.1:5555", is_server=False)
        assert p.is_server is False


# --- SurveyorRespondentPattern ---

def test_surveyor_uses_surveyor0():
    with patch("fastworker.patterns.nng_patterns.pynng.Surveyor0") as MockS, \
         patch("fastworker.patterns.nng_patterns.pynng.Respondent0") as MockR:
        p = SurveyorRespondentPattern("tcp://127.0.0.1:5555", is_surveyor=True)
        assert p.is_surveyor is True
        assert not MockR.called


def test_respondent_uses_respondent0():
    with patch("fastworker.patterns.nng_patterns.pynng.Respondent0") as MockR, \
         patch("fastworker.patterns.nng_patterns.pynng.Surveyor0") as MockS:
        p = SurveyorRespondentPattern("tcp://127.0.0.1:5555", is_surveyor=False)
        assert p.is_surveyor is False
        assert not MockS.called


# --- send/recv/close delegation ---

@pytest.mark.asyncio
async def test_reqrep_send_delegates():
    mock_socket = AsyncMock()
    p = ReqRepPattern("tcp://127.0.0.1:5555", is_server=False)
    p.socket = mock_socket
    await p.send(b"hello")
    mock_socket.asend.assert_called_once_with(b"hello")


@pytest.mark.asyncio
async def test_reqrep_recv_delegates():
    mock_socket = AsyncMock()
    mock_socket.arecv.return_value = b"world"
    p = ReqRepPattern("tcp://127.0.0.1:5555", is_server=False)
    p.socket = mock_socket
    data = await p.recv()
    assert data == b"world"
    mock_socket.arecv.assert_called_once()


def test_close_calls_socket_close():
    mock_socket = MagicMock()
    p = ReqRepPattern("tcp://127.0.0.1:5555", is_server=False)
    p.socket = mock_socket
    p.close()
    mock_socket.close.assert_called_once()
