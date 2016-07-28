class UbiHttpException(Exception):
    '''
    HTTP error when not receiveng proper HTTP RESP CODE.
    '''
    pass


class UbiAuthException(Exception):
    '''
    If for any reason the authetication on AP failed this exception
    should be raised
    '''
    pass


class UbiHostException(Exception):
    '''
    If Host seolution or IP is invalid raise this exception
    '''
    pass


class UbiConfigTest(Exception):
    '''
    While attempting totest the config before applying we encounter
    any issue raise this exception
    '''
    pass


class UbiAlertConnectivityLost(Exception):
    '''
    If we lose the connection while managing an AP raise this
    exception
    '''
    pass


class UbiBadFirmware(Exception):
    '''
    If the AP is complaining about firmware we attempt to inject
    Raise this exception
    '''
    pass


class UbiConfigChangeFailed(Exception):
    '''
    If we try to modify configuration and it's not relevent or it
    fails or parameter is invalid raise this exception
    '''
    pass
