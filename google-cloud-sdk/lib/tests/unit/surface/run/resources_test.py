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
"""Unit tests for resource parsing in the run command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.surface.run import base


class NoProjectResourcesTest(base.ServerlessSurfaceBase):

  def Project(self):
    return None

  def testNoProject(self):
    """Two services are listable using the Serverless API format."""
    with self.assertRaisesRegex(
        Exception,
        'Please specify the argument .?--project.? on the command line or '
        'set the property .?core/project.?.'):
      self.Run('run services list --region=us-central1')
