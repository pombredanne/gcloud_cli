# Copyright 2017 Google Inc. All Rights Reserved.
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
"""gcloud sdk tests command."""

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaCommand(base.Command):
  """gcloud sdk tests command."""

  @staticmethod
  def Args(parser):
    """Adds args for this command."""

    # 1 or more.
    parser.add_argument(
        'ghi',
        metavar='JKL',
        nargs='+',
        help='ghi the JKL.')