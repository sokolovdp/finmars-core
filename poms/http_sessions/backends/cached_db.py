from django.contrib.sessions.backends.cached_db import SessionStore as CashedDBStore

from poms.http_sessions.backends.db import SessionStore as DBStore


class SessionStore(DBStore, CashedDBStore):
    pass
