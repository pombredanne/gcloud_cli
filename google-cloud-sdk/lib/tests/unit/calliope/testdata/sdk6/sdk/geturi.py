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

"""Command with custom uri() transform."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers


class ListGoodAsyncWithGetUri(base.ListCommand):
  """List command with GetUriFunc."""

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat('table(good, async)')
    parser.display_info.AddUriFunc(lambda x, undefined='': 'URI({0})'.format(x))
    parser.display_info.AddCacheUpdater(completers.InstancesCompleter)

  def Run(self, args):
    if args.async and not args.IsSpecified('format'):
      args.format = 'table(good, operations)'
    return ['abc/def', 'xyz']
