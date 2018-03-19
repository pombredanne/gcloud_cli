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
"""gcloud sdk tests command."""

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AplhaCommand(base.Command):
  """gcloud sdk tests command."""

  @staticmethod
  def Args(parser):
    """Adds args for this command."""

    # Exactly 2.
    parser.add_argument(
        'abc',
        metavar='DEF',
        nargs=2,
        help='abc the DEF.')

    # 0 or 1.
    parser.add_argument(
        'ghi',
        metavar='JKL',
        nargs='?',
        help='ghi the JKL.')