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
"""Integration test for the 'data-fusion instances list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from tests.lib import test_case
from tests.lib.surface.data_fusion import base


class ListInstancesIntegrationTest(base.DatafusionE2ETestBase):
  """Integration test for the 'datafusion instances list' command.

  Datafusion gcloud e2e tests are run against a project with existing instances
  for reasons described in base.DatafusionE2ETestBase. Therefore, no
  instances are created before testing list.
  """

  def testListInstances(self):
    self.SetUp()
    test = self.Run(
        'data-fusion instances list --location=us-central1 --limit=2 '
        '--format=disable')
    instances = list(test)
    self.assertGreater(len(instances), 0)
    for instance in instances:
      # instance name follows correct pattern
      match = re.match(
          'projects/' + self.Project() + '/locations/us-central1/instances/'
          '([a-z][-0-9a-z]*[0-9a-z])', instance.name)
      self.assertTrue(bool(match))

if __name__ == '__main__':
  test_case.main()
