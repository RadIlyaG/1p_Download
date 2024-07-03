class Main:
    def __init__(self, mainapp):
        self.tests = ["Ubdate_UBoot", 'Set_Env', 'Download_FlashImage',
                     'Eeprom', 'Run_BootNet', 'ID']

        if mainapp.uut_opt != 'ETX1P':
            self.tests += 'MicroSD'

        self.tests += 'SOC_Flash_Memory', 'SOC_i2C'
