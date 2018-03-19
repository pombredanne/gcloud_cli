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

"""Tests for coshell module."""

import os
import signal
import subprocess
import sys

from googlecloudsdk.command_lib.interactive import coshell
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case


def _GetOpenFds():
  """Returns the set of open fds."""
  fds = set()
  for fd in range(64):
    try:
      os.fstat(fd)
      fds.add(fd)
    except OSError:
      pass
  return fds


class _CoshellTestBase(sdk_test_base.SdkBase, test_case.WithContentAssertions):

  def SetUp(self):
    self.StartDictPatch(os.environ)
    if 'ENV' in os.environ:
      del os.environ['ENV']
    self.coshell = None
    self.tmp = self.CreateTempDir()
    self.output_file = os.path.join(self.tmp, 'coshell.out')
    self.error_file = os.path.join(self.tmp, 'coshell.err')
    self.CoOpen()

  def TearDown(self):
    self.CoClose()

  def CoOpen(self):
    if self.coshell:
      self.coshell.Close()

    sys.stdout.flush()
    sys.stderr.flush()

    old_out_fd = os.dup(1)
    new_out_fd = os.open(self.output_file, os.O_CREAT | os.O_WRONLY)
    os.dup2(new_out_fd, 1)
    os.close(new_out_fd)

    old_err_fd = os.dup(2)
    new_err_fd = os.open(self.error_file, os.O_CREAT | os.O_WRONLY)
    os.dup2(new_err_fd, 2)
    os.close(new_err_fd)

    self.coshell = coshell.Coshell()

    os.dup2(old_out_fd, 1)
    os.close(old_out_fd)

    os.dup2(old_err_fd, 2)
    os.close(old_err_fd)

  def CoClose(self):
    if self.coshell:
      self.coshell.Close()
      self.coshell = None

  def GetOutput(self):
    with open(self.output_file, 'r') as f:
      return f.read()

  def GetErr(self):
    with open(self.error_file, 'r') as f:
      return f.read()

  def AssertOutputEquals(self, expected, normalize_space=False):
    self._AssertEquals(expected, self.GetOutput(), 'output',
                       normalize_space=normalize_space)

  def AssertOutputContains(self, expected, normalize_space=False):
    self._AssertContains(expected, self.GetOutput(), 'output',
                         normalize_space=normalize_space)

  def AssertOutputMatches(self, expected, normalize_space=False):
    self._AssertMatches(expected, self.GetOutput(), 'output',
                        normalize_space=normalize_space)

  def AssertErrEquals(self, expected, normalize_space=False):
    self._AssertEquals(expected, self.GetErr(), 'error',
                       normalize_space=normalize_space)

  def AssertErrContains(self, expected, normalize_space=False):
    self._AssertContains(expected, self.GetErr(), 'error',
                         normalize_space=normalize_space)

  def AssertErrMatches(self, expected, normalize_space=False):
    self._AssertMatches(expected, self.GetErr(), 'error',
                        normalize_space=normalize_space)


