from pysqlite2 import dbapi2 as sqlite3

# The shared cache is only available in SQLite versions 3.3.3 or later
# See the SQLite documentaton for details.

sqlite3.enable_shared_cache(True)
