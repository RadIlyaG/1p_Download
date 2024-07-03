#!/usr/bin/python3
print('jjj')

import re
import os
import sys
import functools
from functools import partial
import glob
from subprocess import check_output
from PIL import Image, ImageTk

import tkinter as tk
from tkinter import ttk
import socket

import lib_gen_1pDownload as lib_gen
# import Main_1pDownload as main


class App(tk.Tk):
    '''Create the application on base of tk.Tk, put the frames'''
    def __init__(self, gui_num):
        super().__init__()
        self.gaSet = {}
        self.title(f'{gui_num}: 1p Download Tool')
        self['relief'] = tk.GROOVE
        self['bd'] = 2
        
        self.os = os.name
        self.gen = lib_gen.Gen()
        ip = self.get_pc_ip()
        self.gaSet['gui_num'] = gui_num
        self.gaSet['pc_ip'] = ip
        hw_dict = self.gen.read_hw_init(gui_num, ip)
        ini_dict = self.gen.read_init(self, gui_num, ip)
        self.gaSet = {**hw_dict, **ini_dict}
        self.gaSet['gui_num'] = gui_num
        self.gaSet['pc_ip'] = ip
        self.gaSet['root'] = self
        self.if_rad_net()
        
        self.put_frames()
        self.put_menu()
        self.gui_num = gui_num

        print(self.gaSet['geom'])
        self.geometry(self.gaSet['geom'])

        self.status_bar_frame.status("Scan UUT barcode to start")
        
    def put_frames(self):
        mainapp = self
        self.main_frame = MainFrame(self, mainapp)
        self.status_bar_frame = StatusBarFrame(self, mainapp)
        
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=2, pady=2)
        self.status_bar_frame.pack(expand=True, fill='x')
        
    def put_menu(self):
        self.config(menu=MainMenu(self))
        
    def quit(self):
        print(quit, self)
        self.gen.save_init(self)
        db_dict = {
            "title": "Confirm exit",
            "message": "Are you sure you want to close the application?",
            "type": ["Yes", "No"],
            "icon": "::tk::icons::question",
            'default': 0
        }
        string, res_but, ent_dict = DialogBox(self, db_dict).show()
        print(string, res_but)
        if res_but == "Yes":
            for f in glob.glob("SW*.txt"):
                os.remove(f)
            self.destroy()
            # ?? no sys ??? sys.exit()
            
    def get_pc_ip(self):
        if self.os == "posix":
            ip = check_output(['hostname', '--all-ip-addresses']).decode().split(' ')[1]
        else:
            ip = socket.gethostbyname_ex(socket.gethostname())[2][0]
            
        print(f'get_pc_ip ip:{ip}')
        return ip
            
    def if_rad_net(self):
        rad_net = False
        ip = self.gaSet['pc_ip']
        if re.search('192.115.243', ip) or re.search('172.18.9', ip):
            rad_net = True
        self.gaSet['rad_net'] = rad_net  
        
                
class MainMenu(tk.Menu):
    def __init__(self, appwin):
        super().__init__(appwin) 
                
        file_menu = tk.Menu(self, tearoff=0)
        file_menu.add_command(label="Capture Console")
        file_menu.add_separator()
        file_menu.add_cascade(label="Quit", command=appwin.quit)
        self.add_cascade(label="File", menu=file_menu)
        
        tools_menu = tk.Menu(self, tearoff=0)
        tools_menu.add_command(label="Setup Downloaded Package")
        tools_menu.add_separator()
        self.pwr_menu = tk.Menu(tools_menu, tearoff=0)
        self.pwr_menu.add_command(label="PS ON", command=lambda: appwin.gen.gui_Power(1, 1))
        self.pwr_menu.add_command(label="PS OFF", command=lambda: appwin.gen.gui_Power(1, 0))
        self.pwr_menu.add_command(label="PS OFF and ON", command=lambda: appwin.gen.gui_PowerOffOn(1))
        tools_menu.add_cascade(label="Power", menu=self.pwr_menu)
        self.add_cascade(label="Tools", menu=tools_menu)
        
        terminal_menu = tk.Menu(self, tearoff=0)
        terminal_menu.add_command(label=f"UUT: {appwin.gaSet['comDut']}",
                             command=lambda: appwin.gen.open_terminal(appwin, "comDut"))
        self.add_cascade(label="Terminal", menu=terminal_menu)

        chk_menu = tk.Menu(self, tearoff=0)
        chk_menu.add_command(label="chk status",
                                  command=lambda: appwin.status_bar_frame.status("comDut", 'green'))
        chk_menu.add_command(label="chk startTime",
                             command=lambda: appwin.status_bar_frame.start_time("11:13:14 23/12/2024"))
        chk_menu.add_command(label="chk runTime",
                             command=lambda: appwin.status_bar_frame.run_time("1234"))
        self.add_cascade(label="checks", menu=chk_menu)
        
class MainFrame(tk.Frame):
    '''Create the Main Frame on base of tk.Frame'''
    def __init__(self, parent, mainapp):
        super().__init__(parent)
        print(f'MainFrame, self:<{self}>, parent:<{parent}>')
        self['relief'] = self.master['relief']
        # self['bd'] = self.master['bd']
        self.put_main_frames(mainapp)
        
    def put_main_frames(self, mainapp):
        self.frame_start_from = StartFromFrame(self, mainapp)
        self.frame_info = InfoFrame(self, mainapp)
        self.frame_barcodes = BarcodesFrame(self, mainapp)
        
        self.frame_start_from.grid(row=0, column=0, columnspan=2, sticky="news")
        self.frame_info.grid(row=1, column=0, sticky="news", padx=2, pady=2)
        self.frame_barcodes.grid(row=1, column=1, sticky="news", padx=2, pady=2)
        
    def put_widgets(self):
        pass
        
class StartFromFrame(tk.Frame):
    '''Create the StartFrom Frame on base of tk.Frame'''
    def __init__(self, parent, mainapp):
        super().__init__(parent)
        print(f'StartFromFrame, self:<{self}>, parent:<{parent}>')
        self.parent = parent
        self['relief'] = self.master['relief']
        self['bd'] = self.master['bd']
        self.put_widgets()

    def put_widgets(self):
        self.lab_start_from = ttk.Label(self, text="Start from ")
        self.cb_start_from = ttk.Combobox(self)

        script_dir = os.path.dirname(__file__)
        self.img = Image.open(os.path.join(script_dir, "images", "run1.gif"))
        use_img = ImageTk.PhotoImage(self.img)
        self.b_start = ttk.Button(self, text="Start", image=use_img)
        self.b_start.image = use_img

        self.img = Image.open(os.path.join(script_dir, "images", "stop1.gif"))
        use_img = ImageTk.PhotoImage(self.img)
        self.b_stop = ttk.Button(self, text="Stop", image=use_img)
        self.b_start.b_stop = use_img
        
        self.lab_start_from.pack(side='left', padx='2')
        self.cb_start_from.pack(side='left', padx='2')
        self.b_start.pack(side='left', padx='2')
        self.b_stop.pack(side='left', padx='2')

    
class InfoFrame(tk.Frame):
    '''Create the Info Frame on base of tk.Frame'''
    def __init__(self, parent, mainapp):
        super().__init__(parent)
        print(f'InfoFrame, self:<{self}>, parent:<{parent}>')
        self['relief'] = self.master['relief']
        self.put_widgets()
        
    def put_widgets(self):
        self.lab_act_package_txt = ttk.Label(self, text='Package:')
        self.lab_act_package_val = ttk.Label(self, text='Package.val')
        self.lab_sw_txt = ttk.Label(self, text='SW Ver.: xxx')
        self.lab_sw_val = ttk.Label(self, text='SW Ver.val')
        self.lab_flash_txt = ttk.Label(self, text='Flash Image:')
        self.lab_flash_val = ttk.Label(self, text='Flash Image.val')
        
        self.lab_act_package_txt.grid(row=0, column=0, sticky='w', padx=2, pady=2)
        self.lab_act_package_val.grid(row=0, column=1, sticky='e', padx=2, pady=2)
        self.lab_sw_txt.grid(row=1, column=0, sticky='w', padx=2, pady=2)
        self.lab_sw_val.grid(row=1, column=1, sticky='e', padx=2, pady=2)
        self.lab_flash_txt.grid(row=2, column=0, sticky='w', padx=2, pady=2)
        self.lab_flash_val.grid(row=2, column=1, sticky='e', padx=2, pady=2)

        
