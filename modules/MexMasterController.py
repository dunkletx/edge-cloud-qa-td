import json
import jwt
import logging
import time
import re
import threading
import requests
import subprocess
import shlex
import os
import imaplib
import email
import queue

from mex_rest import MexRest
from mex_controller_classes import Organization

from mex_master_controller.OrgCloudletPool import OrgCloudletPool
from mex_master_controller.OrgCloudlet import OrgCloudlet
from mex_master_controller.CloudletPool import CloudletPool
from mex_master_controller.CloudletPoolMember import CloudletPoolMember
from mex_master_controller.Cloudlet import Cloudlet
from mex_master_controller.App import App
from mex_master_controller.AppInstance import AppInstance
from mex_master_controller.ClusterInstance import ClusterInstance
from mex_master_controller.AutoScalePolicy import AutoScalePolicy
from mex_master_controller.Metrics import Metrics
from mex_master_controller.Flavor import Flavor
from mex_master_controller.OperatorCode import OperatorCode
from mex_master_controller.PrivacyPolicy import PrivacyPolicy
from mex_master_controller.AutoProvisioningPolicy import AutoProvisioningPolicy
from mex_master_controller.RunCommand import RunCommand
from mex_master_controller.ShowDevice import ShowDevice
from mex_master_controller.ShowDeviceReport import ShowDeviceReport

import shared_variables_mc
import shared_variables

