# Central import point so Base.metadata knows about every table.
# Add one line here whenever a new domain module gets a models.py.

from app.auth.models import EmailVerificationToken, User  # noqa: F401
from app.incident.models import Incident  # noqa: F401
from app.monitor.models import Monitor  # noqa: F401
