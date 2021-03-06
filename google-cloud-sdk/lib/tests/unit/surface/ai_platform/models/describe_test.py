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
"""ai-platform models describe tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import models
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
class DescribeTestBase(object):

  def testDescribe(self, module_name):
    self.Run('{} models describe myModel'.format(module_name))
    self.mocked.assert_called_once_with('myModel')
    self.AssertOutputContains('modelName')


class DescribeGaTest(DescribeTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    self.mocked = self.StartObjectPatch(
        models.ModelsClient, 'Get',
        return_value=self.short_msgs.Model(name='modelName'))


class DescribeBetaTest(DescribeTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    self.mocked = self.StartObjectPatch(
        models.ModelsClient, 'Get',
        return_value=self.short_msgs.Model(name='modelName'))


if __name__ == '__main__':
  test_case.main()
