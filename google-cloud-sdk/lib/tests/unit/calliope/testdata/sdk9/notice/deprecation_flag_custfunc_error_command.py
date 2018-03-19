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

"""This is a command for testing flag deprecation."""

from googlecloudsdk.calliope import actions as calliope_actions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class DeprecationFlagCustfuncErrorCommand(base.Command):
  """A simple command to test flag deprecation.

    Uses a custom function.

   {command} prints a test message.
  """

  @staticmethod
  def Args(parser):
    """Test args for this command."""
    def show_func(value):
      if value and value == 'foo':
        return True
      return False

    parser.add_argument(
        '--testflag',
        action=calliope_actions.DeprecationAction('testflag',
                                                  removed=True,
                                                  show_message=show_func),
        help='Test flag for testing.')

    parser.add_argument(
        '--otherflag',
        nargs='?',
        help='The Other Flag')
    parser.display_info.AddFormat('value(.)')

  def Run(self, args):
    log.status.Print('otherflag={0}'.format(args.otherflag))
    log.status.Print('testflag={0}'.format(args.testflag))
    return 'Deprecation Flag Custom Error Command Complete'