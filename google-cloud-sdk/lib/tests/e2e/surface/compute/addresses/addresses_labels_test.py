# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Integration tests for addresses labels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class AddressesLabelsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.address_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='gcloud-compute-test-address'))

  def RunCompute(self, *cmd):
    return self.Run(('compute',) + cmd)

  def CleanUpResource(self, subcommand, name, *args):
    try:
      cmd = (subcommand, 'delete', name, '--quiet') + args
      self.RunCompute(*cmd)
    except exceptions.ToolException:
      pass

  @contextlib.contextmanager
  def _Address(self, name, region):
    try:
      yield self.RunCompute('addresses', 'create', name, '--region', region)
    finally:
      self.CleanUpResource('addresses', name, '--region', region)

  def testAddresses(self):
    with self._Address(self.address_name, self.region):
      self._TestUpdateLabels()

  def _TestUpdateLabels(self):
    add_labels = (('x', 'y'), ('abc', 'xyz'))
    self.Run(
        'compute addresses update {0} --region {1} --update-labels {2}'
        .format(self.address_name, self.region, ','.join(
            ['{0}={1}'.format(pair[0], pair[1]) for pair in add_labels])))
    self.Run('compute addresses describe {0} --region {1}'
             .format(self.address_name, self.region))
    self.AssertNewOutputContains('abc: xyz\n  x: y')

    update_labels = (('x', 'a'), ('abc', 'xyz'), ('t123', 't7890'))
    remove_labels = ('abc',)
    self.Run("""
         compute addresses update {0} --region {1}
             --update-labels {2} --remove-labels {3}
        """.format(self.address_name, self.region, ','.join([
            '{0}={1}'.format(pair[0], pair[1]) for pair in update_labels
        ]), ','.join(['{0}'.format(k) for k in remove_labels])))

    self.Run('compute addresses describe {0} --region {1}'
             .format(self.address_name, self.region))
    self.AssertNewOutputContains('t123: t7890', reset=False)
    self.AssertNewOutputContains('x: a', reset=False)
    self.AssertNewOutputNotContains('abc: xyz')


if __name__ == '__main__':
  e2e_test_base.main()
