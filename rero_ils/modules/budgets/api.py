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

"""API for manipulating budgets."""

from functools import partial

from .models import BudgetIdentifier
from ..acq_accounts.api import AcqAccountsSearch
from ..api import IlsRecord, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider

# provider
BudgetProvider = type(
    'BudgetProvider',
    (Provider,),
    dict(identifier=BudgetIdentifier, pid_type='budg')
)
# minter
budget_id_minter = partial(id_minter, provider=BudgetProvider)
# fetcher
budget_id_fetcher = partial(id_fetcher, provider=BudgetProvider)


class BudgetsSearch(IlsRecordsSearch):
    """BudgetsSearch."""

    class Meta:
        """Search only on budget index."""

        index = 'budgets'


class Budget(IlsRecord):
    """Budget class."""

    minter = budget_id_minter
    fetcher = budget_id_fetcher
    provider = BudgetProvider

    def get_number_of_acq_accounts(self):
        """Get number of acq accounts."""
        results = AcqAccountsSearch().filter(
            'term', budget__pid=self.pid).source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        acq_accounts = self.get_number_of_acq_accounts()
        if acq_accounts:
            links['acq_accounts'] = acq_accounts
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete