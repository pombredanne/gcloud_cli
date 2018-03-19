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
"""Tests of our yaml parsing logic."""

import os

from googlecloudsdk.api_lib.app import util as app_util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.app import util


class YamlParsingTests(util.WithAppData, sdk_test_base.SdkBase):
  """Tests of yaml parsing."""

  def AssertConfigs(self, appdir, *args):
    self.assertEqual(len(args), len(appdir.Configs()))
    for name in args:
      self.assertTrue(name in appdir.Configs())

  def AssertModule(self, mod, name, is_hermetic=False, env=None,
                   skip_files=None, runtime=None):
    self.assertEqual(name, mod.module)
    self.assertEqual(is_hermetic, mod.is_hermetic)
    if env:
      self.assertIs(mod.env, env)
    if skip_files:
      self.assertEqual(skip_files,
                       str(mod.parsed.skip_files))
    if runtime:
      self.assertEqual(runtime, mod.runtime)

  def testDefaultModuleOnly(self):
    f = self.WriteApp('app.yaml')
    mod = yaml_parsing.ServiceYamlInfo.FromFile(f)
    self.AssertModule(mod, 'default')
    # True only for Managed VMs
    self.assertFalse(mod.RequiresImage())
    self.assertIs(mod.env, app_util.Environment.STANDARD)

  def testRuntimeField(self):
    good = [
        'python',
        'custom',
        'gs://foo.yaml',
        'gs://runtime-builders/aspnetcore-12345.yaml',
        'gs://runtime-builders/some_weird_thing-12345.yaml',
        'go-1.8'
    ]
    bad = [
        'http://google.com/foo.yaml',
        'something_weird'
    ]

    for r in good:
      f = self.WriteApp('app.yaml', runtime=r, env='flex')
      self.AssertModule(yaml_parsing.ServiceYamlInfo.FromFile(f),
                        'default', runtime=r, is_hermetic=True)

    for r in bad:
      with self.assertRaises(yaml_parsing.YamlParseError):
        f = self.WriteApp('app.yaml', runtime=r, env='flex')
        yaml_parsing.ServiceYamlInfo.FromFile(f)

  def testIllegalVersion(self):
    f = self.WriteApp('app.yaml', version='1')
    with self.assertRaisesRegexp(
        yaml_parsing.YamlValidationError,
        r'The \[version\] field is specified'):
      yaml_parsing.ServiceYamlInfo.FromFile(f)

  def testIllegalApplication(self):
    f = self.WriteApp('app.yaml', project='foo')
    with self.assertRaisesRegexp(
        yaml_parsing.YamlValidationError,
        r'The \[application\] field is specified'):
      yaml_parsing.ServiceYamlInfo.FromFile(f)

  def testManagedVMsWarning(self):
    """Assert that we get a deprecation warning for vm: true."""
    f = self.WriteVmRuntime('app.yaml', 'python')
    mod = yaml_parsing.ServiceYamlInfo.FromFile(f)
    self.AssertModule(mod, 'default',
                      env=app_util.Environment.MANAGED_VMS)
    self.AssertErrContains('Deployments using `vm: true` have been deprecated.')

  def testPythonCompatWarning(self):
    """Assert that we get a deprecation warning for python-compat runtime."""
    f = self.WriteApp('app.yaml', env='flex', runtime='python-compat')
    mod = yaml_parsing.ServiceYamlInfo.FromFile(f)
    self.AssertModule(mod, 'default', is_hermetic=True,
                      env=app_util.Environment.FLEX)
    self.AssertErrContains('[runtime: python-compat] is deprecated.  '
                           'Please use [runtime: python] instead.')

  def testAppEngineApisWarning(self):
    """Assert that we get a deprecation warning for enable_app_engine_apis."""
    f = self.WriteApp('app.yaml', env='flex',
                      beta_settings='\n  enable_app_engine_apis: true')
    mod = yaml_parsing.ServiceYamlInfo.FromFile(f)
    self.AssertModule(mod, 'default', is_hermetic=True,
                      env=app_util.Environment.FLEX)
    self.AssertErrContains('Please migrate to a new base image',
                           normalize_space=True)

  def testHasLib(self):
    """Assert that we don't get a warning for python libssl 2.7.11."""
    libdata = """
threadsafe: true
handlers:
- url: /static
  static_dir: static
libraries:
- name: ssl
  version: 2.7.11
"""
    f = self.WriteApp('app.yaml', runtime='python27', data=libdata)
    mod = yaml_parsing.ServiceYamlInfo.FromFile(f)
    parsed = mod.parsed
    self.assertTrue(yaml_parsing.HasLib(parsed, 'ssl'))
    self.assertFalse(yaml_parsing.HasLib(parsed, 'other'))
    self.assertTrue(yaml_parsing.HasLib(parsed, 'ssl', '2.7.11'))
    self.assertFalse(yaml_parsing.HasLib(parsed, 'ssl', '2.7.13'))

  def testPythonSSLWarning(self):
    """Assert that we get a deprecation warning for python libssl 2.7."""
    libdata = """
threadsafe: true
handlers:
- url: /static
  static_dir: static
libraries:
- name: ssl
  version: 2.7
"""
    f = self.WriteApp('app.yaml', runtime='python27', data=libdata)
    mod = yaml_parsing.ServiceYamlInfo.FromFile(f)
    self.AssertModule(mod, 'default',
                      env=app_util.Environment.STANDARD)
    self.AssertErrContains('outdated version [2.7] of the Python SSL library')

  def testPythonNoSSLWarning(self):
    """Assert that we don't get a warning for python libssl 2.7.11."""
    libdata = """
threadsafe: true
handlers:
- url: /static
  static_dir: static
libraries:
- name: ssl
  version: 2.7.11
"""
    f = self.WriteApp('app.yaml', runtime='python27', data=libdata)
    mod = yaml_parsing.ServiceYamlInfo.FromFile(f)
    self.AssertModule(mod, 'default',
                      env=app_util.Environment.STANDARD)
    self.AssertErrNotContains('outdated version [2.7] of the Python SSL lib')

  def testSkipFiles(self):
    # Constants for regex comparison.
    standard_default = (r'^(.*/)?('
                        r'(#.*#)|'
                        r'(.*~)|'
                        r'(.*\.py[co])|'
                        r'(.*/RCS/.*)|'
                        r'(\..*)|'
                        r')$')
    flex_default = (r'^(.*/)?#.*#$|'
                    r'^(.*/)?.*~$|'
                    r'^(.*/)?.*\.py[co]$|'
                    r'^(.*/)?.*/RCS/.*$|'
                    r'^(.*/)?.git(ignore|/.*)$|'
                    r'^(.*/)?node_modules/.*$')

    # Constants for app.yaml contents.
    # pylint:disable=anomalous-backslash-in-string
    standard_skip_data = ('api_version: 1\n'
                          'threadsafe: true\n'
                          'handlers:\n'
                          '- url: /\n'
                          '  script: home.app\n'
                          'skip_files:\n'
                          '- ^(main.py)$')
    flex_test_skip_data = ('skip_files:\n'
                           '- ^(.*/)?#.*#$\n'
                           '- ^(.*/)?.*~$\n'
                           '- ^(.*/)?.*\.py[co]$\n'
                           '- ^(.*/)?.*/RCS/.*$\n'
                           '- ^(.*/)?.git(ignore|/.*)$\n'
                           '- ^(.*/)?node_modules/.*$')
    skip_files_data = ('skip_files:\n'
                       '- {}'.format(standard_default))
    # pylint:enable=anomalous-backslash-in-string

    # Setup: write app.yamls for two standard and two flex services.
    hermetic_module = self.WriteApp('app.yaml', service='default', env='flex')
    hermetic_with_skip = self.WriteApp(
        'app1.yaml', service='mod1', env='flex',
        data=skip_files_data)
    hermetic_with_extra_skip = self.WriteApp(
        'app1b.yaml', service='mod1b', env='flex',
        data=flex_test_skip_data)
    standard_module = self.WriteApp('app2.yaml', service='mod2')
    standard_with_skip = self.WriteApp(
        'app3.yaml', service='mod3',
        data=standard_skip_data)

    fn = yaml_parsing.ServiceYamlInfo.FromFile
    hermetic_module_info = fn(hermetic_module)
    hermetic_with_skip_info = fn(hermetic_with_skip)
    hermetic_with_extra_skip_info = fn(hermetic_with_extra_skip)
    standard_module_info = fn(standard_module)
    standard_with_skip_info = fn(standard_with_skip)

    # Flexible service without explicit skip_files should have flex default
    self.AssertModule(hermetic_module_info, 'default', is_hermetic=True,
                      env=app_util.Environment.FLEX,
                      skip_files=flex_default)
    # Flexible parsing doesn't replace standard default if it was on purpose
    self.AssertModule(hermetic_with_skip_info, 'mod1', is_hermetic=True,
                      env=app_util.Environment.FLEX,
                      skip_files=standard_default)
    # Flexible users who use flex default in app.yaml get what they expect.
    self.AssertModule(hermetic_with_extra_skip_info, 'mod1b', is_hermetic=True,
                      env=app_util.Environment.FLEX,
                      skip_files=flex_default)
    # standard service without explicit skip_files should have standard default
    self.AssertModule(standard_module_info, 'mod2', is_hermetic=False,
                      env=app_util.Environment.STANDARD,
                      skip_files=standard_default)
    # standard service should have different skip_files if one is entered.
    self.AssertModule(standard_with_skip_info, 'mod3', is_hermetic=False,
                      env=app_util.Environment.STANDARD,
                      skip_files=(r'^(main.py)$'))

  def testCustomRuntimeNoEnv(self):
    f = self.WriteApp('app.yaml', runtime='custom')
    with self.assertRaisesRegexp(
        yaml_parsing.YamlValidationError,
        'runtime "custom" requires that env be explicitly specified.'):
      yaml_parsing.ServiceYamlInfo.FromFile(f)

  def testHermeticVm(self):
    hermetic_data = """
vm: true
threadsafe: true
"""
    non_hermetic_data = """
vm: true
threadsafe: true
handlers:
- url: /static
  static_dir: static
"""
    hermetic_vm_module = self.WriteApp(
        'mod1.yaml', service='mymod1', data=hermetic_data)
    non_hermetic_vm_module = self.WriteApp(
        'mod2.yaml', service='mymod2', data=non_hermetic_data)
    mod1 = yaml_parsing.ServiceYamlInfo.FromFile(hermetic_vm_module)
    mod2 = yaml_parsing.ServiceYamlInfo.FromFile(non_hermetic_vm_module)
    self.AssertModule(mod1, 'mymod1', is_hermetic=True,
                      env=app_util.Environment.MANAGED_VMS)
    self.AssertModule(mod2, 'mymod2', is_hermetic=False,
                      env=app_util.Environment.MANAGED_VMS)

  def testBadFile(self):
    file_path = self.WriteFile('junk.txt', '')
    with self.assertRaisesRegexp(
        yaml_parsing.YamlParseError,
        r'An error occurred while parsing file'
        .format(file_path=file_path)):
      yaml_parsing.ServiceYamlInfo.FromFile(file_path)

  def testConfigWithAppId(self):
    f1 = self.WriteApp('app.yaml', project='foo')
    f2 = self.WriteConfig(self.CRON_DATA, project='foo')

    with self.assertRaisesRegexp(
        yaml_parsing.YamlValidationError,
        r'The \[application\] field is specified'):
      yaml_parsing.ServiceYamlInfo.FromFile(f1)
    with self.assertRaisesRegexp(
        yaml_parsing.YamlValidationError,
        r'The \[application\] field is specified'):
      yaml_parsing.ConfigYamlInfo.FromFile(f2)

  def testBadAppParse(self):
    app_file = os.path.join(self.temp_path, 'app.yaml')
    with open(app_file, 'w') as fp:
      fp.write('trash')
    # Need to escape the path for Windows.
    app_file = app_file.replace('\\', r'\\')
    with self.assertRaisesRegexp(
        yaml_parsing.YamlParseError,
        r'An error occurred while parsing file'):
      yaml_parsing.ServiceYamlInfo.FromFile(app_file)

  def testPythonRuntimeWarning(self):
    f1 = self.WriteApp('app.yaml', runtime='python', data="""
api_version: 1
threadsafe: true

handlers:
- url: /
  script: home.app
""")

    with self.assertRaisesRegexp(
        yaml_parsing.YamlValidationError,
        r'Service \[default\] uses unsupported Python 2.5 runtime. Please use '
        r'\[runtime: python27\] instead'):
      yaml_parsing.ServiceYamlInfo.FromFile(f1)

  def testRequiresImage(self):
    f1 = self.WriteVmRuntime('app.yaml', 'python27')
    mod = yaml_parsing.ServiceYamlInfo.FromFile(f1)
    self.AssertModule(mod, 'default', env=app_util.Environment.MANAGED_VMS)
    self.assertTrue(mod.RequiresImage())

  def testRequiresImageLocalAppYaml(self):
    self.WriteVmRuntime('app.yaml', 'dart')
    with files.ChDir(self.temp_path):
      mod = yaml_parsing.ServiceYamlInfo.FromFile('app.yaml')
      self.AssertModule(mod, 'default', env=app_util.Environment.MANAGED_VMS)
      self.assertTrue(mod.RequiresImage())

  def testUpdateManagedVMConfig(self):
    f = self.WriteVmRuntime('app.yaml', runtime='python27')
    mod = yaml_parsing.ServiceYamlInfo.FromFile(f)
    self.AssertModule(mod, 'default', env=app_util.Environment.MANAGED_VMS)
    self.assertTrue(mod.RequiresImage())
    self.assertEqual(mod.parsed.vm_settings['module_yaml_path'], 'app.yaml')

  def testAppDirNames(self):
    yamls = yaml_parsing.ConfigYamlInfo.CONFIG_YAML_PARSERS.keys()
    for yaml in yamls:
      yaml_dir = os.path.join(self.temp_path, yaml)
      files.MakeDir(yaml_dir)
      self.assertIsNone(yaml_parsing.ConfigYamlInfo.FromFile(yaml_dir))

if __name__ == '__main__':
  test_case.main()