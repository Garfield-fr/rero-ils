# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2025 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Collection permissions."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    AllowedByActionRestrictByOrganisation,
    RecordPermissionPolicy,
)

# Actions to control Items policies for CRUD operations
search_action = action_factory("coll-search")
read_action = action_factory("coll-read")
create_action = action_factory("coll-create")
update_action = action_factory("coll-update")
delete_action = action_factory("coll-delete")
access_action = action_factory("coll-access")


def get_libraries(collection):
    """Get a callback function to return library pids."""
    return getattr(collection, "library_pids", None)


class CollectionPermissionPolicy(RecordPermissionPolicy):
    """Collection Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByManageableLibrary(create_action, callback=get_libraries)]
    can_update = [AllowedByActionRestrictByManageableLibrary(update_action, callback=get_libraries)]
    can_delete = [AllowedByActionRestrictByManageableLibrary(delete_action, callback=get_libraries)]
