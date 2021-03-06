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
"""This is a command for testing grabbing the remainder args."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base


class SuppressedPositional(calliope_base.Command):
  """A command to test remainder args."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'suppressed',
        hidden=True,
        help='THIS TEXT SHOULD BE HIDDEN.')
    parser.add_argument(
        '--hidden-no-detailed-help',
        category=calliope_base.COMMONLY_USED_FLAGS,
        hidden=True,
        help='Short help.')
    parser.add_argument(
        '--hidden',
        category=calliope_base.COMMONLY_USED_FLAGS,
        hidden=True,
        help='Detailed help.')

  def Run(self, args):
    return args.suppressed

  def Display(self, args, result):
    print(str(result))
