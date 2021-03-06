# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Base for Genomics gcloud unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error


class _Base(cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.messages = core_apis.GetMessagesModule('genomics', 'v1')
    self.messages_v2 = core_apis.GetMessagesModule('genomics', 'v2alpha1')

  def RunGenomics(self, command, gcloud_args=None):
    gcloud_args = gcloud_args or []
    return super(_Base, self).Run(gcloud_args + ['genomics'] + command)


class GenomicsIntegrationTest(_Base, e2e_base.WithServiceAuth):
  """Base class for all genomics integration tests."""


class GenomicsUnitTest(sdk_test_base.WithFakeAuth, _Base):
  """Base class for Genomics unit tests."""

  def SetUp(self):
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('genomics', 'v1'),
        real_client=core_apis.GetClientInstance('genomics', 'v1', no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

    self.mocked_client_v1a2 = mock.Client(
        core_apis.GetClientClass('genomics', 'v1alpha2'),
        real_client=core_apis.GetClientInstance(
            'genomics', 'v1alpha2', no_http=True))
    self.mocked_client_v1a2.Mock()
    self.addCleanup(self.mocked_client_v1a2.Unmock)

    self.mocked_client_v2 = mock.Client(
        core_apis.GetClientClass('genomics', 'v2alpha1'),
        real_client=core_apis.GetClientInstance(
            'genomics', 'v2alpha1', no_http=True))
    self.mocked_client_v2.Mock()
    self.addCleanup(self.mocked_client_v2.Unmock)

  def MakeHttpError(self, status_code, message='', failing_url=''):
    return http_error.MakeHttpError(code=status_code, message=message,
                                    url=failing_url)
