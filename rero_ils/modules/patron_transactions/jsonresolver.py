# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Patron Transaction resolver."""

import jsonresolver
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus


@jsonresolver.route('/api/patron_transactions/<pid>', host='ils.rero.ch')
def patron_transaction_resolver(pid):
    """Resolver for patron transaction record."""
    persistent_id = PersistentIdentifier.get('pttr', pid)
    if persistent_id.status == PIDStatus.REGISTERED:
        return dict(pid=persistent_id.pid_value)
    current_app.logger.error(
        'record resolver error: /api/patron_transactions/{pid} \
            {persistent_id}'.format(
            pid=pid,
            persistent_id=persistent_id
        )
    )
    raise Exception('unable to resolve')
