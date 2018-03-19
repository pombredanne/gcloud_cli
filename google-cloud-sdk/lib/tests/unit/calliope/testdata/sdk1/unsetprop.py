# Copyright 2015 Google Inc. All Rights Reserved.
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

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class Unsetprop(base.Command):

  def Run(self, args):
    return properties.VALUES.core.disable_prompts.Get(required=True)

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--coolstuff',
        action='store_true',
        help='is your stuff cool?')
    parser.add_argument(
        '--foo',
        action=actions.StoreProperty(properties.VALUES.core.disable_prompts),
        help='Auxilio aliis.')
