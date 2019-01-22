#!/usr/local/bin/python3

#
# create app with access_layer=IpAccessDedicatedOrShared with port 1 and with Docker and QCOW
# verify app is created
# 

import unittest
import grpc
import sys
import time
from delayedassert import expect, expect_equal, assert_expectations
import logging
import os

from MexController import mex_controller

controller_address = os.getenv('AUTOMATION_CONTROLLER_ADDRESS', '127.0.0.1:55001')

stamp = str(time.time())
developer_name = 'developer' + stamp
developer_address = 'allen tx'
developer_email = 'dev@dev.com'
flavor_name = 'x1.small' + stamp
cluster_name = 'cluster' + stamp
app_name = 'app' + stamp
app_version = '1.0'

mex_root_cert = 'mex-ca.crt'
mex_cert = 'localserver.crt'
mex_key = 'localserver.key'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class tc(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.controller = mex_controller.Controller(controller_address = controller_address,
                                                    root_cert = mex_root_cert,
                                                    key = mex_key,
                                                    client_cert = mex_cert
                                                   )
        self.flavor = mex_controller.Flavor(flavor_name=flavor_name, ram=1024, vcpus=1, disk=1)
        self.cluster_flavor = mex_controller.ClusterFlavor(cluster_flavor_name=flavor_name, node_flavor_name=flavor_name, master_flavor_name=flavor_name, number_nodes=1, max_nodes=1, number_masters=1)

        self.developer = mex_controller.Developer(developer_name=developer_name,
                                                  developer_address=developer_address,
                                                  developer_email=developer_email)
        self.cluster = mex_controller.Cluster(cluster_name=cluster_name,
                                              default_flavor_name=flavor_name)

        self.controller.create_flavor(self.flavor.flavor)
        self.controller.create_cluster_flavor(self.cluster_flavor.cluster_flavor)
        self.controller.create_developer(self.developer.developer) 
        self.controller.create_cluster(self.cluster.cluster)

    def test_CreateAppDockerIpAccessDedicatedOrSharedTCP1(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeDocker/tcp:1
        # ... create app with ip_access=IpAccessDedicatedOrShared with tcp:1 and with Docker
        # ... verify app is created

        # print the existing apps 
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared and port=tcp:1
        self.app = mex_controller.App(image_type='ImageTypeDocker',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'tcp:1',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)

        port_match = 'ports:\n        - containerPort: 1\n          protocol: TCP'
        expect(port_match in resp.deployment_manifest, 'manifest ports')
        
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppDockerIpAccessDedicatedOrSharedTCP01(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeDocker/tcp:01
        # ... create app with ip_access=IpAccessDedicatedOrShared with tcp:01 and with Docker
        # ... verify app is created

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared and port=tcp:01
        self.app = mex_controller.App(image_type='ImageTypeDocker',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'tcp:01',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
       
        port_match = 'ports:\n        - containerPort: 01\n          protocol: TCP'
        expect(port_match in resp.deployment_manifest, 'manifest ports')
 
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppDockerIpAccessDedicatedOrSharedUDP1(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeDocker/udp:1
        # ... create app with ip_access=IpAccessDedicatedOrShared with udp:1 and with Docker
        # ... verify app is created

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared and port=udp:1
        self.app = mex_controller.App(image_type='ImageTypeDocker',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'udp:1',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
       
        port_match = 'ports:\n        - containerPort: 1\n          protocol: UDP'
        expect(port_match in resp.deployment_manifest, 'manifest ports')
 
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppDockerIpAccessDedicatedOrSharedUDP01(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeDocker/udp:01
        # ... create app with ip_access=IpAccessDedicatedOrShared with udp:01 and with Docker
        # ... verify app is created

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared and port=udp:01
        self.app = mex_controller.App(image_type='ImageTypeDocker',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'udp:01',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
       
        port_match = 'ports:\n        - containerPort: 01\n          protocol: UDP'
        expect(port_match in resp.deployment_manifest, 'manifest ports')
 
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppDockerIpAccessDedicatedOrSharedHTTP1(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeDocker/http:1
        # ... create app with ip_access=IpAccessDedicatedOrShared with http:1 and with Docker
        # ... verify app is created

        # EDGECLOUD-371 - CreateApp with accessports of http shows protocol as TCP on ShowApp

        # print the existing apps 
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared and port=http:1
        self.app = mex_controller.App(image_type='ImageTypeDocker',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'http:1',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
       
        port_match = 'ports:\n        - containerPort: 1\n          protocol: HTTP'
        expect(port_match in resp.deployment_manifest, 'manifest ports')
 
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppDockerIpAccessDedicatedOrSharedHTTP01(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeDocker/http:01
        # ... create app with ip_access=IpAccessDedicatedOrShared with http:01 and with Docker
        # ... verify app is created

        # EDGECLOUD-371 - CreateApp with accessports of http shows protocol as TCP on ShowApp

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared and port=http:01
        self.app = mex_controller.App(image_type='ImageTypeDocker',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'http:01',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
       
        port_match = 'ports:\n        - containerPort: 01\n          protocol: HTTP'
        expect(port_match in resp.deployment_manifest, 'manifest ports')
 
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppQCOWIpAccessDedicatedOrSharedTCP1(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeQCOW/tcp:1
        # ... create app with ip_access=IpAccessDedicatedOrShared with tcp:1 and with QCOW
        # ... verify app is created

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared QCOW tcp:1
        self.app = mex_controller.App(image_type='ImageTypeQCOW',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'tcp:1',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
        
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppQCOWIpAccessDedicatedOrSharedTCP01(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeQCOW/tcp:01
        # ... create app with ip_access=IpAccessDedicatedOrShared with tcp:01 and with QCOW
        # ... verify app is created

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared QCOW tcp:1
        self.app = mex_controller.App(image_type='ImageTypeQCOW',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'tcp:01',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
        
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppQCOWIpAccessDedicatedOrSharedUDP1(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeQCOW/udp:1
        # ... create app with ip_access=IpAccessDedicatedOrShared with udp:1 and with QCOW
        # ... verify app is created

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared QCOW udp:1
        self.app = mex_controller.App(image_type='ImageTypeQCOW',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'udp:1',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
        
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppQCOWIpAccessDedicatedOrSharedUDP01(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeQCOW/udp:01
        # ... create app with ip_access=IpAccessDedicatedOrShared with udp:01 and with QCOW
        # ... verify app is created

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared QCOW udp:01
        self.app = mex_controller.App(image_type='ImageTypeQCOW',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'udp:01',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
        
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppQCOWIpAccessDedicatedOrSharedHTTP1(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeQCOW/http:1
        # ... create app with ip_access=IpAccessDedicatedOrShared with http:1 and with QCOW
        # ... verify app is created

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared QCOW udp:1
        self.app = mex_controller.App(image_type='ImageTypeQCOW',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'http:1',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
        
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppQCOWIpAccessDedicatedOrSharedHTTP01(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeQCOW/http:01
        # ... create app with ip_access=IpAccessDedicatedOrShared with http:01 and with QCOW
        # ... verify app is created

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared QCOW http:01
        self.app = mex_controller.App(image_type='ImageTypeQCOW',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'http:01',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
        
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    def test_CreateAppQCOWIpAccessDedicatedOrSharedHTTPUppercase(self):
        # [Documentation] App - User shall be able to create an app with IpAccessDedicatedOrShared/ImageTypeQCOW/HTTP:01
        # ... create app with ip_access=IpAccessDedicatedOrShared with uppercase HTTP:01 and with QCOW
        # ... verify app is created

        # print the existing apps
        app_pre = self.controller.show_apps()

        # create the app
        # contains access_layer=IpAccessDedicatedOrShared QCOW HTTP:01
        self.app = mex_controller.App(image_type='ImageTypeQCOW',
                                             app_name=app_name,
                                             app_version=app_version,
                                             cluster_name=cluster_name,
                                             developer_name=developer_name,
                                             ip_access = 'IpAccessDedicatedOrShared',
                                             access_ports = 'HTTP:01',
                                             default_flavor_name=flavor_name)
        resp = self.controller.create_app(self.app.app)

        # print the cluster instances after error
        app_post = self.controller.show_apps()

        # look for app
        found_app = self.app.exists(app_post)

        self.controller.delete_app(self.app.app)
        
        expect_equal(found_app, True, 'find app')
        assert_expectations()

    @classmethod
    def tearDownClass(self):
        self.controller.delete_cluster(self.cluster.cluster)
        self.controller.delete_developer(self.developer.developer)
        self.controller.delete_cluster_flavor(self.cluster_flavor.cluster_flavor)
        self.controller.delete_flavor(self.flavor.flavor)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(tc)
    sys.exit(not unittest.TextTestRunner().run(suite).wasSuccessful())