@test_case.Filters.DoNotRunOnWindows  # UNIX specific tests.
@test_case.Filters.DoNotRunOnMac  # Config based output capture flakes?
@sdk_test_base.Filters.DoNotRunOnGCE  # Config based output capture flakes?
class UnixCoshellTest(_CoshellTestBase):

  def testUnixCoshellEditMode(self):
    self.assertEquals('emacs', self.coshell.edit_mode)
    self.coshell.Run('set -o vi')
    self.assertEquals('vi', self.coshell.edit_mode)
    self.coshell.Run('set -o emacs')
    self.assertEquals('emacs', self.coshell.edit_mode)

  def testUnixCoshellIgnoreEof(self):
    self.assertFalse(self.coshell.ignore_eof)
    self.coshell.Run('set -o ignoreeof')
    self.assertTrue(self.coshell.ignore_eof)
    self.coshell.Run('set +o ignoreeof')
    self.assertFalse(self.coshell.ignore_eof)

  def testUnixCoshellStateIsPreserved(self):
    self.assertTrue(self.coshell.state_is_preserved)

  def testUnixCoshellENV(self):
    os.environ['ENV'] = self.Touch(
        directory=self.tmp,
        name='coshell.env',
        contents='set -o vi\nset -o ignoreeof\n')
    self.CoOpen()
    self.assertEquals('vi', self.coshell.edit_mode)
    self.assertTrue(self.coshell.ignore_eof)

  def testUnixCoshellTrueStatus(self):
    status = self.coshell.Run('true')
    self.assertEquals(0, status)

  def testUnixCoshellFalseStatus(self):
    status = self.coshell.Run('false')
    self.assertEquals(1, status)

  def testUnixCoshellEcho(self):
    self.coshell.Run('echo foo')
    self.CoClose()
    self.AssertOutputEquals('foo\n')

  def testUnixCoshellPwdState(self):
    self.coshell.Run('cd /')
    self.coshell.Run('pwd')
    self.coshell.Run('cd /bin')
    self.coshell.Run('pwd')
    self.CoClose()
    self.AssertOutputEquals('/\n/bin\n')

  def testUnixCoshellVariableState(self):
    self.coshell.Run('echo original :$foo:')
    self.coshell.Run('foo=bar')
    self.coshell.Run('echo updated :$foo:')
    self.CoClose()
    self.AssertOutputEquals('original ::\nupdated :bar:\n')

  def testUnixCoshellVariableStateBackground(self):
    self.coshell.Run('echo original :$foo: &')
    self.coshell.Run('foo=bar')
    self.coshell.Run('echo updated :$foo: &')
    self.coshell.Run('wait')
    # Output order from the two background processes is not guaranteed.
    self.CoClose()
    self.AssertOutputContains('original ::\n')
    self.AssertOutputContains('updated :bar:\n')

  def testUnixCoshellCreateDelete(self):
    with files.TemporaryDirectory(change_to=True):
      self.CoOpen()
      tmp = 'coshell.tst'
      self.AssertFileNotExists(tmp)
      self.coshell.Run('echo foo > {}'.format(tmp))
      self.AssertFileExists(tmp)
      self.coshell.Run('rm {}'.format(tmp))
      self.AssertFileNotExists(tmp)

  def testUnixCoshellFdLeaks(self):
    self.CoClose()
    old_fds = _GetOpenFds()
    self.CoOpen()
    self.CoClose()
    new_fds = _GetOpenFds()
    self.assertEquals(set(), old_fds ^ new_fds)

  def testUnixCoshellJobsBackground(self):
    self.coshell.Run('sleep 1 && echo EXPIRED &')
    self.coshell.Run('jobs')
    self.coshell.Run('fg')
    self.coshell.Run('wait')
    self.CoClose()
    self.AssertOutputMatches(r'^\[1\]\+ Running sleep 1 && echo EXPIRED &$',
                             normalize_space=True)
    self.AssertOutputMatches(r'^sleep 1 && echo EXPIRED$',
                             normalize_space=True)
    self.AssertOutputMatches('^EXPIRED$', normalize_space=True)

  def testUnixCoshellInterrupt(self):
    self.coshell.Run('trap "echo INTERRUPTED" INT')
    self.coshell.Interrupt()
    # Must run some command here to avoid race between INTERRUPTED being printed
    # and checking the output file for INTERRUPTED.
    self.coshell.Run('wait')
    self.CoClose()
    self.AssertOutputMatches('^INTERRUPTED$', normalize_space=True)

  def testUnixCoshellExit(self):
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('exit')
    self.assertEquals(0, self.coshell.Close())

  def testUnixCoshellExit0(self):
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('exit 0')
    self.assertEquals(0, self.coshell.Close())

  @test_case.Filters.skip('rare annoying exit 0 flakes', 'b/65456434')
  def testUnixCoshellExit1(self):
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('exit 1')
    self.assertEquals(1, self.coshell.Close())

  def testUnixCoshellRunAfterExit(self):
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('exit')
      self.coshell.Run(':')
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('echo oops')
    self.assertEquals(0, self.coshell.Close())

  def testUnixCoshellRunAfterClose(self):
    self.assertEquals(0, self.coshell.Close())
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('echo oops')

  def testUnixCoshellDied(self):
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('kill -TERM $$')
    # 15 = index(SIGTERM); 271 = 256 + 15
    status = self.coshell.Close()
    # subprocess.Popen().returncode flakes to 0 in some test environments.
    if status:
      self.assertEquals(271, status)

  def testUnixCoshellSyntaxError(self):
    self.coshell.Run('echo "oops')
    self.coshell.Run('echo ok')
    self.assertEquals(0, self.coshell.Close())
    self.AssertOutputContains('ok\n')
    self.AssertErrContains('unexpected EOF while looking for matching')
    self.AssertErrContains('syntax error: unexpected end of file')

  def testUnixCoshellShellFdRedirections(self):
    self.CoClose()

    # Set up unrelated fds on SHELL_STATUS_FD and SHELL_STDIN_FD.

    shell_status_path = self.Touch(
        directory=self.tmp,
        name='coshell.status',
        contents='SHELL_STATUS_FD')
    try:
      old_shell_status_fd = os.dup(coshell._UnixCoshellBase.SHELL_STATUS_FD)
    except OSError:
      old_shell_status_fd = -1
    fd = os.open(shell_status_path, os.O_RDONLY)
    if fd != coshell._UnixCoshellBase.SHELL_STATUS_FD:
      os.dup2(fd, coshell._UnixCoshellBase.SHELL_STATUS_FD)
      os.close(fd)

    shell_stdin_path = self.Touch(
        directory=self.tmp,
        name='coshell.stdin',
        contents='SHELL_STDIN_FD')
    try:
      old_shell_stdin_fd = os.dup(coshell._UnixCoshellBase.SHELL_STDIN_FD)
    except OSError:
      old_shell_stdin_fd = -1
    fd = os.open(shell_stdin_path, os.O_RDONLY)
    if fd != coshell._UnixCoshellBase.SHELL_STDIN_FD:
      os.dup2(fd, coshell._UnixCoshellBase.SHELL_STDIN_FD)
      os.close(fd)

    # Open and close a coshell object.

    self.CoOpen()
    self.CoClose()

    # Make sure original SHELL_STATUS_FD and SHELL_STDIN_FD weren't clobbered.

    shell_status_contents = os.read(
        coshell._UnixCoshellBase.SHELL_STATUS_FD, 1024)
    self.assertEquals('SHELL_STATUS_FD', shell_status_contents)
    if old_shell_status_fd >= 0:
      os.dup2(old_shell_status_fd, coshell._UnixCoshellBase.SHELL_STATUS_FD)

    shell_stdin_contents = os.read(
        coshell._UnixCoshellBase.SHELL_STDIN_FD, 1024)
    self.assertEquals('SHELL_STDIN_FD', shell_stdin_contents)
    if old_shell_stdin_fd >= 0:
      os.dup2(old_shell_stdin_fd, coshell._UnixCoshellBase.SHELL_STDIN_FD)


