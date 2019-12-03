from webservice import WebService
import logging
import json
import sys
import os

#import shared_variables

logging.basicConfig(format='%(asctime)s %(levelname)s %(funcName)s line:%(lineno)d - %(message)s',datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger('mexInfluxDb')

class MexInfluxDB(WebService) :
    #username = 'uiteam'
    #password = 'pa$$word'
    username = 'root'
    password = 'root'

    cluster_db = 'clusterstats'
    cluster_cpu_table = 'cluster-cpu'
    cluster_disk_table = 'cluster-disk'
    cluster_memory_table = 'cluster-mem'
    cluster_network_table = 'cluster-network'
    appinst_cpu_table = 'appinst-cpu'

    metrics_db = 'metrics'
    cloudlet_utilization_table = 'cloudlet-utilization'
    cloudlet_ipusage_table = 'cloudlet-ipusage'
    
    def __init__(self, influxdb_address='localhost:8086', influxdb_username='root', influxdb_password='root'):
        super().__init__(http_trace=True)
        self.influxdb_address = influxdb_address
        if 'http' not in self.influxdb_address:
            self.influxdb_address = f'https://{self.influxdb_address}'

        self.username = influxdb_username
        self.password = influxdb_password
        
    def query_db(self, db, query):
        data = {'u':self.username,
                'p':self.password,
                'db':db,
                'q':query}
        resp = self.get(f'{self.influxdb_address}/query', params=data)

        if str(self.resp.status_code) != '200':
            raise Exception("ws did not return a 200 response. responseCode = " + str(self.resp.status_code) + ". ResponseBody=" + str(self.resp.text).rstrip())

        return resp
    
    def get_cluster_stats(self, cluster_name=None):
        query = f'select * from \"{self.cluster_table}\"'
        if cluster_name:
            query += f' where cluster=\'{cluster_name}\''
        logger.info('query=' + query)

        resp = self.query_db(db=self.cluster_db, query=query)
        self._decode_content()

        print('*WARN*', self.decoded_data['results'][0]['series'][0]['columns'][2])
        print('*WARN*', self.decoded_data['results'][0]['series'][0]['values'][0][2])

        num_columns = len(self.decoded_data['results'][0]['series'][0]['columns'])
        value_list = []
        value_dict = {}
        for value in self.decoded_data['results'][0]['series'][0]['values']:
            for header in range(0,num_columns):
                value_dict[self.decoded_data['results'][0]['series'][0]['columns'][header]] = value[header]
            value_list.append(value_dict.copy())
                              
        #return self.decoded_data['results'][0]['series'][0]['columns'], self.decoded_data['results'][0]['series'][0]['values']
        return value_list

    def get_appinst_metrics(self, table, cluster_instance_name=None, app_name=None, cloudlet_name=None, developer_name=None, operator_name=None, condition=None):
        query = f'select * from \"{table}\"'
        
        if cluster_instance_name:
            query = query + ' and' if 'where' in query else query + ' where'
            query += f' cluster=\'{cluster_instance_name}\''        
        if app_name:
            query = query + ' and' if 'where' in query else query + ' where'
            query += f' app=\'{app_name}\''
        if cloudlet_name:
            query = query + ' and' if 'where' in query else query + ' where'
            query += f' cloudlet=\'{cloudlet_name}\''
        if developer_name:
            query = query + ' and' if 'where' in query else query + ' where'
            query += f' dev=\'{developer_name}\''
        if operator_name:
            query = query + ' and' if 'where' in query else query + ' where'
            query += f' operator=\'{operator_name}\''
        if condition:
            query += f' {condition}'

        logger.info('query=' + query)

        resp = self.query_db(db=self.metrics_db, query=query)
        self._decode_content()
        value_list = self._parse_data()

        return value_list

    def get_appinst_cpu_metrics(self, cluster_instance_name=None, app_name=None, cloudlet_name=None, developer_name=None, operator_name=None, condition=None):
        return self.get_appinst_metrics(table=self.appinst_cpu_table, cluster_instance_name=cluster_instance_name, app_name=app_name, cloudlet_name=cloudlet_name, developer_name=developer_name, operator_name=operator_name, condition=condition)
        
    def get_influx_cloudlet_metrics(self, selector=None, cloudlet_name=None, operator_name=None, condition=None):
        query = f'select * from '
        if selector == 'utilization':
            query += f'\"{self.cloudlet_utilization_table}\"'
        elif selector == 'ipusage':
            query += f'\"{self.cloudlet_ipusage_table}\"'            

        if cloudlet_name:
            query += f' where cloudlet=\'{cloudlet_name}\''
        if operator_name:
            query += f' where operator=\'{operator_name}\''
        if condition:
            query += f' {condition}'
        logger.info('query=' + query)

        resp = self.query_db(db=self.metrics_db, query=query)
        self._decode_content()

        print('*WARN*', self.decoded_data)
        print('*WARN*', self.decoded_data['results'][0]['series'][0]['values'][0][2])

        num_columns = len(self.decoded_data['results'][0]['series'][0]['columns'])
        value_list = []
        value_dict = {}
        for value in self.decoded_data['results'][0]['series'][0]['values']:
            for header in range(0,num_columns):
                value_dict[self.decoded_data['results'][0]['series'][0]['columns'][header]] = value[header]
            value_list.append(value_dict.copy())
                              
        return value_list

    def get_influx_cloudlet_utilization_metrics(self, cloudlet_name=None, operator_name=None, condition=None):
        return self.get_influx_cloudlet_metrics(selector='utilization', cloudlet_name=cloudlet_name, operator_name=operator_name, condition=condition)

    def get_influx_cloudlet_ipusage_metrics(self, cloudlet_name=None, operator_name=None, condition=None):
        return self.get_influx_cloudlet_metrics(selector='ipusage', cloudlet_name=cloudlet_name, operator_name=operator_name, condition=condition)

    def get_influx_cluster_metrics(self, selector=None, cluster_instance_name=None, cloudlet_name=None, operator_name=None, developer_name=None, condition=None):
        query = f'select * from '
        if selector == 'cpu':
            query += f'\"{self.cluster_cpu_table}\"'
        elif selector == 'disk':
            query += f'\"{self.cluster_disk_table}\"'            
        elif selector == 'memory':
            query += f'\"{self.cluster_memory_table}\"'
        elif selector == 'network':
            query += f'\"{self.cluster_network_table}\"'
            
            
        if cluster_instance_name:
            query += f' where cluster=\'{cluster_instance_name}\''
        if cloudlet_name:
            if 'where' in query:
                query += f' and cloudlet=\'{cloudlet_name}\''
            else:
                query += f' where cloudlet=\'{cloudlet_name}\''
        if operator_name:
            if 'where' in query:
                query += f' and' 
            else:
                query += f' where'
            query += f' operator=\'{operator_name}\''
        if developer_name:
            if 'where' in query:
                query += f' and' 
            else:
                query += f' where'
            query += f' dev=\'{developer_name}\''
            
        if condition:
            query += f' {condition}'
        logger.info('query=' + query)

        resp = self.query_db(db=self.metrics_db, query=query)
        self._decode_content()

        print('*WARN*', self.decoded_data)
        print('*WARN*', self.decoded_data['results'][0]['series'][0]['values'][0][1])

        num_columns = len(self.decoded_data['results'][0]['series'][0]['columns'])
        value_list = []
        value_dict = {}
        for value in self.decoded_data['results'][0]['series'][0]['values']:
            for header in range(0,num_columns):
                value_dict[self.decoded_data['results'][0]['series'][0]['columns'][header]] = value[header]
            value_list.append(value_dict.copy())
                              
        return value_list

    def get_influx_cluster_cpu_metrics(self, cluster_instance_name=None, cloudlet_name=None, operator_name=None, developer_name=None, condition=None):
        return self.get_influx_cluster_metrics(selector='cpu', cluster_instance_name=cluster_instance_name, cloudlet_name=cloudlet_name, operator_name=operator_name, developer_name=developer_name, condition=condition)

    def get_influx_cluster_disk_metrics(self, cluster_instance_name=None, cloudlet_name=None, operator_name=None, developer_name=None, condition=None):
        return self.get_influx_cluster_metrics(selector='disk', cluster_instance_name=cluster_instance_name, cloudlet_name=cloudlet_name, operator_name=operator_name, developer_name=developer_name, condition=condition)

    def get_influx_cluster_memory_metrics(self, cluster_instance_name=None, cloudlet_name=None, operator_name=None, developer_name=None, condition=None):
        return self.get_influx_cluster_metrics(selector='memory', cluster_instance_name=cluster_instance_name, cloudlet_name=cloudlet_name, operator_name=operator_name, developer_name=developer_name, condition=condition)

    def get_influx_cluster_network_metrics(self, cluster_instance_name=None, cloudlet_name=None, operator_name=None, developer_name=None, condition=None):
        return self.get_influx_cluster_metrics(selector='network', cluster_instance_name=cluster_instance_name, cloudlet_name=cloudlet_name, operator_name=operator_name, developer_name=developer_name, condition=condition)

    
    def _decode_content(self):
        logging.debug('content=' + self.resp.content.decode("utf-8"))
        
        self.decoded_data = json.loads(self.resp.content.decode("utf-8"))

    def _parse_data(self):
        num_columns = len(self.decoded_data['results'][0]['series'][0]['columns'])
        value_list = []
        value_dict = {}
        for value in self.decoded_data['results'][0]['series'][0]['values']:
            for header in range(0,num_columns):
                value_dict[self.decoded_data['results'][0]['series'][0]['columns'][header]] = value[header]
            value_list.append(value_dict.copy())

        return value_list
