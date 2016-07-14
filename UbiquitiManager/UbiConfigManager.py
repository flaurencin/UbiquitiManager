from io import StringIO
from functools import reduce
from UbiquitiManager.UbiExceptions import UbiConfigTest


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
        self.connector.ubi_authentication()
        self.config = self.connector.ubi_request_get('cfg.cgi')
        self.config_text_to_dict()

    def push_config(self):
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
