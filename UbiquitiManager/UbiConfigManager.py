import time
from io import StringIO
from functools import reduce
from UbiquitiManager.UbiExceptions import UbiConfigTest
from UbiquitiManager.UbiExceptions import UbiBadFirmware
from UbiquitiManager.UbiExceptions import UbiAuthException
from UbiquitiManager.UbiExceptions import UbiAlertConnectivityLost

class UbiConfigManager(object):
    '''
    This class will allow you togather, manipulate and push configuratio
    file contianed in an ubiquite device.

    Attributes
    ----------
    connector : UbiquitiManager.UbiConnector
        Connector Object.
    config : str
        Text configuration
    config_dict : dict
        Configuration converted in dict od dict of dict etc...

    Methods
    -------
    config_text_to_dict()
        Converts Text config to dict
    config_dict_to_text()
        Converts dict config to text config (understandable by device)
    gather_config()
        gather the config from the device.
    push_config()
        Push and saves configuration to device.
    '''
    def __init__(self, ubiquiti_connector):
        self.connector = ubiquiti_connector
        self.config = None
        self.config_dict = {}
        self.gather_config()

    def _get_from_dict(self, this_dict, k_list):
        return reduce(lambda data, key: data[key], k_list, this_dict)

    def _set_to_dict(self, this_dict, k_list, value):
        self._get_from_dict(this_dict, k_list[:-1])[k_list[-1]] = value

    def config_text_to_dict(self):
        '''
        Takes the text configuation and convert it to dict.
        '''
        for line in str(self.config).splitlines():
            key = line.split('=')[0]
            value = '='.join(line.split('=')[1:])
            tmp_dict = self.config_dict
            for element in key.split('.'):
                if element not in tmp_dict:
                    tmp_dict[element] = {}
                tmp_dict = tmp_dict[element]
            self._set_to_dict(self.config_dict, key.split('.'), value)

    def config_dict_to_text(self):
        '''
        Takes the dict configuation and convert it to text.
        '''
        def parse_dict(thisdict, path=''):
            ret = {}
            for nextpath, val in thisdict.items():
                newpath = path+nextpath
                if isinstance(val, dict):
                    ret.update(parse_dict(val, newpath+'.'))
                else:
                    ret[newpath] = val
            return ret
        final_dict = parse_dict(self.config_dict)
        result = []
        for k, v in sorted(final_dict.items()):
            result.append('{}={}'.format(k, v))
        self.config = '\n'.join(result)

    def gather_config(self):
        '''
        Gatheres the configuration from the device. Then sync the config_dict
        accordingly.
        '''
        self.connector.ubi_authentication()
        self.config = self.connector.ubi_request_get('cfg.cgi')
        self.config_text_to_dict()

    def push_config(self, avoid_test=False):
        '''
        Push textual config to the ubiquiti device. Then Run test on the
        config. If after test the ubuquiti device is still answering, it
        will apply the configuration definitely.

        Parameters
        ----------
        avoid_test : bool
            Default is False, if you want to apply the config no matter what,
            you can use avoid_test=True.

        Raises
        ------
        UbiConfigTest
            If the device is not reachable after test.
        '''
        import time
        self.connector.ubi_authentication()
        config_file = StringIO(self.config)
        config_file.seek(0)
        result = self.connector.ubi_request_post(
            'system.cgi',
            {
                'cfgfile': ('automated.cfg', config_file),
                'cfgupload': 'Restaurer',
                'action': 'cfgupload'
            }
        )
        if not avoid_test:
            self.connector.ubi_request_post(
                'apply.cgi',
                {
                    'testmode': 'on',
                }
            )
            time.sleep(20)
            try:
                result = self.connector.ubi_request_get('system.cgi')
            except Exception as e:
                raise UbiConfigTest(
                    'Configuration Test Failed. Error : {}'.format(str(e))
                )

        result = self.connector.ubi_request_post(
            'apply.cgi',
            {
                'testmode': '',
            }
        )
        del result

    def set_value(self, config_path, value):
        '''
        Grab a config Path either in the form of a list of keys, or textual,
        like ['resolv', 'host', '1', 'name'] or 'resolv.host.1.name', and
        a value. Then set the value if keys where correct.

        Parameters
        ----------
        config_path : list or str
            Path either in the form of a list of keys, or textual.
        value : str
            Value to be set in the configuration

        Raises
        ------
        KeyError
            If path was incorrect somewhere.
        '''
        dict_path = []
        if isinstance(config_path, list):
            dict_path = config_path
        else:
            dict_path = str(config_path).split('.')
        self._set_to_dict(self.config_dict, dict_path, value)
        self.config_dict_to_text()

    def fw_upgrade(self, fwfile, timeout=(3, 1250)):
        '''
        Takes the firmware upgrade file pointed by the given file descriptor.

        Parameters
        ----------
        fwfile : _io.BufferedReader
            File buffer reader.
        timeout : tuple optional
            specific time outs for firmware upgrade. By default, will wait
            3 seconds for tcp connection, and 1600s for answer (10MB at 64kb/s)
            if you have bandwidth available for sure it can be reasonnable to
            lower these values.

        Raises
        ------
            UbiBadFirmware
                When file is not a valid Firmware
            
        '''
        bad_file = 'Invalid Firmware file is uploaded'
        self.connector.ubi_authentication()
        result = self.connector.ubi_request_post(
            'system.cgi',
            {
                'fwfile': ('fw.bin', fwfile),
                'fwupload': 'Restaurer',
                'action': 'fwupload'
            },
            timeout=timeout
        )
        if bad_file in result:
            raise UbiBadFirmware(
                'Ubiquiti device did not accept this firmware'
            )
        elif 'class="logintable"' in result:
            raise UbiAuthException(
                'Ubiquiti disconnected while attemping to push firmware!'
            )
        result = self.connector.ubi_request_get(
            'fwflash.cgi?do_update=do'
        )
        for i in range(0, 20):
            time.sleep(20)
            try:
                self.connector.ubi_authentication()
                return
            except:
                UbiAlertConnectivityLost('Connectivity Lost After Upgrade')