class BarcodesFrame(tk.Frame):
    '''Create the Barcodes Frame on base of tk.Frame'''
    def __init__(self, parent, mainapp):
        super().__init__(parent)
        self['relief'] = self.master['relief']
        self['bd'] = self.master['bd']
        print(f'BarcodesFrame, self:<{self}>, parent:<{parent}>')
        self.parent = parent

        self.put_widgets(mainapp)
        
    def put_widgets(self, mainapp):
        self.barcode_widgets = []
        self.lab_uut_id = ttk.Label(self, text='UUT ID:')
        self.barcode_widgets.append(self.lab_uut_id)

        self.uut_id = tk.StringVar()
        self.ent_uut_id = ttk.Entry(self, textvariable=self.uut_id, width=20)
        self.ent_uut_id.bind('<Return>', partial(self.bind_uutId_entry, mainapp))
        self.barcode_widgets.append(self.ent_uut_id)

        self.lab_uut_dbr = ttk.Label(self, width=22, relief=tk.GROOVE)
        self.barcode_widgets.append(self.lab_uut_dbr)

        self.lab_main_id = ttk.Label(self, text='PCB_MAIN ID:')
        self.barcode_widgets.append(self.lab_main_id)
        self.ent_main_id = ttk.Entry(self)
        self.barcode_widgets.append(self.ent_main_id)
        self.lab_main_dbr = ttk.Label(self, width=16, relief=tk.GROOVE)
        self.barcode_widgets.append(self.lab_main_dbr)

        self.lab_sub1_id = ttk.Label(self, text='PCB_SUB_CARD_1 ID:')
        self.barcode_widgets.append(self.lab_sub1_id)
        self.ent_sub1_id = ttk.Entry(self)
        self.barcode_widgets.append(self.ent_sub1_id)
        self.lab_sub1_dbr = ttk.Label(self, width=16, relief=tk.GROOVE)
        self.barcode_widgets.append(self.lab_sub1_dbr)

        self.lab_ha_id = ttk.Label(self, text='Hardware Addition:')
        self.barcode_widgets.append(self.lab_ha_id)
        self.lab_ha_val = ttk.Label(self, width=16, relief=tk.GROOVE)
        self.barcode_widgets.append(self.lab_ha_val)
        self.lab_ha_0 = ttk.Label(self)
        self.barcode_widgets.append(self.lab_ha_0)

        self.lab_csl_id = ttk.Label(self, text='CSL:')
        self.barcode_widgets.append(self.lab_csl_id)
        self.lab_csl_val = ttk.Label(self, width=16, relief=tk.GROOVE)
        self.barcode_widgets.append(self.lab_csl_val)
        self.lab_csl_0 = ttk.Label(self)
        self.barcode_widgets.append(self.lab_csl_0)

        #print(f'self.barcode_widgets:<{self.barcode_widgets}>')
        for w in self.barcode_widgets:
            w.grid(row=self.barcode_widgets.index(w)//3, 
                   column=self.barcode_widgets.index(w)%3, 
                   sticky='w')

    def bind_uutId_entry(self, mainapp, *event):
        print(f'bind_uutId_entry self:{self} mainapp:{mainapp} event:{event}')
        id_number = self.uut_id.get()
        print(f'bind_uutId_entry id_number:{id_number}')
        mainapp.status_bar_frame.status(id_number)


