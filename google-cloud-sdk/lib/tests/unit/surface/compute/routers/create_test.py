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
"""Tests for the routers create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.routers import router_utils
from tests.lib import test_case
from tests.lib.surface.compute import router_test_base
from tests.lib.surface.compute import router_test_utils


class CreateTestGA(router_test_base.RouterTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCreateBasic_success(self):
    self.SelectApi(self.track, self.api_version)

    expected = router_test_utils.CreateMinimalRouterMessage(
        self.messages, self.api_version)
    expected.description = 'my-desc'
    result = copy.deepcopy(expected)
    result.region = 'us-central1'

    self.ExpectInsert(expected)
    self.ExpectOperationsPolling()
    self.ExpectGet(result)

    self.Run("""
        compute routers create my-router --network default --region us-central1
        --asn 65000
        --description my-desc
        """)

    self.AssertOutputEquals(
        """\
        NAME       REGION       NETWORK
        my-router  us-central1  default
        """,
        normalize_space=True)
    self.AssertErrContains('Creating router [my-router]')

  def testCreate_async(self):
    """Test command with --async flag."""

    self.SelectApi(self.track, self.api_version)

    expected = router_test_utils.CreateMinimalRouterMessage(
        self.messages, self.api_version)

    self.ExpectInsert(expected)

    result = self.Run("""
        compute routers create my-router --network default --region us-central1
        --async
        --asn 65000
        """)
    self.assertIn('operation-X', result.name)
    self.AssertOutputEquals('')
    self.AssertErrEquals(
        'Create in progress for router [my-router] '
        '[https://compute.googleapis.com/compute/{0}/'
        'projects/fake-project/regions/us-central1/operations/operation-X] '
        'Run the [gcloud compute operations describe] command to check the '
        'status of this operation.\n'.format(self.api_version))

  def testCreateWithAdvertisements_default(self):
    self.SelectApi(self.track, self.api_version)

    expected = router_test_utils.CreateMinimalRouterMessage(
        self.messages, self.api_version)
    mode = self.messages.RouterBgp.AdvertiseModeValueValuesEnum.DEFAULT
    expected.bgp.advertiseMode = mode

    result = copy.deepcopy(expected)
    result.region = 'us-central1'

    self.ExpectInsert(expected)
    self.ExpectOperationsPolling()
    self.ExpectGet(result)

    self.Run("""
        compute routers create my-router --network default --region us-central1
        --asn 65000
        --advertisement-mode=DEFAULT
        """)

    self.AssertOutputEquals(
        """\
        NAME       REGION       NETWORK
        my-router  us-central1  default
        """,
        normalize_space=True)
    self.AssertErrContains('Creating router [my-router]')

  def testCreateWithAdvertisements_custom(self):
    self.SelectApi(self.track, self.api_version)

    expected = router_test_utils.CreateMinimalRouterMessage(
        self.messages, self.api_version)
    mode = self.messages.RouterBgp.AdvertiseModeValueValuesEnum.CUSTOM
    groups = [(self.messages.RouterBgp.AdvertisedGroupsValueListEntryValuesEnum.
               ALL_SUBNETS)]
    ranges = [
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.10/30', description='custom-range'),
        self.messages.RouterAdvertisedIpRange(
            range='10.10.10.20/30', description=''),
    ]
    expected.bgp.advertiseMode = mode
    expected.bgp.advertisedGroups = groups
    expected.bgp.advertisedIpRanges = ranges

    result = copy.deepcopy(expected)
    result.region = 'us-central1'

    self.ExpectInsert(expected)
    self.ExpectOperationsPolling()
    self.ExpectGet(result)

    self.Run("""
        compute routers create my-router --network default --region us-central1
        --asn 65000
        --advertisement-mode=CUSTOM
        --set-advertisement-groups=ALL_SUBNETS
        --set-advertisement-ranges=10.10.10.10/30=custom-range,10.10.10.20/30
        """)

    self.AssertOutputEquals(
        """\
        NAME       REGION       NETWORK
        my-router  us-central1  default
        """,
        normalize_space=True)
    self.AssertErrContains('Creating router [my-router]')

  def testCreateWithAdvertisements_customWithDefaultError(self):
    self.SelectApi(self.track, self.api_version)

    error_msg = ('Cannot specify custom advertisements for a router with '
                 'default mode.')
    with self.AssertRaisesExceptionMatches(router_utils.CustomWithDefaultError,
                                           error_msg):
      self.Run("""
          compute routers create my-router --network default
          --region us-central1
          --asn 65000
          --advertisement-mode=DEFAULT
          --set-advertisement-groups=ALL_SUBNETS
          --set-advertisement-ranges=10.10.10.10/30=custom-range,10.10.10.20/30
          """)


class CreateTestBeta(CreateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'

  def testCreateEmptyRouter(self):
    self.SelectApi(self.track, self.api_version)
    expected = router_test_utils.CreateEmptyRouterMessage(
        self.messages, self.api_version)
    expected.description = 'my-desc'
    result = copy.deepcopy(expected)
    result.region = 'us-central1'

    self.ExpectInsert(expected)
    self.ExpectOperationsPolling()
    self.ExpectGet(result)

    self.Run("""
        compute routers create my-router --network default --region us-central1
        --description my-desc
        """)

    self.AssertOutputEquals(
        """\
        NAME       REGION       NETWORK
        my-router  us-central1  default
        """,
        normalize_space=True)
    self.AssertErrContains('Creating router [my-router]')

  def testCreateWithAdvertisements_noAsn(self):
    self.SelectApi(self.track, self.api_version)
    expected = router_test_utils.CreateEmptyRouterMessage(
        self.messages, self.api_version)
    mode = self.messages.RouterBgp.AdvertiseModeValueValuesEnum.DEFAULT
    expected.bgp = self.messages.RouterBgp()
    expected.bgp.advertiseMode = mode

    result = copy.deepcopy(expected)
    result.region = 'us-central1'

    self.ExpectInsert(expected)
    self.ExpectOperationsPolling()
    self.ExpectGet(result)

    self.Run("""
        compute routers create my-router --network default --region us-central1
        --advertisement-mode=DEFAULT
        """)

    self.AssertOutputEquals(
        """\
        NAME       REGION       NETWORK
        my-router  us-central1  default
        """,
        normalize_space=True)
    self.AssertErrContains('Creating router [my-router]')

  def testCreateWithKeepaliveInterval(self):
    self.SelectApi(self.track, self.api_version)

    expected = router_test_utils.CreateMinimalRouterMessage(
        self.messages, self.api_version)
    expected.description = 'my-desc'
    expected.bgp.keepaliveInterval = 40
    result = copy.deepcopy(expected)
    result.region = 'us-central1'

    self.ExpectInsert(expected)
    self.ExpectOperationsPolling()
    self.ExpectGet(result)

    self.Run("""
        compute routers create my-router --network default --region us-central1
        --asn 65000 --keepalive-interval 40
        --description my-desc
        """)

    self.AssertOutputEquals(
        """\
        NAME       REGION       NETWORK
        my-router  us-central1  default
        """,
        normalize_space=True)
    self.AssertErrContains('Creating router [my-router]')


class CreateTestAlpha(CreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
