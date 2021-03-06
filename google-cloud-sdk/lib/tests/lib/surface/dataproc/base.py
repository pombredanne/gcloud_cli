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

"""Base for all Dataproc tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
import os
import sys

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import encoding
from tests.lib import cli_test_base


def _CreateLogger(name, log_level=None):
  """Create logger that does not interact with test_base.WithOutputCapture."""
  log = logging.getLogger(name)
  # sys.stderr is mocked by test_base.WithOutputCapture
  test_log_handler = logging.StreamHandler(sys.__stderr__)
  formatter = logging.Formatter(
      '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
  test_log_handler.setFormatter(formatter)
  log.addHandler(test_log_handler)
  # Prevent log from propagating into test case output.
  log.propagate = False
  if log_level:
    log.setLevel(log_level.upper())
  return log


class DataprocTestBase(cli_test_base.CliTestBase):
  """Base class for all Dataproc tests."""

  REGION = 'global'

  @classmethod
  def SetUpClass(cls):
    log_level = encoding.GetEncodedValue(os.environ,
                                         'CLOUDSDK_TEST_LOG_LEVEL', 'INFO')
    cls.log = _CreateLogger('dataproc-test', log_level)

  def SetUp(self):
    # Show captured output and error on debug and finer.
    if self.log.getEffectiveLevel() <= logging.DEBUG:
      self._show_test_output = True

  def RunDataproc(self, command, output_format='disable', set_region=True):
    """Wrapper around test_base.Run to abstract out common args."""
    region_prop = properties.VALUES.dataproc.region
    if set_region and not region_prop.IsExplicitlySet():
      region_prop.Set(self.REGION)
    cmd = '--format={format} dataproc {command}'.format(
        format=output_format, command=command)
    return self.Run(cmd)


class DataprocTestBaseAlpha(DataprocTestBase):
  """Base class for all Dataproc alpha tests."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class DataprocTestBaseBeta(DataprocTestBase):
  """Base class for all Dataproc beta tests."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class DataprocTestBaseGA(DataprocTestBase):
  """Base class for all Dataproc GA tests."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