class StatusBarFrame(tk.Frame):
    '''Create the Status Bar Frame on base of tk.Frame'''
    def __init__(self, parent, mainapp):
        super().__init__(parent)
        print(f'StatusBarFrame, self:<{self}>, parent:<{parent}>')
        self['relief'] = self.master['relief']
        self['bd'] = self.master['bd']

        self.put_widgets()
        
    def put_widgets(self):
        self.label1 = tk.Label(self, anchor='center', width=66, relief="groove")
        self.label1.pack(side='left', padx=1, pady=1, expand=1, fill=tk.X)
        self.label2 = tk.Label(self, anchor=tk.W, width=15, relief="sunken")
        self.label2.pack(side='left', padx=1, pady=1)
        self.label3 = tk.Label(self, width=5, relief="sunken", anchor='center')
        self.label3.pack(side='left', padx=1, ipadx=2, pady=1)

    def status(self, txt, bg="gray85"):
        #  SystemButtonFace = gray85
        if bg == 'red':
            bg = 'salmon'
        elif bg == 'green':
            bg = 'springgreen'
        self.label1.configure(text=txt, bg=bg)
        self.label1.update_idletasks()

    def read_status(self):
        return self.label1.cget('text')

    def start_time(self, txt):
        self.label2.configure(text=txt)
        self.label2.update_idletasks()

    def run_time(self, txt):
        self.label3.configure(text=txt)
        self.label3.update_idletasks()
        

