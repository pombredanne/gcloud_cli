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
"""This is a command for testing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import log


class TestCommand(calliope_base.Command):
  """A command with context and flags."""

  def Run(self, args):
    log.Print('checking this runs.')

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--bool-flag',
        action='store_true',
        help=('is your flag a boolean?'))

    parser.add_argument(
        '--non-bool-flag',
        help=('does your flag have a value?'))
