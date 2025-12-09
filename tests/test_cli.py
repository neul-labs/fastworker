"""Test cases for FastWorker CLI."""

from unittest.mock import patch, Mock
from fastworker.cli import main, load_tasks, start_worker, submit_task, list_tasks


def test_load_tasks_success():
    """Test successful task loading."""
    with patch("fastworker.cli.importlib.import_module") as mock_import:
        load_tasks(["test_module"])
        mock_import.assert_called_once_with("test_module")


def test_load_tasks_import_error():
    """Test task loading with import error."""
    with patch("fastworker.cli.importlib.import_module") as mock_import:
        mock_import.side_effect = ImportError("Module not found")

        # Capture stdout instead of mocking print directly
        import io
        from contextlib import redirect_stdout

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            load_tasks(["nonexistent_module"])

        output = captured_output.getvalue()
        assert "Failed to import nonexistent_module: Module not found" in output


@patch("fastworker.cli.Worker")
@patch("fastworker.cli.asyncio.run")
def test_start_worker(mock_run, mock_worker_class):
    """Test worker start functionality."""
    mock_worker = Mock()
    mock_worker_class.return_value = mock_worker

    args = Mock()
    args.worker_id = "test-worker"
    args.base_address = "tcp://127.0.0.1:5555"
    args.discovery_address = "tcp://127.0.0.1:5550"
    args.task_modules = ["test_module"]

    with patch("fastworker.cli.load_tasks") as mock_load:
        start_worker(args)

        mock_load.assert_called_once_with(["test_module"])
        mock_worker_class.assert_called_once_with(
            worker_id="test-worker",
            base_address="tcp://127.0.0.1:5555",
            discovery_address="tcp://127.0.0.1:5550",
        )
        mock_run.assert_called_once_with(mock_worker.start())


@patch("fastworker.cli.Client")
@patch("fastworker.cli.asyncio.run")
def test_submit_task(mock_run, mock_client_class):
    """Test task submission functionality."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client

    # Mock asyncio.run to return None (non-blocking mode returns None)
    mock_run.return_value = None

    args = Mock()
    args.discovery_address = "tcp://127.0.0.1:5550"
    args.task_name = "test_task"
    args.args = ["arg1", "arg2"]
    args.priority = "normal"
    args.task_modules = ["test_module"]
    args.non_blocking = True

    with patch("fastworker.cli.load_tasks") as mock_load:
        submit_task(args)

        # Verify task modules were loaded
        mock_load.assert_called_once_with(["test_module"])
        # Verify client was created with correct address
        mock_client_class.assert_called_once_with(
            discovery_address="tcp://127.0.0.1:5550"
        )
        # Verify asyncio.run was called (which runs the submit coroutine)
        mock_run.assert_called_once()


@patch("fastworker.cli.task_registry")
def test_list_tasks(mock_registry):
    """Test task listing functionality."""
    mock_registry.list_tasks.return_value = ["task1", "task2", "task3"]

    args = Mock()
    args.task_modules = ["test_module"]

    with patch("fastworker.cli.load_tasks") as mock_load:
        with patch("builtins.print") as mock_print:
            list_tasks(args)

            mock_load.assert_called_once_with(["test_module"])
            mock_print.assert_any_call("Available tasks:")
            mock_print.assert_any_call("  - task1")
            mock_print.assert_any_call("  - task2")
            mock_print.assert_any_call("  - task3")


def test_main_no_command():
    """Test main function with no command."""
    with patch("sys.argv", ["fastworker"]):
        with patch("fastworker.cli.argparse.ArgumentParser.print_help") as mock_help:
            main()
            mock_help.assert_called_once()


def test_main_with_worker_command():
    """Test main function with worker command."""
    test_args = [
        "fastworker",
        "worker",
        "--worker-id",
        "test-worker",
        "--base-address",
        "tcp://127.0.0.1:5555",
        "--discovery-address",
        "tcp://127.0.0.1:5550",
    ]

    with patch("sys.argv", test_args):
        with patch("fastworker.cli.start_worker") as mock_start:
            main()
            # Verify that start_worker was called with correct arguments
            mock_start.assert_called_once()


def test_main_with_submit_command():
    """Test main function with submit command."""
    test_args = [
        "fastworker",
        "submit",
        "--task-name",
        "test_task",
        "--args",
        "arg1",
        "arg2",
    ]

    with patch("sys.argv", test_args):
        with patch("fastworker.cli.submit_task") as mock_submit:
            main()
            mock_submit.assert_called_once()


def test_main_with_list_command():
    """Test main function with list command."""
    test_args = ["fastworker", "list"]

    with patch("sys.argv", test_args):
        with patch("fastworker.cli.list_tasks") as mock_list:
            main()
            mock_list.assert_called_once()
