# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2026 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Tests for concurrent record update protection via ETag / If-Match."""

import json

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from invenio_records_rest.errors import PIDResolveRESTError
from sqlalchemy.orm.exc import StaleDataError

from tests.utils import get_json


def test_concurrent_error_handlers_return_409(app):
    """Both StaleDataError paths must return 409 Conflict.

    Two error handlers cover the two ways a concurrent PUT can surface:

    1. Direct StaleDataError — raised by SQLAlchemy optimistic locking when two
       sessions try to commit the same record revision.

    2. PIDResolveRESTError wrapping StaleDataError — invenio-records-rest's
       pass_record decorator catches any SQLAlchemyError (including StaleDataError)
       raised inside the PUT handler and re-raises it as PIDResolveRESTError.
       Python sets __context__ automatically, which our handler inspects to detect
       this specific case and return 409 instead of 500.

    Both routes are registered before the first test_client() call because Flask
    forbids adding routes after the app has handled its first request.
    """

    @app.route("/test-stale-data-error", methods=["PUT"])
    def trigger_stale():
        raise StaleDataError()

    @app.route("/test-pid-resolve-wrapping-stale", methods=["PUT"])
    def trigger_wrapped():
        try:
            raise StaleDataError()
        except StaleDataError as e:
            raise PIDResolveRESTError("pid") from e

    with app.test_client() as client:
        res = client.put("/test-stale-data-error")
        assert res.status_code == 409
        assert res.get_json() == {
            "status": 409,
            "message": "Record was modified concurrently, please retry.",
        }

        res = client.put("/test-pid-resolve-wrapping-stale")
        assert res.status_code == 409
        assert res.get_json() == {
            "status": 409,
            "message": "Record was modified concurrently, please retry.",
        }


def test_sequential_updates_without_etag_succeed(client, librarian_martigny, patron_martigny, json_header):
    """Sequential PUTs without If-Match must both succeed.

    Without concurrent requests there is no version conflict, so two
    sequential PUTs without If-Match must each return 200 and advance
    the ETag independently.
    """
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for("invenio_records_rest.ptrn_item", pid_value=patron_martigny.pid)

    res = client.get(item_url)
    assert res.status_code == 200
    etag = res.headers["ETag"]
    data = get_json(res)["metadata"]

    # First PUT — must succeed and advance the revision
    res = client.put(item_url, data=json.dumps(data), headers=json_header)
    assert res.status_code == 200
    assert res.headers["ETag"] != etag

    # Second PUT — must also succeed (sequential, no real concurrency)
    etag = res.headers["ETag"]
    res = client.put(item_url, data=json.dumps(data), headers=json_header)
    assert res.status_code == 200
    assert res.headers["ETag"] != etag


def test_etag_prevents_stale_concurrent_update(client, librarian_martigny, patron_martigny, json_header):
    """Second PUT with a stale ETag must be rejected with 412.

    Simulates a double-click or two concurrent saves by sending two PUT
    requests carrying the same If-Match value. After the first PUT commits,
    the record revision advances and the second PUT must fail with 412
    Precondition Failed rather than silently overwriting or returning 500.
    """
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for("invenio_records_rest.ptrn_item", pid_value=patron_martigny.pid)

    # Capture the current ETag from a GET
    res = client.get(item_url)
    assert res.status_code == 200
    etag = res.headers["ETag"]
    data = get_json(res)["metadata"]

    headers_with_etag = [*json_header, ("If-Match", etag)]

    # First PUT with the correct ETag — must succeed and advance the revision
    res = client.put(item_url, data=json.dumps(data), headers=headers_with_etag)
    assert res.status_code == 200
    assert res.headers["ETag"] != etag

    # Second PUT with the now-stale ETag — must be rejected
    res = client.put(item_url, data=json.dumps(data), headers=headers_with_etag)
    assert res.status_code == 412
    assert res.get_json() == {
        "status": 412,
        "message": "The precondition on the request for the URL failed positive evaluation.",
    }
