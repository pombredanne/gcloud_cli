# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Test for container util functions."""

import os
import stat

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import http_wrapper

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import config as core_config
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms
from surface.container.clusters import get_credentials
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container import base
import mock


_EMPTY_KUBECONFIG = '''\
apiVersion: v1
clusters: []
contexts: []
current-context: ''
kind: Config
preferences: {}
users: []
'''

_EXISTING_KUBECONFIG = '''\
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: CA_DATA
    server: https://123.4.4.4
  name: existing-cluster
contexts:
- context:
    cluster: existing-cluster
    user: existing-user
  name: existing-context
current-context: existing-context
kind: Config
preferences: {}
users:
- name: existing-user
  user:
    client-certificate-data: CLIENT_CERT_DATA
    client-key-data: CLIENT_KEY_DATA
'''


class ClusterUrlTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def testGenerateClusterUrl(self):
    registry = resources.Registry()
    cluster_ref = registry.Parse(
        'some-cluster-name',
        params={
            'projectId': 'some-project-id',
            'zone': 'some-zone',
        },
        collection='container.projects.zones.clusters')
    self.assertEqual('https://console.cloud.google.com/kubernetes/'
                     'workload_/gcloud/some-zone/some-cluster-name?'
                     'project=some-project-id',
                     c_util.GenerateClusterUrl(cluster_ref))


class ClusterConfigTestBase(base.UnitTestBase):

  def _RmPath(self, path):
    if os.path.isfile(path):
      os.unlink(path)
    elif os.path.isdir(path):
      file_utils.RmTree(path)

  def _LoadConfig(self):
    return c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID)

  def _PersistConfig(self, cluster):
    return c_util.ClusterConfig.Persist(cluster, self.PROJECT_ID)

  def _TestGetCredentials(self, cluster):
    properties.VALUES.compute.zone.Set(self.ZONE)
    self.ExpectGetCluster(cluster)
    self.Run(self.COMMAND_BASE + ' clusters get-credentials '
             + self.CLUSTER_NAME)
    c_config = c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID)
    self.assertIsNotNone(c_config)
    self.assertEqual(kconfig.Kubeconfig.Default().current_context,
                     c_config.kube_context)
    self.AssertErrContains(c_util.KUBECONFIG_USAGE_FMT.format(
        cluster=self.CLUSTER_NAME,
        context=c_config.kube_context))
    return c_config


