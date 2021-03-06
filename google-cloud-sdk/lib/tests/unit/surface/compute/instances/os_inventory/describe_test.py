# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.surface.compute.instances.os_inventory.describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import textwrap
import zlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.instances.os_inventory import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class DescribeTestGA(test_base.BaseTest, test_case.WithOutputCapture):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi('v1')

  def testDescribeWithRegularInventoryData(self):
    installed_packages = (
        b'{"deb":[{"Name":"test-package","Arch":"all","Version":"v1"}]}')
    self.make_requests.side_effect = iter([[
        self.messages.GuestAttributes(
            kind='compute#guestAttributes',
            queryPath='guestInventory/',
            queryValue=self.messages.GuestAttributesValue(items=[
                self.messages.GuestAttributesEntry(
                    key='Architecture',
                    namespace='guestInventory',
                    value='x86_64'),
                self.messages.GuestAttributesEntry(
                    key='ShortName', namespace='guestInventory',
                    value='debian'),
                self.messages.GuestAttributesEntry(
                    key='InstalledPackages',
                    namespace='guestInventory',
                    value=base64.b64encode(zlib.compress(installed_packages)))
            ]),
            selfLink='link-to-instance?')
    ]])

    self.Run(
        """compute instances os-inventory describe test-instance --zone zone-1"""
    )

    service = self.compute.instances
    method = 'GetGuestAttributes'
    request = self.messages.ComputeInstancesGetGuestAttributesRequest(
        instance='test-instance',
        project='my-project',
        queryPath='guestInventory/',
        zone='zone-1')
    self.CheckRequests([(service, method, request)])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
          +-------------------------------------------------------+
          |                Installed Packages (DEB)               |
          +----------------------+--------------+-----------------+
          |         NAME         |     ARCH     |     VERSION     |
          +----------------------+--------------+-----------------+
          | test-package         | all          | v1              |
          +----------------------+--------------+-----------------+
          Architecture: x86_64
          ShortName: debian
        """))
    self.AssertErrEquals('')

  def testDescribeWithWindowsUpdateAgentInventoryData(self):
    installed_packages = (
        b'{"wua":[{"Categories":["Updates"],'
        b'"CategoryIDs":["abc"],'
        b'"Description":"Test","KBArticleIDs":["4530715"],'
        b'"LastDeploymentChangeTime":"2019-12-10","RevisionNumber":1,'
        b'"SupportURL":"https://abc",'
        b'"Title":"Title","UpdateID":"12345"}]}')
    self.make_requests.side_effect = iter([[
        self.messages.GuestAttributes(
            kind='compute#guestAttributes',
            queryPath='guestInventory/',
            queryValue=self.messages.GuestAttributesValue(items=[
                self.messages.GuestAttributesEntry(
                    key='Architecture',
                    namespace='guestInventory',
                    value='x86_64'),
                self.messages.GuestAttributesEntry(
                    key='ShortName', namespace='guestInventory',
                    value='debian'),
                self.messages.GuestAttributesEntry(
                    key='InstalledPackages',
                    namespace='guestInventory',
                    value=base64.b64encode(zlib.compress(installed_packages)))
            ]),
            selfLink='link-to-instance?')
    ]])

    self.Run(
        """compute instances os-inventory describe test-instance --zone zone-1"""
    )

    service = self.compute.instances
    method = 'GetGuestAttributes'
    request = self.messages.ComputeInstancesGetGuestAttributesRequest(
        instance='test-instance',
        project='my-project',
        queryPath='guestInventory/',
        zone='zone-1')
    self.CheckRequests([(service, method, request)])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
          +---------------------------------------------------------------------+
          |              Installed Packages (Windows Update Agent)              |
          +-------+------------+----------------+-------------+-----------------+
          | TITLE | CATEGORIES | KB_ARTICLE_IDS | SUPPORT_URL | LAST_DEPLOYMENT |
          +-------+------------+----------------+-------------+-----------------+
          | Title | Updates    | 4530715        | https://abc | 2019-12-10      |
          +-------+------------+----------------+-------------+-----------------+
          Architecture: x86_64
          ShortName: debian
        """))
    self.AssertErrEquals('')

  def testDescribeWithWindowsQuickFixEngineeringInventoryData(self):
    installed_packages = (b'{"qfe":[{"Caption":"http://abc",'
                          b'"Description":"Update","HotFixID":"KB4480979",'
                          b'"InstalledOn":"1/9/2019"}]}')
    self.make_requests.side_effect = iter([[
        self.messages.GuestAttributes(
            kind='compute#guestAttributes',
            queryPath='guestInventory/',
            queryValue=self.messages.GuestAttributesValue(items=[
                self.messages.GuestAttributesEntry(
                    key='Architecture',
                    namespace='guestInventory',
                    value='x86_64'),
                self.messages.GuestAttributesEntry(
                    key='ShortName', namespace='guestInventory',
                    value='debian'),
                self.messages.GuestAttributesEntry(
                    key='InstalledPackages',
                    namespace='guestInventory',
                    value=base64.b64encode(zlib.compress(installed_packages)))
            ]),
            selfLink='link-to-instance?')
    ]])

    self.Run(
        """compute instances os-inventory describe test-instance --zone zone-1"""
    )

    service = self.compute.instances
    method = 'GetGuestAttributes'
    request = self.messages.ComputeInstancesGetGuestAttributesRequest(
        instance='test-instance',
        project='my-project',
        queryPath='guestInventory/',
        zone='zone-1')
    self.CheckRequests([(service, method, request)])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
          +------------------------------------------------------+
          |      Installed Packages (Quick Fix Engineering)      |
          +------------+-------------+------------+--------------+
          |  CAPTION   | DESCRIPTION | HOT_FIX_ID | INSTALLED_ON |
          +------------+-------------+------------+--------------+
          | http://abc | Update      | KB4480979  | 1/9/2019     |
          +------------+-------------+------------+--------------+
          Architecture: x86_64
          ShortName: debian
        """))
    self.AssertErrEquals('')

  def testDescribeWithZypperPatchesInventoryData(self):
    installed_packages = (
        b'{"zypperPatches":[{"Name":"SUSE-SLE-Module-Basesystem-15-2019-2992",'
        b'"Category":"recommended","Severity":"moderate",'
        b'"Summary":"Update"}]}')
    self.make_requests.side_effect = iter([[
        self.messages.GuestAttributes(
            kind='compute#guestAttributes',
            queryPath='guestInventory/',
            queryValue=self.messages.GuestAttributesValue(items=[
                self.messages.GuestAttributesEntry(
                    key='Architecture',
                    namespace='guestInventory',
                    value='x86_64'),
                self.messages.GuestAttributesEntry(
                    key='ShortName', namespace='guestInventory',
                    value='sles'),
                self.messages.GuestAttributesEntry(
                    key='InstalledPackages',
                    namespace='guestInventory',
                    value=base64.b64encode(zlib.compress(installed_packages)))
            ]),
            selfLink='link-to-instance?')
    ]])

    self.Run(
        """compute instances os-inventory describe test-instance --zone zone-1"""
    )

    service = self.compute.instances
    method = 'GetGuestAttributes'
    request = self.messages.ComputeInstancesGetGuestAttributesRequest(
        instance='test-instance',
        project='my-project',
        queryPath='guestInventory/',
        zone='zone-1')
    self.CheckRequests([(service, method, request)])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
          +----------------------------------------------------------------------------+
          |                      Installed Patches (Zypper Patch)                      |
          +-----------------------------------------+-------------+----------+---------+
          |                   NAME                  |   CATEGORY  | SEVERITY | SUMMARY |
          +-----------------------------------------+-------------+----------+---------+
          | SUSE-SLE-Module-Basesystem-15-2019-2992 | recommended | moderate | Update  |
          +-----------------------------------------+-------------+----------+---------+
          Architecture: x86_64
          ShortName: sles
        """))
    self.AssertErrEquals('')

  def testTextOutput(self):
    self.make_requests.side_effect = iter([[
        self.messages.GuestAttributes(
            kind='compute#guestAttributes',
            queryPath='guestInventory/',
            queryValue=self.messages.GuestAttributesValue(items=[
                self.messages.GuestAttributesEntry(
                    key='KernelVersion',
                    namespace='guestInventory',
                    value='4.9.0-8-amd64'),
                self.messages.GuestAttributesEntry(
                    key='OSConfigAgentVersion',
                    namespace='guestInventory',
                    value='0.4.3')
            ]),
            selfLink='link-to-instance?')
    ]])

    self.Run("""compute instances os-inventory describe test-instance
          --zone zone-1
          --format text
        """)

    service = self.compute.instances
    method = 'GetGuestAttributes'
    request = self.messages.ComputeInstancesGetGuestAttributesRequest(
        instance='test-instance',
        project='my-project',
        queryPath='guestInventory/',
        zone='zone-1')
    self.CheckRequests([(service, method, request)])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
          SystemInformation.KernelVersion:        4.9.0-8-amd64
          SystemInformation.OSConfigAgentVersion: 0.4.3
        """))
    self.AssertErrEquals('')

  def testJsonOutput(self):
    self.make_requests.side_effect = iter([[
        self.messages.GuestAttributes(
            kind='compute#guestAttributes',
            queryPath='guestInventory/',
            queryValue=self.messages.GuestAttributesValue(items=[
                self.messages.GuestAttributesEntry(
                    key='LongName',
                    namespace='guestInventory',
                    value='Debian GNU/Linux 9 (stretch)'),
                self.messages.GuestAttributesEntry(
                    key='Version', namespace='guestInventory', value='9')
            ]),
            selfLink='link-to-instance?')
    ]])

    self.Run("""compute instances os-inventory describe test-instance
          --zone zone-1
          --format json
        """)

    service = self.compute.instances
    method = 'GetGuestAttributes'
    request = self.messages.ComputeInstancesGetGuestAttributesRequest(
        instance='test-instance',
        project='my-project',
        queryPath='guestInventory/',
        zone='zone-1')
    self.CheckRequests([(service, method, request)])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
          {
            "SystemInformation": {
              "LongName": "Debian GNU/Linux 9 (stretch)",
              "Version": "9"
            }
          }
        """))
    self.AssertErrEquals('')

  def testDescribeWithoutInventoryData(self):

    def MakeRequests(*_, **kwargs):
      # pylint: disable=using-constant-test
      if False:
        yield
      kwargs['errors'].append((
          404,
          'The resource \'guestInventory/\' of type \'Guest Attribute\' was not'
          ' found.'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesExceptionRegexp(
        exceptions.OsInventoryNotFoundException,
        textwrap.dedent("""\
        Could not fetch resource:
         - OS inventory data was not found. Make sure the OS Config agent is running on this instance."""
                       )):
      self.Run(
          """compute instances os-inventory describe test-instance --zone zone-1"""
      )

    service = self.compute.instances
    method = 'GetGuestAttributes'
    request = self.messages.ComputeInstancesGetGuestAttributesRequest(
        instance='test-instance',
        project='my-project',
        queryPath='guestInventory/',
        zone='zone-1')
    self.CheckRequests([(service, method, request)])
    self.assertFalse(self.GetOutput())

  def testOtherToolException(self):

    def MakeRequests(*_, **kwargs):
      # pylint: disable=using-constant-test
      if False:
        yield
      kwargs['errors'].append((
          404,
          'The resource \'projects/wjchen-osconfig-test/zones/us-east1-b/instances/my-project\' was not found.'
      ))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not fetch resource:
         - The resource \'projects/wjchen-osconfig-test/zones/us-east1-b/instances/my-project\' was not found."""
                       )):
      self.Run(
          """compute instances os-inventory describe test-instance --zone zone-1"""
      )

    service = self.compute.instances
    method = 'GetGuestAttributes'
    request = self.messages.ComputeInstancesGetGuestAttributesRequest(
        instance='test-instance',
        project='my-project',
        queryPath='guestInventory/',
        zone='zone-1')
    self.CheckRequests([(service, method, request)])
    self.assertFalse(self.GetOutput())


class DescribeTestBeta(DescribeTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SelectApi('beta')


class DescribeTestAlpha(DescribeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.SelectApi('alpha')


if __name__ == '__main__':
  test_case.main()