@test_case.Filters.DoNotRunOnWindows  # UNIX specific tests.
@test_case.Filters.DoNotRunOnMac  # Config based output capture flakes?
@sdk_test_base.Filters.DoNotRunOnGCE  # Config based output capture flakes?
class UnixCoshellInteractiveTest(_CoshellTestBase):

  def _RawInput(self, prompt):
    if not self._input:
      raise EOFError('EOF')
    return self._input.pop(0)

  def _HandleInterrupt(self, signal_number=None, frame=None):
    """Handles keyboard interrupts (aka SIGINT, ^C)."""
    del signal_number, frame  # currently unused
    raise KeyboardInterrupt('Test harness interrupted.')

  def _InteractiveLoop(self):
    """A typical coshell interactive loop."""
    cosh = coshell.Coshell()
    prompt = '$ '

    try:
      old_handler = signal.signal(signal.SIGINT, self._HandleInterrupt)

      while True:

        try:
          command = self._RawInput(prompt)
        except EOFError:
          if not cosh.ignore_eof:
            break
          sys.stdout.write('\b' * len(prompt))
          continue
        except KeyboardInterrupt:
          sys.stdout.write('\n')
          continue

        if command == 'TEST-Interrupt':
          cosh.Interrupt()
          continue
        try:
          cosh.Run(command)
        except coshell.CoshellExitException:
          break

    finally:
      signal.signal(signal.SIGINT, old_handler)

    return cosh.Close()

  def Interactive(self, commands):
    self._input = commands
    self.CoClose()
    old_out_fd = os.dup(1)
    old_err_fd = os.dup(2)
    new_out_fd = os.open(self.output_file, os.O_CREAT | os.O_WRONLY)
    new_err_fd = os.open(self.error_file, os.O_CREAT | os.O_WRONLY)
    os.dup2(new_out_fd, 1)
    os.dup2(new_err_fd, 2)
    os.close(new_out_fd)
    os.close(new_err_fd)

    status = 127
    try:
      status = self._InteractiveLoop()
    finally:
      os.dup2(old_out_fd, 1)
      os.dup2(old_err_fd, 2)
      os.close(old_out_fd)
      os.close(old_err_fd)
    return status

  def testUnixCoshellInteractiveTrue(self):
    status = self.Interactive([
        'true',
    ])
    self.assertEquals(0, status)

  def testUnixCoshellInteractiveFalse(self):
    status = self.Interactive([
        'false',
    ])
    self.assertEquals(1, status)

  @test_case.Filters.skip('rare annoying exit 0 flakes', 'b/65456434')
  def testUnixCoshellInteractiveExit(self):
    status = self.Interactive([
        'exit 123',
    ])
    self.assertEquals(123, status)

  def testUnixCoshellInteractiveEcho(self):
    status = self.Interactive([
        'echo foo',
        'echo bar',
    ])
    self.assertEquals(0, status)
    self.AssertOutputEquals('foo\nbar\n')

  def testUnixCoshellInteractiveInterrupt(self):
    status = self.Interactive([
        'trap "echo INTERRUPTED" INT',
        'sleep 2 &',
        'TEST-Interrupt',
        'echo DONE',
    ])
    self.assertEquals(0, status)
    self.AssertOutputEquals('INTERRUPTED\nDONE\n')


