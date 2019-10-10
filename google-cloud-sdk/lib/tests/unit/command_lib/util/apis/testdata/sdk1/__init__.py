# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties


class Sdk1(calliope_base.Group):

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--project',
        metavar='PROJECT_ID',
        action=actions.StoreProperty(properties.VALUES.core.project),
        dest='project',
        help='Auxilio aliis.')