class DialogBox(tk.Toplevel):
    def __init__(self, parent, db_dict, *args):
        self.args = args
        print(f"DialogBox parent:{parent} txt:{db_dict['message']} args:{args}")
        tk.Toplevel.__init__(self, parent)
        x_pos = parent.winfo_x() + 20
        y_pos = parent.winfo_y() + 20

        if 'message' in db_dict:
            msg = db_dict['message']
        else:
            db_dict['message'] = ''
            msg = ""
        message = msg

        if 'entry_qty' in db_dict:
            self.entry_qty = db_dict['entry_qty']
        else:
            self.entry_qty = 0

        if 'entry_per_row' in db_dict:
            entry_per_row = db_dict['entry_per_row']
        else:
            entry_per_row = 1

        entry_lines_qty = int(self.entry_qty/entry_per_row)
        # print(f'entry_lines_qty {entry_lines_qty}')

        new_lines_qty = message.count('\n')
        hei = 16*new_lines_qty + 44*entry_lines_qty + 60

        minH = 80
        # set minimum height to minH pixels
        if hei < minH:
            hei = minH
        # print(f'new_lines_qty {new_lines_qty} hei {hei}')

        maxW = 0
        for line in message.split('\n'):
            if len(line) > maxW:
                maxW = len(line)

        width = maxW * 8

        minW = 270
        # set minimum with to $minW pixels
        if width < minW:
            width = minW

        # print(f'self.max {maxW}, width {width}')
        # self.geometry(f'{width}x{hei}+{x_pos}+{y_pos}')
        self.geometry(f'+{x_pos}+{y_pos}')
        self.title(db_dict['title'])
        # self.bind('<Configure>', lambda event: print(self.geometry()))

        self.fr1 = tk.Frame(self)
        fr_img = tk.Frame(self.fr1)
        if re.search("tk::icons", db_dict['icon']):
            use_img_run = db_dict['icon']
        else:
            self.imgRun = Image.open(db_dict['icon'])
            use_img_run = ImageTk.PhotoImage(self.imgRun)
        l_img = tk.Label(fr_img, image=use_img_run)
        l_img.image = use_img_run
        l_img.pack(padx=10, anchor='n')

        fr_right = tk.Frame(self.fr1)
        fr_msg = tk.Frame(fr_right)
        l_msg = tk.Label(fr_msg, text=db_dict['message'])
        l_msg.pack(padx=10)

        if 'entry_lbl' in db_dict:
            entry_lbl = db_dict['entry_lbl']
        else:
            entry_lbl = ""
        if 'entry_frame_bd' in db_dict:
            bd = db_dict['entry_frame_bd']
        else:
            bd = 2
        self.ent_dict = {}
        if self.entry_qty > 0:
            self.list_ents = []
            fr_ent = tk.Frame(fr_right, bd=bd, relief='groove')
            for fi in range(0, self.entry_qty):
                f = tk.Frame(fr_ent, bd=0, relief='groove')
                txt = entry_lbl[fi]
                lab = tk.Label(f, text=txt)
                self.ent_dict[txt] = tk.StringVar()
                # CustomDialog.ent_dict[fi] = self.ent_dict[fi]
                self.list_ents.append(ttk.Entry(f, textvariable=self.ent_dict[txt]))
                # print(f'txt:{len(txt)}, entW:{ent.cget("width")}')
                self.list_ents[fi].pack(padx=2, side='right', fill='x')
                self.list_ents[fi].bind("<Return>", functools.partial(self.cmd_ent, fi))
                if entry_lbl != "":
                    lab.pack(padx=2, side='right')
                row = int((fi)/entry_per_row)
                column = int((fi)%entry_per_row)
                # print(f'fi:{fi}, txt:{txt}, row:{row} column:{column} entW:{ent.cget("width")}')
                f.grid(padx=(2, 10), pady=2, row=row, column=column, sticky='e')

        fr_msg.pack()
        if self.entry_qty > 0:
            fr_ent.pack(anchor='e', padx=2, pady=2, expand=1)

        fr_img.grid(row=0, column=0)
        fr_right.grid(row=0, column=1)

        self.frBut = tk.Frame(self)
        print(f"buts:{db_dict['type']}")

        self.buts_lst = []
        for butn in db_dict['type']:
            self.but = tk.ttk.Button(self.frBut, text=butn, width=10, command=functools.partial(self.on_but, butn))
            if args and butn == args[0]['invokeBut']:
                self.buts_lst.append((butn, self.but))
            self.but.bind("<Return>", functools.partial(self.on_but, butn))
            self.but.pack(side="left", padx=2)
            if 'default' in db_dict:
                default = db_dict['default']
            else:
                default = 0
            if db_dict['type'].index(butn) == default:
                self.but.configure(state="active")
                # self.bind('<space>', (lambda e, b=self.but: self.but.invoke()))
                self.but.focus_set()
                self.default_but = self.but

        if self.entry_qty > 0:
            self.list_ents[0].focus_set()

        self.fr1.pack(fill="both", padx=2, pady=2)

        self.frBut.pack(side="bottom", fill="y", padx=2, pady=2)

        self.var = tk.StringVar()
        self.but = ""

        if self.entry_qty > 0:
            # print(self.list_ents)
            # print(self.ent_dict)
            # print(self.args)
            # print(self.buts_lst)
            self.bind('<Control-y>', functools.partial(self.bind_diaBox, 'y'))
            self.bind('<Alt-l>', functools.partial(self.bind_diaBox, 'l'))

    def bind_diaBox(self, let, *event):
        for arg in self.args:
            for key, val in arg.items():
                print(let, key, val)
                if key != 'invokeBut':
                    if let == 'l':
                        val = arg['last']
                        key = "Scan here the Operator's Employee Number "
                    elif let == 'y' and 'ilya' in arg.keys():
                        val = arg['ilya']
                        key = "Scan here the Operator's Employee Number "

                    self.ent_dict[key].set(val)

        for butn, butn_obj in self.buts_lst:
            butn_obj.invoke()

    def cmd_ent(self, fi, event=None):
        # print(f'cmd_ent self:{self}, fi:{fi}, entry_qty:{self.entry_qty}, event:{event}')
        if fi+1 == self.entry_qty:
            # last entry -> set focus to default button
            self.default_but.invoke()
            # pass
        else:
            # not last entry -> set focus to next entry
            self.list_ents[fi+1].focus_set()

    def on_but(self, butn, event=None):
        # print(f'on_but self:{self}, butn:{butn}, event:{event}')
        self.but = butn
        self.destroy()
    # def on_ok(self, event=None):
    #     self.but = "ok"
    #     self.destroy()
    # def ca_ok(self, event=None):
    #     self.but = "ca"
    #     self.destroy()

    def show(self):
        self.wm_deiconify()
        # self.entry.focus_force()
        self.wait_window()
        # try:
        #     print(f'DialogBox show ent_dict:{self.ent_dict}')
        # except Exception as err:
        #     print(err)
        return [self.var.get(), self.but, self.ent_dict]


'''print(sys.argv, len(sys.argv))
gui_num = sys.argv[1]
    
app = App(gui_num)
app.mainloop()'''

if __name__ == '__main__':
    print(sys.argv, len(sys.argv))
    if len(sys.argv)==2:
        gui_num = sys.argv[1]
    else:
        gui_num = 2
    app = App(gui_num)
    app.mainloop()
