"""Level 2: Package — Tasks organized as importable modules.

When you have more than a handful of tasks, split them into a package.
The __init__.py re-exports everything so --task-modules still works
with a single import path.

Usage:
    fastworker control-plane --task-modules fastworker.examples.level2_package.tasks
    fastworker submit --task-name send_welcome_email --args 42 '"user@example.com"'
"""

from fastworker.examples.level2_package.tasks.emails import *  # noqa: F401, F403
from fastworker.examples.level2_package.tasks.reports import *  # noqa: F401, F403
