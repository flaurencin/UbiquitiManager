import socket
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from UbiquitiManager.UbiExceptions import UbiHttpException
from UbiquitiManager.UbiExceptions import UbiAuthException
from UbiquitiManager.UbiExceptions import UbiHostException

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class UbiConnector(object):
    '''
    UbiConnector Allow you to poll Ubiquiti AP. It handles login, and
    requests. It detects json data and returns python data if possible. It
    also keeps track of data gathered.

    Attributes
    ----------
    host : str
        host targeted for data gathering
    login : str
        Login crediential to access the target.
    passwords : list
        List of str, containing potential passwords crediential to access
        the target.
    protocol : str
        Use http or https for eccessing the device
    port : str
        strcontaining the port number to access te device.
    baseurl : str
        url validated after authentication.
    data : dict
        for every page requested will store latest gathered data.

    Methods
    -------
    ubi_authentication()
        Attemps authentication to the device, Raise exception if failed to log
        in.
    ubi_request_post(path, data)
        Attemps to gather data via post to the given path, setting encoding
        type to multipart/form-data.
    ubi_request_get(path)
        Attemps to gather data via get to the given path.
    ubi_add_password(other_password)
        Extend the possible passwords list.
    '''

    def __init__(self, host, login, password, protocol='https', port=443):
        self.host = None
        try:
            self.host = socket.gethostbyname(str(host))
        except socket.gaierror:
            raise UbiHostException('enable to resolve given host')

        self.login = str(login)
        if isinstance(password, list):
            self.passwords = [str(p) for p in password]
        else:
            self.passwords = [str(password)]
        self.protocol = protocol
        self.port = str(port)
        self.baseurl = None
        self.data = {}

    def ubi_authentication(self):
        '''
        Attemps authentication to the device, Raise exception if failed to log
        in.

        Raises
        ------
        UbiAuthException
            if none of the login:pawwsords worked.
        '''
        session = requests.session()
        session.verify = False
        session.get(
            '{0}://{1}:{2}/login.cgi'.format(
                self.protocol,
                self.host,
                self.port
            )
        )
        for password in self.passwords:
            data = session.post(
                '{0}://{1}:{2}/login.cgi'.format(
                    self.protocol,
                    self.host,
                    self.port
                ),
                files={
                    'username': (None, self.login),
                    'password': (None, password),
                    'uri': (None, '')
                },
                verify=False
            )
            clean_data = data.text.replace(' ', '')
            clean_data = clean_data.replace('\t', '')
#            valid_conditions = [
#                'class="logintable"' not in clean_data,
#                '<divid="errmsg"class="error">\n\n</div>' in clean_data
#            ]
#            valid_conditions = any(valid_conditions)
            print(clean_data)
            if 'class="logintable"' not in clean_data:
                base_url = '{0}://{1}:{2}'.format(
                    self.protocol,
                    self.host,
                    self.port
                )
                self.baseurl = base_url
                self.session = session
                return
        raise UbiAuthException('Authentication Failed')

    def _treat_http_return(self, result, path):
        if result.status_code < 200 or result.status_code > 299:
            raise UbiHttpException(
                'Http server returned Code {}'.format(
                    result.status_code
                )
            )
        try:
            self.data[path] = result.json()
            return self.data[path]
        except:
            return result.text

    def ubi_request_post(self, path, data, timeout=(3, 250)):
        '''
        Attemps to gather data via post to the given path, setting encoding
        type to multipart/form-data.

        Parameters
        ----------
        path : str
            path to add to the base connection url.
        data : dict
            parameter to post to the given path. With key=form_id and and
            value=form_value, if you want to add filename use a tuple in the
            value as (filename, value)
        timeout : tuple optional
            Time outs for genereal purpose requests. By default, will wait
            3 seconds for tcp connection, and 250s for answer.

        Returns
        -------
        result : dict or str
            if the output was readable json returns the dict loaded from the
            json, else return text data.

        Raises
        ------
        UbiHttpException
            if http return code was not of type 2xx.
        '''
        for key in data:
            if not isinstance(data[key], tuple):
                data[key] = (None, data[key])

        result = self.session.post(
            '{}/{}'.format(self.baseurl, path),
            files=data,
            timeout=timeout
        )
        result = self._treat_http_return(result, path)
        return result

    def ubi_request_get(self, path, timeout=(3, 250)):
        '''
        Attemps to gather data via post to the given path, setting encoding
        type to multipart/form-data.

        Parameters
        ----------
        path : str
            path to add to the base connection url.
        data : dict
            parameter to post to the given path. With key=form_id and and
            value=form_value
        timeout : tuple optional
            Time outs for genereal purpose requests. By default, will wait
            3 seconds for tcp connection, and 250s for answer.

        Returns
        -------
        result : dict or str
            if the output was readable json returns the dict loaded from the
            json, else return text data.

        Raises
        ------
        UbiHttpException
            if http return code was not of type 2xx.
        '''
        result = self.session.get(
            '{}/{}'.format(self.baseurl, path),
            timeout=timeout
        )
        return self._treat_http_return(result, path)

    def ubi_add_password(self, other_password):
        '''
        Add one or more possible passwords.

        Parameters
        ----------
        other_password : str or list
            Adds the password or the list of password to the potential
            passwords.
        '''
        if isinstance(other_password, list):
            self.passwords.extend([str(p) for p in other_password])
        else:
            self.passwords.append(str(other_password))


if __name__ == '__main__':
    ap = UbiConnector(
        'localhost',
        'admin',
        'password',
        port='443'
    )
    ap.ubi_add_password('password2')
    ap.ubi_authentication()
    data = ap.ubi_request_get('status.cgi')
    import yaml
    print(yaml.dump(data, default_flow_style=False))
    data = ap.ubi_request_get('cfg.cgi')
    print(data)
