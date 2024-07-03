import ssl
import socket
import requests
import json
import certifi
import urllib3
import urllib.parse
import re
import xmltodict
import subprocess
import sqlite3
from sqlite3 import Error
# import paramiko
from datetime import datetime
from subprocess import CalledProcessError, check_output


class GetSWVersions:
    def __init__(self):
        self.url = 'http://ws-proxy01.rad.com:8081/ExtAppsWS/Proxy/Select'
        self.data_obj = {'queryName': 'qry.get.sw.for_idNumber_2', 'db': 'inventory'}

    def gets_sw(self, id_barcode):
        """

        @type id_barcode: ID Barcode, may be 11 or 12 digits
        """
        self.data_obj['params'] = id_barcode[:11]

        http = urllib3.PoolManager()
        encoded_args = urllib.parse.urlencode(self.data_obj)
        url = self.url + "/?" + encoded_args
        try:
            resp = http.request('POST', url)
        except Exception as e:
            return False, f'Failed to connect to {url}, {e}'

        print(resp.data)
        print(f'resp.status:{resp.status}')
        # print(f'r.data:<{resp.data.decode()}>')
        data = resp.json()
        # print(f'r.text:<{data}>')
        if len(data) == 0:
            return False, f"No SW for {id}"
        return True, data

        # r = requests.post(self.url, data=self.data_obj)
        # # print(r.text)
        # data = json.loads(r.text)
        # # print(f'data:{data} {len(data)}')
        # if len(data)==0:
        #     return False, f"No SW for {id}"
        # return True, data


class MacReg:
    def __init__(self):
        self.hostname = 'ws-proxy01.rad.com'
        self.port = '8445'
        self.path = '/MacRegREST/MacRegExt/ws/'
        self.data_obj = {}

    def connect(self):
        context = ssl.create_default_context()
        try:
            with socket.create_connection((self.hostname, self.port)) as sock:
                # print(f'connect url:{url}')
                return True, True
        except Exception as e:
            return False, f'Failed to connect to {self.hostname}:{self.port}, {e}'

    def check_mac(self, id_barcode, mac):
        """Check if id_barcode is connected to mac
        1. Returns 0 if both connected to each other
        2. Returns 0 if both not connected to any other
        3. Returns message regarding existing connections:
            0020D2268EAA is already connected to CB100035563
            IO3001930212 is already connected to 0020D2640B22
        """
        ret = ''
        short_id = id_barcode[:11]
        res, connected_id = self.chk_connection_to_mac(mac)
        if not res:
            return connected_id
        res, connected_mac = self.chk_connection_to_id(short_id)
        if not res:
            return connected_mac
        print(f'check_mac input_id:{short_id}, to {mac} connected id:{connected_id}')
        print(f'check_mac input_mac:{mac}, to {short_id} connected mac:{connected_mac}')
        if connected_id == short_id and connected_mac == mac:
            return 0
        if connected_id == 'nc' and connected_mac == 'nc':
            return 0
        if connected_id != 'nc' and connected_id != short_id:
            ret += f'{mac} is already connected to {connected_id}\n'
        if connected_mac != 'nc' and connected_mac != mac:
            ret += f'{id_barcode} is already connected to {connected_mac}\n'
        return ret

    def chk_connection_to_mac(self, mac):
        res, resTxt = self.connect()
        if not res:
            return res, resTxt

        self.data_obj = {'macID': mac}
        url = 'https://' + self.hostname + ':' + self.port + self.path + 'q001_mac_extant_chack'
        r = requests.post(url, data=self.data_obj)
        # print(r.text)
        data = json.loads(r.text)
        # print(f"data:<{data['q001']}> {type(data['q001'])} {len(data['q001'])}")
        if len(data['q001']) == 0:
            return True, 'nc'
        else:
            return True, data['q001'][0]['id_number']

    def chk_connection_to_id(self, id_barcode):
        res, resTxt = self.connect()
        if not res:
            return res, resTxt

        self.data_obj = {'idNumber': id_barcode}
        url = 'https://' + self.hostname + ':' + self.port + self.path + 'q003_idnumber_extant_check'
        r = requests.post(url, data=self.data_obj)
        # print(r.text)
        data = json.loads(r.text)
        # print(f"data:<{data['q003']}> {type(data['q003'])} {len(data['q003'])}")
        if len(data['q003']) == 0:
            return True, 'nc'
        else:
            return True, data['q003'][0]['mac']

    def q002_get_idnumber_data(self, idnumber):
        self.data_obj = {'idnumber': idnumber[:11]}
        url = 'https://' + self.hostname + ':' + self.port + self.path + 'q002_get_idnumber_data'
        # print(url)
        r = requests.post(url, data=self.data_obj)
        # print(r.text)

    def q001_get_current_mac(self):
        self.data_obj = {}
        url = 'https://' + self.hostname + ':' + self.port + self.path + 'q001_get_current_mac'
        # r = requests.post(url, data=self.data_obj)
        print('r.text')

    def calc_control_digit(self, id_barcode):
        barcode = id_barcode[3:-1]  # DF1002704216 -> 100270421
        temp = 0
        if len(barcode) < 8:
            return True

        for i in range(0, len(barcode)):
            if i % 2 == 0:
                temp += int(barcode[i]) * 3
            else:
                temp += int(barcode[i])
            # print(id_barcode, barcode[i], temp)

        temp = 10 - (temp % 10)
        if temp == 10:
            return 0
        else:
            return temp

    def mac_server(self, qty):
        res, resTxt = self.connect()
        if not res:
            return res, resTxt

        self.data_obj = {'p_mode': '0', 'p_trace_id': '0', 'p_serial': '0', 'p_idnumber_id': '0',
                         'p_alloc_qty': str(qty), 'p_file_version': '1'}
        url = 'https://' + self.hostname + ':' + self.port + self.path + 'sp001_mac_address_alloc'
        r = requests.post(url, data=self.data_obj)
        #print(r.text)
        data = json.loads(r.text)
        data = data["sp001_mac_address_alloc"][0]
        if data['Error']=='0':
            res = True
        else:
            ret = False
        new_mac = data['New_MAC_Address']
        #print(f'data:<{data["sp001_mac_address_alloc"][0]}>')
        return res, (new_mac, qty)




class SoapWS(MacReg):
    def __init__(self):
        self.pages_dict = {'Page0': 'NA', 'Page1': 'NA', 'Page2': 'NA', 'Page3': 'NA'}
        self.pages_type = 'list'

    def get_pages(self, id_barcode, trace_id='', macs_qty=10):
        """Gets ready XML form, supplies ID number (as string), Traceability ID Number (or '' or integer or string)"""

        mr_obj = MacReg()
        r1 = mr_obj.calc_control_digit(id_barcode)
        print(r1)
        url = 'http://ws-proxy01.rad.com:10211/Pages96WS/services/MacWS'
        # headers = {'content-type': 'application/soap+xml'}
        headers = {'content-type': 'text/xml', 'SOAPAction': ''}
        body = """<soapenv:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:mod="http://model.macregid.webservices.rad.com">
   <soapenv:Header/>
   <soapenv:Body>
      <mod:get_Data_4_Dallas soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
         <ParamStr1 xsi:type="xsd:string">"""
        body += str(2)
        body += """</ParamStr1>
         <ParamStr2 xsi:type="xsd:string">"""
        body += id_barcode
        body += """</ParamStr2>
         <ParamStr3 xsi:type="xsd:string">"""
        body += str(macs_qty)
        body += """</ParamStr3>
         <ParamStr4 xsi:type="xsd:string">"""
        body += str(trace_id)
        body += """</ParamStr4>  
      </mod:get_Data_4_Dallas>
   </soapenv:Body>
</soapenv:Envelope>"""

        try:
            response = requests.post(url, data=body, headers=headers)
        except Exception as e:
            return False, f'Failed to connect to {url}, {e}'
        # print(type(response.content), response.content)
        data_dict = xmltodict.parse(response.content)
        # print(data_dict)
        if 'ns1:get_Data_4_DallasResponse' not in data_dict['soapenv:Envelope']['soapenv:Body']:
            # print(f"soapenv:Body {data_dict['soapenv:Envelope']['soapenv:Body']}")
            return False, f"Failed to get Pages for ID:{id} TraceID:{trace_id}"
        for page in range(0, 4):
            page_data = (
            data_dict['soapenv:Envelope']['soapenv:Body']['ns1:get_Data_4_DallasResponse']['get_Data_4_DallasReturn'][
                'get_Data_4_DallasReturn'][page]['#text'])
            # print(f'page_data:{page_data}')
            if 'ERROR' in page_data:
                return False, page_data

            page_data = list(page_data.split(' '))[3:]
            if self.pages_type != 'list':
                page_data = ' '.join(page_data)
            # print(type(page_data), page_data)
            self.pages_dict[f'Page{page}'] = page_data

        return True, self.pages_dict


