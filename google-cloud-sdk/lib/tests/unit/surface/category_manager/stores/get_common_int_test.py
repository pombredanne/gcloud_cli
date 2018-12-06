# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for 'gcloud category-manager stores get-common'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib.surface.category_manager import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,])
class GetCommonIntTest(base.CategoryManagerUnitTestBase):

  def _ExpectCommonStoreResponse(self, expected_store_name):
    """Mocks backend call that gets the common taxonomy store."""
    self.mock_client.taxonomyStores.GetCommon.Expect(
        self.messages.CategorymanagerTaxonomyStoresGetCommonRequest(),
        self.messages.TaxonomyStore(name=expected_store_name))

  def testGettingCommonStore(self, track):
    self.track = track
    expected_store_name = 'taxonomyStores/predefined'
    self._ExpectCommonStoreResponse(expected_store_name)
    common_store = self.Run('category-manager stores get-common')
    self.assertEqual(
        common_store, self.messages.TaxonomyStore(name=expected_store_name))
