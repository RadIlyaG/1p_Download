import os
import time
from pathlib import Path
import subprocess
import socket
import json


class Gen:
    def __init__(self):
        self.os = os.name
        
    def power(self, ps, state):
        print(f'Power self:{self}, ps:{ps}, state:{state}')
        
        # pio = lib_UsbPio.UsbPio()
        # channel = pio.retrive_usb_channel(main_obj.gaSet['pioBoxSerNum'])
        # print(f'gen power channel:{channel}')

        # group = 'RBA'
        # ret = lib_UsbPio.UsbPio.osc_pio(pio, channel, ps, group, state)

        cmd = f'usbrelay /dev/hidraw1_{str(ps)}={state}'
        print(cmd)
    # for i in range(1,11):
    #     with subprocess
        return 0

    def gui_Power(self, ps, state):
        print(f"gui_Power self:{self},  ps:{ps}, state:{state}")
        self.power(ps, state)

    def gui_PowerOffOn(self, ps):
        self.gui_Power(ps, 0)
        time.sleep(2)
        self.gui_Power(ps, 1)
        
        
    def open_terminal(self, appwin, com_name):
        print(f'open_terminal appwin:{appwin} os:{self.os}')
        if self.os == "nt":
            com = appwin.gaSet[com_name][3:]  # COM8 -> 8 (cut off COM)
            print(f"open_teraterm com_name:{com_name}, com:{com}")

            command = os.path.join('C:/Program Files (x86)', 'teraterm', 'ttermpro.exe')
            command = str(command) + ' /c=' + str(com) + ' /baud=115200'
            # os.startfile(command)
            subprocess.Popen(command)
            print(command)
        else:
            pass
            
    def read_hw_init(self, gui_num, ip):
        print(f'read_hw_init {self}, {gui_num}, {ip}')
        host = ip.replace('.', '_')
        Path(host).mkdir(parents=True, exist_ok=True)
        hw_file = Path(os.path.join(host, f"HWinit.{gui_num}.json"))
        if not os.path.isfile(hw_file):
            hw_dict = {
                'comDut': 'COM1',
                'pioBoxSerNum': "FT31CTG9",
            }
            # di = {**hw_dict, **dict2}

            with open(hw_file, 'w') as fi:
                # json.dump(hw_dict, fi, indent=2, sort_keys=True)
                json.dump(hw_dict, fi, indent=2, sort_keys=True)

        try:
            with open(hw_file, 'r') as fi:
                hw_dict = json.load(fi)
        except Exception as e:
            # print(e)
            # raise(e)
            raise Exception("e")

        return hw_dict

    def read_init(self, appwin, gui_num, ip):
        print(f'read_init, self:{self}, appwin:{appwin}, gui_num:{gui_num}, ip:{ip}')
        # print(f'read_init script_dir {os.path.dirname(__file__)}')
        host = ip.replace('.', '_')
        Path(host).mkdir(parents=True, exist_ok=True)
        ini_file = Path(os.path.join(host, "init." + str(gui_num) + ".json"))
        if os.path.isfile(ini_file) is False:
            dicti = {
                'geom': '+210+210'
            }
            self.save_init(appwin)

        try:
            with open(ini_file, 'r') as fi:
                dicti = json.load(fi)
        except Exception as e:
            # print(e)
            # raise(e)
            raise Exception("e")

        print(f'read_init {ini_file} {dicti}')
        return dicti

    def save_init(self, appwin):
        print(f'save_init, self:{self}, appwin:{appwin}')
        ip = appwin.gaSet['pc_ip']
        host = ip.replace('.', '_')
        gui_num = appwin.gaSet['gui_num']
        Path(host).mkdir(parents=True, exist_ok=True)
        ini_file = Path(os.path.join(host, "init." + str(gui_num) + ".json"))

        di = {}
        try:
            # di['geom'] = "+" + str(dicti['root'].winfo_x()) + "+" + str(dicti['root'].winfo_y())
            geom = self.get_xy(appwin)
        except:
            geom = "+230+233"
        di['geom'] = geom
        print(f'save_init, geom:{geom}')
        try:
            with open(ini_file, 'w') as fi:
                json.dump(di, fi, indent=2, sort_keys=True)
                # json.dump(gaSet, fi, indent=2, sort_keys=True)
        except Exception as e:
            print(e)
            raise (e)

    def get_xy(self, top):
        print('get_xy', top)
        return str("+" + str(top.winfo_x()) + "+" + str(top.winfo_y()))
            
