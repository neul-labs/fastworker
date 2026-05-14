"""Level 3: Organized — Production-ready project structure.

Separates concerns: tasks, services (business logic), and models.
Tasks are thin wrappers that delegate to services.

Usage:
    fastworker control-plane --task-modules fastworker.examples.level3_organized.app.tasks
"""

from fastworker.examples.level3_organized.app.tasks.background import *  # noqa: F401, F403
from fastworker.examples.level3_organized.app.tasks.scheduled import *  # noqa: F401, F403