class WebServices:
    def __init__(self):
        self.headers = {'Authorization': 'Basic d2Vic2VydmljZXM6cmFkZXh0ZXJuYWw='}
        self.tcc_db_path = '//prod-svm1/tds/Temp/SQLiteDB/'
        self.tcc_db_file = 'JerAteStats.db'
        self.print_rtext = True
        self.url = ''
        self.dict_key = ''
        self.dict_val = ''

        self.partial_url = ''
        self.param_name = ''  # for use in err_msg = {self.dict_val: f"Fail to get {self.param_name} for {self.in_par}"}
        self.in_par = ''      # for use in err_msg

    def connect(self, command):
        if command == "update_tcc_db":
            self.hostname = 'webservices03.rad.com'
            self.port = '10211'  # '10211'
            self.path = '/ATE_WS/ws/tcc_rest/'
            url = 'http://'
        else:
            self.hostname = 'ws-proxy01.rad.com'
            self.port = '8445'  # '10211'  # '8445'
            self.path = '/ATE_WS/ws/rest/'
            url = 'https://'

        # context = ssl.create_default_context()
        url += self.hostname + ':' + self.port + self.path
        try:
            with socket.create_connection((self.hostname, self.port)):
                # print(f'connect url:{url}')
                return True, url
        except Exception as e:
            return False, {self.dict_val: f'Failed to connect to {self.hostname}:{self.port}, {e}'}

    def get_data(self):
        # print(f'get_data {self.url}')
        err_msg = {self.dict_val: f"Fail to get {self.param_name} for {self.in_par}"}
        r = requests.get(self.url, headers=self.headers, verify=False)
        if self.print_rtext:
            print(f'r.text:<{r.text}>')
        if len(r.text) == 0:
            return False, err_msg
        if re.search('Status 40', r.text):
            return False, err_msg
        if re.search('null', r.text):
            return False, err_msg

        if re.search("DisconnectBarcode", self.url):
            return True, {self.in_par: r.text}

        data = json.loads(r.text)
        # print(f'data:{data}')
        inside_data = data[self.dict_key]
        # print(f'inside_data:{inside_data} type(inside_data):{type(inside_data)} len(inside_data):{len(inside_data)}')
        if len(inside_data) == 0:
            return False, err_msg
        else:
            return True, inside_data[0]

    def get_data_cert(self):
        # print(f'get_data_cert {self.url}')
        data = {}
        err_msg = {self.dict_val: f"Fail to get {self.param_name} for {self.in_par}"}
        http = urllib3.PoolManager(
            cert_reqs="CERT_REQUIRED",
            ca_certs=certifi.where()
        )

        resp = http.request('GET', self.url, headers=self.headers)
        print(f'resp.status:{resp.status}')
        if resp.status != 200:
            return False, err_msg

        if self.print_rtext:
            print(f'r.data:<{resp.data.decode()}>')
        if re.search("DisconnectBarcode", self.url):
            return True, {self.in_par: resp.data.decode()}
        if self.print_rtext:
            print(f'r.text:<{data}>')
        data = resp.json()

        inside_data = data[self.dict_key]
        # print(f'inside_data:{inside_data} type(inside_data):{type(inside_data)} len(inside_data):{len(inside_data)}')
        if len(inside_data) == 0:
            return False, err_msg
        else:
            if 'null' in inside_data[0].values():
                return False, err_msg
            return True, inside_data[0]

    def retrieve_mkt_number(self, dbr_assm):
        """Gets DbrAssemblyName and returns tuple (True/False, MarketingNumber/ErrorText)"""
        self.dict_key = 'MKTPDNByDBRAssembly'
        self.dict_val = 'MKT_PDN'
        self.in_par = dbr_assm
        partial_url = self.dict_key + '?dbrAssembly=' + dbr_assm
        self.param_name = 'Marketing Number'

        res, url = self.connect('MKTPDNByDBR')
        # print(f'retrieve_mktPdn res:{res} url:{url}')
        if res:
            self.url = url + partial_url
            return self.get_data_cert()
        else:
            return False, url

    def retrieve_oi4barcode(self, id_barcode):
        """Gets ID Barcode (11 or 12 chars) and returns tuple (True/False, DbrAssemblyName/ErrorText)"""
        id_barcode = id_barcode[:11]  # OI4Barcode gets only 11 characters
        self.dict_key = 'OperationItem4Barcode'
        self.dict_val = 'item'
        self.in_par = id_barcode
        partial_url = self.dict_key + '?barcode=' + id_barcode + '&traceabilityID=null'
        self.param_name = 'DBR Assembly Name'

        res, url = self.connect('OI4Barcode')
        # print(f'retrieve_oi4barcode res:{res} url:{url}')
        if res:
            self.url = url + partial_url
            return self.get_data_cert()
        else:
            return False, url

    def retrieve_csl(self, id_barcode):
        """Gets ID Barcode (11 or 12 chars) and returns tuple (True/False, CSL/ErrorText)"""
        id_barcode = id_barcode[:11]  # gets only 11 characters
        self.dict_key = 'CSLByBarcode'
        self.dict_val = 'CSL'
        self.in_par = id_barcode
        partial_url = self.dict_key + '?barcode=' + id_barcode + '&traceabilityID=null'
        self.param_name = 'CSL'

        res, url = self.connect('CSLByBarcode')
        if res:
            self.url = url + partial_url
            return self.get_data_cert()
        else:
            return False, url

    def retrieve_mkt_name(self, id_barcode):
        """Gets ID Barcode (11 or 12 chars) and returns tuple (True/False, CSL/ErrorText)"""
        id_barcode = id_barcode[:11]  # gets only 11 characters
        self.dict_key = 'MKTItem4Barcode'
        self.dict_val = 'MKT Item'
        self.in_par = id_barcode
        partial_url = self.dict_key + '?barcode=' + id_barcode + '&traceabilityID=null'
        self.param_name = 'MKT Item'

        res, url = self.connect('MKTItem4Barcode')
        if res:
            self.url = url + partial_url
            return self.get_data_cert()
        else:
            return False, url

    def unreg_id_mac(self, id_barcode, mac=''):
        # '''Gets ID Barcode (11 or 12 chars) and returns tuple (True/False, CSL/ErrorText)'''
        id_barcode = id_barcode[:11]  # gets only 11 characters
        self.dict_key = 'DisconnectBarcode'
        self.dict_val = 'Disconnect Barcode'
        self.in_par = id_barcode
        partial_url = self.dict_key + '?mac=' + mac + '&idNumber=' + id_barcode
        self.param_name = 'Disconnect Barcode'

        res, url = self.connect('DisconnectBarcode')
        if res:
            self.url = url + partial_url
            return self.get_data_cert()
        else:
            return False, url

    def retrieve_traceId_data(self, id_barcode):
        self.dict_key = 'PCBTraceabilityIDData'
        self.dict_val = 'pcb'
        self.in_par = id_barcode
        partial_url = self.dict_key + '?barcode=null&traceabilityID=' + id_barcode
        self.param_name = 'PCB Data'

        res, url = self.connect('PCBTraceabilityIDData')
        if res:
            self.url = url + partial_url
            return self.get_data_cert()
        else:
            return False, url

    def update_db(self):
        print(f'update_db {self.url}')
        err_msg = f"Fail to update {self.tcc_db_path}{self.tcc_db_file}"
        r = requests.get(self.url, headers=self.headers, verify=False)
        print(f'r.text:<{r.text}>')
        if len(r.text) == 0:
            return True, ""
        if re.search('Status 40', r.text):
            return False, err_msg

    def update_tcc_db(self, id_barcode, uut_name, host_description, date, time, status, fail_tests_list,
                      fail_description, dealt_by_server, trace_id, po_number, data1="", data2="", data3=""):
        self.dict_val = 'some_val'
        self.param_name = 'param_name'
        self.in_par = 'in_par'
        res, url = self.connect('update_tcc_db')
        print(f'update_tcc_db res_of_connect:{res}')
        if res:
            url += ('add_row2_with_db?barcode=' + id_barcode + '&uutName=' + uut_name +
                    '&hostDescription=' + host_description + '&date=' + date + '&time=' +
                    time + '&status=' + status + '&failTestsList=' + fail_tests_list +
                    '&failDescription=' + fail_description + '&dealtByServer=' + dealt_by_server +
                    '&dbPath=' + self.tcc_db_path + '&dbName=' + self.tcc_db_file + '&traceID=' + str(trace_id) +
                    '&poNumber=' + str(po_number) + '&data1=' + data1 + '&data2=' + data2 + '&data3=' + data3)
            url = urllib.parse.quote(url, safe='&:/=?')
            print(f'update_tcc_db url:{url}')
            if res:
                self.url = url
                return self.update_db()
            else:
                return False, url
        else:
            return False, "Failed to connect to TCC DB"


