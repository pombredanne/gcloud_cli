# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the instance-groups managed list-instances subcommand."""

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'beta'


class InstanceGroupsListInstancesBetaZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.track = calliope_base.ReleaseTrack.BETA
    self.make_requests.side_effect = iter([
        [self.messages.InstanceGroupManagersListManagedInstancesResponse(
            managedInstances=(
                test_resources.MakeInstancesInManagedInstanceGroupBeta(
                    self.messages, API_VERSION)))],
    ])

  def testListInstances(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS          ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING         NONE       template-1        xxx
            inst-2 central2-a STOPPED         RECREATING template-1
            inst-3 central2-a RUNNING         DELETING   template-2        yyy
            inst-4 central2-a                 CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """), normalize_space=True)

  def testListInstancesWithLimit(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --limit 2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS          ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING         NONE       template-1        xxx
            inst-2 central2-a STOPPED         RECREATING template-1
            """), normalize_space=True)

  def testListInstancesByUri(self):
    self.Run("""
        compute instance-groups managed list-instances
          https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instanceGroupManagers/group-1
          --zone central2-a
        """.format(API_VERSION))
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS          ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING         NONE       template-1        xxx
            inst-2 central2-a STOPPED         RECREATING template-1
            inst-3 central2-a RUNNING         DELETING   template-2        yyy
            inst-4 central2-a                 CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """), normalize_space=True)

  def testListInstancesBySorted(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --sort-by ~NAME
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS          ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-4 central2-a                 CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            inst-3 central2-a RUNNING         DELETING   template-2        yyy
            inst-2 central2-a STOPPED         RECREATING template-1
            inst-1 central2-a RUNNING         NONE       template-1        xxx
            """), normalize_space=True)

  def testListInstancesUriOutput(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-1
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-2
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-3
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-4
            """.format(API_VERSION)))


class InstanceGroupsListInstancesBetaRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.track = calliope_base.ReleaseTrack.BETA
    self.make_requests.side_effect = iter([
        [self.messages.InstanceGroupManagersListManagedInstancesResponse(
            managedInstances=(
                test_resources.MakeInstancesInManagedInstanceGroupBeta(
                    self.messages, API_VERSION)))],
    ])

  def testListInstances(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS          ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING         NONE       template-1        xxx
            inst-2 central2-a STOPPED         RECREATING template-1
            inst-3 central2-a RUNNING         DELETING   template-2        yyy
            inst-4 central2-a                 CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """), normalize_space=True)

  def testListInstancesWithLimit(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --limit 2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS          ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING         NONE       template-1        xxx
            inst-2 central2-a STOPPED         RECREATING template-1
            """), normalize_space=True)

  def testListInstancesByUri(self):
    self.Run("""
        compute instance-groups managed list-instances
          https://www.googleapis.com/compute/{0}/projects/my-project/regions/central2/instanceGroupManagers/group-1
          --region central2
        """.format(API_VERSION))
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS          ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING         NONE       template-1        xxx
            inst-2 central2-a STOPPED         RECREATING template-1
            inst-3 central2-a RUNNING         DELETING   template-2        yyy
            inst-4 central2-a                 CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """), normalize_space=True)

  def testListInstancesBySorted(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --sort-by ~NAME
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS          ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-4 central2-a                 CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            inst-3 central2-a RUNNING         DELETING   template-2        yyy
            inst-2 central2-a STOPPED         RECREATING template-1
            inst-1 central2-a RUNNING         NONE       template-1        xxx
            """), normalize_space=True)

  def testListInstancesUriOutput(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-1
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-2
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-3
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-4
            """.format(API_VERSION)))

  def testPrompting(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='central2')],
        [self.messages.Zone(name='central2-a')],
        [self.messages.InstanceGroupManagersListManagedInstancesResponse(
            managedInstances=(
                test_resources.MakeInstancesInManagedInstanceGroupBeta(
                    self.messages, API_VERSION)))],
    ])
    self.WriteInput('2\n')
    self.Run("""
        compute instance-groups managed list-instances group-1
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS          ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING         NONE       template-1        xxx
            inst-2 central2-a STOPPED         RECREATING template-1
            inst-3 central2-a RUNNING         DELETING   template-2        yyy
            inst-4 central2-a                 CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """), normalize_space=True)

if __name__ == '__main__':
  test_case.main()
