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
"""Module for instance-groups managed integration test base classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class ManagedTestBase(e2e_test_base.BaseTest):
  """Base class for instance-groups managed tests."""

  DEFAULT_DISK_IMAGE_FAMILY = 'centos-7'
  DEFAULT_DISK_IMAGE_PROJECT = 'centos-cloud'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

    # Containers for created resources.
    self.instance_template_names = []
    self.instance_group_manager_names = []
    self.region_instance_group_manager_names = []
    self.target_pool_names = []
    self.instance_uris = []
    # self.stateful_disk_names = []
    self.potential_stateful_disk_urls = set()

  def TearDown(self):
    self.DeleteResources(self.instance_group_manager_names,
                         self.DeleteInstanceGroupManager,
                         'instance group manager')
    self.DeleteResources(self.region_instance_group_manager_names,
                         self.DeleteRegionalInstanceGroupManager,
                         'regional instance group manager')
    try:
      self.DeleteResources(self.instance_template_names,
                           self.DeleteInstanceTemplate, 'instance template')
    except AssertionError:
      # Cleanup script should handle teardown issues
      pass
    self.DeleteResources(self.target_pool_names, self.DeleteTargetPool,
                         'target pool')
    self.DeleteResources(self.instance_uris, self.DeleteInstanceByUri,
                         'instance')
    self.CleanUpStatefulDisks(self.potential_stateful_disk_urls)

  def GetScopeFlag(self, plural=False):
    flag_value = ''
    if self.scope == e2e_test_base.ZONAL:
      flag_value = self.zone
    elif self.scope == e2e_test_base.REGIONAL:
      flag_value = self.region
    elif self.scope == e2e_test_base.EXPLICIT_GLOBAL:
      flag_value = ''
    return ManagedTestBase.GetScopeFlagForScopeTypeAndName(
        self.scope, flag_value, plural=plural)

  @staticmethod
  def GetScopeFlagForScopeTypeAndName(scope_type, scope_name, plural=False):
    if scope_type == e2e_test_base.ZONAL:
      scope_flag_name = 'zone'
    elif scope_type == e2e_test_base.REGIONAL:
      scope_flag_name = 'region'
    elif scope_type == e2e_test_base.EXPLICIT_GLOBAL:
      scope_flag_name = 'global'
    else:
      return ''
    if plural:
      scope_flag_name += 's'
    return '--' + scope_flag_name + ' ' + scope_name

  def CreateInstanceTemplate(self,
                             machine_type='n1-standard-1',
                             additional_disks=None):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    command = 'compute instance-templates create {0} --machine-type {1}'.format(
        name, machine_type)
    for additional_disk in additional_disks or []:
      command += (' --create-disk device-name={0},image-family={1},'
                  'image-project={2},auto-delete=yes').format(
                      additional_disk, self.DEFAULT_DISK_IMAGE_FAMILY,
                      self.DEFAULT_DISK_IMAGE_PROJECT)
    self.Run(command)
    self.instance_template_names.append(name)
    self.AssertNewOutputContains(name)
    return name

  def CreateTargetPool(self):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    self.Run('compute target-pools create {0} --region {1}'
             .format(name, e2e_test_base.REGION))
    self.target_pool_names.append(name)
    self.AssertNewOutputContains(name)
    return name

  def CreateInstanceGroupManager(
      self, instance_template_name, size=0, scope_flag=None):
    if scope_flag is None:
      scope_flag = self.GetScopeFlag()
    name = next(e2e_utils.GetResourceNameGenerator(prefix=self.prefix))
    if self.scope == e2e_test_base.ZONAL:
      self.instance_group_manager_names.append(name)
    elif self.scope == e2e_test_base.REGIONAL:
      self.region_instance_group_manager_names.append(name)

    self.Run('compute instance-groups managed create {0} '
             '{1} '
             '--base-instance-name {0} '
             '--size {2} '
             '--template {3}'
             .format(name, scope_flag, size, instance_template_name))
    self.AssertNewOutputContains(name)
    return name

  def CreateInstanceTemplateAndInstanceGroupManager(self, size=0):
    instance_template_name = self.CreateInstanceTemplate()
    return self.CreateInstanceGroupManager(instance_template_name, size)

  def DescribeManagedInstanceGroup(self, name):
    self.Run("""
      compute instance-groups managed describe {group_name} \
        {scope_flag}""".format(group_name=name, scope_flag=self.GetScopeFlag()))

  def GetInstanceUris(self, igm_name):
    self.ClearOutput()
    self.Run('compute instance-groups managed list-instances {0} '
             '--uri '
             '{1}'.format(igm_name, self.GetScopeFlag()))
    output = self.GetNewOutput()
    return re.findall(r'\S+', output)

  @staticmethod
  def ExtractInstanceNameFromUri(uri):
    return re.search(r'/instances/([^/]+)', uri).group(1)

  def WaitUntilStable(self, igm_name):
    self.Run('compute instance-groups managed wait-until --stable {0} '
             '--timeout 600 '
             '{1}'.format(igm_name, self.GetScopeFlag()))
    self.AssertNewErrNotContains('Timeout')

  def CleanUpStatefulDisks(self, stateful_disks):
    """Cleanup potential stateful disks, since they may have auto-delete set to false."""
    for disk_uri in stateful_disks:
      disk_name = self._ExtractDiskNameFromUri(disk_uri)
      disk_zone = self.ExtractZoneFromUri(disk_uri)
      if not disk_zone:
        raise ValueError(
            'Unsupported disk URI for cleanup: {0}'.format(disk_uri))
      self.CleanUpDisk(
          disk_name, scope=e2e_test_base.ZONAL, scope_name=disk_zone)

  def CleanUpDisk(self, name, scope=e2e_test_base.ZONAL, scope_name=None):
    """Attempt to clean up a disk, without signaling an error on failure."""
    scope_flag = self.scope_flag[scope]
    if scope_name:
      scope_flag = self.GetScopeFlagForScopeTypeAndName(scope, scope_name)
    try:
      self.Run('compute disks delete {0} {1} --quiet'.format(name, scope_flag))
    except exceptions.ToolException:
      pass

  @staticmethod
  def ExtractZoneFromUri(uri):
    return re.search(r'/zones/([^/]+)/', uri).group(1)

  @staticmethod
  def _ExtractDiskNameFromUri(uri):
    return re.search(r'/disks/([^/]+)', uri).group(1)


if __name__ == '__main__':
  e2e_test_base.main()