if __name__ == '__main__':
    if True:
        mr = MacReg()
        for barc in ['EA1004489579', 'EA1004489579', 'IO3001930212', 'FP2000796994']:
            # print(f'{barc} cd: {mr.calc_control_digit(barc)}')
            pass
        print(mr.mac_server(0))
        # mr.q002_get_idnumber_data('EA1004489579') # returns "id": 12535174
        # mr.q002_get_idnumber_data('FB1000F5815')  # returns ""
        # mr.q002_get_idnumber_data('DC1002331131')  # returns "id": 17297868

        # mr.q001_get_current_mac()

    if False:
        gswv = GetSWVersions()
        res, sw_l = gswv.gets_sw("DC10023311315")
        print(res, sw_l)

    if False:
        sws = SoapWS()
        sws.pages_type = 'str'  # 'list' 'str'
        # 'DF100265011', "21181408", 'DF1002704164' '21449941'
        # res, p_dict = sws.get_pages('DF1002704164', "", 10)
        # if res:
        #     print(p_dict['Page3'])
        # else:
        #     print(p_dict)
        # res, p_dict = sws.get_pages('DF1002704164', 21449941, 10)
        # if res:
        #     print(p_dict['Page3'])

        res, p_dict = sws.get_pages('IO3001960310', "50190576", 10)
        if res:
            print(p_dict['Page3'])
        else:
            print(p_dict)

    if False:
        ws = WebServices()
        ws.print_rtext = False

        # regular unit ETX-203AX_BYT/N/GE30/1SFP1UTP/2UTP2SFP DF100265011
        # ER / RDC  SF-1P/ER/RDC/4U2S/2RSM/LG/G/LG/2R  DC100232838
        res, dicti = ws.retrieve_mkt_number('ETX-203AX_BYT/N/GE30/1SFP1UTP/2UTP2SFP')
        # print(type(res), type(dicti))
        print(res, dicti['MKT_PDN'])
        # print(type(res), type(dicti))
        res, dicti = ws.retrieve_oi4barcode('DC100232838')
        # print(type(res), type(dicti))
        print(res, dicti['item'])
        res, dicti = ws.retrieve_csl('DC100232838')
        # print(type(res), type(dicti))
        print(res, dicti['CSL'])
        res, dicti = ws.retrieve_mkt_name('DF100265011')
        # print(type(res), type(dicti))
        print(res, dicti['MKT Item'])
        res, dicti = ws.retrieve_traceId_data('21181408')
        # print(res, type(dicti))
        if res:
            print(dicti['po number'], dicti['pcb_pdn'], dicti['pcb'])
        else:
            print(dicti)
        res, dicti = ws.unreg_id_mac('EA1004489579')
        print(res, dicti)  # 'EA1004489579'

    if False:
        import os
        from App_1pDownload import App

        app = App(1)
        if os.name == "nt":
            host = socket.gethostname()
        else:
            host = app.get_pc_ip().replace('.', '_')
        # host = ip.replace('.', '_')
        now = datetime.now()
        date = now.strftime("%Y.%m.%d")
        time = now.strftime("%H:%M:%S")
        ws = WebServices()
        res, txt = ws.update_tcc_db('DE1005790454', 'IlyaGinzburg', host, date, time, 'Pass',
                                    'failTestsList', "sadas", 'ILYAG INZBURG',
                                    12345678, 10987, "data1", 'data2')
        print(res, txt)


