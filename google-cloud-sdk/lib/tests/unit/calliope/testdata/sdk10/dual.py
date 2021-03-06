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
"""This is a command for testing."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base


@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class DualCommand(calliope_base.Command):

  @staticmethod
  def Args(parser):
    parser.add_argument('--foo', help='Auxilio aliis.')

  def Run(self, args):
    print('This is the ALPHA track')
    print(args.foo)