class KubeconfigTestsV1(base.TestBaseV1, base.UnitTestBase):

  # Verifies expected permission bits of written kubeconfig.
  @test_case.Filters.DoNotRunOnWindows
  def testDefaultKubeconfig(self):
    path = kconfig.Kubeconfig.DefaultPath()
    self.assertFalse(os.path.isfile(path))
    kconfig.Kubeconfig.Default()
    self.assertTrue(os.path.isfile(path))
    st = os.stat(path)
    # the oct() is just to make reading failures easier
    self.assertEquals(
        oct(st.st_mode),
        oct(stat.S_IFREG | stat.S_IWUSR | stat.S_IRUSR))
    with open(path, 'r') as fp:
      self.assertEquals(fp.read(), _EMPTY_KUBECONFIG)

  def testEmptyDefaultKubeconfig(self):
    path = kconfig.Kubeconfig.DefaultPath()
    file_utils.MakeDir(os.path.dirname(path))
    with open(path, 'w') as fp:
      fp.write('')
    self.assertTrue(os.path.isfile(path))
    kconfig.Kubeconfig.Default()
    data = yaml.load_path(path)
    self.assertIsNotNone(data)
    with open(path, 'r') as fp:
      self.assertEquals(fp.read(), _EMPTY_KUBECONFIG)

  def testPartialDefaultKubeconfig(self):
    path = kconfig.Kubeconfig.DefaultPath()
    file_utils.MakeDir(os.path.dirname(path))
    with open(path, 'w') as fp:
      fp.write('clusters: []')
    self.assertTrue(os.path.isfile(path))
    kconfig.Kubeconfig.Default()
    with open(path, 'r') as fp:
      self.assertEquals(fp.read(), _EMPTY_KUBECONFIG)

  def testKubeconfigEnvvar(self):
    default_path = kconfig.Kubeconfig.DefaultPath()
    env_path = os.path.join(
        os.path.expanduser('~'), 'other_kubeconfig')
    file_utils.MakeDir(os.path.dirname(default_path))
    with open(default_path, 'w') as fp:
      fp.write(_EXISTING_KUBECONFIG)
    kubeconfig = kconfig.Kubeconfig.Default()
    self.assertEquals(kubeconfig.current_context, 'existing-context')
    # We overwrite $HOME in base.UnitTestBase.SetUp
    os.environ['KUBECONFIG'] = env_path
    kubeconfig = kconfig.Kubeconfig.Default()
    self.assertEquals(kubeconfig.current_context, '')
    with open(default_path, 'r') as fp:
      self.assertEquals(fp.read(), _EXISTING_KUBECONFIG)
    with open(env_path, 'r') as fp:
      self.assertEquals(fp.read(), _EMPTY_KUBECONFIG)

  @test_case.Filters.DoNotRunOnWindows
  def testDefaultPathNix(self):
    self.StartDictPatch('os.environ',
                        {'HOME': 'foo', 'HOMEDRIVE': 'bar', 'HOMEPATH': 'baz',
                         'USERPROFILE': 'junk'})
    self.assertEquals(kconfig.Kubeconfig.DefaultPath(),
                      os.path.join('foo', '.kube', 'config'))
    self.StartDictPatch('os.environ', {'HOME': ''})
    with self.assertRaises(kconfig.MissingEnvVarError):
      kconfig.Kubeconfig.DefaultPath()

  @test_case.Filters.RunOnlyOnWindows
  def testDefaultPathWindows(self):
    self.StartDictPatch('os.environ',
                        {'HOME': 'foo', 'HOMEDRIVE': 'C:', 'HOMEPATH': 'bar',
                         'USERPROFILE': 'baz'})
    self.assertEquals(kconfig.Kubeconfig.DefaultPath(),
                      os.path.join('foo', '.kube', 'config'))
    self.StartDictPatch('os.environ', {'HOME': ''})
    self.assertEquals(kconfig.Kubeconfig.DefaultPath(),
                      os.path.join('C:', 'bar', '.kube', 'config'))
    self.StartDictPatch('os.environ', {'HOMEDRIVE': '', 'HOMEPATH': ''})
    self.assertEquals(kconfig.Kubeconfig.DefaultPath(),
                      os.path.join('baz', '.kube', 'config'))
    self.StartDictPatch('os.environ', {'USERPROFILE': ''})
    with self.assertRaises(kconfig.MissingEnvVarError):
      kconfig.Kubeconfig.DefaultPath()

  def testLoadStoreKubeconfig(self):
    kubeconfig = kconfig.Kubeconfig.Default()
    cluster1 = kconfig.Cluster(
        'cluster1', 'https://1.1.1.1', ca_data='FAKE_CA_DATA')
    cluster2 = kconfig.Cluster(
        'cluster2', 'https://2.2.2.2', ca_data=None)
    user = kconfig.User('user', cert_data='FAKECERTDATA',
                        key_data='FAKE_KEY_DATA')
    context = kconfig.Context('context1', 'cluster1', 'user')
    kubeconfig.clusters['cluster1'] = cluster1
    kubeconfig.clusters['cluster2'] = cluster2
    kubeconfig.users['user'] = user
    kubeconfig.contexts['context'] = context

    kubeconfig.SaveToFile()

    # reload
    kubeconfig = kconfig.Kubeconfig.Default()
    self.assertEquals(kubeconfig.users[user['name']], user)
    self.assertEquals(kubeconfig.contexts[context['name']], context)
    for c in cluster1, cluster2:
      self.assertEquals(kubeconfig.clusters[c['name']], c)

    self.assertTrue(
        kubeconfig.clusters['cluster2']['cluster']['insecure-skip-tls-verify'])

  @sdk_test_base.Filters.DoNotRunInBundle
  def testNotFoundSdkBinPath(self):
    with self.AssertRaisesExceptionMatches(
        kconfig.Error, kconfig.SDK_BIN_PATH_NOT_FOUND):
      kconfig._AuthProvider('gcp')


class KubeconfigTestsV1Alpha1(base.TestBaseV1Alpha1, KubeconfigTestsV1):
  pass


