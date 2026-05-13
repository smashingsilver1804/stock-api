"""
Patch for yfinance to properly handle cookies with curl_cffi.
This solves the YFRateLimitError by impersonating a real browser.
"""

from requests.cookies import create_cookie
import yfinance.data as _data
from curl_cffi import requests as curl_requests

def _wrap_cookie(cookie, session):
    """Convert cookie string to proper Cookie object"""
    if isinstance(cookie, str):
        value = session.cookies.get(cookie)
        if value:
            return create_cookie(name=cookie, value=value)
    return cookie

def patch_yfdata_cookie_basic():
    """Patch yfinance's cookie handling to work with curl_cffi"""
    original = _data.YfData._get_cookie_basic
    
    def _patched(self, proxy=None, timeout=30):
        cookie = original(self, proxy, timeout)
        return _wrap_cookie(cookie, self._session)
    
    _data.YfData._get_cookie_basic = _patched

def create_browser_session(impersonate="chrome120"):
    """Create a session that impersonates a real browser"""
    return curl_requests.Session(impersonate=impersonate)
