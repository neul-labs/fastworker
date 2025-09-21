"""Test cases for FastQueue CLI."""
import pytest
from unittest.mock import patch, Mock
import argparse
from fastqueue.cli import main, load_tasks, start_worker, submit_task, list_tasks


def test_load_tasks_success():
    """Test successful task loading."""
    with patch('fastqueue.cli.importlib.import_module') as mock_import:
        load_tasks(['test_module'])
        mock_import.assert_called_once_with('test_module')


def test_load_tasks_import_error():
    """Test task loading with import error."""
    with patch('fastqueue.cli.importlib.import_module') as mock_import:
        mock_import.side_effect = ImportError("Module not found")

        # Capture stdout instead of mocking print directly
        import io
        import sys
        from contextlib import redirect_stdout

        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            load_tasks(['nonexistent_module'])

        output = captured_output.getvalue()
        assert "Failed to import nonexistent_module: Module not found" in output


@patch('fastqueue.cli.Worker')
@patch('fastqueue.cli.asyncio.run')
def test_start_worker(mock_run, mock_worker_class):
    """Test worker start functionality."""
    mock_worker = Mock()
    mock_worker_class.return_value = mock_worker

    args = Mock()
    args.worker_id = "test-worker"
    args.base_address = "tcp://127.0.0.1:5555"
    args.discovery_address = "tcp://127.0.0.1:5550"
    args.task_modules = ["test_module"]

    with patch('fastqueue.cli.load_tasks') as mock_load:
        start_worker(args)

        mock_load.assert_called_once_with(["test_module"])
        mock_worker_class.assert_called_once_with(
            worker_id="test-worker",
            base_address="tcp://127.0.0.1:5555",
            discovery_address="tcp://127.0.0.1:5550"
        )
        mock_run.assert_called_once_with(mock_worker.start())


@patch('fastqueue.cli.Client')
@patch('fastqueue.cli.asyncio.run')
def test_submit_task(mock_run, mock_client_class):
    """Test task submission functionality."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client

    # Mock task result
    mock_result = Mock()
    mock_result.status = "success"
    mock_result.result = "Task completed"
    mock_run.return_value = mock_result

    args = Mock()
    args.discovery_address = "tcp://127.0.0.1:5550"
    args.task_name = "test_task"
    args.args = ["arg1", "arg2"]
    args.priority = "normal"
    args.task_modules = ["test_module"]

    with patch('fastqueue.cli.load_tasks') as mock_load:
        with patch('builtins.print') as mock_print:
            submit_task(args)

            mock_load.assert_called_once_with(["test_module"])
            mock_client_class.assert_called_once_with(discovery_address="tcp://127.0.0.1:5550")
            mock_print.assert_any_call("Task result: {}".format(mock_result))


@patch('fastqueue.cli.task_registry')
def test_list_tasks(mock_registry):
    """Test task listing functionality."""
    mock_registry.list_tasks.return_value = ["task1", "task2", "task3"]

    args = Mock()
    args.task_modules = ["test_module"]

    with patch('fastqueue.cli.load_tasks') as mock_load:
        with patch('builtins.print') as mock_print:
            list_tasks(args)

            mock_load.assert_called_once_with(["test_module"])
            mock_print.assert_any_call("Available tasks:")
            mock_print.assert_any_call("  - task1")
            mock_print.assert_any_call("  - task2")
            mock_print.assert_any_call("  - task3")


def test_main_no_command():
    """Test main function with no command."""
    with patch('sys.argv', ['fastqueue']):
        with patch('fastqueue.cli.argparse.ArgumentParser.print_help') as mock_help:
            main()
            mock_help.assert_called_once()


def test_main_with_worker_command():
    """Test main function with worker command."""
    test_args = [
        'fastqueue', 'worker',
        '--worker-id', 'test-worker',
        '--base-address', 'tcp://127.0.0.1:5555',
        '--discovery-address', 'tcp://127.0.0.1:5550'
    ]

    with patch('sys.argv', test_args):
        with patch('fastqueue.cli.start_worker') as mock_start:
            main()
            # Verify that start_worker was called with correct arguments
            mock_start.assert_called_once()


def test_main_with_submit_command():
    """Test main function with submit command."""
    test_args = [
        'fastqueue', 'submit',
        '--task-name', 'test_task',
        '--args', 'arg1', 'arg2'
    ]

    with patch('sys.argv', test_args):
        with patch('fastqueue.cli.submit_task') as mock_submit:
            main()
            mock_submit.assert_called_once()


def test_main_with_list_command():
    """Test main function with list command."""
    test_args = ['fastqueue', 'list']

    with patch('sys.argv', test_args):
        with patch('fastqueue.cli.list_tasks') as mock_list:
            main()
            mock_list.assert_called_once()