class APIAdapterTests(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Tests for ApiAdapter."""

  TEST_ENDPOINT = 'http://localhost:8787/'

  def _Test503NotRetried(self, adapter_fn):
    """Test case: no retry when 503.

    Args:
      adapter_fn: an adapter initialization function.
    _Test503NotRetried takes an adapter initialization function
    because it has to patch core before creating the adapter.
    """
    properties.VALUES.api_endpoint_overrides.container.Set(self.TEST_ENDPOINT)
    properties.VALUES.api_endpoint_overrides.compute.Set(self.TEST_ENDPOINT)
    mock_http = mock.Mock()
    self.StartPatch('googlecloudsdk.core.credentials.http.Http',
                    return_value=mock_http)
    mock_http.request.return_value = ({'status': 503}, '')
    mock_http.connections = None
    adapter = adapter_fn()
    with self.assertRaises(apitools_exceptions.HttpError):
      adapter.ListClusters(self.Project())
    mock_http.request.assert_called_once_with(
        mock.ANY, method='GET', body='', headers=mock.ANY,
        redirections=mock.ANY, connection_type=mock.ANY)

  def test503NotRetriedV1(self):
    self._Test503NotRetried(api_adapter.NewV1APIAdapter)

  def test503NotRetriedV1Alpha1(self):
    self._Test503NotRetried(api_adapter.NewV1Alpha1APIAdapter)

  def _TestDefault(self, adapter_fn):
    # This test just verifies the client uses default CheckResponse
    # for non-503 status codes.
    properties.VALUES.api_endpoint_overrides.container.Set(self.TEST_ENDPOINT)
    properties.VALUES.api_endpoint_overrides.compute.Set(self.TEST_ENDPOINT)
    default_check = self.StartObjectPatch(
        http_wrapper,
        'CheckResponse',
        autospec=True)
    mock_http = mock.Mock()
    self.StartPatch('googlecloudsdk.core.credentials.http.Http',
                    return_value=mock_http)
    for status in [500, 404, 403]:
      info = {'status': status}
      mock_http.reset_mock()
      mock_http.connections = None
      mock_http.request.return_value = (info, '')
      adapter = adapter_fn()
      default_check.side_effect = apitools_exceptions.HttpError(info, '', '')
      with self.assertRaises(apitools_exceptions.HttpError):
        adapter.ListClusters(self.Project())
      mock_http.request.assert_called_once_with(
          mock.ANY, method='GET', body='', headers=mock.ANY,
          redirections=mock.ANY, connection_type=mock.ANY)
      default_check.assert_called_once_with(mock.ANY)
      default_check.reset_mock()

  def testDefaultV1(self):
    self._TestDefault(api_adapter.NewV1APIAdapter)

  def testDefaultV1Alpha1(self):
    self._TestDefault(api_adapter.NewV1Alpha1APIAdapter)


class ClusterConfigTest(
    base.TestBaseV1, base.GATestBase, ClusterConfigTestBase):

  def SetUp(self):
    self._PatchSDKBinPath()

  # TODO(b/70856999) Decide what auth behavior we want for client cert and fix
  # these tests.

  def testPersistAndLoadEmbeddedConfig(self):
    cluster = self._MakeCluster(
        status=self.running,
        statusMessage='Running',
        endpoint=self.ENDPOINT,
        zone=self.ZONE,
        clusterApiVersion='1.1.1',
        ca_data='base64cadata',
        cert_data='base64certdata',
        key_data='base64keydata',
    )
    config = c_util.ClusterConfig.Persist(cluster, self.PROJECT_ID)
    self.assertIsNotNone(config)
    self.assertTrue(config.has_certs)
    self.assertTrue(config.has_cert_data)
    self.assertEquals(config.ca_data, 'base64cadata')
    self.assertEquals(config.client_cert_data, 'base64certdata')
    self.assertEquals(config.client_key_data, 'base64keydata')

    loaded = c_util.ClusterConfig.Load(
        self.CLUSTER_NAME, self.ZONE, self.PROJECT_ID)
    self.assertTrue(loaded.has_cert_data)
    self.assertTrue(loaded.has_certs)
    self.assertEquals(config.ca_data, loaded.ca_data)
    self.assertEquals(config.client_key_data, loaded.client_key_data)
    self.assertEquals(config.client_cert_data, loaded.client_cert_data)

  def testPersistNoCertDataNotLegacyVersion(self):
    cluster = self._MakeCluster(
        status=self.running,
        statusMessage='Running',
        endpoint=self.ENDPOINT,
        zone=self.ZONE,
        currentMasterVersion=self.VERSION,
    )
    config = c_util.ClusterConfig.Persist(cluster, self.PROJECT_ID)
    self.assertFalse(config.has_certs)
    self.AssertErrContains('Cluster is missing certificate authority data.')

  def _TestPurgeConfig(self):
    path = kconfig.Kubeconfig.DefaultPath()
    file_utils.MakeDir(os.path.dirname(path))
    with open(path, 'w') as fp:
      fp.write(_EXISTING_KUBECONFIG)
    existing = kconfig.Kubeconfig.Default()
    existing._data['current-context'] = ''

    cluster = self._RunningCluster()
    config = c_util.ClusterConfig.Persist(cluster, self.PROJECT_ID)
    self.assertIsNotNone(config)
    self.assertTrue(config.has_certs)

    # set current-context to cluster config
    kubeconfig = kconfig.Kubeconfig.Default()
    kubeconfig._data['current-context'] = config.kube_context
    kubeconfig.SaveToFile()

    c_util.ClusterConfig.Purge(cluster.name, cluster.zone, self.PROJECT_ID)

    # reload kubeconfig
    kubeconfig = kconfig.Kubeconfig.Default()
    # current-context should be cleared, since it was set to the cluster
    # that got purged
    self.assertEquals(kubeconfig._data, existing._data)

  def testExistingKubeconfig(self):
    path = kconfig.Kubeconfig.DefaultPath()
    file_utils.MakeDir(os.path.dirname(path))
    with open(path, 'w') as fp:
      fp.write(_EXISTING_KUBECONFIG)
    existing = kconfig.Kubeconfig.Default()

    cluster = self._RunningCluster()
    config = c_util.ClusterConfig.Persist(cluster, self.PROJECT_ID)

    kubeconfig = kconfig.Kubeconfig.Default()
    cluster = kconfig.Cluster(
        config.kube_context, config.server, ca_data=config.ca_data)
    user = kconfig.User(config.kube_context, auth_provider='gcp')
    context = kconfig.Context(
        config.kube_context, config.kube_context, config.kube_context)

    # verify added kubeconfig data is correct
    self.assertEquals(kubeconfig.clusters[config.kube_context], cluster)
    self.assertEquals(kubeconfig.users[config.kube_context], user)
    self.assertEquals(kubeconfig.contexts[config.kube_context], context)
    self.assertEquals(kubeconfig.current_context, config.kube_context)

    # verify purge clears cluster data from kubeconfig
    c_util.ClusterConfig.Purge(
        config.cluster_name, config.zone_id, config.project_id)
    # reload kubeconfig
    kubeconfig = kconfig.Kubeconfig.Default()
    # Purge unsets current-context if it was set to the deleted
    # cluster's context
    existing.SetCurrentContext('')
    self.assertEquals(kubeconfig._data, existing._data)

  def testLoadInvalidKubeconfigFails(self):
    properties.VALUES.container.use_client_certificate.Set(True)
    cluster = self._RunningCluster()
    config = c_util.ClusterConfig.Persist(cluster, self.PROJECT_ID)
    self.assertIsNotNone(config)
    self.assertTrue(config.has_certs)

    kubeconfig = kconfig.Kubeconfig.Default()
    user = kubeconfig.users[config.kube_context]['user']
    client_cert = user['client-certificate-data']
    client_key = user['client-key-data']
    del kubeconfig.users[config.kube_context]['user']['client-certificate-data']
    del kubeconfig.users[config.kube_context]['user']['client-key-data']
    # client-cert and client-key are only valid when you have both.
    user = kubeconfig.users[config.kube_context]['user']
    user['client-certificate-data'] = client_cert
    user['client-key-data'] = client_key
    for key in ('client-certificate-data', 'client-key-data'):
      val = kubeconfig.users[config.kube_context]['user'][key]
      del kubeconfig.users[config.kube_context]['user'][key]
      kubeconfig.SaveToFile()
      self.assertIsNone(
          self._LoadConfig(),
          msg='ClusterConfig.Load should fail if %s is missing' % key)
      kubeconfig.users[config.kube_context]['user'][key] = val

  def testGetCredentials(self):
    c_config = self._TestGetCredentials(self._RunningCluster())
    self._TestDefaultAuth(c_config)

  def testGetCredentialsNotRunning(self):
    name = 'brokencluster'
    properties.VALUES.compute.zone.Set(self.ZONE)
    cluster = self._MakeCluster(
        name=name,
        status=self.error,
        statusMessage='shits on fire yo',
        clusterApiVersion='1.1.2',
        zone=self.ZONE,
        endpoint=self.ENDPOINT,
        ca_data='cadata',
        key_data='keydata',
        cert_data='certdata')
    self.ExpectGetCluster(cluster)
    self.Run(self.COMMAND_BASE + ' clusters get-credentials ' + name)
    c_config = c_util.ClusterConfig.Load(name, self.ZONE, self.PROJECT_ID)
    self.assertIsNotNone(c_config)
    self.assertEqual(kconfig.Kubeconfig.Default().current_context,
                     c_config.kube_context)
    self.assertEquals(c_config.ca_data, 'cadata')
    self.assertEquals(c_config.client_cert_data, 'certdata')
    self.assertEquals(c_config.client_key_data, 'keydata')
    self.assertEqual(kconfig.Kubeconfig.Default().current_context,
                     c_config.kube_context)
    self.AssertErrContains(c_util.KUBECONFIG_USAGE_FMT.format(
        cluster=name, context=c_config.kube_context))
    self.AssertErrContains('WARNING')
    self.AssertErrContains(get_credentials.NOT_RUNNING_MSG.format(
        'brokencluster'))

  def testGetCredentialsMissingZone(self):
    properties.VALUES.compute.zone.Set(None)
    with self.assertRaises(calliope_exceptions.MinimumArgumentException):
      self.Run(self.COMMAND_BASE + ' clusters get-credentials '
               + self.CLUSTER_NAME)

  def testGetCredentialsMissingEnv(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    cluster = self._RunningCluster()
    self.ExpectGetCluster(cluster)
    self.ExpectGetCluster(cluster)

    self.StartDictPatch('os.environ',
                        {'HOME': '', 'HOMEDRIVE': '', 'HOMEPATH': '',
                         'USERPROFILE': ''})
    platform_mock = self.StartObjectPatch(platforms.OperatingSystem,
                                          'IsWindows')

    platform_mock.return_value = False
    with self.AssertRaisesExceptionMatches(
        kconfig.MissingEnvVarError,
        'environment variable HOME or KUBECONFIG must be set to store '
        'credentials for kubectl'):
      self.Run(self.COMMAND_BASE + ' clusters get-credentials '
               + self.CLUSTER_NAME)
    platform_mock.return_value = True
    with self.AssertRaisesExceptionMatches(
        kconfig.MissingEnvVarError,
        'environment variable HOMEDRIVE/HOMEPATH, USERPROFILE, HOME, or '
        'KUBECONFIG must be set to store credentials for kubectl'):
      self.Run(self.COMMAND_BASE + ' clusters get-credentials '
               + self.CLUSTER_NAME)

  # TODO(b/70856999) This isn't really working as intended; fix it.
  def testGetCredentialsNoEndpoint(self):
    name = 'newcluster'
    properties.VALUES.compute.zone.Set(self.ZONE)
    cluster = self._MakeCluster(
        name=name,
        status=self.provisioning,
        currentMasterVersion=self.VERSION,
        zone=self.ZONE,
        endpoint=None)
    self.ExpectGetCluster(cluster)
    with self.assertRaises(c_util.Error):
      self.Run(self.COMMAND_BASE + ' clusters get-credentials ' + name)
    self.assertIsNone(
        c_util.ClusterConfig.Load(name, self.ZONE, self.PROJECT_ID))
    self.AssertErrContains('WARNING')
    self.AssertErrContains(get_credentials.NOT_RUNNING_MSG.format('newcluster'))
    self.AssertErrContains(
        'cluster newcluster is missing endpoint. Is it still PROVISIONING?')

  def testGetCredentialsDefaultAuthOldCluster(self):
    properties.VALUES.container.use_client_certificate.Set(None)
    c_config = self. _TestGetCredentials(
        self._RunningClusterForVersion('1.2.0'))
    self.assertTrue(c_config.has_certs)
    self.assertTrue(c_config.has_ca_cert)

  def testGetCredentialsClientCertAuthOldCluster(self):
    properties.VALUES.container.use_client_certificate.Set(True)
    c_config = self. _TestGetCredentials(
        self._RunningClusterForVersion('1.2.0'))
    self.assertTrue(c_config.has_certs)
    self.assertTrue(c_config.has_ca_cert)

  def testGetCredentialsGCPAuthOldCluster(self):
    properties.VALUES.container.use_client_certificate.Set(False)
    c_config = self. _TestGetCredentials(
        self._RunningClusterForVersion('1.2.0'))
    self.assertTrue(c_config.has_certs)
    self.assertTrue(c_config.has_ca_cert)

  def testGetCredentialsDefaultAuthNewCluster(self):
    properties.VALUES.compute.zone.Set(self.ZONE)
    c_config = self. _TestGetCredentials(
        self._RunningClusterForVersion('1.3.0'))
    self.assertFalse(c_config.has_certs)
    self.assertTrue(c_config.has_ca_cert)

  def testGetCredentialsClientCertAuthNewCluster(self):
    properties.VALUES.container.use_client_certificate.Set(True)
    c_config = self. _TestGetCredentials(
        self._RunningClusterForVersion('1.3.0'))
    self.assertTrue(c_config.has_certs)
    self.assertTrue(c_config.has_ca_cert)

  def testGetCredentialsGCPAuthNewCluster(self):
    properties.VALUES.container.use_app_default_credentials.Set(None)
    c_config = self. _TestGetCredentials(
        self._RunningClusterForVersion('1.3.0'))
    self.assertFalse(c_config.has_certs)
    self.assertTrue(c_config.has_ca_cert)
    self.assertIsNotNone(c_config.auth_provider)
    self.assertEqual(c_config.auth_provider.get('name'), 'gcp')


class ClusterConfigTestAlpha(ClusterConfigTest, base.AlphaTestBase):
  pass


class ClusterConfigTestBeta(ClusterConfigTest, base.BetaTestBase):
  pass


class BundleTest(
    base.TestBaseV1, base.GATestBase,
    ClusterConfigTestBase,
    sdk_test_base.BundledBase):

  def SetUp(self):
    self.current_versions_mock = self.StartObjectPatch(
        update_manager.UpdateManager, 'GetCurrentVersionsInformation',
        autospec=True)
    self.tmp_dir = file_utils.TemporaryDirectory()
    self.StartDictPatch('os.environ', {'PATH': self.tmp_dir.path})

  def TearDown(self):
    self.tmp_dir.Close()

  def _RemoveKubectlComponent(self):
    def empty(*unused_args, **unused_kwargs):
      return {}
    self.current_versions_mock.side_effect = empty

  def _AddKubectlComponent(self):
    def kubectl(*unused_args, **unused_kwargs):
      return {'kubectl': ''}
    self.current_versions_mock.side_effect = kubectl

  def _AddKubectlExecutable(self):
    kubectl_path = os.path.join(self.tmp_dir.path, 'kubectl')
    if platforms.OperatingSystem.IsWindows():
      open(kubectl_path + '.exe', 'w').close()
    else:
      open(kubectl_path, 'w').close()
      kubect_stat = os.stat(kubectl_path)
      os.chmod(kubectl_path, kubect_stat.st_mode | stat.S_IEXEC)

  def testMissingKubectl(self):
    self._RemoveKubectlComponent()
    self._TestGetCredentials(self._RunningCluster())
    self.AssertErrContains(c_util.MISSING_KUBECTL_MSG)

  def testKubectlInstalled_AsComponent(self):
    self._AddKubectlComponent()
    self._TestGetCredentials(self._RunningCluster())
    self.AssertErrNotContains(c_util.MISSING_KUBECTL_MSG)

  def testKubectlInstalled_Externally(self):
    self._RemoveKubectlComponent()
    self._AddKubectlExecutable()
    self._TestGetCredentials(self._RunningCluster())
    self.AssertErrNotContains(c_util.MISSING_KUBECTL_MSG)

  def testGetCredentialsGcloudAuth(self):
    properties.VALUES.container.use_client_certificate.Set(None)
    properties.VALUES.container.use_app_default_credentials.Set(False)
    c_config = self._TestGetCredentials(self._RunningClusterForVersion('1.5.0'))
    kubeconfig = kconfig.Kubeconfig.Default()
    bin_name = 'gcloud'
    if platforms.OperatingSystem.IsWindows():
      bin_name = 'gcloud.cmd'
    path = os.path.join(core_config.Paths().sdk_bin_path, bin_name)
    self.assertTrue(os.path.isfile(path))
    self.assertDictEqual(
        kubeconfig.users[c_config.kube_context]['user']['auth-provider'],
        {
            'name': 'gcp',
            'config': {
                'cmd-path': path,
                'cmd-args': 'config config-helper --format=json',
                'token-key': '{.credential.access_token}',
                'expiry-key': '{.credential.token_expiry}',
            }
        })


if __name__ == '__main__':
  test_case.main()