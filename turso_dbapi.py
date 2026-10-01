"""
Turso DBAPI 2.0 Client over HTTP (PEP 249 Compliant)
Enables SQLAlchemy & Flask-SQLAlchemy to interface directly with Turso Database
over HTTP without requiring native C/Rust binaries.
"""

import base64
import requests
import sqlite3
from sqlite3 import Error, DatabaseError, OperationalError, IntegrityError, ProgrammingError

apilevel = "2.0"
threadsafety = 1
paramstyle = "qmark"

sqlite_version = sqlite3.sqlite_version
sqlite_version_info = sqlite3.sqlite_version_info

class TursoCursor:
    def __init__(self, connection):
        self.connection = connection
        self._description = None
        self._rows = []
        self._rowcount = -1
        self._lastrowid = None

    @property
    def description(self):
        return self._description

    @property
    def rowcount(self):
        return self._rowcount

    @property
    def lastrowid(self):
        return self._lastrowid

    def execute(self, sql, parameters=None):
        if parameters is None:
            parameters = ()
        
        args = []
        for p in parameters:
            if p is None:
                args.append({"type": "null"})
            elif isinstance(p, bool):
                args.append({"type": "integer", "value": "1" if p else "0"})
            elif isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                args.append({"type": "float", "value": str(p)})
            elif isinstance(p, (bytes, bytearray)):
                args.append({"type": "blob", "base64": base64.b64encode(p).decode('ascii')})
            else:
                args.append({"type": "text", "value": str(p)})

        req_payload = {
            "type": "execute",
            "stmt": {
                "sql": sql,
                "args": args
            }
        }

        res = self.connection._post([req_payload])
        if not res:
            raise OperationalError("Empty response from Turso server")

        result_obj = res[0]
        if result_obj.get("type") == "error":
            err_msg = result_obj.get("error", {}).get("message", "Unknown Turso Error")
            raise OperationalError(err_msg)

        resp_data = result_obj.get("response", {}).get("result", {})
        cols = resp_data.get("cols", [])
        if cols:
            self._description = [(col.get("name", ""), None, None, None, None, None, None) for col in cols]
        else:
            self._description = None

        raw_rows = resp_data.get("rows", [])
        converted_rows = []
        for r in raw_rows:
            row_tuple = []
            for cell in r:
                ctype = cell.get("type")
                cval = cell.get("value")
                if ctype == "null":
                    row_tuple.append(None)
                elif ctype == "integer":
                    row_tuple.append(int(cval))
                elif ctype == "float":
                    row_tuple.append(float(cval))
                elif ctype == "text":
                    row_tuple.append(str(cval))
                elif ctype == "blob":
                    row_tuple.append(base64.b64decode(cell.get("base64", "")))
                else:
                    row_tuple.append(cval)
            converted_rows.append(tuple(row_tuple))

        self._rows = converted_rows
        self._rowcount = resp_data.get("affected_row_count", len(converted_rows))
        raw_last_id = resp_data.get("last_insert_rowid")
        self._lastrowid = int(raw_last_id) if raw_last_id is not None else None
        return self

    def executemany(self, sql, seq_of_parameters):
        for params in seq_of_parameters:
            self.execute(sql, params)

    def fetchone(self):
        if not self._rows:
            return None
        return self._rows.pop(0)

    def fetchmany(self, size=None):
        if size is None:
            size = len(self._rows)
        res = self._rows[:size]
        self._rows = self._rows[size:]
        return res

    def fetchall(self):
        res = self._rows
        self._rows = []
        return res

    def close(self):
        self._rows = []

class TursoConnection:
    def __init__(self, url, auth_token):
        clean_url = url.replace("libsql://", "https://").replace("sqlite+libsql://", "https://")
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = "https://" + clean_url
        clean_url = clean_url.rstrip("/")
        if not clean_url.endswith("/v2/pipeline"):
            clean_url = clean_url + "/v2/pipeline"

        self.endpoint = clean_url
        self.auth_token = auth_token
        self.isolation_level = None
        self.row_factory = None
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        })

    @property
    def in_transaction(self):
        return False

    def create_function(self, name, num_params, func, *args, **kwargs):
        pass

    def create_aggregate(self, *args, **kwargs):
        pass

    def create_collation(self, *args, **kwargs):
        pass

    def _post(self, requests_list):
        r = self.session.post(self.endpoint, json={"requests": requests_list})
        if r.status_code != 200:
            raise OperationalError(f"Turso HTTP Error {r.status_code}: {r.text}")
        data = r.json()
        return data.get("results", [])

    def cursor(self):
        return TursoCursor(self)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        self.session.close()

def connect(url="", auth_token="", **kwargs):
    return TursoConnection(url, auth_token)