logging.basicConfig(format='%(asctime)s %(levelname)s %(funcName)s line:%(lineno)d - %(message)s',datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger('mex_mastercontroller rest')

timestamp = str(time.time())

class MexMasterController(MexRest):
    """Library for talking to the Master Controller
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, mc_address='127.0.0.1:9900', root_cert=None, auto_login=True):
        """The MC address should be given at import time. The default is the local address
        
        Examples:
        | =Setting= | =Value=             | =Value=                             | =Comment= |
        | Library   | MexMasterController | mc_address=%{AUTOMATION_MC_ADDRESS} | # Read mc address from environment variable |
        """
        self.root_cert = None

        if root_cert and len(root_cert) > 0:
            self.root_cert = self._findFile(root_cert)

        super().__init__(address=mc_address, root_cert=self.root_cert)
        
        #print('*WARN*', 'mcinit')
        self.root_url = f'https://{mc_address}/api/v1'
        self.mc_address = mc_address
        
        self.token = None
        self.prov_stack = []

        self.username = 'mexadmin'
        self.password = 'mexadmin123'

        self.admin_username = 'mexadmin'
       
        self.super_token = None
        self._decoded_token = None
        self.orgname = None
        self.orgtype = None
        self.address = None
        self.phone = None
        self.email_address = None
        self.organization_name = None
        self._mail = None

        self._queue_obj = queue.Queue()

        self._number_login_requests = 0
        self._number_login_requests_success = 0
        self._number_login_requests_fail = 0
        self._number_createuser_requests = 0
        self._number_createuser_requests_success = 0
        self._number_createuser_requests_fail = 0
        self._number_currentuser_requests = 0
        self._number_currentuser_requests_success = 0
        self._number_currentuser_requests_fail = 0
        self._number_showrole_requests = 0
        self._number_showrole_requests_success = 0
        self._number_showrole_requests_fail = 0
        self._number_createorg_requests = 0
        self._number_createorg_requests_success = 0
        self._number_createorg_requests_fail = 0
        self._number_showorg_requests = 0
        self._number_showorg_requests_success = 0
        self._number_showorg_requests_fail = 0
        self._number_adduserrole_requests = 0
        self._number_adduserrole_requests_success = 0
        self._number_adduserrole_requests_fail = 0
        self._number_removeuserrole_requests = 0
        self._number_removeuserrole_requests_success = 0
        self._number_removeuserrole_requests_fail = 0

#        self._number_showclusterinst_requests = 0
#        self._number_showclusterinst_requests_success = 0
#        self._number_showclusterinst_requests_fail = 0
#        self._number_createclusterinst_requests = 0
#        self._number_createclusterinst_requests_success = 0
#        self._number_createclusterinst_requests_fail = 0
#        self._number_deleteclusterinst_requests = 0
#        self._number_deleteclusterinst_requests_success = 0
#        self._number_deleteclusterinst_requests_fail = 0

#        self._number_showcloudlet_requests = 0
#        self._number_showcloudlet_requests_success = 0
#        self._number_showcloudlet_requests_fail = 0
#        self._number_createcloudlet_requests = 0
#        self._number_createcloudlet_requests_success = 0
#        self._number_createcloudlet_requests_fail = 0
#        self._number_deletecloudlet_requests = 0
#        self._number_deletecloudlet_requests_success = 0
#        self._number_deletecloudlet_requests_fail = 0

        self._number_showaccount_requests = 0
        self._number_showaccount_requests_success = 0
        self._number_showaccount_requests_fail = 0

        self.flavor = None
        self.app = None
        self.app_instance = None
        self.cloudlet = None
        self.cloudlet_pool = None
        self.cloudlet_pool_member = None
        self.org_cloudlet_pool = None
        self.org_cloudlet = None
        self.operatorcode =  None
        self.privacy_policy =  None
        self.autoprov_policy =  None
        self.run_cmd = None
        
        if auto_login:
            self.super_token = self.login(self.username, self.password, None, False)

        self.autoscale_policy = AutoScalePolicy(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)

        #self.flavor = Flavor(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        #self.app = App(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        #self.app_instance = AppInstance(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token, thread_queue=self._queue_obj)
        #self.cloudlet = Cloudlet(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        #self.cloudlet_pool = CloudletPool(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        #self.cloudlet_pool_member = CloudletPoolMember(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        #self.org_cloudlet_pool = OrgCloudletPool(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        #self.org_cloudlet = OrgCloudlet(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)

    def _create_classes(self):
        self.flavor = Flavor(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.app = App(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.app_instance = AppInstance(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token, thread_queue=self._queue_obj)
        self.cluster_instance = ClusterInstance(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token, thread_queue=self._queue_obj)
        self.cloudlet = Cloudlet(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.cloudlet_pool = CloudletPool(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.cloudlet_pool_member = CloudletPoolMember(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.org_cloudlet_pool = OrgCloudletPool(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.org_cloudlet = OrgCloudlet(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.operatorcode = OperatorCode(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.privacy_policy = PrivacyPolicy(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.run_cmd = RunCommand(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.showdevice = ShowDevice(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.showdevicereport = ShowDeviceReport(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)
        self.autoprov_policy = AutoProvisioningPolicy(root_url=self.root_url, prov_stack=self.prov_stack, token=self.token, super_token=self.super_token)

    def find_file(self, filename):
        return self._findFile(filename)

    def get_supertoken(self):
        return self.super_token

    def get_token(self):
        return self.token

    def get_roletype(self):
        if self.orgtype == 'developer': return 'DeveloperContributor'
        else: return 'OperatorContributor'

    def get_default_developer_name(self):
        return shared_variables.developer_name_default

    def get_default_cluster_name(self):
        return shared_variables.cluster_name_default

    def get_default_app_name(self):
        return shared_variables.app_name_default

    def get_default_app_version(self):
        return shared_variables.app_version_default

    def get_default_flavor_name(self):
        return shared_variables.flavor_name_default

    def get_default_autoscale_policy_name(self):
        return shared_variables.autoscale_policy_name_default

    def get_default_cloudlet_pool_name(self):
        return shared_variables.cloudletpool_name_default

    def get_default_organization_name(self):
        return shared_variables.organization_name_default

    def get_default_privacy_policy_name(self):
        return shared_variables.privacy_policy_name_default

    def get_default_time_stamp(self):
        return shared_variables.time_stamp_default
    
    def number_of_login_requests(self):
        return self._number_login_requests

    def number_of_successful_login_requests(self):
        return self._number_login_requests_success

    def number_of_failed_login_requests(self):
        return self._number_login_requests_fail

    def number_of_createuser_requests(self):
        return self._number_createuser_requests

    def number_of_successful_createuser_requests(self):
        return self._number_createuser_requests_success

    def number_of_failed_createuser_requests(self):
        return self._number_createuser_requests_fail

    def number_of_currentuser_requests(self):
        return self._number_currentuser_requests

    def number_of_successful_currentuser_requests(self):
        return self._number_currentuser_requests_success

    def number_of_failed_currentuser_requests(self):
        return self._number_currentuser_requests_fail

    def number_of_showrole_requests(self):
        return self._number_showrole_requests

    def number_of_successful_showrole_requests(self):
        return self._number_showrole_requests_success

    def number_of_failed_showrole_requests(self):
        return self._number_showrole_requests_fail

    def number_of_createorg_requests(self):
        return self._number_createorg_requests

    def number_of_successful_createorg_requests(self):
        return self._number_createorg_requests_success

    def number_of_failed_createorg_requests(self):
        return self._number_createorg_requests_fail

    def number_of_showorg_requests(self):
        return self._number_showorg_requests

    def number_of_successful_showorg_requests(self):
        return self._number_showorg_requests_success

    def number_of_failed_showorg_requests(self):
        return self._number_showorg_requests_fail

    def reset_user_count(self):
        self._number_createuser_requests = 0
        self._number_createuser_requests_success = 0
        self._number_createuser_requests_fail = 0

    def number_of_adduserrole_requests(self):
        return self._number_adduserrole_requests

    def number_of_successful_adduserrole_requests(self):
        return self._number_adduserrole_requests_success

    def number_of_failed_adduserrole_requests(self):
        return self._number_adduserrole_requests_fail

    def number_of_removeuserrole_requests(self):
        return self._number_removeuserrole_requests

    def number_of_successful_removeuserrole_requests(self):
        return self._number_removeuserrole_requests_success

    def number_of_failed_renmoveuserrole_requests(self):
        return self._number_removeuserrole_requests_fail

    def decoded_token(self):
        return self._decoded_token

    def created_username(self):
        return self.username

    def created_password(self):
        return self.password

    def created_org(self):
        orginfo = 'Name:' + self.org + '  Type:' + self.orgtype + '  Address:' + self.address + '  Phone:' + self.phone
        return orginfo

    def login(self, username=None, password=None, json_data=None, use_defaults=True, use_thread=False):
        url = self.root_url + '/login'
        payload = None

        if json_data is not None:
            payload = json_data
        else:
            if use_defaults == True:
                if username == None: username = self.username
                if password == None: password = self.password

            login_dict = {}
            if username != None:
                login_dict['username'] = username
            if password != None:
                login_dict['password'] = password
            payload = json.dumps(login_dict)

        logger.info('login to mc at {}. \n\t{}'.format(url, payload))

        def send_message():
            self._number_login_requests += 1

            try:
                self.post(url=url, data=payload)

                logger.info('response:\n' + str(self.resp.text))

                self.token = self.decoded_data['token']
                if username == self.admin_username:  self.super_token = self.token
                
                self._decoded_token = jwt.decode(self.token, verify=False)

                if str(self.resp.status_code) != '200':
                    self._number_login_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            except Exception as e:
                self._number_login_requests_fail += 1
                raise Exception("post failed:", e)

        self._number_login_requests_success += 1

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            self._create_classes()
            return self.token

    def create_user(self, username=None, password=None, email_address=None, email_password=None, server='imap.gmail.com', email_check=True, json_data=None, use_defaults=True, use_thread=False):
        namestamp = str(time.time())
        url = self.root_url + '/usercreate'
        payload = None

        if not email_password:
            email_password = password
            
        if use_defaults == True:
            if username == None: username = 'name' + namestamp
            if password == None: password = 'password' + timestamp
            if email_address == None: email_address = username + '@email.com'

        shared_variables_mc.username_default = username
        shared_variables_mc.password_default = password
        self.emal = email_address
        
        if json_data != None:
            payload = json_data
        else:
            user_dict = {}
            if username is not None:
                user_dict['name'] = username
            if password is not None:
                user_dict['passhash'] = password
            if email_address is not None:
                user_dict['email'] = email_address

            payload = json.dumps(user_dict)

        logger.info('usercreate on mc at {}. \n\t{}'.format(url, payload))

        if email_check:
            logging.info(f'checking email with email={email_address} password={password}')
            mail = imaplib.IMAP4_SSL(server)
            mail.login(email_address, email_password)
            mail.select('inbox')
            self._mail = mail
            logging.info('login successful')
            
            status, email_list_pre = mail.search(None, '(SUBJECT "Welcome to MobiledgeX!")')
            mail_ids_pre = email_list_pre[0].split()
            num_emails_pre = len(mail_ids_pre)
            self._mail_count = num_emails_pre
            logging.info(f'number of emails pre is {num_emails_pre}')

        def send_message():
            self._number_createuser_requests += 1

            try:
                self.post(url=url, data=payload)

                logger.info('response:\n' + str(self.resp.text))

                if str(self.resp.status_code) != '200':
                    self._number_createuser_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())

            except Exception as e:
                self._number_createuser_requests_fail += 1
                raise Exception("post failed:", e)

            self.prov_stack.append(lambda:self.delete_user(username, self.super_token, None, False))

        self.username = username
        self.password = password
        self.email_address = email_address

        self._number_createuser_requests_success += 1

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            return self.decoded_data
            #return username, password, email

    def get_current_user(self, token=None, use_defaults=True, use_thread=False):
        url = self.root_url + '/auth/user/current'

        logger.info('user/current on mc at {}'.format(url))

        if use_defaults == True:
            if token is None: token = self.token

        def send_message():
            self._number_currentuser_requests += 1

            try:
                self.post(url=url, bearer=token)

                logger.info('response:\n' + str(self.resp.text))

                if str(self.resp.status_code) != '200':
                    self._number_currentuser_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            except Exception as e:
                self._number_currentuser_requests_fail += 1
                raise Exception("post failed:", e)

        self._number_currentuser_requests_success += 1

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            return self.decoded_data

    def delete_user(self, username=None, token=None, json_data=None, use_defaults=True):
        url = self.root_url + '/auth/user/delete'
        payload = None

        if use_defaults == True:
            if token is None: token = self.token
            if username is None: username = self.username
            #if password is None: password = self.password
            #if email is None: email = self.username

        if json_data !=  None:
            payload = json_data
        else:
            user_dict = {}
            if username is not None:
                user_dict['name'] = username

            payload = json.dumps(user_dict)

        logger.info('delete user on mc at {}. \n\t{}'.format(url, payload))

        self.post(url=url, data=payload, bearer=token)

        logger.info('response:\n' + str(self.resp.text))

        if str(self.resp.text) != '{"message":"user deleted"}':
            raise Exception("error deleting  user. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())

    def update_user_restriction(self, username=None, locked=None, token=None, json_data=None, use_defaults=True):
        url = self.root_url + '/auth/restricted/user/update'
        payload = None

        if use_defaults == True:
            if token is None: token = self.super_token
            if username is None: username = self.username

        if json_data !=  None:
            payload = json_data
        else:
            user_dict = {}
            if username is not None:
                user_dict['name'] = username
            if locked is not None:
                user_dict['locked'] = locked

            payload = json.dumps(user_dict)

        logger.info('update user restriction on mc at {}. \n\t{}'.format(url, payload))

        self.post(url=url, data=payload, bearer=token)

        logger.info('response:\n' + str(self.resp.text))

        #if str(self.resp.text) != '{"message":"user deleted"}':
        #    raise Exception("error deleting  user. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())

    def unlock_user(self, username=None):
        if username is None: username = shared_variables_mc.username_default
        logging.info(f'unlocking username={username}')
        self.update_user_restriction(username=username, locked=False)

    def new_password(self, password=None, token=None, json_data=None, use_defaults=True):
        url = self.root_url + '/auth/user/newpass'

        if use_defaults == True:
            if token == None: token = self.token
            if password == None: password = self.password

        if json_data != None:
            payload = json_data
        else:
            user_dict = {}
            if password != None:
                user_dict['password'] = password

            payload = json.dumps(user_dict)

        #print('*WARN*',token)

        self.post(url=url, data=payload, bearer=token)

        logger.info('response:\n' + str(self.resp.text))

        if str(self.resp.text) != '{"message":"password updated"}':
            raise Exception("error changing password. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())

    def show_role(self, token=None, use_defaults=True, use_thread=False):
        url = self.root_url + '/auth/role/show'

        if use_defaults == True:
            if token == None: token = self.token

        #print('*WARN*',token)

        def send_message():
            self._number_showrole_requests += 1

            try:
                self.post(url=url, bearer=token)

                logger.info('response:\n' + str(self.resp.text))

                if str(self.resp.status_code) != '200':
                    self._number_showrole_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            except Exception as e:
                self._number_showrole_requests_fail += 1
                raise Exception("post failed:", e)

        self._number_showrole_requests_success += 1

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            if str(self.resp.text) != '["AdminContributor","AdminManager","AdminViewer","DeveloperContributor","DeveloperManager","DeveloperViewer","OperatorContributor","OperatorManager","OperatorViewer"]':
                raise Exception("error showing roles. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            return str(self.resp.text)

    def show_role_assignment(self, token=None, json_data=None, use_defaults=True, use_thread=False, sort_field='username', sort_order='ascending'):
        url = self.root_url + '/auth/role/assignment/show'

        payload = None

        if use_defaults == True:
            if token == None: token = self.token

        if json_data !=  None:
            payload = json_data
        else:
            user_dict = {}
            #if email is not None:
            #    user_dict['email'] = email
            payload = json.dumps(user_dict)

        logger.info('show users and roles on mc at {}. \n\t{}'.format(url, payload))
        #self.post(url=url, bearer=token)

        #logger.info('response:\n' + str(self.resp.text))

        #respText = str(self.resp.text)
        #print('*WARN*', respText)

        #if respText != '[]':
        #    match = re.search('.*org.*username.*role.*', respText)
            # print('*WARN*',match)
        #    if not match:
        #        raise Exception("error showing role assignments. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())

        #return self.decoded_data

        def send_message():

            try:
                self.post(url=url, bearer=token, data=payload)

                logger.info('response:\n' + str(self.resp.text))

                respText = str(self.resp.text)

                if str(self.resp.status_code) != '200':
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            except Exception as e:
                raise Exception("post failed:", e)

            resp_data = self.decoded_data
            if type(resp_data) is dict:
                resp_data = [resp_data]

            reverse = True if sort_order == 'descending' else False
            if sort_field == 'username':
                logging.info('sorting by username')
                resp_data = sorted(resp_data, key=lambda x: x['username'].casefold(),reverse=reverse) # sorting since need to check for may apps. this return the sorted list instead of the response itself
            elif sort_field == 'organization':
                logging.info('sorting by organization')
                resp_data = sorted(resp_data, key=lambda x: x['org'].casefold(),reverse=reverse)
            return resp_data

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            #if str(self.resp.) != '[]':
            #    #match = re.search('.*Name.*Type.*Address.*Phone.*AdminUsername.*CreatedAt.*UpdatedAt.*', str(self.resp.text))
            #    # print('*WARN*',match)
            #    if not match:
            #        raise Exception("error showing organization. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            #return self.decoded_data
            return resp

    def create_org(self, orgname=None, orgtype=None, address=None, phone=None, token=None, json_data=None, use_defaults=True, use_thread=False):
        #orgstamp = str(time.time())
        url = self.root_url + '/auth/org/create'
        payload = None
        
        if use_defaults == True:
            if token == None: token = self.token
            #if orgname == None: orgname = 'orgname' + orgstamp
            #if orgtype == None: orgtype = 'developer'
            #if address == None: address = '111 somewhere dr'
            #if phone == None: phone = '123-456-7777'

        if json_data !=  None:
            payload = json_data
        else:
            org_dict = Organization(organization_name=orgname, organization_type=orgtype, phone=phone, address=address, use_defaults=use_defaults).organization
            if 'name' in org_dict:
                self.organization_name = org_dict['name']
            #org_dict = {}
            #if orgname is not None:
            #    org_dict['name'] = orgname
            #if orgtype is not None:
            #    org_dict['type'] = orgtype
            #if address is not None:
            #    org_dict['address'] = address
            #if phone is not None:
            #    org_dict['phone'] = phone

            payload = json.dumps(org_dict)

        logger.info('create org on mc at {}. \n\t{}'.format(url, payload))

        #print('*WARN*', orgname, token)

        def send_message():
            self._number_createorg_requests += 1

            try:
                self.post(url=url, data=payload, bearer=token)

                logger.info('response:\n' + str(self.resp.text))

                if str(self.resp.status_code) != '200':
                    self._number_createorg_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())

                self.prov_stack.append(lambda:self.delete_org(orgname=org_dict['name'], token=self.super_token))

            except Exception as e:
                self._number_createorg_requests_fail += 1
                raise Exception("post failed:", e)

            self._number_createorg_requests_success += 1


        #self.orgname = org_dict['name']
        self.orgname = orgname
        self.orgtype = orgtype
        self.address = address
        self.phone = phone

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            if str(self.resp.text) != '{"message":"Organization created"}':
                #if str(self.resp.text) == '{"message":"Organization type must be developer, or operator"}':
                #    raise Exception("error creating organization. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
                raise Exception("error creating organization. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            return self.organization_name

    def show_organizations(self, token=None, use_defaults=True, use_thread=False):
        url = self.root_url + '/auth/org/show'

        if use_defaults == True:
            if token == None: token = self.token

        def send_message():
            self._number_showorg_requests += 1

            try:
                self.post(url=url, bearer=token)

                logger.info('response:\n' + str(self.resp.text))

                respText = str(self.resp.text)

                if str(self.resp.status_code) != '200':
                    self._number_showorg_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            except Exception as e:
                self._number_showorg_requests_fail += 1
                raise Exception("post failed:", e)

            self._number_showorg_requests_success += 1


        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            if str(self.resp.text) != '[]':
                match = re.search('.*Name.*Type.*Address.*Phone.*CreatedAt.*UpdatedAt.*', str(self.resp.text))
                # print('*WARN*',match)
                if not match:
                    raise Exception("error showing organization. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            return self.decoded_data


    def delete_org(self, orgname=None, token=None, json_data=None, use_defaults=True):
        url = self.root_url + '/auth/org/delete'
        payload = None

        if use_defaults == True:
            if token is None: token = self.token
            if orgname is None: orgname = self.orgname
        print('*WARN*','org',orgname)
        if json_data !=  None:
            payload = json_data
        else:
            org_dict = {}
            if orgname is not None:
                org_dict['name'] = orgname
                
            payload = json.dumps(org_dict)

        logger.info('delete org on mc at {}. \n\t{}'.format(url, payload))

        try:
            self.post(url=url, data=payload, bearer=token)

            logger.info('response:\n' + str(self.resp.text))

            if str(self.resp.text) != '{"message":"Organization deleted"}':
                raise Exception("error deleting org. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
        except Exception as e:
            raise Exception(f'code={self.resp.status_code}', f'error={self.resp.text}')

    def adduser_role(self, orgname= None, username=None, role=None, token=None, json_data=None, use_defaults=True, use_thread=False):
        """ Sends role add
        """
        url = self.root_url + '/auth/role/adduser'
        payload = None

        if use_defaults == True:
            if token is None: token = self.token
            #if orgname is None: orgname = self.orgname
            if orgname is None: orgname = shared_variables.organization_name_default
            if username is None: username = self.username
            if role is None: role = self.get_roletype()

        if json_data !=  None:
            payload = json_data
        else:
            adduser_dict = {}
            if orgname is not None:
                adduser_dict['org'] = orgname
            if username is not None:
                adduser_dict['username'] = username
            if role is not None:
                adduser_dict['role'] = role

            payload = json.dumps(adduser_dict)

        logger.info('role adduser on mc at {}. \n\t{}'.format(url, payload))

        #print('*WARN*', orgname, token)

        def send_message():
            self._number_adduserrole_requests += 1

            try:
                self.post(url=url, data=payload, bearer=token)

                logger.info('response:\n' + str(self.resp.text))

                if str(self.resp.status_code) != '200':
                    self._number_adduserrole_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            except Exception as e:
                self._number_adduserrole_requests_fail += 1
                raise Exception(f'code={self.resp.status_code}', f'error={self.resp.text}')

            self.prov_stack.append(lambda:self.removeuser_role(orgname, username, role, self.super_token))
            self._number_adduserrole_requests_success += 1

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            if str(self.resp.text) != '{"message":"Role added to user"}':
                raise Exception("error adding user role. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())


    def removeuser_role(self, orgname= None, username=None, role=None, token=None, json_data=None, use_defaults=True, use_thread=False):
        url = self.root_url + '/auth/role/removeuser'
        payload = None

        if use_defaults == True:
            if token is None: token = self.token
            if orgname is None: orgname = self.orgname
            if username is None: username = self.username
            if role is None: role = self.get_roletype()

        if json_data !=  None:
            payload = json_data
        else:
            removeuser_dict = {}
            if orgname is not None:
                removeuser_dict['org'] = orgname
            if username is not None:
                removeuser_dict['username'] = username
            if role is not None:
                removeuser_dict['role'] = role

            payload = json.dumps(removeuser_dict)

        logger.info('role removeuser on mc at {}. \n\t{}'.format(url, payload))

        #print('*WARN*', orgname, token)

        def send_message():
            self._number_removeuserrole_requests += 1

            try:
                self.post(url=url, data=payload, bearer=token)

                logger.info('response:\n' + str(self.resp.text))

                if str(self.resp.status_code) != '200':
                    self._number_removeuserrole_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            except Exception as e:
                self._number_removeuserrole_requests_fail += 1
                raise Exception("post failed:", e)

            self._number_removeuserrole_requests_success += 1

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            if str(self.resp.text) != '{"message":"Role removed from user"}':
                raise Exception("error adding user role. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            return str(self.resp.text)

#    def show_flavors(self, token=None, region=None, json_data=None, use_defaults=True, use_thread=False, sort_field='flavor_name', sort_order='ascending'):
#        return self.flavor.show_flavor(token=token, region=region, flavor_name=flavor_name, ram=ram, vcpus=vcpus, disk=disk, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)
#
#        url = self.root_url + '/auth/ctrl/ShowFlavor'
#
#        payload = None
#
#        if use_defaults == True:
#            if token == None: token = self.token
#
#        if json_data !=  None:
#            payload = json_data
#        else:
#            flavor_dict = {}
#            if region is not None:
#                flavor_dict['region'] = region
#
#            payload = json.dumps(flavor_dict)
#
#        logger.info('show flavor on mc at {}. \n\t{}'.format(url, payload))
#
#        def send_message():
#            self._number_showflavor_requests += 1
#
#            try:
#                self.post(url=url, bearer=token, data=payload)
#
#                logger.info('response:\n' + str(self.resp.text))
#
#                respText = str(self.resp.text)
#
#                if str(self.resp.status_code) != '200':
#                    self._number_showorg_requests_fail += 1
#                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#            except Exception as e:
#                self._number_showflavor_requests_fail += 1
#                raise Exception("post failed:", e)
#
#            self._number_showflavor_requests_success += 1
#
#            resp_data = self.decoded_data
#            if type(resp_data) is dict:
#                resp_data = [resp_data]
#
#            reverse = True if sort_order == 'descending' else False
#            if sort_field == 'flavor_name':
#                logging.info('sorting by flavor_name')
#                resp_data = sorted(resp_data, key=lambda x: x['data']['key']['name'].casefold(),reverse=reverse) # sorting since need to check for may apps. this return the sorted list instead of the response itself
#
#            return resp_data
#
#        if use_thread is True:
#            t = threading.Thread(target=send_message)
#            t.start()
#            return t
#        else:
#            print('sending message')
#            resp = send_message()
#            #if str(self.resp.) != '[]':
#            #    #match = re.search('.*Name.*Type.*Address.*Phone.*AdminUsername.*CreatedAt.*UpdatedAt.*', str(self.resp.text))
#            #    # print('*WARN*',match)
#            #    if not match:
#            #        raise Exception("error showing organization. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#            #return self.decoded_data
#            return resp
    def show_flavors(self, token=None, region=None, flavor_name=None, ram=None, vcpus=None, disk=None, json_data=None, use_defaults=True, use_thread=False, sort_field='flavor_name', sort_order='ascending'):
        resp = self.flavor.show_flavor(token=token, region=region, flavor_name=flavor_name, ram=ram, vcpus=vcpus, disk=disk, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

        reverse = True if sort_order == 'descending' else False
        if sort_field == 'flavor_name':
            #allregion = sorted(allregion, key=lambda x: (x['data']['region'].casefold(), x['data']['key']['name'].casefold()),reverse=reverse)
            resp_data = sorted(resp, key=lambda x: (x['data']['key']['name'].casefold()),reverse=reverse)
            print('*WARN*', 'post', resp_data)
        elif sort_field == 'ram':
            logging.info('sorting by ram')
            resp_data = sorted(resp, key=lambda x: (x['data']['key']['ram'].casefold()),reverse=reverse)
        elif sort_field == 'region':
            resp_data = sorted(resp, key=lambda x: x['data']['region'].casefold(),reverse=reverse)

        return resp_data
    
    def create_flavor(self, token=None, region=None, flavor_name=None, ram=None, vcpus=None, disk=None, optional_resources=None, json_data=None, use_defaults=True, use_thread=False, auto_delete=True):
        return self.flavor.create_flavor(token=token, region=region, flavor_name=flavor_name, ram=ram, vcpus=vcpus, disk=disk, optional_resources=optional_resources, json_data=json_data, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def delete_flavor(self, token=None, region=None, flavor_name=None, ram=None, vcpus=None, disk=None, json_data=None, use_defaults=True, use_thread=False):
        return self.flavor.delete_flavor(token=token, region=region, flavor_name=flavor_name, ram=ram, vcpus=vcpus, disk=disk, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)
        
    def show_apps(self, token=None, region=None, json_data=None, use_defaults=True, use_thread=False, sort_field='app_name', sort_order='ascending'):
        url = self.root_url + '/auth/ctrl/ShowApp'

        payload = None

        if use_defaults == True:
            if token == None: token = self.token

        if json_data !=  None:
            payload = json_data
        else:
            app_dict = {}
            if region is not None:
                app_dict['region'] = region

            payload = json.dumps(app_dict)

        logger.info('show app on mc at {}. \n\t{}'.format(url, payload))

        def send_message():
            self._number_showapp_requests += 1

            try:
                self.post(url=url, bearer=token, data=payload)

                logger.info('response:\n' + str(self.resp.text))

                respText = str(self.resp.text)

                if str(self.resp.status_code) != '200':
                    self._number_showapp_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            except Exception as e:
                self._number_showapp_requests_fail += 1
                raise Exception("post failed:", e)

            self._number_showapp_requests_success += 1

            resp_data = self.decoded_data
            if type(resp_data) is dict:
                resp_data = [resp_data]

            reverse = True if sort_order == 'descending' else False
            if sort_field == 'app_name':
                resp_data = sorted(resp_data, key=lambda x: x['data']['key']['name'].casefold(),reverse=reverse)

            return resp_data

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            return resp

    def show_cloudlets(self, token=None, region=None, operator_org_name=None, cloudlet_name=None, latitude=None, longitude=None, number_dynamic_ips=None, ip_support=None, platform_type=None, physical_name=None, env_vars=None, crm_override=None, notify_server_address=None, json_data=None, use_defaults=True, use_thread=False, sort_field='cloudlet_name', sort_order='ascending'):
        return self.cloudlet.show_cloudlet(token=token, region=region, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, latitude=latitude, longitude=longitude, number_dynamic_ips=number_dynamic_ips, ip_support=ip_support, platform_type=platform_type, physical_name=physical_name, env_vars=env_vars, notify_server_address=notify_server_address, crm_override=crm_override, use_defaults=use_defaults, use_thread=use_thread)

#        url = self.root_url + '/auth/ctrl/ShowCloudlet'
#
#        payload = None
#
#        if use_defaults == True:
#            if token == None: token = self.token
#
#        if json_data !=  None:
#            payload = json_data
#        else:
#            cloudlet_dict = {}
#            if region is not None:
#                cloudlet_dict['region'] = region
#
#            payload = json.dumps(cloudlet_dict)
#
#        logger.info('show cloudlet on mc at {}. \n\t{}'.format(url, payload))
#
#        def send_message():
#            self._number_showcloudlet_requests += 1
#
#            try:
#                self.post(url=url, bearer=token, data=payload)
#
#                logger.info('response:\n' + str(self.resp.text))
#
#                respText = str(self.resp.text)
#
#                if str(self.resp.status_code) != '200':
#                    self._number_showcloudlet_requests_fail += 1
#                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#            except Exception as e:
#                self._number_showcloudlet_requests_fail += 1
#                raise Exception("post failed:", e)
#
#            self._number_showcloudlet_requests_success += 1
#
#            resp_data = self.decoded_data
#            if type(resp_data) is dict:
#                resp_data = [resp_data]
#
#            reverse = True if sort_order == 'descending' else False
#            if sort_field == 'cloudlet_name':
#                resp_data = sorted(resp_data, key=lambda x: x['data']['key']['name'].casefold(),reverse=reverse)
#
#            return resp_data
#
#        if use_thread is True:
#            t = threading.Thread(target=send_message)
#            t.start()
#            return t
#        else:
#            resp = send_message()
#            return resp

    def show_cluster_instances(self, token=None, region=None, cluster_name=None, cloudlet_name=None, json_data=None, use_thread=False, use_defaults=True, sort_field='cluster_name', sort_order='ascending'):
        resp_data = self.cluster_instance.show_cluster_instance(token=token, region=region, cluster_name=cluster_name, cloudlet_name=cloudlet_name, json_data=json_data, use_thread=use_thread, use_defaults=use_defaults)

        if type(resp_data) is dict:
            resp_data = [resp_data]

        reverse = True if sort_order == 'descending' else False
        if sort_field == 'cluster_name':
            resp_data = sorted(resp_data, key=lambda x: x['data']['key']['cluster_key']['name'].casefold(),reverse=reverse)

        return resp_data
#        url = self.root_url + '/auth/ctrl/ShowClusterInst'
#
#        payload = None
#
#        if use_defaults == True:
#            if token == None: token = self.token
#
#        if json_data !=  None:
#            payload = json_data
#        else:
#            cluster_dict = {}
#            if cluster_name or cloudlet_name:
#                clusterinst = ClusterInstance(cluster_name=cluster_name, cloudlet_name=cloudlet_name, use_defaults=False).cluster_instance
#                cluster_dict = {'clusterinst': clusterinst}
#
#            if region is not None:
#                cluster_dict['region'] = region
#
#            payload = json.dumps(cluster_dict)
#
#        logger.info('show clusterinst on mc at {}. \n\t{}'.format(url, payload))
#
#        def send_message():
#            self._number_showclusterinst_requests += 1
#
#            try:
#                self.post(url=url, bearer=token, data=payload)
#
#                logger.info('response:\n' + str(self.resp.text))
#
#                respText = str(self.resp.text)
#
#                if str(self.resp.status_code) != '200':
#                    self._number_showclusterinst_requests_fail += 1
#                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#            except Exception as e:
#                self._number_showclusterinst_requests_fail += 1
#                raise Exception("post failed:", e)
#
#            self._number_showclusterinst_requests_success += 1
#
#            resp_data = self.decoded_data
#            if type(resp_data) is dict:
#                resp_data = [resp_data]
#
#            reverse = True if sort_order == 'descending' else False
#            if sort_field == 'cluster_name':
#                resp_data = sorted(resp_data, key=lambda x: x['data']['key']['cluster_key']['name'].casefold(),reverse=reverse)
#
#            return resp_data
#
#        if use_thread is True:
#            t = threading.Thread(target=send_message)
#            t.start()
#            return t
#        else:
#            resp = send_message()
#            return resp

    def show_app_instances(self, token=None, region=None, appinst_id=None, app_name=None, app_version=None, cloudlet_name=None, operator_org_name=None, developer_org_name=None, cluster_instance_name=None, cluster_instance_developer_org_name=None, json_data=None, use_defaults=False, use_thread=False, sort_field='app_name', sort_order='ascending'):
        if app_name or app_version or cloudlet_name or operator_name or developer_name or cluster_instance_name or cluster_instance_developer_name:
            resp_data = self.app_instance.show_app_instance(token=token, region=region, appinst_id=appinst_id, app_name=app_name, app_version=app_version, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, cluster_instance_name=cluster_instance_name, cluster_instance_developer_org_name=cluster_instance_developer_org_name, developer_org_name=developer_org_name, use_defaults=use_defaults, use_thread=use_thread)
            if type(resp_data) is dict:
                resp_data = [resp_data]

            reverse = True if sort_order == 'descending' else False
            if sort_field == 'app_name':
                resp_data = sorted(resp_data, key=lambda x: x['data']['key']['app_key']['name'].casefold(),reverse=reverse)

            return resp_data
        
    def show_all_flavors(self, sort_field='flavor_name', sort_order='ascending'):
        # should enhance by querying for the regions. But hardcode for now

        usregion = self.show_flavors(region='US', token=self.token, use_defaults=False)
        euregion = self.show_flavors(region='EU', token=self.token, use_defaults=False)

        for region in usregion:
            region['data']['region'] = 'US'

        for region in euregion:
            region['data']['region'] = 'EU'

        allregion = usregion + euregion
        print('*WARN*', 'pre', allregion)
        reverse = True if sort_order == 'descending' else False
        if sort_field == 'flavor_name':
            #allregion = sorted(allregion, key=lambda x: (x['data']['region'].casefold(), x['data']['key']['name'].casefold()),reverse=reverse)
            allregion = sorted(allregion, key=lambda x: (x['data']['key']['name'].casefold()),reverse=reverse)
            print('*WARN*', 'post', allregion)
        elif sort_field == 'ram':
            allregion = sorted(allregion, key=lambda x: (x['data']['ram'], x['data']['key']['name'].casefold()),reverse=reverse)
        elif sort_field == 'vcpus':
            allregion = sorted(allregion, key=lambda x: (x['data']['vcpus'], x['data']['key']['name'].casefold()),reverse=reverse)
        elif sort_field == 'disk':
            allregion = sorted(allregion, key=lambda x: (x['data']['disk'], x['data']['key']['name'].casefold()),reverse=reverse)
        elif sort_field == 'region':
            allregion = sorted(allregion, key=lambda x: x['data']['region'].casefold(),reverse=reverse)

        return allregion

    def show_all_cloudlets(self, sort_field='cloudlet_name', sort_order='ascending'):
        # should enhance by querying for the regions. But hardcode for now

        usregion = self.show_cloudlets(region='US')
        euregion = self.show_cloudlets(region='EU')

        for region in usregion:
            region['data']['region'] = 'US'

        for region in euregion:
            region['data']['region'] = 'EU'

        allregion = usregion + euregion

        reverse = True if sort_order == 'descending' else False
        if sort_field == 'cloudlet_name':
            #allregion = sorted(allregion, key=lambda x: (x['data']['region'].casefold(), x['data']['key']['name'].casefold()),reverse=reverse)
            allregion = sorted(allregion, key=lambda x: (x['data']['key']['name'].casefold()),reverse=reverse)
        elif sort_field == 'region':
            allregion = sorted(allregion, key=lambda x: x['data']['region'].casefold(),reverse=reverse)

        return allregion


    def show_all_cluster_instances(self, sort_field='cluster_name', sort_order='ascending'):
        # should enhance by querying for the regions. But hardcode for now

        usregion = self.show_cluster_instances(region='US', token=self.token, use_defaults=False)
        euregion = self.show_cluster_instances(region='EU', token=self.token, use_defaults=False)

        for region in usregion:
            region['data']['region'] = 'US'

        for region in euregion:
            region['data']['region'] = 'EU'

        allregion = usregion + euregion

        reverse = True if sort_order == 'descending' else False
        if sort_field == 'cluster_name':
            allregion = sorted(allregion, key=lambda x: x['data']['key']['cluster_key']['name'].casefold(),reverse=reverse)
        elif sort_field == 'region':
            allregion = sorted(allregion, key=lambda x: x['data']['region'].casefold(),reverse=reverse)

        return allregion

    def show_all_apps(self, sort_field='app_name', sort_order='ascending'):
        # should enhance by querying for the regions. But hardcode for now

        usregion = self.show_apps(region='US')
        euregion = self.show_apps(region='EU')

        for region in usregion:
            region['data']['region'] = 'US'

        for region in euregion:
            region['data']['region'] = 'EU'

        allregion = usregion + euregion

        reverse = True if sort_order == 'descending' else False
        if sort_field == 'app_name':
            allregion = sorted(allregion, key=lambda x: x['data']['key']['name'].casefold(),reverse=reverse)
        elif sort_field == 'region':
            allregion = sorted(allregion, key=lambda x: x['data']['region'].casefold(),reverse=reverse)

        return allregion

    def show_accounts(self, token=None, email=None, json_data=None, use_defaults=True, use_thread=False, sort_field='username', sort_order='ascending'):
        url = self.root_url + '/auth/user/show'

        payload = None

        if use_defaults == True:
            if token == None: token = self.token

        if json_data !=  None:
            payload = json_data
        else:
            account_dict = {}
            if email is not None:
                account_dict['email'] = email

            payload = json.dumps(account_dict)

        logger.info('show account on mc at {}. \n\t{}'.format(url, payload))

        def send_message():
            self._number_showaccount_requests += 1

            try:
                self.post(url=url, bearer=token, data=payload)

                logger.info('response:\n' + str(self.resp.text))

                respText = str(self.resp.text)

                if str(self.resp.status_code) != '200':
                    self._number_showorg_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            except Exception as e:
                self._number_showaccount_requests_fail += 1
                raise Exception("post failed:", e)

            self._number_showaccount_requests_success += 1

            resp_data = self.decoded_data
            if type(resp_data) is dict:
                resp_data = [resp_data]

            reverse = True if sort_order == 'descending' else False
            if sort_field == 'username':
                logging.info('sorting by username')
                resp_data = sorted(resp_data, key=lambda x: x['Name'].casefold(),reverse=reverse) # sorting since need to check for may apps. this return the sorted list instead of the response itself
            elif  sort_field == 'email':
                logging.info('sorting by email')
                resp_data = sorted(resp_data, key=lambda x: x['Email'].casefold(),reverse=reverse) # sorting since need to check for may apps. this return the sorted list instead of the response itself

            return resp_data

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            #if str(self.resp.) != '[]':
            #    #match = re.search('.*Name.*Type.*Address.*Phone.*AdminUsername.*CreatedAt.*UpdatedAt.*', str(self.resp.text))
            #    # print('*WARN*',match)
            #    if not match:
            #        raise Exception("error showing organization. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
            #return self.decoded_data
            return resp

    def show_nodes(self, region=None, token=None, json_data=None, use_defaults=True, sort_field='pod_name', sort_order='ascending'):
        url = self.root_url + '/auth/ctrl/ShowNode'
        payload = None

        if use_defaults == True:
            if token is None: token = self.token
            if region is None: region = self.region
            #if password is None: password = self.password
            #if email is None: email = self.username

        if json_data !=  None:
            payload = json_data
        else:
            region_dict = {}
            if region is not None:
                region_dict['region'] = region
            node_dict = {'node': {'key': region_dict}}
            payload = json.dumps(node_dict)

        logger.info('shownode on mc at {}. \n\t{}'.format(url, payload))

        self.post(url=url, data=payload, bearer=token)

        logger.info('response:\n' + str(self.resp.text))

        #if str(self.resp.text) != '{"message":"user deleted"}':
        #    raise Exception("error deleting  user. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())

        resp_data = self.decoded_data
        if type(resp_data) is dict:
            resp_data = [resp_data]

        reverse = True if sort_order == 'descending' else False
        if sort_field == 'pod_name':
            logging.info('sorting by pod name')
            resp_data = sorted(resp_data, key=lambda x: x['data']['key']['name'].casefold(),reverse=reverse) # sorting since need to check for may apps. this return the sorted list instead of the response itself

        return resp_data

    def create_cluster_instance(self, token=None, region=None, cluster_name=None, operator_org_name=None, cloudlet_name=None, developer_org_name=None, flavor_name=None, liveness=None, ip_access=None, deployment=None, number_masters=None, number_nodes=None, shared_volume_size=None, privacy_policy=None, reservable=None, json_data=None, use_defaults=True, use_thread=False):
        if developer_org_name is None:
            if self.organization_name:
                developer_org_name = self.organization_name
                cluster_instance_developer_name = self.organization_name
        return self.cluster_instance.create_cluster_instance(token=token, region=region, cluster_name=cluster_name, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, developer_org_name=developer_org_name, flavor_name=flavor_name, liveness=liveness, ip_access=ip_access, deployment=deployment, number_masters=number_masters, number_nodes=number_nodes, shared_volume_size=shared_volume_size, privacy_policy=privacy_policy, reservable=reservable, use_defaults=use_defaults)

#        url = self.root_url + '/auth/ctrl/CreateClusterInst'
#
#        payload = None
#        clusterInst = None
#
#        if use_defaults == True:
#            if token == None: token = self.token
#
#        if json_data !=  None:
#            payload = json_data
#        else:
#            if developer_name is None and self.organization_name: developer_name = self.organization_name
#            clusterInst = ClusterInstance(cluster_name=cluster_name, operator_name=operator_name, cloudlet_name=cloudlet_name, developer_name=developer_name, flavor_name=flavor_name, liveness=liveness, ip_access=ip_access, deployment=deployment, number_masters=number_masters, number_nodes=number_nodes, shared_volume_size=shared_volume_size, privacy_policy=privacy_policy, reservable=reservable, use_defaults=use_defaults).cluster_instance
#            cluster_dict = {'clusterinst': clusterInst}
#            if region is not None:
#                cluster_dict['region'] = region
#
#            payload = json.dumps(cluster_dict)
#
#        logger.info('create cluster instance on mc at {}. \n\t{}'.format(url, payload))
#
#        def send_message():
#            self._number_createclusterinst_requests += 1
#
#            try:
#                self.post(url=url, bearer=token, data=payload)
#                logger.info('response:\n' + str(self.resp.text))
#
#                if str(self.resp.status_code) != '200':
#                    self._number_createclusterinst_requests_fail += 1
#                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#                if 'Created ClusterInst successfully' not in str(self.resp.text):
#                    raise Exception('ERROR: ClusterInst not created successfully:' + str(self.resp.text))
#
#            except Exception as e:
#                self._number_createclusterinst_requests_fail += 1
#                raise Exception("post failed:", e)
#
#            self.prov_stack.append(lambda:self.delete_cluster_instance(region=region, token=self.super_token, cluster_name=clusterInst['key']['cluster_key']['name'], cloudlet_name=clusterInst['key']['cloudlet_key']['name'], operator_name=clusterInst['key']['cloudlet_key']['operator_key']['name'], developer_name=clusterInst['key']['developer']))
#
#            self._number_createclusterinst_requests_success += 1
#
#            resp =  self.show_cluster_instances(token=token, region=region, cluster_name=clusterInst['key']['cluster_key']['name'], cloudlet_name=clusterInst['key']['cloudlet_key']['name'])
#
#            return resp
#
#        if use_thread is True:
#            t = threading.Thread(target=send_message)
#            t.start()
#            return t
#        else:
#            resp = send_message()
#            return self.decoded_data

    def delete_cluster_instance(self, token=None, region=None, cluster_name=None, operator_org_name=None, cloudlet_name=None, developer_org_name=None, flavor_name=None, liveness=None, ip_access=None, crm_override=None, json_data=None, use_defaults=True, use_thread=False):
        return self.cluster_instance.delete_cluster_instance(token=token, region=region, cluster_name=cluster_name, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, developer_org_name=developer_org_name, flavor_name=flavor_name, liveness=liveness, ip_access=ip_access, use_defaults=use_defaults)
#
#        url = self.root_url + '/auth/ctrl/DeleteClusterInst'
#
#        payload = None
#        clusterInst = None
#
#        if use_defaults == True:
#            if token == None: token = self.token
#
#        if json_data !=  None:
#            payload = json_data
#        else:
#            clusterInst = ClusterInstance(cluster_name=cluster_name, operator_name=operator_name, cloudlet_name=cloudlet_name, developer_name=developer_name, flavor_name=flavor_name, liveness=liveness, ip_access=ip_access, crm_override=crm_override).cluster_instance
#            cluster_dict = {'clusterinst': clusterInst}
#            if region is not None:
#                cluster_dict['region'] = region
#
#            payload = json.dumps(cluster_dict)
#
#        logger.info('delete cluster instance on mc at {}. \n\t{}'.format(url, payload))
#
#        def send_message():
#            self._number_deleteclusterinst_requests += 1
#
#            try:
#                self.post(url=url, bearer=token, data=payload)
#                logger.info('response:\n' + str(self.resp.text))
#
#                if str(self.resp.status_code) != '200':
#                    self._number_deleteclusterinst_requests_fail += 1
#                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#                if crm_override is None and 'Deleted ClusterInst successfully' not in str(self.resp.text):
#                    raise Exception('ERROR: ClusterInst not deleted successfully:' + str(self.resp.text))
#            except Exception as e:
#                self._number_deleteclusterinst_requests_fail += 1
#                raise Exception("post failed:", e)
#
#            self._number_deleteclusterinst_requests_success += 1
#
#        if use_thread is True:
#            t = threading.Thread(target=send_message)
#            t.start()
#            return t
#        else:
#            resp = send_message()
#            return self.decoded_data

    def delete_all_cluster_instances(self, region, cloudlet_name, crm_override=None):
        clusterinstances = self.show_cluster_instances(token=self.token, region=region, cloudlet_name=cloudlet_name, use_defaults=False)
        for cluster in clusterinstances:
            logging.info(f'deleting {cluster}')
            self.cluster_instance.delete_cluster_instance(token=self.token, region=region, cluster_name=cluster['data']['key']['cluster_key']['name'], developer_org_name=cluster['data']['key']['organization'], cloudlet_name=cloudlet_name, operator_org_name=cluster['data']['key']['cloudlet_key']['organization'], crm_override=crm_override, use_defaults=False)

    def create_app(self, token=None, region=None, app_name=None, app_version=None, ip_access=None, access_ports=None, image_type=None, image_path=None, cluster_name=None, developer_org_name=None, default_flavor_name=None, config=None, command=None, app_template=None, auth_public_key=None, permits_platform_apps=None, deployment=None, deployment_manifest=None,  scale_with_cluster=False, official_fqdn=None, annotations=None, auto_prov_policy=None, access_type=None, configs_kind=None, configs_config=None, json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        """ Send region CreateApp
        """
        return self.app.create_app(token=token, region=region, app_name=app_name, app_version=app_version, ip_access=ip_access, access_ports=access_ports, image_type=image_type, image_path=image_path,cluster_name=cluster_name, developer_org_name=developer_org_name, default_flavor_name=default_flavor_name, config=config, command=command, app_template=app_template, auth_public_key=auth_public_key, permits_platform_apps=permits_platform_apps, deployment=deployment, deployment_manifest=deployment_manifest, scale_with_cluster=scale_with_cluster, official_fqdn=official_fqdn, annotations=annotations, auto_prov_policy=auto_prov_policy, access_type=access_type, configs_kind=configs_kind, configs_config=configs_config, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def delete_app(self, token=None, region=None, app_name=None, app_version=None, ip_access=None, access_ports=None, image_type=None, image_path=None, cluster_name=None, developer_org_name=None, default_flavor_name=None, config=None, command=None, app_template=None, auth_public_key=None, permits_platform_apps=None, deployment=None, deployment_manifest=None,  scale_with_cluster=False, official_fqdn=None, json_data=None, use_defaults=True, use_thread=False):
        """ Send region DeleteApp
        """
        return self.app.delete_app(token=token, region=region, app_name=app_name, app_version=app_version, ip_access=ip_access, access_ports=access_ports, image_type=image_type, image_path=image_path,cluster_name=cluster_name, developer_org_name=developer_org_name, default_flavor_name=default_flavor_name, config=config, command=command, app_template=app_template, auth_public_key=auth_public_key, permits_platform_apps=permits_platform_apps, deployment=deployment, deployment_manifest=deployment_manifest, scale_with_cluster=scale_with_cluster, official_fqdn=official_fqdn, annotations=annotations, use_defaults=use_defaults)

    def update_app(self, token=None, region=None, app_name=None, app_version=None, ip_access=None, access_ports=None, image_type=None, image_path=None, cluster_name=None, developer_org_name=None, default_flavor_name=None, config=None, command=None, app_template=None, auth_public_key=None, permits_platform_apps=None, deployment=None, deployment_manifest=None,  scale_with_cluster=False, official_fqdn=None, annotations=None, json_data=None, use_defaults=True, use_thread=False):
        """ Send region UpdateApp
        """
        return self.app.update_app(token=token, region=region, app_name=app_name, app_version=app_version, ip_access=ip_access, access_ports=access_ports, image_type=image_type, image_path=image_path,cluster_name=cluster_name, developer_org_name=developer_org_name, default_flavor_name=default_flavor_name, config=config, command=command, app_template=app_template, auth_public_key=auth_public_key, permits_platform_apps=permits_platform_apps, deployment=deployment, deployment_manifest=deployment_manifest, scale_with_cluster=scale_with_cluster, official_fqdn=official_fqdn, annotations=annotations, use_defaults=use_defaults)

    def create_app_instance(self, token=None, region=None, appinst_id = None, app_name=None, app_version=None, cloudlet_name=None, operator_org_name=None, developer_org_name=None, cluster_instance_name=None, cluster_instance_developer_org_name=None, flavor_name=None, config=None, uri=None, latitude=None, longitude=None, autocluster_ip_access=None, privacy_policy=None, shared_volume_size=None, crm_override=None, json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        """ Send region CreateAppInst
        """
        if developer_org_name is None:
            if self.organization_name:
                developer_org_name = self.organization_name
                cluster_instance_developer_org_name = self.organization_name
        return self.app_instance.create_app_instance(token=token, region=region, appinst_id=appinst_id, app_name=app_name, app_version=app_version, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, cluster_instance_name=cluster_instance_name, cluster_instance_developer_org_name=cluster_instance_developer_org_name, developer_org_name=developer_org_name, flavor_name=flavor_name, config=config, uri=uri, latitude=latitude, longitude=longitude, autocluster_ip_access=autocluster_ip_access, privacy_policy=privacy_policy, shared_volume_size=shared_volume_size, crm_override=crm_override, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def delete_app_instance(self, token=None, region=None, appinst_id = None, app_name=None, app_version=None, cloudlet_name=None, operator_org_name=None, developer_org_name=None, cluster_instance_name=None, cluster_instance_developer_org_name=None, flavor_name=None, config=None, uri=None, latitude=None, longitude=None, autocluster_ip_access=None, crm_override=None, json_data=None, use_defaults=True, use_thread=False):
        """ Send region DeleteAppInst
        """
        return self.app_instance.delete_app_instance(token=token, region=region, appinst_id=appinst_id, app_name=app_name, app_version=app_version, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, cluster_instance_name=cluster_instance_name, cluster_instance_developer_org_name=cluster_instance_developer_org_name, developer_org_name=developer_org_name, flavor_name=flavor_name, config=config, uri=uri, latitude=latitude, longitude=longitude, autocluster_ip_access=autocluster_ip_access, crm_override=crm_override, use_defaults=use_defaults, use_thread=use_thread)

    def delete_all_app_instances(self, region, cloudlet_name, crm_override=None):
        """ Send region DeleteAppInst for all instances filter by cloudlet
        """
        appinstances = self.show_app_instances(region=region, cloudlet_name=cloudlet_name)
        found_failure = False
        for app in appinstances:
            logging.info(f'deleting {app}')
            try:
                self.app_instance.delete_app_instance(region=region, app_name=app['data']['key']['app_key']['name'], app_version=app['data']['key']['app_key']['version'], developer_org_name=app['data']['key']['app_key']['organization'], cloudlet_name=cloudlet_name, cluster_instance_name=app['data']['key']['cluster_inst_key']['cluster_key']['name'], operator_org_name=app['data']['key']['cluster_inst_key']['cloudlet_key']['organization'], cluster_instance_developer_org_name=app['data']['key']['cluster_inst_key']['organization'], crm_override=crm_override)
            except Exception as e:
                found_failure = True
                logging.error(f'error deleting appinst:{e}')

        if found_failure:
            raise Exception('deleting all app instances failed')

    def run_command(self, token=None, region=None, command=None, app_name=None, app_version=None, cloudlet_name=None, operator_org_name=None, developer_org_name=None, cluster_instance_name=None, cluster_instance_developer_org_name=None, container_id=None, timeout=120, json_data=None, use_defaults=True, use_thread=False):
        return self.run_cmd.run_command(token=token, region=region, mc_address=self.mc_address, app_name=app_name, app_version=app_version, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, developer_org_name=developer_org_name, cluster_instance_name=cluster_instance_name, cluster_instance_developer_org_name=cluster_instance_developer_org_name, container_id=container_id, command=command, use_defaults=use_defaults, use_thread=use_thread, timeout=timeout)

    def show_logs(self, token=None, region=None, command=None, app_name=None, app_version=None, cloudlet_name=None, operator_org_name=None, developer_org_name=None, cluster_instance_name=None, cluster_instance_developer_org_name=None, container_id=None, since=None, tail=None, time_stamps=None, follow=None, json_data=None, use_defaults=True, use_thread=False):
        return self.run_cmd.show_logs(token=token, region=region, mc_address=self.mc_address, app_name=app_name, app_version=app_version, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, developer_org_name=developer_org_name, cluster_instance_name=cluster_instance_name, cluster_instance_developer_org_name=cluster_instance_developer_org_name, container_id=container_id, since=since, tail=tail, time_stamps=time_stamps, follow=follow, use_defaults=use_defaults, use_thread=use_thread)

    def run_console(self, token=None, region=None, command=None, app_name=None, app_version=None, cloudlet_name=None, operator_org_name=None, developer_org_name=None, cluster_instance_name=None, cluster_instance_developer_org_name=None, container_id=None, json_data=None, use_defaults=True, use_thread=False):
        return self.run_cmd.run_console(token=token, region=region, mc_address=self.mc_address, app_name=app_name, app_version=app_version, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, developer_org_name=developer_org_name, cluster_instance_name=cluster_instance_name, cluster_instance_developer_org_name=cluster_instance_developer_org_name, container_id=container_id, use_defaults=use_defaults, use_thread=use_thread)
    
    def verify_email(self, username=None, password=None, email_address=None, server='imap.gmail.com', wait=30):
        if username is None: username = self.username
        if password is None: password = self.password
        if email_address is None: email_address = self.email_address

        mail = self._mail
        num_emails_pre = self._mail_count
        for attempt in range(wait):
            mail.recent()
            status, email_list = mail.search(None, '(SUBJECT "Welcome to MobiledgeX!")')
            mail_ids = email_list[0].split()
            num_emails = len(mail_ids)
            logging.info(f'number of emails found is {num_emails}')
            if num_emails > num_emails_pre:
                logging.info('new email found')
                mail_id = email_list[0].split()
                typ, data = mail.fetch(mail_id[-1], '(RFC822)')
                for response_part in data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_string(response_part[1].decode('utf-8'))
                        email_subject = msg['subject']
                        email_from = msg['from']
                        date_received = msg['date']
                        payload = msg.get_payload(decode=True).decode('utf-8')
                        logging.info(payload)

                        if f'Hi {username},' in payload:
                            logging.info('greetings found')
                        else:
                            raise Exception('Greetings not found')

                        if 'Thanks for creating a MobiledgeX account! You are now one step away from utilizing the power of the edge. Please verify this email account by clicking on the link below. Then you\'ll be able to login and get started.' in payload:
                            logging.info('body1 found')
                        else:
                            raise Exception('Body1 not found')

                        #if f'Click to verify: {self.console_url}/verify?token=' in payload:
                        if f'Copy and paste to verify your email:' in payload:
                            for line in payload.split('\n'):
                                if 'mcctl user verifyemail token=' in line:
                                    #label, link = line.split('Click to verify:')
                                    self._verify_link = line.rstrip()

                                    cmd = f'docker run registry.mobiledgex.net:5000/mobiledgex/edge-cloud:latest mcctl login --addr https://{self.mc_address} username=mexadmin password=mexadmin123 --skipverify'
                                    logging.info('login with:' + cmd)
                                    self._run_command(cmd)
                                    cmd = f'docker run registry.mobiledgex.net:5000/mobiledgex/edge-cloud:latest {line} --addr https://{self.mc_address} --skipverify '
                                    logging.info('verifying email with:' + cmd)
                                    self._run_command(cmd)

                                    #cmd = line + f'--addr https://{self.mc_address} --skipverify'
                                    #logging.info('verifying email with:' + cmd)
                                    #try:
                                    #    process = subprocess.Popen(shlex.split(cmd),
                                    #                               stdout=subprocess.PIPE,
                                    #                               stderr=subprocess.PIPE,
                                    #    )
                                    #    stdout, stderr = process.communicate()
                                    #    logging.info('verify returned:',stdout, stderr)
                                    #    if stderr:
                                    #        raise Exception('runCommandee failed:' + stderr.decode('utf-8'))
                                    #except subprocess.CalledProcessError as e:
                                    #    raise Exception("runCommanddd failed:", e)
                                    #except Exception as e:
                                    #    raise Exception("runCommanddd failed:", e)


                                    break
                            logging.info('verify link found')
                        else:
                            raise Exception('Verify link not found')

                        if f'For security, this request was received for {email_address} from' in payload and 'If you are not expecting this email, please ignore this email or contact MobiledgeX support for assistance.' in payload and 'Thanks!' in payload and 'MobiledgeX Team' in payload:
                            logging.info('body2 link found')
                        else:
                            raise Exception('Body2 not found')
                        return True
            time.sleep(1)

        raise Exception('verification email not found')

    def _run_command(self, cmd):
        try:
            process = subprocess.Popen(shlex.split(cmd),
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       )
            stdout, stderr = process.communicate()
            logging.info('verify returned:',stdout, stderr)
            print('*WARN*',stdout, stderr)
            if stderr:
                raise Exception('runCommandee failed:' + stderr.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            raise Exception("runCommanddd failed:", e)
        except Exception as e:
            raise Exception("runCommanddd failed:", e)

    def create_cloudlet(self, token=None, region=None, operator_org_name=None, cloudlet_name=None, latitude=None, longitude=None, number_dynamic_ips=None, ip_support=None, platform_type=None, physical_name=None, env_vars=None, crm_override=None, notify_server_address=None, json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        return self.cloudlet.create_cloudlet(token=token, region=region, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, latitude=latitude, longitude=longitude, number_dynamic_ips=number_dynamic_ips, ip_support=ip_support, platform_type=platform_type, physical_name=physical_name, env_vars=env_vars, notify_server_address=notify_server_address, crm_override=crm_override, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)
#        url = self.root_url + '/auth/ctrl/CreateCloudlet'
#
#        payload = None
#        cloudlet = None
#
#        if use_defaults == True:
#            if token == None: token = self.token
#
#        if json_data !=  None:
#            payload = json_data
#        else:
#            cloudlet = Cloudlet(operator_name=operator_name, cloudlet_name=cloudlet_name, latitude=latitude, longitude=longitude, number_dynamic_ips=number_dynamic_ips, ip_support=ip_support, platform_type=platform_type, physical_name=physical_name, env_vars=env_vars, notify_server_address=notify_server_address, crm_override=crm_override).cloudlet
#            cloudlet_dict = {'cloudlet': cloudlet}
#            if region is not None:
#                cloudlet_dict['region'] = region
#
#            payload = json.dumps(cloudlet_dict)
#
#        logger.info('create cloudlet instance on mc at {}. \n\t{}'.format(url, payload))
#
#        def send_message():
 #           self._number_createcloudlet_requests += 1
#
#            try:
#                self.post(url=url, bearer=token, data=payload)
#                
#                logger.info('response:\n' + str(self.resp.status_code) + '\n' + str(self.resp.text))
#
#                if str(self.resp.status_code) != '200':
#                    self._number_createcloudlet_requests_fail += 1
#                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#                if 'Created Cloudlet successfully' not in str(self.resp.text):
#                    raise Exception('ERROR: Cloudlet not created successfully:' + str(self.resp.text))
#                    
#            except Exception as e:
#                self._number_createcloudlet_requests_fail += 1
#                raise Exception("post failed:", e)
#
#            self.prov_stack.append(lambda:self.delete_cloudlet(region=region, token=self.super_token, cloudlet_name=cloudlet['key']['name'], operator_name=cloudlet['key']['operator_key']['name']))
#
#            self._number_createcloudlet_requests_success += 1
#
#            
#        if use_thread is True:
#            t = threading.Thread(target=send_message)
#            t.start()
#            return t
#        else:
#            resp = send_message()
#            return self.decoded_data

    def delete_cloudlet(self, token=None, region=None, operator_org_name=None, cloudlet_name=None, latitude=None, longitude=None, number_dynamic_ips=None, ip_support=None, platform_type=None, physical_name=None, crm_override=None, json_data=None, use_defaults=True, use_thread=False):
        return self.cloudlet.delete_cloudlet(token=token, region=region, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, latitude=latitude, longitude=longitude, number_dynamic_ips=number_dynamic_ips, ip_support=ip_support, platform_type=platform_type, physical_name=physical_name, crm_override=crm_override, use_defaults=use_defaults, use_thread=use_thread)
#
#        url = self.root_url + '/auth/ctrl/DeleteCloudlet'
#
#        payload = None
#        clusterInst = None
#
#        if use_defaults == True:
#            if token == None: token = self.token
#
#        if json_data !=  None:
#            payload = json_data
#        else:
#            cloudlet = Cloudlet(operator_name=operator_name, cloudlet_name=cloudlet_name, latitude=latitude, longitude=longitude, number_dynamic_ips=number_dynamic_ips, ip_support=ip_support, platform_type=platform_type, physical_name=physical_name).cloudlet
#            cloudlet_dict = {'cloudlet': cloudlet}
#            if region is not None:
#                cloudlet_dict['region'] = region
#
#            payload = json.dumps(cloudlet_dict)
#
#        logger.info('delete cloudlet instance on mc at {}. \n\t{}'.format(url, payload))
#
#        def send_message():
#            self._number_deletecloudlet_requests += 1
#
#            try:
#                self.post(url=url, bearer=token, data=payload)
#                logger.info('response:\n' + str(self.resp.status_code) + '\n' + str(self.resp.text))
#
#                if str(self.resp.status_code) != '200':
#                    self._number_deletecloudlet_requests_fail += 1
#                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#                if 'Deleted Cloudlet successfully' not in str(self.resp.text):
#                    raise Exception('ERROR: Cloudlet not deleted successfully:' + str(self.resp.text))
#
#            except Exception as e:
#                self._number_deletecloudlet_requests_fail += 1
#                raise Exception("post failed:", e)
#
#            self._number_deletecloudlet_requests_success += 1
#
#        if use_thread is True:
#            t = threading.Thread(target=send_message)
#            t.start()
#            return t
#        else:
#            resp = send_message()
#            return self.decoded_data

    def update_cloudlet(self, token=None, region=None,  operator_org_name=None, cloudlet_name=None, latitude=None, longitude=None, number_dynamic_ips=None, ip_support=None, platform_type=None, physical_name=None, env_vars=None, crm_override=None, notify_server_address=None, container_version=None, package_version=None, json_data=None, use_defaults=True, use_thread=False):
        return self.cloudlet.update_cloudlet(token=token, region=region, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, number_dynamic_ips=number_dynamic_ips, latitude=latitude, longitude=longitude, ip_support=ip_support, platform_type=platform_type, physical_name=physical_name, container_version=container_version, package_version=package_version, env_vars=env_vars, crm_override=crm_override, notify_server_address=notify_server_address, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def get_cloudlet_metrics(self, token=None, region=None, operator_org_name=None, cloudlet_name=None, selector=None, last=None, start_time=None, end_time=None, json_data=None, use_defaults=True, use_thread=False):
        return self.cloudlet.get_cloudlet_metrics(token=token, region=region, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, selector=selector, last=last, start_time=start_time, end_time=end_time, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

#        url = self.root_url + '/auth/metrics/cloudlet'
#
#        payload = None
#        metric_dict = {}
#
#        if use_defaults == True:
#            if token == None: token = self.token
#
#        if json_data !=  None:
#            payload = json_data
#        else:
#            cloudlet = Cloudlet(operator_name=operator_name, cloudlet_name=cloudlet_name, use_defaults=False).cloudlet
#            print('*WARN*', cloudlet)
#            if 'key' in cloudlet:
#                metric_dict = {'cloudlet': cloudlet['key']}
#            print('*WARN*', 'after cloudlet')
#            if region is not None:
#                metric_dict['region'] = region
#            if selector is not None:
#                metric_dict['selector'] = selector
#            if last is not None:
#                try:
#                    metric_dict['last'] = int(last)
#                except:
#                    metric_dict['last'] = last
#            if start_time is not None:
#                metric_dict['starttime'] = start_time
#            if end_time is not None:
#                metric_dict['endtime'] = end_time
#                
#
#            payload = json.dumps(metric_dict)
#
#        logger.info('get cloudlet metrics on mc at {}. \n\t{}'.format(url, payload))
#
#        def send_message():
#            #self._number_deletecloudlet_requests += 1#
#
#            try:
#                self.post(url=url, bearer=token, data=payload)
#                logger.info('response:\n' + str(self.resp.status_code) + '\n' + str(self.resp.text))
#
#                if str(self.resp.status_code) != '200':
#                    #self._number_deletecloudlet_requests_fail += 1
#                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#
#            except Exception as e:
#                #self._number_deletecloudlet_requests_fail += 1
#                raise Exception("post failed:", e)
#
#            #self._number_deletecloudlet_requests_success += 1
#
#        if use_thread is True:
#            t = threading.Thread(target=send_message)
#            t.start()
#            return t
#        else:
#            resp = send_message()
#            return self.decoded_data

    def add_cloudlet_resource_mapping(self, token=None, region=None, operator_org_name=None, cloudlet_name=None, mapping=None, json_data=None, use_defaults=True, use_thread=False):
        """ Sends region AddCloudletResMapping
        """
        return self.cloudlet.add_cloudlet_resource_mapping(token=token, region=region, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, mapping=mapping, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def add_resource_tag(self, token=None, region=None, resource_name=None, operator_org_name=None, tags=None, json_data=None, use_defaults=True, use_thread=False):
        """ Sends region AddResTag
        """
        return self.cloudlet.add_resource_tag(token=token, region=region, resource_name=resource_name, operator_org_name=operator_org_name, tags=tags, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def get_cluster_metrics(self, token=None, region=None, cluster_name=None, operator_org_name=None, cloudlet_name=None, developer_org_name=None, selector=None, last=None, start_time=None, end_time=None, json_data=None, use_defaults=True, use_thread=False):
      return self.cluster_instance.get_cluster_metrics(token=token, region=region, cluster_name=cluster_name, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, developer_org_name=developer_org_name, selector=selector, last=last, start_time=start_time, end_time=end_time, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)
        
#        url = self.root_url + '/auth/metrics/cluster'
#
#        payload = None
#        metric_dict = {}
#
#        if use_defaults == True:
#            if token == None: token = self.token
#
#        if json_data !=  None:
#            payload = json_data
#        else:
#            cluster = ClusterInstance(cluster_name=cluster_instance_name, operator_name=operator_name, cloudlet_name=cloudlet_name, developer_name=developer_name, use_defaults=False).cluster_instance
#            print('*WARN*', cluster)
#            if 'key' in cluster:
#                metric_dict = {'clusterinst': cluster['key']}
#            if region is not None:
#                metric_dict['region'] = region
#            if selector is not None:
#                metric_dict['selector'] = selector
#            if last is not None:
#                try:
#                    metric_dict['last'] = int(last)
#                except:
#                    metric_dict['last'] = last
#            if start_time is not None:
#                metric_dict['starttime'] = start_time
#            if end_time is not None:
#                metric_dict['endtime'] = end_time
 #               
#
#            payload = json.dumps(metric_dict)
#
#        logger.info('get cluster metrics on mc at {}. \n\t{}'.format(url, payload))
#
#        def send_message():
#            #self._number_deletecloudlet_requests += 1
#
#            try:
#                self.post(url=url, bearer=token, data=payload)
#                logger.info('response:\n' + str(self.resp.status_code) + '\n' + str(self.resp.text))
#
#                if str(self.resp.status_code) != '200':
#                    #self._number_deletecloudlet_requests_fail += 1
#                    raise Exception(f'code={self.resp.status_code}', f'error={self.resp.text}')
#                    #raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#
#            except Exception as e:
#                #self._number_deletecloudlet_requests_fail += 1
#                #raise Exception("post failed:", e)
#                raise Exception(f'code={self.resp.status_code}', f'error={self.resp.text}')
#
#
#            #self._number_deletecloudlet_requests_success += 1
#
#        if use_thread is True:
#            t = threading.Thread(target=send_message)
#            t.start()
#            return t
#        else:
#            resp = send_message()
#            return self.decoded_data

    def get_app_metrics(self, token=None, region=None, app_name=None, app_version=None, cluster_instance_name=None, developer_org_name=None, operator_org_name=None, cloudlet_name=None, selector=None, last=None, start_time=None, end_time=None, json_data=None, use_defaults=True, use_thread=False):
        return self.app_instance.get_app_metrics(token=token, region=region, app_name=app_name, app_version=app_version, cluster_instance_name=cluster_instance_name, developer_org_name=developer_org_name, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, selector=selector, last=last, start_time=start_time, end_time=end_time, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

#        url = self.root_url + '/auth/metrics/app'
#
#        payload = None
#        metric_dict = {}
#
#        if use_defaults == True:
#            if token == None: token = self.token
#
#        if json_data !=  None:
#            payload = json_data
#        else:
#            print('*WARN*', 'xxxx', developer_name)
#            app = AppInstance(app_name=app_name, cluster_instance_name=cluster_name, developer_name=developer_name, operator_name=operator_name, cloudlet_name=cloudlet_name, use_defaults=False).app_instance
#            print('*WARN*', 'app',app)
#            if 'key' in app:
#                metric_dict = {'appinst': app['key']}
#            if region is not None:
#                metric_dict['region'] = region
#            if selector is not None:
#                metric_dict['selector'] = selector
#            if last is not None:
#                try:
#                    metric_dict['last'] = int(last)
#                except:
#                    metric_dict['last'] = last
#            if start_time is not None:
#                metric_dict['starttime'] = start_time
#            if end_time is not None:
#                metric_dict['endtime'] = end_time
#                
#
#            payload = json.dumps(metric_dict)
#
#        logger.info('get app metrics on mc at {}. \n\t{}'.format(url, payload))
#
#        def send_message():
#            #self._number_deletecloudlet_requests += 1
#
#            try:
#                self.post(url=url, bearer=token, data=payload)
#                logger.info('response:\n' + str(self.resp.status_code) + '\n' + str(self.resp.text))
#
#                if str(self.resp.status_code) != '200':
#                    #self._number_deletecloudlet_requests_fail += 1
#                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
#
#            except Exception as e:
#                #self._number_deletecloudlet_requests_fail += 1
#                raise Exception("post failed:", e)
#
#            #self._number_deletecloudlet_requests_success += 1
#
#        if use_thread is True:
#            t = threading.Thread(target=send_message)
#            t.start()
#            return t
#        else:
#            resp = send_message()
#            return self.decoded_data

    def get_dme_metrics(self, token=None, region=None, method=None, app_name=None, developer_org_name=None, app_version=None, cloudlet_name=None, operator_org_name=None, selector=None, last=None, start_time=None, end_time=None, cell_id=None, json_data=None, use_defaults=True, use_thread=False):
        return self.app_instance.get_api_metrics(method=method, token=token, region=region, app_name=app_name, developer_org_name=developer_org_name, app_version=app_version, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, cell_id=cell_id, last=last, start_time=start_time, end_time=end_time, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def get_find_cloudlet_api_metrics(self, token=None, region=None, app_name=None, developer_org_name=None, app_version=None, selector=None, last=None, start_time=None, end_time=None, cell_id=None, json_data=None, use_defaults=True, use_thread=False):
        return self.app_instance.get_api_metrics(method='FindCloudlet', token=token, region=region, app_name=app_name, developer_org_name=developer_org_name, app_version=app_version, cell_id=cell_id, last=last, start_time=start_time, end_time=end_time, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def get_register_client_api_metrics(self, token=None, region=None, app_name=None, developer_org_name=None, app_version=None, selector=None, last=None, start_time=None, end_time=None, cell_id=None, json_data=None, use_defaults=True, use_thread=False):
        return self.app_instance.get_api_metrics(method='RegisterClient', token=token, region=region, app_name=app_name, developer_org_name=developer_org_name, app_version=app_version, cell_id=cell_id, last=last, start_time=start_time, end_time=end_time, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def show_app_instance_client_metrics(self, token=None, region=None, app_name=None, developer_org_name=None, app_version=None, cluster_instance_name=None, operator_org_name=None, cloudlet_name=None, uuid=None, json_data=None, use_defaults=True, use_thread=False):
        return self.app_instance.show_app_instance_client_metrics(token=token, region=region, app_name=app_name, developer_org_name=developer_org_name, app_version=app_version, cluster_instance_name=cluster_instance_name, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, uuid=uuid, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def get_show_app_instance_client_metrics_output(self):
        return self.app_instance.get_show_app_instance_client_metrics()

    def create_autoscale_policy(self, token=None, region=None, policy_name=None, developer_name=None, min_nodes=None, max_nodes=None, scale_up_cpu_threshold=None, scale_down_cpu_threshold=None, trigger_time=None, json_data=None, use_defaults=True, use_thread=False):
        return self.autoscale_policy.create_autoscale_policy(token=token, region=region, policy_name=policy_name, developer_name=developer_name, min_nodes=min_nodes, max_nodes=max_nodes, scale_up_cpu_threshold=scale_up_cpu_threshold, scale_down_cpu_threshold=scale_down_cpu_threshold, trigger_time=trigger_time, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def delete_autoscale_policy(self, token=None, region=None, policy_name=None, developer_name=None, min_nodes=None, max_nodes=None, scale_up_cpu_threshold=None, scale_down_cpu_threshold=None, trigger_time=None, json_data=None, use_defaults=True, use_thread=False):
        return self.autoscale_policy.delete_autoscale_policy(token=token, region=region, policy_name=policy_name, developer_name=developer_name, min_nodes=min_nodes, max_nodes=max_nodes, scale_up_cpu_threshold=scale_up_cpu_threshold, scale_down_cpu_threshold=scale_down_cpu_threshold, trigger_time=trigger_time, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def update_autoscale_policy(self, token=None, region=None, policy_name=None, developer_name=None, min_nodes=None, max_nodes=None, scale_up_cpu_threshold=None, scale_down_cpu_threshold=None, trigger_time=None, json_data=None, use_defaults=False, use_thread=False):
        url = self.root_url + '/auth/ctrl/UpdateAutoScalePolicy'

        payload = None
        policy = None

        if use_defaults == True:
            if token == None: token = self.token

        if json_data !=  None:
            payload = json_data
        else:
            policy = AutoScalePolicy(policy_name=policy_name, developer_name=developer_name, min_nodes=min_nodes, max_nodes=max_nodes,  scale_up_cpu_threshold=scale_up_cpu_threshold, scale_down_cpu_threshold=scale_down_cpu_threshold, trigger_time=trigger_time, use_defaults=use_defaults, include_fields=True).policy
            policy_dict = {'autoscalepolicy': policy}
            if region is not None:
                policy_dict['region'] = region

            payload = json.dumps(policy_dict)

        logger.info('update autoscalepolicy on mc at {}. \n\t{}'.format(url, payload))

        def send_message():
            self._number_updateautoscalepolicy_requests += 1

            try:
                self.post(url=url, bearer=token, data=payload)
                
                logger.info('response:\n' + str(self.resp.status_code) + '\n' + str(self.resp.text))

                if str(self.resp.status_code) != '200':
                    self._number_updateautoscalepolicy_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
                    
            except Exception as e:
                self._number_updateautoscalepolicy_requests_fail += 1
                raise Exception("post failed:", e)

            self._number_updateautoscalepolicy_requests_success += 1

            resp =  self.show_autoscale_policy(region=region, token=self.super_token, policy_name=policy['key']['name'], developer_name=policy['key']['developer'], use_defaults=False)

            return resp

        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            return self.decoded_data

    def show_autoscale_policy(self, token=None, region=None, policy_name=None, developer_name=None, min_nodes=None, max_nodes=None, scale_up_cpu_threshold=None, scale_down_cpu_threshold=None, trigger_time=None, json_data=None, use_defaults=True, use_thread=False):
        url = self.root_url + '/auth/ctrl/ShowAutoScalePolicy'

        payload = None
        policy = None

        if use_defaults == True:
            if token == None: token = self.token

        if json_data !=  None:
            payload = json_data
        else:
            policy = AutoScalePolicy(policy_name=policy_name, developer_name=developer_name, min_nodes=min_nodes, max_nodes=max_nodes,  scale_up_cpu_threshold=scale_up_cpu_threshold, scale_down_cpu_threshold=scale_down_cpu_threshold, trigger_time=trigger_time, use_defaults=use_defaults).policy
            policy_dict = {'autoscalepolicy': policy}
            if region is not None:
                policy_dict['region'] = region

            payload = json.dumps(policy_dict)

        logger.info('show autoscalepolicy on mc at {}. \n\t{}'.format(url, payload))

        def send_message():
            self._number_showautoscalepolicy_requests += 1

            try:
                self.post(url=url, bearer=token, data=payload)
                
                logger.info('response:\n' + str(self.resp.status_code) + '\n' + str(self.resp.text))

                if str(self.resp.status_code) != '200':
                    self._number_showautoscalepolicy_requests_fail += 1
                    raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())
                    
            except Exception as e:
                self._number_showautoscalepolicy_requests_fail += 1
                raise Exception("post failed:", e)

            self._number_showautoscalepolicy_requests_success += 1
            
        if use_thread is True:
            t = threading.Thread(target=send_message)
            t.start()
            return t
        else:
            resp = send_message()
            return self.decoded_data

    def create_operator_code (self, token=None, region=None, operator_org_name=None, code=None, json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        return self.operatorcode.create_operator_code(token=token, region=region, operator_org_name=operator_org_name,code=code, json_data=json_data, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def delete_operator_code (self, token=None, region=None, operator_org_name=None, code=None, json_data=None, use_defaults=True, use_thread=False):
        return self.operatorcode.delete_operator_code(token=token, region=region, operator_org_name=operator_org_name,code=code, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def show_operator_code (self, token=None, region=None, operator_org_name=None, code=None, json_data=None, use_defaults=True, use_thread=False):
        return self.operatorcode.show_operator_code(token=token, region=region, operator_org_name=operator_org_name,code=code, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)


    def create_cloudlet_pool_member(self, token=None, region=None, cloudlet_pool_name=None, operator_org_name=None, cloudlet_name=None, json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        return self.cloudlet_pool_member.create_cloudlet_pool_member(token=token, region=region, cloudlet_pool_name=cloudlet_pool_name, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, json_data=json_data, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def delete_cloudlet_pool_member(self, token=None, region=None, cloudlet_pool_name=None, operator_org_name=None, cloudlet_name=None, json_data=None, use_defaults=True, use_thread=False):
        return self.cloudlet_pool_member.delete_cloudlet_pool_member(token=token, region=region, cloudlet_pool_name=cloudlet_pool_name, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def show_cloudlet_pool_member(self, token=None, region=None, cloudlet_pool_name=None, operator_org_name=None, cloudlet_name=None, json_data=None, use_defaults=True, use_thread=False):
        return self.cloudlet_pool_member.show_cloudlet_pool_member(token=token, region=region, cloudlet_pool_name=cloudlet_pool_name, operator_org_name=operator_org_name, cloudlet_name=cloudlet_name, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def create_cloudlet_pool(self, token=None, region=None, cloudlet_pool_name=None, json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        return self.cloudlet_pool.create_cloudlet_pool(token=token, region=region, cloudlet_pool_name=cloudlet_pool_name, json_data=json_data, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def show_cloudlet_pool(self, token=None, region=None, cloudlet_pool_name=None, json_data=None, use_defaults=True, use_thread=False):
        return self.cloudlet_pool.show_cloudlet_pool(token=token, region=region, cloudlet_pool_name=cloudlet_pool_name, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def delete_cloudlet_pool(self, token=None, region=None, cloudlet_pool_name=None, json_data=None, use_defaults=True, use_thread=False):
        return self.cloudlet_pool.delete_cloudlet_pool(token=token, region=region, cloudlet_pool_name=cloudlet_pool_name, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def create_org_cloudlet_pool(self, token=None, region=None, cloudlet_pool_name=None, org_name=None, json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        return self.org_cloudlet_pool.create_org_cloudlet_pool(token=token, region=region, cloudlet_pool_name=cloudlet_pool_name, org_name=org_name, json_data=json_data, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def show_org_cloudlet_pool(self, token=None, region=None, cloudlet_pool_name=None, org_name=None, json_data=None, use_defaults=True, use_thread=False):
        return self.org_cloudlet_pool.show_org_cloudlet_pool(token=token, region=region, cloudlet_pool_name=cloudlet_pool_name, org_name=org_name, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def delete_org_cloudlet_pool(self, token=None, region=None, cloudlet_pool_name=None, org_name=None, json_data=None, use_defaults=True, use_thread=False):
        return self.org_cloudlet_pool.delete_org_cloudlet_pool(token=token, region=region, cloudlet_pool_name=cloudlet_pool_name, org_name=org_name, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def show_org_cloudlet(self, token=None, region=None, org_name=None, json_data=None, use_defaults=True, use_thread=False):
        return self.org_cloudlet.show_org_cloudlet(token=token, region=region, org_name=org_name, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def create_privacy_policy(self, token=None, region=None, policy_name=None, developer_org_name=None, rule_list=[], json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        return self.privacy_policy.create_privacy_policy(token=token, region=region, policy_name=policy_name, developer_org_name=developer_org_name, rule_list=rule_list, json_data=json_data, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def show_privacy_policy(self, token=None, region=None, policy_name=None, developer_org_name=None, json_data=None, use_defaults=True, use_thread=False):
        return self.privacy_policy.show_privacy_policy(token=token, region=region, policy_name=policy_name, developer_org_name=developer_org_name, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def delete_privacy_policy(self, token=None, region=None, policy_name=None, developer_org_name=None, rule_list=[], json_data=None, use_defaults=True, use_thread=False):
        return self.privacy_policy.delete_privacy_policy(token=token, region=region, policy_name=policy_name, developer_org_name=developer_org_name, rule_list=rule_list, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def update_privacy_policy(self, token=None, region=None, policy_name=None, developer_org_name=None, rule_list=[], json_data=None, use_defaults=True, use_thread=False):
        return self.privacy_policy.update_privacy_policy(token=token, region=region, policy_name=policy_name, developer_org_name=developer_org_name, rule_list=rule_list, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def create_auto_provisioning_policy(self, token=None, region=None, policy_name=None, developer_org_name=None, deploy_client_count=None, deploy_interval_count=None, json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        return self.autoprov_policy.create_autoprov_policy(token=token, region=region, policy_name=policy_name, developer_org_name=developer_org_name, deploy_client_count=deploy_client_count, deploy_interval_count=deploy_interval_count, json_data=json_data, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def show_auto_provisioning_policy(self, token=None, region=None, policy_name=None, developer_org_name=None, json_data=None, use_defaults=True, use_thread=False):
        return self.autoprov_policy.show_autoprov_policy(token=token, region=region, policy_name=policy_name, developer_org_name=developer_org_name, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def delete_auto_provisioning_policy(self, token=None, region=None, policy_name=None, developer_org_name=None, json_data=None, use_defaults=True, use_thread=False):
        return self.autoprov_policy.delete_autoprov_policy(token=token, region=region, policy_name=policy_name, developer_org_name=developer_org_name, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def update_auto_provisioning_policy(self, token=None, region=None, policy_name=None, developer_org_name=None, deploy_client_count=None, deploy_interval_count=None, cloudlet_list=[], json_data=None, use_defaults=True, use_thread=False):
        return self.autoprov_policy.update_autoprov_policy(token=token, region=region, policy_name=policy_name, developer_org_name=developer_org_name, deploy_client_count=deploy_client_count, deploy_interval_count=deploy_interval_count, cloudlet_list=cloudlet_list, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def add_auto_provisioning_policy_cloudlet(self, token=None, region=None, policy_name=None, developer_org_name=None, cloudlet_name=None, operator_org_name=None, json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        return self.autoprov_policy.add_autoprov_policy_cloudlet(token=token, region=region, policy_name=policy_name, developer_org_name=developer_org_name, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, json_data=json_data, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def remove_auto_provisioning_policy_cloudlet(self, token=None, region=None, policy_name=None, developer_org_name=None, cloudlet_name=None, operator_org_name=None, json_data=None, use_defaults=True, auto_delete=True, use_thread=False):
        return self.autoprov_policy.remove_autoprov_policy_cloudlet(token=token, region=region, policy_name=policy_name, developer_org_name=developer_org_name, cloudlet_name=cloudlet_name, operator_org_name=operator_org_name, json_data=json_data, use_defaults=use_defaults, auto_delete=auto_delete, use_thread=use_thread)

    def show_device(self, token=None, region=None, unique_id=None, unique_id_type=None, first_seen_seconds=None, first_seen_nanos=None, last_seen_seconds=None, last_seen_nanos=None, notify_id=None, json_data=None, use_defaults=True, use_thread=False):
        return self.showdevice.show_device(token=token, region=region, unique_id=unique_id, unique_id_type=unique_id_type, first_seen_seconds=first_seen_seconds, first_seen_nanos=first_seen_nanos, last_seen_seconds=last_seen_seconds, last_seen_nanos=last_seen_nanos, notify_id=notify_id, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def show_device_report(self, token=None, region=None, unique_id=None, unique_id_type=None, begin_seconds=None, begin_nanos=None, end_seconds=None, end_nanos=None, notify_id=None, json_data=None, use_defaults=True, use_thread=False):
        return self.showdevicereport.show_device_report(token=token, region=region, unique_id=unique_id, unique_id_type=unique_id_type, begin_seconds=begin_seconds, begin_nanos=begin_nanos, end_seconds=end_seconds, end_nanos=end_nanos, notify_id=notify_id, json_data=json_data, use_defaults=use_defaults, use_thread=use_thread)

    def cleanup_provisioning(self):
        """ Deletes all the provisiong that was added during the test
        """
        if not os.environ.get('AUTOMATION_NO_CLEANUP'):
            logging.info('cleaning up provisioning')
            print(self.prov_stack)
            #temp_prov_stack = self.prov_stack
            temp_prov_stack = list(self.prov_stack)
            temp_prov_stack.reverse()
            for obj in temp_prov_stack:
                logging.debug('deleting obj' + str(obj))
                obj()
                del self.prov_stack[-1]
        else:
            logging.info('cleanup disable since AUTOMATION_NO_CLEANUP is set')

    def wait_for_replies(self, *args):
        """ Waits for operations that were sent in threaded mode to complete
        """
        logging.info(f'waiting on {len(args)} threads')
        failed_thread_list = []

        for x in args:
            if isinstance(x, list):
                for x2 in x:
                    x.join()
            x.join()

        while not self._queue_obj.empty():
            try:
                exec = self._queue_obj.get(block=False)
                logging.error(f'thread {list(exec)[0]} failed with {exec[list(exec)[0]]}')
                failed_thread_list.append(exec)
            except queue.Empty:
                pass

        logging.info(f'number of failed threads:{len(failed_thread_list)}')
        if failed_thread_list:
            raise Exception(f'{len(failed_thread_list)} threads failed:', failed_thread_list)
