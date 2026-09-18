import os

# The question shown on the submission form and on the display screen.
# Change this text and redeploy (see README "Changing the question") to tweak it.
QUESTION_TEXT = os.environ.get(
    "QUESTION_TEXT",
    "One concrete goal/milestone you aim to achieve during the next week. "
    "“By Thursday I will have x number of customers.”",
)

EVENT_TITLE = os.environ.get("EVENT_TITLE", "Founder Residency — Week 1")

# Basic auth credentials for /admin and /export. Set ADMIN_PASSWORD in your
# Render environment variables before the event - do not rely on the default.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

# Where the SQLite file lives. On Render this should point at a mounted
# persistent disk (see render.yaml) so data survives restarts/redeploys.
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "submissions.db"))

MAX_NAME_LENGTH = 80
MAX_ANSWER_LENGTH = 4000

# Simple anti-spam: max submissions allowed per IP within the window below.
RATE_LIMIT_MAX_REQUESTS = 8
RATE_LIMIT_WINDOW_SECONDS = 60
