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
"""A group for testing how well required/not-required arguments are handled."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base


class Lotsofargs(calliope_base.Group):
  """A group with required and optional flags."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('table(mid)')
    parser.display_info.AddAliases({'ALL': ['mid'], 'MID': ['Mid']})
    parser.add_argument('--group-required-test',
                        required=True,
                        help='Auxilio aliis.')
    parser.add_argument('--group-not-required-test',
                        default='9999',
                        help='Auxilio aliis.')
