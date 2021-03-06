# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Unit tests for the `run services delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.console import console_io
from tests.lib.surface.run import base


class DeleteTestBeta(base.ServerlessSurfaceBase):
  """Tests outputs of delete command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testDeleteSucceed(self):
    """Tests successful delete with default output format."""
    self.WriteInput('Y\n')
    self.operations.DeleteService.return_value = None
    self.Run('run services delete s1')
    self.operations.DeleteService.assert_called_once_with(
        self._ServiceRef('s1'))
    self.AssertErrContains('Deleted service [s1].')

  def testDeleteFailsIfUnattended(self):
    """Tests that delete fails if console is unattended."""
    self.is_interactive.return_value = False
    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run('run services delete s1')
    self.operations.DeleteService.assert_not_called()


class DeleteTestAlpha(DeleteTestBeta):
  """Tests outputs of delete command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
