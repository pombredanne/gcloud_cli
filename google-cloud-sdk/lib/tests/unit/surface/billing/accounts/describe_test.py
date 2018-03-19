# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for surface.billing.accounts.describe ."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.billing import base


class AccountsDescribeTest(base.BillingMockNoDisplayTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testDescribe(self):
    self.mocked_billing.billingAccounts.Get.Expect(
        self.messages.CloudbillingBillingAccountsGetRequest(
            name=base.BILLING_ACCOUNTS[0].name
        ),
        base.BILLING_ACCOUNTS[0]
    )

    self.assertEqual(
        self.Run('billing accounts describe {account_id}'.format(
            account_id=base.BILLING_ACCOUNTS[0].name[16:]
        )),
        base.BILLING_ACCOUNTS[0],
    )


if __name__ == '__main__':
  test_case.main()