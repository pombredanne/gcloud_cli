# -*- coding: utf-8 -*- #
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
"""The super-group for the cloud CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.calliope import base as calliope_base


class ExceptionAction(argparse.Action):

  def __init__(self, **kwargs):
    kwargs['nargs'] = 0
    super(ExceptionAction, self).__init__(**kwargs)

  def __call__(self, parser, namespace, values, option_string=None):
    raise Exception('Everything has gone wrong!')


class NewStyleGroup(calliope_base.Group):
  """Group short help.

  Group long help.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--action', action=ExceptionAction, help='Auxilio aliis.')

  def Filter(self, context, unused_args):
    context['newstyle'] = 'working'
