'''
Created on Mar 14, 2015

@author: Andrew Kittredge
@copyright: Calcbench, Inc.
@contact: andrew@calcbench.com
'''
from __future__ import print_function
import os
import requests
import json
import pandas as pd

_CALCBENCH_USER_NAME = os.environ.get("CALCBENCH_USERNAME")
_CALCBENCH_PASSWORD = os.environ.get("CALCBENCH_PASSWORD")
_CALCBENCH_API_URL_BASE = "https://www.calcbench.com/api/{0}"

_SESSION = None

def _calcbench_session():
    global _SESSION
    if not _SESSION:
        _SESSION = requests.Session()
        r = _SESSION.post('https://www.calcbench.com/account/LogOnAjax', 
                  {'email' : _CALCBENCH_USER_NAME, 
                   'strng' : _CALCBENCH_PASSWORD, 
                   'rememberMe' : 'true'},
                  verify=False)
        assert r.text == 'true', 'login failed'
    return _SESSION

def set_credentials(cb_username, cb_password):
    '''Set your calcbench credentials.
    
    username is the email address you use to login to calcbench.com.
    '''
    _CALCBENCH_USER_NAME = cb_username
    _CALCBENCH_PASSWORD = cb_password

def normalized_data(company_identifiers, 
                    metrics, 
                    start_year, 
                    start_period,
                    end_year,
                    end_period):
    '''Normalized data.'''
    url = _CALCBENCH_API_URL_BASE.format("/NormalizedValues")
    payload = {"start_year" : start_year,
           'start_period' : start_period,
           'end_year' : end_year,
           'end_period' : end_period,
           'company_identifiers' : company_identifiers,
           'metrics' : metrics,
           }
    response = _calcbench_session().post(
                                    url,
                                    data=json.dumps(payload), 
                                    headers={'content-type' : 'application/json'}
                                    )
    response.raise_for_status()
    data = response.json()
    quarterly = start_period and end_period
    if quarterly:
        build_period = _build_quarter_period
    else:
        build_period = _build_annual_period
   
    for d in data:                          
        d['period'] = build_period(d)
        d['ticker'] = d['ticker'].upper()

        
    data = pd.DataFrame(data)
    data.set_index(keys=['ticker', 'metric', 'period'],
                   inplace=True)
    data = data.unstack('metric')['value']
    data = data.unstack('ticker')
    data = data[metrics]
    return data

def _build_quarter_period(data_point):
    return pd.Period(year=data_point.pop('calendar_year'),
                     quarter=data_point.pop('calendar_period'),
                     freq='q')

def _build_annual_period(data_point):
    data_point.pop('calendar_period')
    return pd.Period(year=data_point.pop('calendar_year'), freq='a')

    
def tickers(SIC_code=None, index=None):
    '''Return a list of tickers in the peer-group'''
    if index:
        if index not in ("SP500", "DJIA"):
            raise ValueError("index must be either 'SP500' or 'DJIA'")
        query = "index={0}".format(index)
    else:
        query = "siccodes={0}".format(SIC_code)
    url = _CALCBENCH_API_URL_BASE.format("companies?" + query)
    r = _calcbench_session().get(url)
    r.raise_for_status()
    tickers = r.json()
    tickers = [co['ticker'] for co in tickers]
    return tickers


if __name__ == '__main__':
    print(tickers(index="DJIA"))
    data = normalized_data(company_identifiers=['ibm', 'msft'], 
                          metrics=['revenue', 'assets', ],
                          start_year=2010,
                          start_period=1,
                          end_year=2014,
                          end_period=4)
    print(data)
 