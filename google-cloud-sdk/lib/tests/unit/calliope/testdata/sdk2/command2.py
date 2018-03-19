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

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class BetaCommand2(base.Command):
  """Test empty DESCRIPTION followed by EXAMPLES.

  ## EXAMPLES

  Don't use this example as an example for writing examples.
  """

  def Run(self, args):
    return None


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Command2(base.Command):
  """A command with context and flags."""

  def Run(self, args):
    log.Print('we cool? '+str(args.coolstuff))

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--coolstuff',
        action='store_true',
        help=('is your stuff cool?'))