@test_case.Filters.DoNotRunOnWindows  # UNIX specific tests.
@test_case.Filters.DoNotRunOnMac  # Config based output capture flakes?
@sdk_test_base.Filters.DoNotRunOnGCE  # Config based output capture flakes?
class MingWCoshellOnUnixTest(_CoshellTestBase):

  def _Popen(self):
    return subprocess.Popen(
        '/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE)

  def CoOpen(self):
    if self.coshell:
      self.coshell.Close()
    else:
      self.StartObjectPatch(
          coshell._MinGWCoshell, '_Popen', side_effect=self._Popen)

    sys.stdout.flush()
    sys.stderr.flush()

    old_out_fd = os.dup(1)
    new_out_fd = os.open(self.output_file, os.O_CREAT | os.O_WRONLY)
    os.dup2(new_out_fd, 1)
    os.close(new_out_fd)

    old_err_fd = os.dup(2)
    new_err_fd = os.open(self.error_file, os.O_CREAT | os.O_WRONLY)
    os.dup2(new_err_fd, 2)
    os.close(new_err_fd)

    self.coshell = coshell._MinGWCoshell()
    self.coshell.STDIN_PATH = '/dev/null'
    self.coshell.STDOUT_PATH = self.output_file

    os.dup2(old_out_fd, 1)
    os.close(old_out_fd)

    os.dup2(old_err_fd, 2)
    os.close(old_err_fd)

  def testMinGWCoshellEditMode(self):
    self.assertEquals('emacs', self.coshell.edit_mode)
    self.coshell.Run('set -o vi')
    self.assertEquals('vi', self.coshell.edit_mode)
    self.coshell.Run('set -o emacs')
    self.assertEquals('emacs', self.coshell.edit_mode)

  def testMinGWCoshellIgnoreEof(self):
    self.assertFalse(self.coshell.ignore_eof)
    self.coshell.Run('set -o ignoreeof')
    self.assertTrue(self.coshell.ignore_eof)
    self.coshell.Run('set +o ignoreeof')
    self.assertFalse(self.coshell.ignore_eof)

  def testMinGWCoshellStateIsPreserved(self):
    self.assertTrue(self.coshell.state_is_preserved)

  def testMinGWCoshellTrueStatus(self):
    status = self.coshell.Run('true')
    self.assertEquals(0, status)

  def testMinGWCoshellFalseStatus(self):
    status = self.coshell.Run('false')
    self.assertEquals(1, status)

  def testMinGWCoshellEcho(self):
    self.coshell.Run('echo foo')
    self.CoClose()
    self.AssertOutputEquals('foo\n')

  def testMinGWCoshellPwdState(self):
    self.coshell.Run('cd /')
    self.coshell.Run('pwd')
    self.coshell.Run('cd /bin')
    self.coshell.Run('pwd')
    self.CoClose()
    self.AssertOutputEquals('/\n/bin\n')

  def testMinGWCoshellVariableState(self):
    self.coshell.Run('echo original :$foo:')
    self.coshell.Run('foo=bar')
    self.coshell.Run('echo updated :$foo:')
    self.CoClose()
    self.AssertOutputEquals('original ::\nupdated :bar:\n')

  def testMinGWCoshellVariableStateBackground(self):
    self.coshell.Run('echo original :$foo: &')
    self.coshell.Run('foo=bar')
    self.coshell.Run('echo updated :$foo: &')
    self.coshell.Run('wait')
    # Output order from the two background processes is not guaranteed.
    self.CoClose()
    self.AssertOutputContains('original ::\n')
    self.AssertOutputContains('updated :bar:\n')

  @test_case.Filters.SkipInDebPackage('Flakes', 'b/67582029')
  @test_case.Filters.SkipInRpmPackage('Flakes', 'b/67582029')
  def testMinGWCoshellExit(self):
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('exit')
    self.assertEquals(0, self.coshell.Close())

  def testMinGWCoshellExit0(self):
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('exit 0')
    self.assertEquals(0, self.coshell.Close())

  def testMinGWCoshellExit1(self):
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('exit 1')
    # EPIPE before status can be retrieved.
    # self.assertEquals(1, self.coshell.Close())

  def testMinGWCoshellRunAfterExit(self):
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('exit')
      self.coshell.Run(':')
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('echo oops')
    self.assertEquals(0, self.coshell.Close())

  def testMinGWCoshellRunAfterClose(self):
    self.assertEquals(0, self.coshell.Close())
    with self.assertRaises(coshell.CoshellExitException):
      self.coshell.Run('echo oops')


class WindowsCoshellTest(_CoshellTestBase):
  """Funny that the Windows sepcific tests run everywhere."""

  def SetUp(self):
    # Mock the coshell module generic "is running on windows" test.
    self.StartObjectPatch(coshell, '_RunningOnWindows', return_value=True)
    # Un-memoize the initial implementation.
    coshell.Coshell._IMPLEMENTATION = None
    # This coshell.Open() will think its running on Windows.
    self.CoOpen()
    # True if its Windows cmd.exe coshell, MinGW bash otherwise.
    self.is_windows_cmd = isinstance(self.coshell, coshell._WindowsCoshell)
    if not self.is_windows_cmd:
      # /dev/tty doesn't work in the test environment.
      self.coshell.STDIN_PATH = '/dev/null'
      self.coshell.STDOUT_PATH = self.output_file

  def testWindowsCoshellUnixCoshellNotSelected(self):
    self.assertFalse(isinstance(self.coshell, coshell._UnixCoshell))

  def testWindowsCoshellEditMode(self):
    self.assertEquals('emacs', self.coshell.edit_mode)

  def testWindowsCoshellIgnoreEof(self):
    self.assertFalse(self.coshell.ignore_eof)

  def testWindowsCoshellStateIsPreserved(self):
    # If the test is running on a system with MinGW or git installed then bash
    # is available and preserves state across commands.
    self.assertEqual(not self.is_windows_cmd, self.coshell.state_is_preserved)

  def testWindowsCoshellCreateDelete(self):
    tmp = os.path.join(self.tmp, 'coshell.tst')
    self.AssertFileNotExists(tmp)
    self.coshell.Run("echo foo > '{}'".format(tmp))
    self.AssertFileExists(tmp)

  # No output tests yet because cmd.exe is entwined with the terminal and
  # we don't know how to intercept that.


if __name__ == '__main__':
  sdk_test_base.main()