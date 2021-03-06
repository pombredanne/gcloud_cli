# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Tests of the progress_tracker module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os
import signal
import time

from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

from six.moves import range  # pylint: disable=redefined-builtin


class ProgressTrackerTest(sdk_test_base.WithOutputCapture,
                          parameterized.TestCase):

  def SetUp(self):
    self._interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    self._interactive_mock.return_value = True
    self.console_size_mock = self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermSize')
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)

  def TearDown(self):
    # Wait for ProgressTracker ticker thread to end
    self.JoinAllThreads()

  def SetConsoleSize(self, size):
    self.console_size_mock.return_value = (size + 1, 'unused size')
    return size

  def testNoOp(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.OFF.name)
    with progress_tracker.ProgressTracker('tracker', autotick=False):
      pass
    self.AssertErrEquals('')

  def testStub(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    with progress_tracker.ProgressTracker('tracker', autotick=False):
      pass
    self.AssertErrEquals('{"ux": "PROGRESS_TRACKER", "message": "tracker", '
                         '"status": "SUCCESS"}\n')

  def testStubError(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    with self.assertRaises(ValueError):
      with progress_tracker.ProgressTracker('tracker', autotick=False):
        raise ValueError()
    self.AssertErrEquals('{"ux": "PROGRESS_TRACKER", "message": "tracker", '
                         '"status": "FAILURE"}\n')

  def testProgressTrackerDoesNotCrash(self):
    self.console_size_mock.return_value = (0, 'unused size')
    with progress_tracker.ProgressTracker('tracker', autotick=True):
      time.sleep(1)

  def testProgressTrackerZeroWidth(self):
    # To simulate pseudo-TTY
    self.console_size_mock.return_value = (0, 'unused size')
    with progress_tracker.ProgressTracker('tracker', autotick=False) as t:
      t.Tick()
      t.Tick()
    self.AssertErrEquals('')

  def testProgressTrackerTickEndExactSize(self):
    # 15: size of longest line not counting new line character
    console_size = self.SetConsoleSize(15)
    with progress_tracker.ProgressTracker('tracker', autotick=False) as t:
      t.Tick()
      t.Tick()
    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker.../'
        '\r' + ' ' * console_size +
        '\rtracker...-'
        '\r' + ' ' * console_size +
        '\rtracker...done.\n')

  def testProgressTrackerTickEndExactSizeWithBadSignal(self):
    def _BadSignal(sig, val):
      del sig, val
      raise ValueError('signal only works in the main thread')
    self.StartObjectPatch(signal, 'signal', side_effect=_BadSignal)
    # 15: size of longest line not counting new line character
    console_size = self.SetConsoleSize(15)
    with progress_tracker.ProgressTracker('tracker', autotick=False) as t:
      t.Tick()
      t.Tick()
    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker.../'
        '\r' + ' ' * console_size +
        '\rtracker...-'
        '\r' + ' ' * console_size +
        '\rtracker...done.\n')

  def testProgressTrackerTickConsoleWiderThanText(self):
    # 20: arbitrary size that is bigger than size of longest line
    console_size = self.SetConsoleSize(20)
    with progress_tracker.ProgressTracker('track', autotick=False) as t:
      t.Tick()
      t.Tick()
    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtrack...'
        '\r' + ' ' * console_size +
        '\rtrack.../'
        '\r' + ' ' * console_size +
        '\rtrack...-'
        '\r' + ' ' * console_size +
        '\rtrack...done.\n')

  def testProgressTrackerNoTty(self):
    # 20: arbitrary size that is bigger than size of longest line
    console_size = self.SetConsoleSize(20)
    self._interactive_mock.return_value = False
    with progress_tracker.ProgressTracker('tracker', autotick=False) as t:
      t.Tick()
      t.Tick()
    self.AssertErrNotContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker.../'
        '\r' + ' ' * console_size +
        '\rtracker...-'
        '\r' + ' ' * console_size +
        '\rtracker...done.\n')
    self.AssertErrEquals('tracker...\n..done.\n')

  def testProgressTrackerWithException(self):
    self.SetConsoleSize(30)
    with self.assertRaises(core_exceptions.Error):
      with progress_tracker.ProgressTracker('tracker', autotick=False) as t:
        t.Tick()
        t.Tick()
        raise core_exceptions.Error('some-error')
    self.AssertErrContains('...failed.\n')
    self.AssertErrNotContains('...done.\n')

  def testProgressTrackerWithDetailedMessageCallbackEndExactSize(self):
    # 22: size of longest line not counting new line character
    console_size = self.SetConsoleSize(22)
    msg = None
    with progress_tracker.ProgressTracker(
        'tracker', autotick=False,
        detail_message_callback=lambda: msg) as t:
      msg = 'msg'
      t.Tick()
    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker... msg.../'
        '\r' + ' ' * console_size +
        '\rtracker... msg...done.\n')

  def testProgressTrackerWithDetailedMessageCallbackWithError(self):
    # 30: arbitrary size that is bigger than size of longest line
    console_size = self.SetConsoleSize(30)
    msg = None
    with self.assertRaises(core_exceptions.Error):
      with progress_tracker.ProgressTracker(
          'tracker', autotick=False,
          detail_message_callback=lambda: msg) as t:
        msg = 'msg'
        t.Tick()
        raise core_exceptions.Error('some-error')
    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker... msg.../'
        '\r' + ' ' * console_size +
        '\rtracker... msg...failed.\n')
    self.AssertErrNotContains('...done.\n')

  def testProgressTrackerWithDetailedMessageCallbackSetToNoneWithError(self):
    # 30: arbitrary size that is bigger than size of longest line
    console_size = self.SetConsoleSize(30)
    msg = None
    with self.assertRaises(core_exceptions.Error):
      with progress_tracker.ProgressTracker(
          'tracker', autotick=False,
          detail_message_callback=lambda: msg) as t:
        msg = 'msg'
        t.Tick()
        msg = None
        raise core_exceptions.Error('some-error')
    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker... msg.../'
        '\r' + ' ' * console_size +
        '\rtracker...failed.\n')
    self.AssertErrNotContains('...done.\n')

  def testProgressTrackerWithShorterMessage(self):
    # 30: arbitrary size that is bigger than size of longest line
    console_size = self.SetConsoleSize(30)
    msg = None
    with progress_tracker.ProgressTracker(
        'tracker', autotick=False,
        detail_message_callback=lambda: msg) as t:
      msg = 'msg'
      t.Tick()
      msg = 'm'
    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker... msg.../'
        '\r' + ' ' * console_size +
        '\rtracker... m...done.\n')

  def testProgressTrackerMultiOnce(self):
    # 20: arbitrary size that will make a multiline display
    console_size = self.SetConsoleSize(20)
    msg = None
    with progress_tracker.ProgressTracker(
        'tracker', autotick=False,
        detail_message_callback=lambda: msg) as t:
      msg = 'this is a multiline display message'
      t.Tick()

    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker... this is a\n'
        ' multiline display m\n'
        'essage.../'
        '\r' + ' ' * console_size +
        '\ressage...done.\n')

  def testProgressTrackerSameMultiTwice(self):
    # 20: arbitrary size that will make a multiline display
    console_size = self.SetConsoleSize(20)
    msg = None
    with progress_tracker.ProgressTracker(
        'tracker', autotick=False,
        detail_message_callback=lambda: msg) as t:
      msg = 'this is a multiline display message'
      t.Tick()
      msg = 'this is a multiline display message'
      t.Tick()

    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker... this is a\n'
        ' multiline display m\n'
        'essage.../'
        '\r' + ' ' * console_size +
        '\ressage...-'
        '\r' + ' ' * console_size +
        '\ressage...done.\n')

  def testProgressTrackerSameMultiFour(self):
    # 20: arbitrary size that will make a multiline display
    console_size = self.SetConsoleSize(20)
    msg = None
    with progress_tracker.ProgressTracker(
        'tracker', autotick=False,
        detail_message_callback=lambda: msg) as t:
      msg = 'this is a multiline display message'
      t.Tick()
      msg = 'this is a multiline display message'
      t.Tick()
      msg = 'this is a multiline display message'
      t.Tick()
      msg = 'this is a multiline display message'
      t.Tick()
    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker... this is a\n'
        ' multiline display m\n'
        'essage.../'
        '\r' + ' ' * console_size +
        '\ressage...-'
        '\r' + ' ' * console_size +
        '\ressage...\\'
        '\r' + ' ' * console_size +
        '\ressage...|'
        '\r' + ' ' * console_size +
        '\ressage...done.\n')

  def testProgressTrackerDiffMultiThenShort(self):
    # 20: arbitrary size that will make a multiline displa
    console_size = self.SetConsoleSize(20)
    msg = None
    with progress_tracker.ProgressTracker(
        'tracker', autotick=False,
        detail_message_callback=lambda: msg) as t:
      msg = 'this is a multiline display message'
      t.Tick()
      msg = 'this is an another different multiline display message'
      t.Tick()
      msg = 'short'
      t.Tick()
    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...'
        '\r' + ' ' * console_size +
        '\rtracker... this is a\n'
        ' multiline display m\n'
        'essage.../'
        '\ntracker... this is a\n'
        'n another different \n'
        'multiline display me\n'
        'ssage...-'
        '\ntracker... short...\\'
        '\r' + ' ' * console_size +
        '\rtracker... short...d\n' +
        'one.\n')

  def testOutputDisabled(self):
    self.SetConsoleSize(20)
    log.SetUserOutputEnabled(False)
    with progress_tracker.ProgressTracker('tracker', autotick=True) as t:
      t.Tick()
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  @test_case.Filters.DoNotRunOnWindows
  def testCtrlCHandler(self):
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with self.assertRaisesRegex(console_io.OperationCancelledError,
                                'Aborted by user.'):
      with progress_tracker.ProgressTracker('tracker', autotick=False) as t:
        t.Tick()
        os.kill(os.getpid(), signal.SIGINT)
        t.Tick()
    self.AssertOutputEquals('')
    self.AssertErrContains('...aborted by ctrl-c.')

  @test_case.Filters.DoNotRunOnWindows
  def testCtrlCHandlerCustom(self):
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with self.assertRaisesRegex(console_io.OperationCancelledError,
                                'blah'):
      with progress_tracker.ProgressTracker('tracker', aborted_message='blah',
                                            autotick=False) as t:
        t.Tick()
        os.kill(os.getpid(), signal.SIGINT)
        t.Tick()
    self.AssertOutputEquals('')
    self.AssertErrContains('...aborted by ctrl-c.')

  @test_case.Filters.DoNotRunOnWindows
  def testCtrlCHandlerCustomStub(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with self.assertRaisesRegex(console_io.OperationCancelledError, 'blah'):
      with progress_tracker.ProgressTracker('tracker', aborted_message='blah',
                                            autotick=False) as t:
        t.Tick()
        os.kill(os.getpid(), signal.SIGINT)
        t.Tick()
    self.AssertOutputEquals('')
    self.AssertErrContains('{"ux": "PROGRESS_TRACKER", "message": "tracker",'
                           ' "status": "INTERRUPTED"}\n')

  @test_case.Filters.DoNotRunOnWindows
  def testUnInterruptable(self):
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with progress_tracker.ProgressTracker('tracker', interruptable=False,
                                          autotick=False) as t:
      t.Tick()
      os.kill(os.getpid(), signal.SIGINT)
      t.Tick()
    self.AssertOutputEquals('')
    self.AssertErrContains('...done.')
    self.AssertErrContains('This operation cannot be cancelled')

  @test_case.Filters.DoNotRunOnWindows
  def testUnInterruptableStub(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with progress_tracker.ProgressTracker('tracker', interruptable=False,
                                          autotick=False) as t:
      t.Tick()
      os.kill(os.getpid(), signal.SIGINT)
      t.Tick()
    self.AssertOutputEquals('')
    self.AssertErrEquals('{"ux": "PROGRESS_TRACKER", "message": "tracker", '
                         '"status": "SUCCESS"}\n')

  @parameterized.named_parameters(
      ('Utf8', 'utf-8', ['⠏', '⠛', '⠹', '⠼', '⠶', '⠧']),
      ('Cp437', 'cp437', ['|', '/', '-', '\\']),  # windows
      ('Ascii', 'ascii', ['|', '/', '-', '\\']))
  def testProgressTrackerSpinnersByEncoding(self, encoding, spinners):
    self.SetConsoleSize(30)
    self.SetEncoding(encoding)
    with progress_tracker.ProgressTracker('tracker', autotick=False) as t:
      for _ in range(len(spinners)):
        t.Tick()
    for tick_mark in spinners:
      self.AssertErrContains('\rtracker...' + tick_mark)

  def testProgressTrackerNonInteractivePseudoTty(self):
    # This actually sets it to 0. This size is incremented due to legacy
    # reasons.
    self.SetConsoleSize(-1)
    self._interactive_mock.return_value = False
    with progress_tracker.ProgressTracker('tracker', autotick=False) as t:
      t.Tick()
      t.Tick()
    self.AssertErrEquals('')

  def testProgressTrackerScreenReader(self):
    console_size = self.SetConsoleSize(30)
    with progress_tracker.ProgressTracker(
        'tracker', autotick=False, screen_reader=True) as t:
      for _ in range(5):
        t.Tick()
    self.AssertErrContains(
        '\r' + ' ' * console_size +
        '\rtracker...working.'
        '\r' + ' ' * console_size +
        '\rtracker...working..'
        '\r' + ' ' * console_size +
        '\rtracker...working...'
        '\r' + ' ' * console_size +
        '\rtracker...working'
        '\r' + ' ' * console_size +
        '\rtracker...working.'
        '\r' + ' ' * console_size +
        '\rtracker...done.\n')


# TODO(b/125840199) Add tab completion support on windows.
@test_case.Filters.DoNotRunOnWindows('Tab completion not supported on Windows.')
class CompletionProgressTrackerTest(sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)

  def testNoOp(self):
    for style in (properties.VALUES.core.InteractiveUXStyles.OFF.name,
                  properties.VALUES.core.InteractiveUXStyles.TESTING.name):
      properties.VALUES.core.interactive_ux_style.Set(style)
      ofile = io.StringIO()
      with progress_tracker.CompletionProgressTracker('tracker', autotick=True):
        pass
      actual = ofile.getvalue()
      ofile.close()
      self.assertEqual('', actual)

  def testSpinnerToStream(self):
    ofile = io.StringIO()
    with progress_tracker.CompletionProgressTracker(ofile, autotick=True) as t:
      for _ in range(0, 5):
        t._Spin()
    actual = ofile.getvalue()
    ofile.close()
    self.assertFalse(t._TimedOut())
    self.assertEqual('/\b-\b\\\b|\b/\b \b', actual)

  def testNoTimeout(self):
    # return_value=0 exercises the background code.
    self.StartObjectPatch(os, 'fork', return_value=0)
    ofile = io.StringIO()
    with progress_tracker.CompletionProgressTracker(
        ofile, autotick=True, timeout=0.4, tick_delay=0.1,
        background_ttl=0.1) as t:
      # Spin a bit but not enough to time out.
      for _ in range(0, 3):
        t._Spin()  # Bypass signal.setitimer() in unit tests.
    actual = ofile.getvalue()
    ofile.close()
    self.assertEqual('/\b-\b\\\b \b', actual)

  def testTimedOut(self):
    # return_value=0 exercises the background code.
    self.StartObjectPatch(os, 'fork', return_value=0)
    ofile = io.StringIO()
    with progress_tracker.CompletionProgressTracker(
        ofile, autotick=True, timeout=0.4, tick_delay=0.1,
        background_ttl=0.1) as t:
      # Spin enough to time out.
      for _ in range(0, 6):
        t._Spin()  # Bypass signal.setitimer() in unit tests.
    actual = ofile.getvalue()
    ofile.close()
    self.assertEqual('/\b-\b\\\b|\b/\b?\b', actual)


# TODO(b/125840199) Add tab completion support on windows.
@test_case.Filters.DoNotRunOnWindows('Tab completion not supported on Windows.')
@test_case.Filters.DoNotRunOnMac('b/147804852')
class CompletionProgressTrackerFdTest(sdk_test_base.SdkBase):

  def SetUp(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)
    # The argparse/argcomplete contract includes a fixed file descriptor number
    # progress_tracker.CompletionProgressTracker._COMPLETION_FD.  Completion
    # progress tracker output is writtent to this fd.  During testing this fd
    # may already be in use, so we save it to another fd at the start of each
    # test if it is in use and restore it at the end of each test.
    self.completion_file = self.Touch(self.temp_path, name='test.txt')
    self.completion_fd = (
        progress_tracker._NormalCompletionProgressTracker._COMPLETION_FD)
    try:
      # completion_fd is in use -- save it until TearDown and close it so the
      # it will be available to the first open() in the test
      self.original_completion_fd = os.dup(self.completion_fd)
      os.close(self.completion_fd)
    except OSError:
      # completion_fd is not in use
      self.original_completion_fd = None

  def OpenCompletionFile(self, mode):
    f = open(self.completion_file, mode)
    fd = f.fileno()
    if fd != self.completion_fd:
      # the completion fd is not where we want it -- dup it
      os.dup2(fd, self.completion_fd)
      # - don't close fd here because subsequent f.close() needs it
      # - it's OK to have both file descriptors open
      # - read/writes to either descriptor go to the same underlying file
    return f

  def TearDown(self):
    if self.original_completion_fd is None:
      # completion_fd not in use by tests -- close it if it was opened/duped
      try:
        os.close(self.completion_fd)
      except OSError:
        pass
    else:
      # completion_fd in use by tests -- restore it
      os.dup2(self.original_completion_fd, self.completion_fd)
      os.close(self.original_completion_fd)

  def testSpinnerToFile(self):
    with self.OpenCompletionFile('w'):
      with progress_tracker.CompletionProgressTracker(autotick=True) as t:
        for _ in range(0, 5):
          t._Spin()
        with self.OpenCompletionFile('r') as r:
          preliminary = r.read()
    self.assertFalse(t._TimedOut())
    self.assertEqual('/\b-\b\\\b|\b/\b', preliminary)
    with self.OpenCompletionFile('r') as r:
      final = r.read()
    self.assertEqual('/\b-\b\\\b|\b/\b \b', final)

  def testGetStream(self):
    expected = 'This is the completion progress tracker stream.\n'
    with self.OpenCompletionFile('w') as f:
      with progress_tracker._NormalCompletionProgressTracker._GetStream() as s:
        s.write(expected)
    with self.OpenCompletionFile('r') as f:
      actual = f.read()
    self.assertEqual(expected, actual)


class StagedProgressTrackerTest(sdk_test_base.WithOutputCapture,
                                parameterized.TestCase):

  def SetUp(self):
    self._interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    self._interactive_mock.return_value = True
    self.console_size_mock = self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermSize')
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)
    self.stages = [
        progress_tracker.Stage('Hello World...', key='a'),
        progress_tracker.Stage('A' + 'h' * 15 + '...', key='b')]
    self.keys = [s.key for s in self.stages]

  def TearDown(self):
    # Wait for ProgressTracker ticker thread to end
    self.JoinAllThreads()

  def SetConsoleSize(self, size):
    self.console_size_mock.return_value = (size, 'unused size')
    return size

  def testNoOp(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.OFF.name)
    with progress_tracker.StagedProgressTracker(
        'tracker', self.stages, autotick=False):
      pass
    self.AssertErrEquals('')

  def testMapNature(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.OFF.name)
    with progress_tracker.StagedProgressTracker(
        'tracker', self.stages, autotick=False) as tracker:
      self.assertEqual(tracker[self.keys[0]], self.stages[0])
      self.assertEqual(list(tracker.keys()), self.keys)
    self.AssertErrEquals('')

  def testStubNoStages(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    with progress_tracker.StagedProgressTracker(
        'tracker', self.stages, autotick=False):
      pass
    self.AssertErrEquals('{"ux": "STAGED_PROGRESS_TRACKER", "message": '
                         '"tracker", "status": "SUCCESS"}\n')

  def testStub(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    with progress_tracker.StagedProgressTracker(
        'tracker', self.stages, autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.CompleteStage(self.keys[0])
    self.AssertErrEquals(
        '{"ux": "STAGED_PROGRESS_TRACKER", "message": "tracker", "status": '
        '"SUCCESS", "succeeded_stages": ["Hello World..."]}\n')

  def testStubFailedStage(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    with self.assertRaises(ValueError):
      with progress_tracker.StagedProgressTracker(
          'tracker', self.stages, autotick=False) as spt:
        spt.StartStage(self.keys[0])
        spt.StartStage(self.keys[1])
        spt.CompleteStage(self.keys[1])
        spt.FailStage(self.keys[0], ValueError())
    self.AssertErrEquals(
        '{"ux": "STAGED_PROGRESS_TRACKER", "message": "tracker", "status": '
        '"FAILURE", "succeeded_stages": ["Ahhhhhhhhhhhhhhh..."], '
        '"failed_stage": "Hello World..."}\n')

  def testStubCompletedWithWarningStage(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    with progress_tracker.StagedProgressTracker(
        'tracker', self.stages, autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.StartStage(self.keys[1])
      spt.CompleteStageWithWarning(self.keys[0], 'Nooooooo')
      spt.CompleteStage(self.keys[1])
    self.AssertErrEquals(
        '{"ux": "STAGED_PROGRESS_TRACKER", "message": "tracker", '
        '"status": "WARNING", "succeeded_stages": ["Ahhhhhhhhhhhhhhh..."]}\n')

  def testStubUncaughtError(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    with self.assertRaises(ValueError):
      with progress_tracker.StagedProgressTracker(
          'tracker', self.stages, autotick=False) as spt:
        spt.StartStage(self.keys[0])
        spt.CompleteStage(self.keys[0])
        raise ValueError()
    self.AssertErrEquals('{"ux": "STAGED_PROGRESS_TRACKER", "message": '
                         '"tracker", "status": "FAILURE", "succeeded_stages": '
                         '["Hello World..."]}\n')

  def testProgressTrackerDoesNotCrash(self):
    self.console_size_mock.return_value = (0, 'unused size')
    with progress_tracker.StagedProgressTracker(
        'tracker', self.stages, autotick=False):
      time.sleep(1)

  def testProgressTrackerZeroWidth(self):
    # To simulate pseudo-TTY
    self.console_size_mock.return_value = (0, 'unused size')
    with progress_tracker.StagedProgressTracker(
        'tracker', self.stages, autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.CompleteStage(self.keys[0])
      spt.Tick()
      spt.Tick()
    self.AssertErrEquals('')

  @parameterized.parameters(
      (1, 0, 0), (0, 1, 0), (0, 0, 1))
  def testProgressTrackerStageDoesNotBelong(self, start_stage, update_stage,
                                            complete_stage):
    self.console_size_mock.return_value = (0, 'unused size')
    with self.assertRaisesRegex(
        ValueError, 'This stage does not belong to this progress tracker.'):
      with progress_tracker.StagedProgressTracker(
          'tracker', [self.stages[0]], autotick=False) as spt:
        spt.StartStage(self.keys[start_stage])
        spt.UpdateStage(self.keys[update_stage], 'new message')
        spt.CompleteStage(self.keys[complete_stage])

  def testProgressTrackerUpdatingCompletedStage(self):
    self.console_size_mock.return_value = (0, 'unused size')
    with self.assertRaisesRegex(
        ValueError, 'This stage has already completed.'):
      with progress_tracker.StagedProgressTracker(
          'tracker', self.stages, autotick=False) as spt:
        spt.StartStage(self.keys[0])
        spt.CompleteStage(self.keys[0])
        spt.StartStage(self.keys[0])

  def testProgressTrackerNonInteractive(self):
    self._interactive_mock.return_value = False
    self.SetConsoleSize(30)
    with progress_tracker.StagedProgressTracker(
        'tracker',
        self.stages,
        success_message='Goodbye.',
        autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.Tick()
      self.AssertErrEquals(
          'tracker\n'
          'Hello World.....')
      spt.CompleteStage(self.keys[0])
    self.AssertErrEquals(
        'tracker\n'
        'Hello World.....done\n'
        'Goodbye.\n')

  def testProgressTrackerNonInteractiveFailedStage(self):
    self._interactive_mock.return_value = False
    self.SetConsoleSize(30)
    with self.assertRaises(ValueError):
      with progress_tracker.StagedProgressTracker(
          'tracker',
          self.stages,
          failure_message='Badbye.',
          autotick=False) as spt:
        spt.StartStage(self.keys[0])
        spt.StartStage(self.keys[1])
        spt.Tick()
        self.AssertErrEquals(
            'tracker\n'
            'Hello World......')
        error = ValueError('an error')
        spt.FailStage(self.keys[0], error)
    self.AssertErrEquals(
        'tracker\n'
        'Hello World......failed\n'
        'Ahhhhhhhhhhhhhhh...interrupted\n'
        'Badbye.\n')

  def testProgressTrackerNonInteractiveUncaughtError(self):
    self._interactive_mock.return_value = False
    self.SetConsoleSize(30)
    with self.assertRaises(ValueError):
      with progress_tracker.StagedProgressTracker(
          'tracker',
          self.stages,
          failure_message='Badbye.',
          autotick=False) as spt:
        spt.StartStage(self.keys[0])
        spt.StartStage(self.keys[1])
        spt.Tick()
        self.AssertErrEquals(
            'tracker\n'
            'Hello World......')
        raise ValueError('an error')
    self.AssertErrEquals(
        'tracker\n'
        'Hello World......failed\n'
        'Badbye.\n')

  def testProgressTracker(self):
    clear_width = self.SetConsoleSize(30) - 1
    with progress_tracker.StagedProgressTracker(
        'tracker',
        self.stages,
        success_message='Goodbye.',
        autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.Tick()
      self.AssertErrContains(
          '\r' + ' ' * clear_width + '\r'
          'tracker'
          '\r' + ' ' * clear_width + '\r'
          'tracker\n'
          '\r' + ' ' * clear_width + '\r'
          '  Hello World.../')
      spt.CompleteStage(self.keys[0])
    self.AssertErrEquals(
        '\r' + ' ' * clear_width + '\r'
        'tracker'
        '\r' + ' ' * clear_width + '\r'
        'tracker\n'
        '\r' + ' ' * clear_width + '\r'
        '  Hello World.../'
        '\r' + ' ' * clear_width + '\r'
        '  Hello World...-'
        '\r' + ' ' * clear_width + '\r'
        '  Hello World...done'
        '\r' + ' ' * clear_width + '\r'
        '  Hello World...done\n'
        '\r' + ' ' * clear_width + '\r'
        'Goodbye.\n')

  def testProgressTrackerLatterStageCompletedFirst(self):
    self.SetConsoleSize(30)
    with progress_tracker.StagedProgressTracker(
        'tracker',
        self.stages,
        success_message='Goodbye.',
        autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.StartStage(self.keys[1])
      spt.CompleteStage(self.keys[1])
      spt.Tick()
      self.AssertErrContains('tracker\n')
      self.AssertErrContains('  Hello World.../')
      self.AssertErrNotContains(self.stages[1].header)
      spt.CompleteStage(self.keys[0])
    self.AssertErrContains('tracker\n')
    self.AssertErrContains('  Hello World...done\n')
    self.AssertErrContains('  Ahhhhhhhhhhhhhhh...done\n')
    self.AssertErrContains('Goodbye.\n')

  def testProgressTrackerFailedStage(self):
    self.SetConsoleSize(30)
    with self.assertRaises(ValueError):
      with progress_tracker.StagedProgressTracker(
          'tracker',
          self.stages,
          failure_message='Badbye.',
          autotick=False) as spt:
        spt.StartStage(self.keys[0])
        spt.StartStage(self.keys[1])
        spt.Tick()
        self.AssertErrContains('tracker\n')
        self.AssertErrContains('  Hello World.../')
        error = ValueError('an error')
        spt.FailStage(self.keys[0], error)
    self.AssertErrContains('  Hello World...failed\n')
    self.AssertErrContains('  Ahhhhhhhhhhhhhhh...interrup\n')
    self.AssertErrContains('  ted\n')
    self.AssertErrContains('Badbye.\n')

  def testProgressTrackerUncaughtError(self):
    self.SetConsoleSize(30)
    with self.assertRaises(ValueError):
      with progress_tracker.StagedProgressTracker(
          'tracker',
          self.stages,
          failure_message='Badbye.',
          autotick=False) as spt:
        spt.StartStage(self.keys[0])
        spt.StartStage(self.keys[1])
        spt.Tick()
        self.AssertErrContains('tracker\n')
        self.AssertErrContains('  Hello World.../')
        raise ValueError('an error')
    self.AssertErrContains('  Hello World...failed\n')
    self.AssertErrContains('Badbye.\n')

  @parameterized.parameters(True, False)
  def testProgressTrackerDoneMessageCallback(self, interactive):
    self._interactive_mock.return_value = interactive
    self.SetConsoleSize(30)
    msg = ''
    done_message_callback = lambda: msg
    with progress_tracker.StagedProgressTracker(
        'tracker',
        self.stages,
        done_message_callback=done_message_callback,
        autotick=False):
      msg = 'For more information...'
    self.AssertErrContains('Done. For more information...\n')

  @test_case.Filters.DoNotRunOnWindows
  def testCtrlCHandler(self):
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with self.assertRaisesRegex(console_io.OperationCancelledError,
                                'Aborted by user.'):
      with progress_tracker.StagedProgressTracker(
          'tracker', self.stages, autotick=False) as spt:
        spt.Tick()
        os.kill(os.getpid(), signal.SIGINT)
        spt.Tick()
    self.AssertOutputEquals('')
    self.AssertErrContains('aborted by ctrl-c')

  @test_case.Filters.DoNotRunOnWindows
  def testCtrlCHandlerCustom(self):
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with self.assertRaisesRegex(console_io.OperationCancelledError,
                                'blah'):
      with progress_tracker.StagedProgressTracker(
          'tracker', self.stages, aborted_message='blah', autotick=False) as t:
        t.Tick()
        os.kill(os.getpid(), signal.SIGINT)
        t.Tick()
    self.AssertOutputEquals('')
    self.AssertErrContains('aborted by ctrl-c')

  @test_case.Filters.DoNotRunOnWindows
  def testCtrlCHandlerCustomStub(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with self.assertRaisesRegex(console_io.OperationCancelledError, 'blah'):

      with progress_tracker.StagedProgressTracker(
          'tracker', self.stages, aborted_message='blah', autotick=False) as t:
        t.StartStage(self.keys[0])
        t.CompleteStage(self.keys[0])
        t.Tick()
        os.kill(os.getpid(), signal.SIGINT)
        t.Tick()
    self.AssertOutputEquals('')
    self.AssertErrContains('{"ux": "STAGED_PROGRESS_TRACKER", "message": '
                           '"tracker", "status": "INTERRUPTED", '
                           '"succeeded_stages": ["Hello World..."]}\n')

  @test_case.Filters.DoNotRunOnWindows
  def testUnInterruptable(self):
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.

    with progress_tracker.StagedProgressTracker(
        'tracker', self.stages, autotick=False, interruptable=False) as spt:
      spt.StartStage(self.keys[0])
      spt.CompleteStage(self.keys[0])
      spt.Tick()
      os.kill(os.getpid(), signal.SIGINT)
      spt.Tick()
    self.AssertOutputEquals('')
    self.AssertErrContains('  Hello World...done\n')
    self.AssertErrContains('This operation cannot be cancelled')

  @test_case.Filters.DoNotRunOnWindows
  def testUnInterruptableStub(self):
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.TESTING.name)
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with progress_tracker.StagedProgressTracker(
        'tracker', self.stages, autotick=False, interruptable=False) as spt:
      spt.StartStage(self.keys[0])
      spt.CompleteStage(self.keys[0])
      spt.Tick()
      os.kill(os.getpid(), signal.SIGINT)
      spt.Tick()
    self.AssertOutputEquals('')
    self.AssertErrEquals('{"ux": "STAGED_PROGRESS_TRACKER", "message": '
                         '"tracker", "status": "SUCCESS", "succeeded_stages": '
                         '["Hello World..."]}\n')

  @parameterized.named_parameters(
      ('Utf8', 'utf-8', ['⠏', '⠛', '⠹', '⠼', '⠶', '⠧']),
      ('Cp437', 'cp437', ['|', '/', '-', '\\']),  # windows
      ('Ascii', 'ascii', ['|', '/', '-', '\\']))
  def testProgressTrackerSpinnersByEncoding(self, encoding, spinners):
    self.SetConsoleSize(30)
    self.SetEncoding(encoding)
    with progress_tracker.StagedProgressTracker(
        'tracker', self.stages, autotick=False) as spt:
      spt.StartStage(self.keys[0])
      for _ in range(len(spinners)):
        spt.Tick()
    for tick_mark in spinners:
      self.AssertErrContains('  Hello World...' + tick_mark)


class MultilineStagedProgressTrackerTest(sdk_test_base.WithOutputCapture,
                                         parameterized.TestCase):

  def SetUp(self):
    self._interactive_mock = self.StartObjectPatch(console_io, 'IsInteractive')
    self._interactive_mock.return_value = True
    self.console_size_mock = self.StartObjectPatch(
        console_attr.ConsoleAttr, 'GetTermSize')
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)
    self.stages = [
        progress_tracker.Stage('Hello World...'),
        progress_tracker.Stage('A' + 'h' * 15 + '...')]
    self.keys = [s.key for s in self.stages]

  def TearDown(self):
    # Wait for ProgressTracker ticker thread to end
    self.JoinAllThreads()

  def _GetMultilineStagedProgressTracker(self, header, stages, autotick=False,
                                         interruptable=True):
    return progress_tracker._MultilineStagedProgressTracker(
        header, stages, None, None, None, False, 0.1, interruptable,
        console_io.OperationCancelledError.DEFAULT_MESSAGE, None, None)

  def SetConsoleSize(self, size):
    self.console_size_mock.return_value = (size, 'unused size')
    return size

  def AssertErrContainsLines(self, *lines):
    for line in lines:
      self.AssertErrContains(line)

  def testPseudoTty(self):
    self.SetConsoleSize(0)
    with self._GetMultilineStagedProgressTracker(
        'tracker', self.stages, autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.CompleteStage(self.keys[0])
      spt.Tick()
      spt.Tick()
    self.AssertErrEquals('')

  def testCompleted(self):
    self.SetConsoleSize(30)
    with self._GetMultilineStagedProgressTracker(
        'tracker', self.stages, autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.CompleteStage(self.keys[0])
      spt.StartStage(self.keys[1])
      spt.CompleteStage(self.keys[1])
      spt.Tick()
    self.AssertErrContainsLines(
        'OK tracker\n',
        '  OK Hello World...\n',
        '  OK Ahhhhhhhhhhhhhhh...\n',
        'Done.\n')

  def testStageFailed(self):
    self.SetConsoleSize(30)
    with self.assertRaises(ValueError):
      with self._GetMultilineStagedProgressTracker(
          'tracker', self.stages, autotick=False) as spt:
        spt.StartStage(self.keys[0])
        spt.StartStage(self.keys[1])
        spt.FailStage(self.keys[1], ValueError('Oh no!'), 'I failed.')
        spt.Tick()
    self.AssertErrContainsLines(
        'X  tracker\n',
        '  -  Hello World...\n',
        '  X  Ahhhhhhhhhhhhhhh... I fa\n',
        '  iled.\n',
        'Failed.\n')

  def testUpdateStage(self):
    self.SetConsoleSize(30)
    with self._GetMultilineStagedProgressTracker(
        'tracker', self.stages, autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.CompleteStage(self.keys[0])
      spt.StartStage(self.keys[1])
      spt.Tick()
      spt.UpdateStage(self.keys[1], 'whoops')
      spt.CompleteStage(self.keys[1])
    self.AssertErrContainsLines(
        # Before Update (don't test the spinner)
        '  Ahhhhhhhhhhhhhhh...\n',
        # Final result
        'OK tracker\n',
        '  OK Hello World...\n',
        '  OK Ahhhhhhhhhhhhhhh... whoo\n',
        '  ps\n',
        'Done.\n')

  def testUpdateHeader(self):
    self.SetConsoleSize(30)
    with self._GetMultilineStagedProgressTracker(
        'tracker', self.stages, autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.CompleteStage(self.keys[0])
      spt.StartStage(self.keys[1])
      spt.UpdateStage(self.keys[1], 'whoops')
      spt.CompleteStage(self.keys[1])
      spt.Tick()
      spt.UpdateHeaderMessage('details')
      spt.Tick()
    self.AssertErrContainsLines(
        '/  tracker\n',
        # Final result
        'OK tracker details\n',
        '  OK Hello World...\n',
        '  OK Ahhhhhhhhhhhhhhh... whoo\n',
        '  ps\n',
        'Done.\n')

  def testUncaughtException(self):
    self.SetConsoleSize(30)
    with self.assertRaises(ValueError):
      with self._GetMultilineStagedProgressTracker(
          'tracker', self.stages, autotick=False) as spt:
        spt.StartStage(self.keys[0])
        spt.CompleteStage(self.keys[0])
        spt.StartStage(self.keys[1])
        spt.Tick()
        raise ValueError()
    self.AssertErrContainsLines(
        'X  tracker\n',
        '  OK Hello World...\n',
        '  -  Ahhhhhhhhhhhhhhh...\n',
        'Failed.\n')

  @parameterized.named_parameters(
      ('Utf8', 'utf-8', ['⠏', '⠛', '⠹', '⠼', '⠶', '⠧'], 1, '✓ '),
      ('Cp437', 'cp437', ['|', '/', '-', '\\'], 2, 'OK '),  # windows
      ('Ascii', 'ascii', ['|', '/', '-', '\\'], 2, 'OK '))
  def testProgressTrackerSpinnersByEncoding(self, encoding, spinners,
                                            spaces, success_mark):
    self.SetConsoleSize(30)
    self.SetEncoding(encoding)
    with self._GetMultilineStagedProgressTracker(
        'tracker', self.stages, autotick=False) as spt:
      spt.StartStage(self.keys[0])
      for _ in range(len(spinners)):
        spt.Tick()
      spt.CompleteStage(self.keys[0])
    for tick_mark in spinners:
      # Header ticks
      self.AssertErrContains(tick_mark + ' ' * spaces + 'tracker\n')
      # Stage ticks
      self.AssertErrContains(tick_mark + ' ' * spaces + 'Hello World...\n')
    self.AssertErrContains(success_mark + 'tracker\n')
    self.AssertErrContains(success_mark + 'Hello World...\n')

  @test_case.Filters.DoNotRunOnWindows
  def testCtrlCHandler(self):
    self.SetConsoleSize(30)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.
    with self.assertRaisesRegex(console_io.OperationCancelledError,
                                'Aborted by user.'):
      with self._GetMultilineStagedProgressTracker(
          'tracker', self.stages, autotick=False) as spt:
        spt.StartStage(self.keys[0])
        spt.CompleteStage(self.keys[0])
        spt.Tick()
        spt.StartStage(self.keys[1])
        os.kill(os.getpid(), signal.SIGINT)
        spt.Tick()
    self.AssertOutputEquals('')
    self.AssertErrContainsLines(
        'X  tracker\n',
        '  OK Hello World...\n',
        '  -  Ahhhhhhhhhhhhhhh...\n',
        'Aborted by user.\n')

  @test_case.Filters.DoNotRunOnWindows
  def testUnInterruptable(self):
    self.SetConsoleSize(50)
    # The code under test should work on Windows. However, Python does not
    # support sending POSIX signals on Windows. The Windows shell catches
    # CTRL-C and converts it into a SIGINT (which is why the code works).
    # Also, sending a CTRL_C_EVENT does not actually trigger the SIGINT handler.

    with self._GetMultilineStagedProgressTracker(
        'tracker', self.stages, autotick=False, interruptable=False) as spt:
      spt.StartStage(self.keys[0])
      spt.CompleteStage(self.keys[0])
      spt.Tick()
      os.kill(os.getpid(), signal.SIGINT)
      spt.StartStage(self.keys[1])
      spt.CompleteStage(self.keys[1])
      spt.Tick()
    self.AssertOutputEquals('')
    self.AssertErrContainsLines(
        'OK tracker This operation cannot be cancelled.\n',
        '  OK Hello World...\n',
        '  OK Ahhhhhhhhhhhhhhh...\n',
        'Done.\n')

  def testProgressTrackerHandlesTypedText(self):
    properties.VALUES.core.color_theme.Set('testing')
    self.SetConsoleSize(30)
    self.SetEncoding('utf-8')
    with self._GetMultilineStagedProgressTracker(
        'tracker', self.stages, autotick=False) as spt:
      spt.StartStage(self.keys[0])
      spt.CompleteStage(self.keys[0])
    self.AssertErrContains('[✓](PT_SUCCESS) Hello World')


if __name__ == '__main__':
  sdk_test_base.main()
