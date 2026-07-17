#!/usr/bin/env python
"""
install_analysis_modal.py — adds the "Analysis" button (desktop + mobile More
menu) and the Expenses-vs-Rent Analysis modal to act_expense.html.

Run from the project root (where manage.py lives):

    python install_analysis_modal.py             # apply (backs up the template)
    python install_analysis_modal.py --dry-run   # preview only

Requires the act_expense_analysis_data endpoint (install_analysis_endpoint.py)
to be in place first. Idempotent and non-destructive (backs up the template to
<file>.bak_analysis_modal once). TIP: commit/stash first so you can git diff.
"""
import base64
import os
import re
import sys

DRY = '--dry-run' in sys.argv

MODAL_BLOCK = base64.b64decode("".join([
    "PCEtLSA9PT09PT09PT09PT09PT09PT09PSBFWFBFTlNFUyB2cyBSRU5UIOKAlCBBTkFMWVNJUyBNT0RBTCA9PT09PT09PT09PT09"
    "PT09PT09PSAtLT4KPHN0eWxlPgouYW5hbHlzaXMtZGlhbG9nIHsgbWF4LXdpZHRoOiA5MjBweDsgfQouYW5hbHlzaXMtZGlhbG9n"
    "IC5tb2RhbC1ib2R5IHsgbWF4LWhlaWdodDogNzh2aDsgb3ZlcmZsb3cteTogYXV0bzsgfQouYW5hbHlzaXMtc3ViIHsgY29sb3I6"
    "IzZjNzU3ZDsgZm9udC1zaXplOjEzcHg7IG1hcmdpbjogNHB4IDAgMTRweDsgfQouYW5hbHlzaXMtY2hhcnQtd3JhcCB7IHBvc2l0"
    "aW9uOiByZWxhdGl2ZTsgd2lkdGg6IDEwMCU7IGhlaWdodDogNDMwcHg7IG1hcmdpbi1ib3R0b206IDE2cHg7IH0KLmFuYWx5c2lz"
    "LXRhYmxlIHRib2R5IHRyLmRhbmdlci1yb3cgeyBiYWNrZ3JvdW5kOiNmZGVjZWM7IH0KLmFuYWx5c2lzLXRhYmxlIHRkLm51bSwg"
    "LmFuYWx5c2lzLXRhYmxlIHRoLm51bSB7IHRleHQtYWxpZ246cmlnaHQ7IGZvbnQtdmFyaWFudC1udW1lcmljOiB0YWJ1bGFyLW51"
    "bXM7IH0KLmFuYWx5c2lzLWZsYWcgeyBmb250LXNpemU6MTFweDsgZm9udC13ZWlnaHQ6NzAwOyBwYWRkaW5nOjJweCA4cHg7IGJv"
    "cmRlci1yYWRpdXM6MjBweDsgfQouYW5hbHlzaXMtZmxhZy53YXJuIHsgYmFja2dyb3VuZDojZmRlY2VjOyBjb2xvcjojYzAzMjJm"
    "OyB9Ci5hbmFseXNpcy1mbGFnLm9rIHsgYmFja2dyb3VuZDojZThmNmVjOyBjb2xvcjojMWY3YTM3OyB9Ci5hbmFseXNpcy1zcmMg"
    "eyBmb250LXNpemU6MTFweDsgY29sb3I6I2FkYjViZDsgfQpAbWVkaWEgKG1heC13aWR0aDogNzY4cHgpIHsKICAuYW5hbHlzaXMt"
    "ZGlhbG9nIHsgbWF4LXdpZHRoOjEwMCU7IG1hcmdpbjowOyBoZWlnaHQ6MTAwdmg7IH0KICAuYW5hbHlzaXMtZGlhbG9nIC5tb2Rh"
    "bC1jb250ZW50IHsgaGVpZ2h0OjEwMHZoOyBib3JkZXItcmFkaXVzOjA7IGJvcmRlcjpub25lOyBkaXNwbGF5OmZsZXg7IGZsZXgt"
    "ZGlyZWN0aW9uOmNvbHVtbjsgfQogIC5hbmFseXNpcy1kaWFsb2cgLm1vZGFsLWhlYWRlciB7IGZsZXgtc2hyaW5rOjA7IHBhZGRp"
    "bmc6MTJweCAxNHB4OyB9CiAgLmFuYWx5c2lzLWRpYWxvZyAubW9kYWwtYm9keSB7IGZsZXg6MSAxIGF1dG87IG1heC1oZWlnaHQ6"
    "bm9uZTsgb3ZlcmZsb3cteTphdXRvOyAtd2Via2l0LW92ZXJmbG93LXNjcm9sbGluZzp0b3VjaDsgcGFkZGluZzoxMnB4OyB9CiAg"
    "LmFuYWx5c2lzLWNoYXJ0LXdyYXAgeyBoZWlnaHQ6MzQwcHg7IH0KICAuYW5hbHlzaXMtdGFibGUgdGgsIC5hbmFseXNpcy10YWJs"
    "ZSB0ZCB7IGZvbnQtc2l6ZToxM3B4OyBwYWRkaW5nOjhweCA2cHg7IH0KfQo8L3N0eWxlPgo8ZGl2IGNsYXNzPSJtb2RhbCBmYWRl"
    "IiBpZD0iZXhwZW5zZUFuYWx5c2lzTW9kYWwiIHRhYmluZGV4PSItMSIgcm9sZT0iZGlhbG9nIiBhcmlhLWxhYmVsbGVkYnk9ImV4"
    "cGVuc2VBbmFseXNpc0xhYmVsIiBhcmlhLWhpZGRlbj0idHJ1ZSI+CiAgPGRpdiBjbGFzcz0ibW9kYWwtZGlhbG9nIG1vZGFsLWxn"
    "IGFuYWx5c2lzLWRpYWxvZyIgcm9sZT0iZG9jdW1lbnQiPgogICAgPGRpdiBjbGFzcz0ibW9kYWwtY29udGVudCI+CiAgICAgIDxk"
    "aXYgY2xhc3M9Im1vZGFsLWhlYWRlciI+CiAgICAgICAgPGg1IGNsYXNzPSJtb2RhbC10aXRsZSIgaWQ9ImV4cGVuc2VBbmFseXNp"
    "c0xhYmVsIj4KICAgICAgICAgIDxpIGNsYXNzPSJmYXMgZmEtY2hhcnQtbGluZSIgc3R5bGU9ImNvbG9yOiMxN2EyYjg7Ij48L2k+"
    "IEV4cGVuc2VzIHZzIFJlbnQg4oCUIEFuYWx5c2lzCiAgICAgICAgPC9oNT4KICAgICAgICA8YnV0dG9uIHR5cGU9ImJ1dHRvbiIg"
    "Y2xhc3M9ImNsb3NlIiBkYXRhLWRpc21pc3M9Im1vZGFsIiBhcmlhLWxhYmVsPSJDbG9zZSI+PHNwYW4gYXJpYS1oaWRkZW49InRy"
    "dWUiPiZ0aW1lczs8L3NwYW4+PC9idXR0b24+CiAgICAgIDwvZGl2PgogICAgICA8ZGl2IGNsYXNzPSJtb2RhbC1ib2R5Ij4KICAg"
    "ICAgICA8ZGl2IGNsYXNzPSJyZXBvcnQteWVhci1iYXIiPgogICAgICAgICAgPHNwYW4gY2xhc3M9InJlcG9ydC15ZWFyLWxhYmVs"
    "Ij48aSBjbGFzcz0iZmFzIGZhLWNhbGVuZGFyLWFsdCI+PC9pPiBZZWFyczo8L3NwYW4+CiAgICAgICAgICA8bGFiZWwgY2xhc3M9"
    "InJlcG9ydC15ZWFyLWNoayI+PGlucHV0IHR5cGU9ImNoZWNrYm94IiBpZD0iYW5hbHlzaXNZZWFyQWxsIiBjaGVja2VkPiBBbGwg"
    "eWVhcnM8L2xhYmVsPgogICAgICAgICAgPHNwYW4gaWQ9ImFuYWx5c2lzWWVhckxpc3QiIGNsYXNzPSJyZXBvcnQteWVhci1saXN0"
    "Ij48L3NwYW4+CiAgICAgICAgPC9kaXY+CiAgICAgICAgPHAgY2xhc3M9ImFuYWx5c2lzLXN1YiIgaWQ9ImFuYWx5c2lzU3ViIj48"
    "L3A+CiAgICAgICAgPGRpdiBpZD0iYW5hbHlzaXNMb2FkaW5nIiBjbGFzcz0idGV4dC1jZW50ZXIgdGV4dC1tdXRlZCIgc3R5bGU9"
    "InBhZGRpbmc6MzBweDsiPgogICAgICAgICAgPGkgY2xhc3M9ImZhcyBmYS1zcGlubmVyIGZhLXNwaW4iPjwvaT4gTG9hZGluZy4u"
    "LgogICAgICAgIDwvZGl2PgogICAgICAgIDxkaXYgaWQ9ImFuYWx5c2lzRW1wdHkiIGNsYXNzPSJ0ZXh0LWNlbnRlciB0ZXh0LW11"
    "dGVkIiBzdHlsZT0iZGlzcGxheTpub25lOyBwYWRkaW5nOjMwcHg7Ij4KICAgICAgICAgIE5vdCBlbm91Z2ggZGF0YSB0byBjb21w"
    "YXJlIHlldC4KICAgICAgICA8L2Rpdj4KICAgICAgICA8ZGl2IGlkPSJhbmFseXNpc0NvbnRlbnQiIHN0eWxlPSJkaXNwbGF5Om5v"
    "bmU7Ij4KICAgICAgICAgIDxkaXYgY2xhc3M9ImFuYWx5c2lzLWNoYXJ0LXdyYXAiPjxjYW52YXMgaWQ9ImFuYWx5c2lzQ2hhcnQi"
    "PjwvY2FudmFzPjwvZGl2PgogICAgICAgICAgPGRpdiBjbGFzcz0idGFibGUtcmVzcG9uc2l2ZSI+CiAgICAgICAgICAgIDx0YWJs"
    "ZSBjbGFzcz0idGFibGUgdGFibGUtc20gdGFibGUtaG92ZXIgYW5hbHlzaXMtdGFibGUiPgogICAgICAgICAgICAgIDx0aGVhZD4K"
    "ICAgICAgICAgICAgICAgIDx0cj4KICAgICAgICAgICAgICAgICAgPHRoPlByb3BlcnR5PC90aD4KICAgICAgICAgICAgICAgICAg"
    "PHRoIGNsYXNzPSJudW0iPlJlbnQ8L3RoPgogICAgICAgICAgICAgICAgICA8dGggY2xhc3M9InRleHQtY2VudGVyIj5MZXQ8L3Ro"
    "PgogICAgICAgICAgICAgICAgICA8dGggY2xhc3M9Im51bSI+QWN0dWFsPC90aD4KICAgICAgICAgICAgICAgICAgPHRoIGNsYXNz"
    "PSJudW0iPiUgb2YgcmVudDwvdGg+CiAgICAgICAgICAgICAgICAgIDx0aCBjbGFzcz0ibnVtIj5SZW50ICZEZWx0YTs8L3RoPgog"
    "ICAgICAgICAgICAgICAgICA8dGggY2xhc3M9InRleHQtY2VudGVyIj5TdGF0dXM8L3RoPgogICAgICAgICAgICAgICAgPC90cj4K"
    "ICAgICAgICAgICAgICA8L3RoZWFkPgogICAgICAgICAgICAgIDx0Ym9keSBpZD0iYW5hbHlzaXNUYWJsZUJvZHkiPjwvdGJvZHk+"
    "CiAgICAgICAgICAgIDwvdGFibGU+CiAgICAgICAgICA8L2Rpdj4KICAgICAgICAgIDxwIGNsYXNzPSJ0ZXh0LW11dGVkIHNtYWxs"
    "IG1iLTAiIGlkPSJhbmFseXNpc05vdGUiPjwvcD4KICAgICAgICA8L2Rpdj4KICAgICAgPC9kaXY+CiAgICA8L2Rpdj4KICA8L2Rp"
    "dj4KPC9kaXY+CjxzY3JpcHQ+CihmdW5jdGlvbigpIHsKICAgICd1c2Ugc3RyaWN0JzsKICAgIHZhciBBTkFMWVNJU19VUkwgPSAi"
    "eyUgdXJsICdhY3RfZXhwZW5zZV9hbmFseXNpc19kYXRhJyAlfSI7CiAgICB2YXIgREFOR0VSX1BDVCA9IDEwOwogICAgdmFyIGNo"
    "YXJ0ID0gbnVsbCwgbG9hZGVkID0gZmFsc2UsIERBVEEgPSBudWxsOwoKICAgIGZ1bmN0aW9uIGV1cm8obikgeyByZXR1cm4gJ+KC"
    "rCcgKyBOdW1iZXIobiB8fCAwKS50b0xvY2FsZVN0cmluZygnZW4tSUUnLCB7bWF4aW11bUZyYWN0aW9uRGlnaXRzOiAwfSk7IH0K"
    "ICAgIGZ1bmN0aW9uIHBjdChuKSB7IHJldHVybiAobiA+IDAgPyAnKycgOiAnJykgKyBOdW1iZXIobikudG9GaXhlZCgxKSArICcl"
    "JzsgfQogICAgZnVuY3Rpb24gZXNjYXBlSHRtbChzKXsgcmV0dXJuIFN0cmluZyhzPT1udWxsPycnOnMpLnJlcGxhY2UoLyYvZywn"
    "JmFtcDsnKS5yZXBsYWNlKC88L2csJyZsdDsnKS5yZXBsYWNlKC8+L2csJyZndDsnKTsgfQoKICAgIGZ1bmN0aW9uIGVmZmVjdGl2"
    "ZVllYXJzKCkgewogICAgICAgIHZhciBhbGwgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgnYW5hbHlzaXNZZWFyQWxsJykuY2hl"
    "Y2tlZDsKICAgICAgICB2YXIgcGlja2VkID0gW107CiAgICAgICAgZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbCgnI2FuYWx5c2lz"
    "WWVhckxpc3QgaW5wdXRbdHlwZT1jaGVja2JveF06Y2hlY2tlZCcpLmZvckVhY2goZnVuY3Rpb24oY2IpeyBwaWNrZWQucHVzaChw"
    "YXJzZUludChjYi52YWx1ZSwgMTApKTsgfSk7CiAgICAgICAgaWYgKGFsbCB8fCBwaWNrZWQubGVuZ3RoID09PSAwKSByZXR1cm4g"
    "KERBVEEuYXZhaWxhYmxlX3llYXJzIHx8IFtdKS5zbGljZSgpOwogICAgICAgIHJldHVybiBwaWNrZWQ7CiAgICB9CgogICAgZnVu"
    "Y3Rpb24gYnVpbGRZZWFyQ2hlY2tib3hlcyh5ZWFycykgewogICAgICAgIHZhciBsaXN0ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5"
    "SWQoJ2FuYWx5c2lzWWVhckxpc3QnKTsKICAgICAgICBpZiAobGlzdC5kYXRhc2V0LmJ1aWx0ID09PSAnMScpIHJldHVybjsKICAg"
    "ICAgICBsaXN0LmlubmVySFRNTCA9ICcnOwogICAgICAgIHllYXJzLmZvckVhY2goZnVuY3Rpb24oeSkgewogICAgICAgICAgICB2"
    "YXIgbGJsID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgnbGFiZWwnKTsKICAgICAgICAgICAgbGJsLmNsYXNzTmFtZSA9ICdyZXBv"
    "cnQteWVhci1jaGsnOwogICAgICAgICAgICBsYmwuaW5uZXJIVE1MID0gJzxpbnB1dCB0eXBlPSJjaGVja2JveCIgdmFsdWU9Iicg"
    "KyB5ICsgJyI+ICcgKyB5OwogICAgICAgICAgICBsaXN0LmFwcGVuZENoaWxkKGxibCk7CiAgICAgICAgfSk7CiAgICAgICAgbGlz"
    "dC5kYXRhc2V0LmJ1aWx0ID0gJzEnOwogICAgICAgIHZhciBhbGxDYiA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdhbmFseXNp"
    "c1llYXJBbGwnKTsKICAgICAgICBhbGxDYi5hZGRFdmVudExpc3RlbmVyKCdjaGFuZ2UnLCBmdW5jdGlvbigpIHsKICAgICAgICAg"
    "ICAgaWYgKGFsbENiLmNoZWNrZWQpIGxpc3QucXVlcnlTZWxlY3RvckFsbCgnaW5wdXRbdHlwZT1jaGVja2JveF0nKS5mb3JFYWNo"
    "KGZ1bmN0aW9uKGNiKXsgY2IuY2hlY2tlZCA9IGZhbHNlOyB9KTsKICAgICAgICAgICAgZWxzZSBpZiAobGlzdC5xdWVyeVNlbGVj"
    "dG9yQWxsKCdpbnB1dFt0eXBlPWNoZWNrYm94XTpjaGVja2VkJykubGVuZ3RoID09PSAwKSB7IGFsbENiLmNoZWNrZWQgPSB0cnVl"
    "OyByZXR1cm47IH0KICAgICAgICAgICAgcmVuZGVyKCk7CiAgICAgICAgfSk7CiAgICAgICAgbGlzdC5xdWVyeVNlbGVjdG9yQWxs"
    "KCdpbnB1dFt0eXBlPWNoZWNrYm94XScpLmZvckVhY2goZnVuY3Rpb24oY2IpIHsKICAgICAgICAgICAgY2IuYWRkRXZlbnRMaXN0"
    "ZW5lcignY2hhbmdlJywgZnVuY3Rpb24oKSB7CiAgICAgICAgICAgICAgICBpZiAoY2IuY2hlY2tlZCkgYWxsQ2IuY2hlY2tlZCA9"
    "IGZhbHNlOwogICAgICAgICAgICAgICAgaWYgKGxpc3QucXVlcnlTZWxlY3RvckFsbCgnaW5wdXRbdHlwZT1jaGVja2JveF06Y2hl"
    "Y2tlZCcpLmxlbmd0aCA9PT0gMCkgYWxsQ2IuY2hlY2tlZCA9IHRydWU7CiAgICAgICAgICAgICAgICByZW5kZXIoKTsKICAgICAg"
    "ICAgICAgfSk7CiAgICAgICAgfSk7CiAgICB9CgogICAgZnVuY3Rpb24gYnViYmxlUmFkaXVzU2NhbGUodmFscykgewogICAgICAg"
    "IHZhciBtaW4gPSBNYXRoLm1pbi5hcHBseShudWxsLCB2YWxzKSwgbWF4ID0gTWF0aC5tYXguYXBwbHkobnVsbCwgdmFscyk7CiAg"
    "ICAgICAgcmV0dXJuIGZ1bmN0aW9uKHYpIHsgcmV0dXJuIChtYXggPT09IG1pbikgPyAxMSA6IDcgKyAodiAtIG1pbikgLyAobWF4"
    "IC0gbWluKSAqIDE1OyB9OwogICAgfQoKICAgIGZ1bmN0aW9uIGxvYWQoKSB7CiAgICAgICAgdmFyIGxvYWRpbmcgPSBkb2N1bWVu"
    "dC5nZXRFbGVtZW50QnlJZCgnYW5hbHlzaXNMb2FkaW5nJyk7CiAgICAgICAgdmFyIGVtcHR5ID0gZG9jdW1lbnQuZ2V0RWxlbWVu"
    "dEJ5SWQoJ2FuYWx5c2lzRW1wdHknKTsKICAgICAgICB2YXIgY29udGVudCA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdhbmFs"
    "eXNpc0NvbnRlbnQnKTsKICAgICAgICBsb2FkaW5nLnN0eWxlLmRpc3BsYXkgPSAnYmxvY2snOyBlbXB0eS5zdHlsZS5kaXNwbGF5"
    "ID0gJ25vbmUnOyBjb250ZW50LnN0eWxlLmRpc3BsYXkgPSAnbm9uZSc7CiAgICAgICAgZmV0Y2goQU5BTFlTSVNfVVJMLCB7aGVh"
    "ZGVyczogeydYLVJlcXVlc3RlZC1XaXRoJzogJ1hNTEh0dHBSZXF1ZXN0J319KQogICAgICAgICAgICAudGhlbihmdW5jdGlvbihy"
    "KXsgcmV0dXJuIHIuanNvbigpOyB9KQogICAgICAgICAgICAudGhlbihmdW5jdGlvbihkYXRhKSB7CiAgICAgICAgICAgICAgICBE"
    "QVRBID0gZGF0YTsKICAgICAgICAgICAgICAgIGJ1aWxkWWVhckNoZWNrYm94ZXMoZGF0YS5hdmFpbGFibGVfeWVhcnMgfHwgW10p"
    "OwogICAgICAgICAgICAgICAgbG9hZGluZy5zdHlsZS5kaXNwbGF5ID0gJ25vbmUnOwogICAgICAgICAgICAgICAgcmVuZGVyKCk7"
    "CiAgICAgICAgICAgIH0pCiAgICAgICAgICAgIC5jYXRjaChmdW5jdGlvbihlcnIpIHsKICAgICAgICAgICAgICAgIGxvYWRpbmcu"
    "aW5uZXJIVE1MID0gJzxzcGFuIGNsYXNzPSJ0ZXh0LWRhbmdlciI+RmFpbGVkIHRvIGxvYWQgYW5hbHlzaXMuPC9zcGFuPic7CiAg"
    "ICAgICAgICAgICAgICBjb25zb2xlLmVycm9yKCdBbmFseXNpcyBsb2FkIGVycm9yOicsIGVycik7CiAgICAgICAgICAgIH0pOwog"
    "ICAgfQoKICAgIGZ1bmN0aW9uIHJlbmRlcigpIHsKICAgICAgICBpZiAoIURBVEEpIHJldHVybjsKICAgICAgICB2YXIgZW1wdHkg"
    "PSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgnYW5hbHlzaXNFbXB0eScpOwogICAgICAgIHZhciBjb250ZW50ID0gZG9jdW1lbnQu"
    "Z2V0RWxlbWVudEJ5SWQoJ2FuYWx5c2lzQ29udGVudCcpOwogICAgICAgIHZhciB5ZWFycyA9IGVmZmVjdGl2ZVllYXJzKCkuc2xp"
    "Y2UoKS5zb3J0KGZ1bmN0aW9uKGEsYil7IHJldHVybiBhIC0gYjsgfSk7CiAgICAgICAgdmFyIHNpbmdsZSA9IHllYXJzLmxlbmd0"
    "aCA8IDI7CiAgICAgICAgdmFyIHkwID0geWVhcnNbMF0sIHkxID0geWVhcnNbeWVhcnMubGVuZ3RoIC0gMV07CgogICAgICAgIC8v"
    "IEJ1aWxkIHRoZSBwZXItcHJvcGVydHkgcm93cyBmb3IgdGhlIHNlbGVjdGVkIHNwYW4uCiAgICAgICAgdmFyIHJvd3MgPSBbXTsK"
    "ICAgICAgICAoREFUQS5wcm9wZXJ0aWVzIHx8IFtdKS5mb3JFYWNoKGZ1bmN0aW9uKHApIHsKICAgICAgICAgICAgdmFyIGEgPSBw"
    "LnllYXJzW3kwXSwgYiA9IHAueWVhcnNbeTFdOwogICAgICAgICAgICBpZiAoIWIpIHJldHVybjsKICAgICAgICAgICAgdmFyIHJl"
    "bnROb3cgPSBiLnJlbnQsIGFjdHVhbCA9IGIuYWN0dWFsOwogICAgICAgICAgICB2YXIgcGN0UmVudCA9IHJlbnROb3cgPyAoYWN0"
    "dWFsIC8gcmVudE5vdyAqIDEwMCkgOiBudWxsOwogICAgICAgICAgICB2YXIgY2hhbmdlID0gKCFzaW5nbGUgJiYgYSAmJiBhLnJl"
    "bnQpID8gKChiLnJlbnQgLSBhLnJlbnQpIC8gYS5yZW50ICogMTAwKSA6IG51bGw7CiAgICAgICAgICAgIHJvd3MucHVzaCh7CiAg"
    "ICAgICAgICAgICAgICBpZDogcC5wcm9wX2lkLCBuYW1lOiBwLnByb3BfbmFtZSwKICAgICAgICAgICAgICAgIHJlbnQ6IHJlbnRO"
    "b3csIGxldDogYi5tb250aHNfbGV0LCBhY3R1YWw6IGFjdHVhbCwKICAgICAgICAgICAgICAgIHBjdFJlbnQ6IHBjdFJlbnQsIGNo"
    "YW5nZTogY2hhbmdlLCBzb3VyY2U6IGIuc291cmNlLAogICAgICAgICAgICAgICAgZGFuZ2VyOiAocGN0UmVudCAhPSBudWxsICYm"
    "IHBjdFJlbnQgPj0gREFOR0VSX1BDVCAmJiAoY2hhbmdlID09IG51bGwgfHwgY2hhbmdlIDw9IDApKQogICAgICAgICAgICB9KTsK"
    "ICAgICAgICB9KTsKICAgICAgICByb3dzID0gcm93cy5maWx0ZXIoZnVuY3Rpb24ocil7IHJldHVybiByLnJlbnQgfHwgci5hY3R1"
    "YWw7IH0pOwoKICAgICAgICBpZiAoIXJvd3MubGVuZ3RoKSB7IGVtcHR5LnN0eWxlLmRpc3BsYXkgPSAnYmxvY2snOyBjb250ZW50"
    "LnN0eWxlLmRpc3BsYXkgPSAnbm9uZSc7IHJldHVybjsgfQogICAgICAgIGNvbnRlbnQuc3R5bGUuZGlzcGxheSA9ICdibG9jayc7"
    "IGVtcHR5LnN0eWxlLmRpc3BsYXkgPSAnbm9uZSc7CgogICAgICAgIGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdhbmFseXNpc1N1"
    "YicpLmlubmVySFRNTCA9IHNpbmdsZQogICAgICAgICAgICA/ICgnUmFua2luZyBwcm9wZXJ0aWVzIGJ5IGFjdHVhbCAoYWQtaG9j"
    "KSBzcGVuZCBhcyBhICUgb2YgcmVudCBmb3IgPGI+JyArIHkxICsgJzwvYj4uIFNlbGVjdCAyKyB5ZWFycyB0byBjb21wYXJlIG1v"
    "dmVtZW50LicpCiAgICAgICAgICAgIDogKCdFYWNoIGJ1YmJsZSBpcyBhIHByb3BlcnR5LiBYID0gcmVudCBjaGFuZ2UgJyArIHkw"
    "ICsgJ+KGkicgKyB5MSArICcuIFkgPSBhY3R1YWwgc3BlbmQgYXMgJSBvZiByZW50ICgnICsgeTEgKyAnKS4gQnViYmxlIHNpemUg"
    "PSByZW50LiBSZWQgPSBzdXJwcmlzZXMgb3ZlciAnICsgREFOR0VSX1BDVCArICclIG9mIHJlbnQgd2l0aCByZW50IGZsYXQgb3Ig"
    "ZG93bi4nKTsKCiAgICAgICAgaWYgKHNpbmdsZSkgcmVuZGVyUmFua2luZyhyb3dzLCB5MSk7IGVsc2UgcmVuZGVyU2NhdHRlcihy"
    "b3dzLCB5MCwgeTEpOwogICAgICAgIHJlbmRlclRhYmxlKHJvd3MsIHNpbmdsZSk7CgogICAgICAgIHZhciBmbGFnZ2VkID0gcm93"
    "cy5maWx0ZXIoZnVuY3Rpb24ocil7IHJldHVybiByLmRhbmdlcjsgfSkubGVuZ3RoOwogICAgICAgIGRvY3VtZW50LmdldEVsZW1l"
    "bnRCeUlkKCdhbmFseXNpc05vdGUnKS5pbm5lckhUTUwgPSBmbGFnZ2VkCiAgICAgICAgICAgID8gKCc8aSBjbGFzcz0iZmFzIGZh"
    "LWV4Y2xhbWF0aW9uLXRyaWFuZ2xlIiBzdHlsZT0iY29sb3I6I2RjMzU0NTsiPjwvaT4gJyArIGZsYWdnZWQgKyAnIHByb3BlcnQn"
    "ICsgKGZsYWdnZWQ+MT8naWVzJzoneScpICsgJyBpbiB0aGUgd2F0Y2ggem9uZSAoYWN0dWFsIG92ZXIgJyArIERBTkdFUl9QQ1Qg"
    "KyAnJSBvZiByZW50LCByZW50IGZsYXQgb3IgZG93bikuJykKICAgICAgICAgICAgOiAnTm8gcHJvcGVydGllcyBpbiB0aGUgd2F0"
    "Y2ggem9uZS4nOwogICAgfQoKICAgIGZ1bmN0aW9uIHJlbmRlclNjYXR0ZXIocm93cywgeTAsIHkxKSB7CiAgICAgICAgdmFyIHB0"
    "cyA9IHJvd3MuZmlsdGVyKGZ1bmN0aW9uKHIpeyByZXR1cm4gci5jaGFuZ2UgIT0gbnVsbCAmJiByLnBjdFJlbnQgIT0gbnVsbDsg"
    "fSk7CiAgICAgICAgdmFyIHJTY2FsZSA9IGJ1YmJsZVJhZGl1c1NjYWxlKHB0cy5tYXAoZnVuY3Rpb24ocil7IHJldHVybiByLnJl"
    "bnQgfHwgMDsgfSkpOwogICAgICAgIHZhciBkYXRhID0gcHRzLm1hcChmdW5jdGlvbihyKXsgcmV0dXJuIHt4OiByLmNoYW5nZSwg"
    "eTogci5wY3RSZW50LCByOiByU2NhbGUoci5yZW50KSwgX3I6IHJ9OyB9KTsKICAgICAgICB2YXIgYmcgPSBwdHMubWFwKGZ1bmN0"
    "aW9uKHIpeyByZXR1cm4gci5kYW5nZXIgPyAncmdiYSgyMjAsNTMsNjksMC43NSknIDogJ3JnYmEoMjMsMTYyLDE4NCwwLjcyKSc7"
    "IH0pOwogICAgICAgIHZhciBiZCA9IHB0cy5tYXAoZnVuY3Rpb24ocil7IHJldHVybiByLmRhbmdlciA/ICcjYjAyYTM3JyA6ICcj"
    "MTE3YThiJzsgfSk7CgogICAgICAgIHZhciB4cyA9IHB0cy5tYXAoZnVuY3Rpb24ocil7IHJldHVybiByLmNoYW5nZTsgfSk7CiAg"
    "ICAgICAgdmFyIHhtaW4gPSBNYXRoLm1pbi5hcHBseShudWxsLCB4cy5jb25jYXQoWzBdKSksIHhtYXggPSBNYXRoLm1heC5hcHBs"
    "eShudWxsLCB4cy5jb25jYXQoWzBdKSk7CiAgICAgICAgdmFyIHBhZCA9ICh4bWF4IC0geG1pbikgKiAwLjEyIHx8IDU7IHhtaW4g"
    "LT0gcGFkOyB4bWF4ICs9IHBhZDsKCiAgICAgICAgaWYgKGNoYXJ0KSBjaGFydC5kZXN0cm95KCk7CiAgICAgICAgdmFyIGN0eCA9"
    "IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdhbmFseXNpc0NoYXJ0JykuZ2V0Q29udGV4dCgnMmQnKTsKICAgICAgICBjaGFydCA9"
    "IG5ldyBDaGFydChjdHgsIHsKICAgICAgICAgICAgZGF0YTogewogICAgICAgICAgICAgICAgZGF0YXNldHM6IFsKICAgICAgICAg"
    "ICAgICAgICAgICB7IHR5cGU6ICdidWJibGUnLCBsYWJlbDogJ1Byb3BlcnRpZXMnLCBkYXRhOiBkYXRhLCBiYWNrZ3JvdW5kQ29s"
    "b3I6IGJnLCBib3JkZXJDb2xvcjogYmQsIGJvcmRlcldpZHRoOiAxIH0sCiAgICAgICAgICAgICAgICAgICAgeyB0eXBlOiAnbGlu"
    "ZScsIGxhYmVsOiBEQU5HRVJfUENUICsgJyUgb2YgcmVudCcsIGRhdGE6IFt7eDogeG1pbiwgeTogREFOR0VSX1BDVH0sIHt4OiB4"
    "bWF4LCB5OiBEQU5HRVJfUENUfV0sCiAgICAgICAgICAgICAgICAgICAgICBib3JkZXJDb2xvcjogJyNkYzM1NDUnLCBib3JkZXJE"
    "YXNoOiBbNSw0XSwgYm9yZGVyV2lkdGg6IDEsIHBvaW50UmFkaXVzOiAwLCBmaWxsOiBmYWxzZSB9CiAgICAgICAgICAgICAgICBd"
    "CiAgICAgICAgICAgIH0sCiAgICAgICAgICAgIG9wdGlvbnM6IHsKICAgICAgICAgICAgICAgIHJlc3BvbnNpdmU6IHRydWUsIG1h"
    "aW50YWluQXNwZWN0UmF0aW86IGZhbHNlLAogICAgICAgICAgICAgICAgc2NhbGVzOiB7CiAgICAgICAgICAgICAgICAgICAgeDog"
    "eyBtaW46IHhtaW4sIG1heDogeG1heCwgdGl0bGU6IHtkaXNwbGF5OiB0cnVlLCB0ZXh0OiAnUmVudCBjaGFuZ2UgKCUpJ30sCiAg"
    "ICAgICAgICAgICAgICAgICAgICAgICB0aWNrczogeyBjYWxsYmFjazogZnVuY3Rpb24odil7IHJldHVybiAodj4wPycrJzonJykg"
    "KyB2ICsgJyUnOyB9IH0gfSwKICAgICAgICAgICAgICAgICAgICB5OiB7IGJlZ2luQXRaZXJvOiB0cnVlLCB0aXRsZToge2Rpc3Bs"
    "YXk6IHRydWUsIHRleHQ6ICdBY3R1YWwgZXhwZW5zZXMgKCUgb2YgcmVudCknfSwKICAgICAgICAgICAgICAgICAgICAgICAgIHRp"
    "Y2tzOiB7IGNhbGxiYWNrOiBmdW5jdGlvbih2KXsgcmV0dXJuIHYgKyAnJSc7IH0gfSB9CiAgICAgICAgICAgICAgICB9LAogICAg"
    "ICAgICAgICAgICAgcGx1Z2luczogewogICAgICAgICAgICAgICAgICAgIGxlZ2VuZDogeyBkaXNwbGF5OiBmYWxzZSB9LAogICAg"
    "ICAgICAgICAgICAgICAgIHRvb2x0aXA6IHsgY2FsbGJhY2tzOiB7IGxhYmVsOiBmdW5jdGlvbihjKSB7CiAgICAgICAgICAgICAg"
    "ICAgICAgICAgIHZhciByID0gYy5yYXcgJiYgYy5yYXcuX3I7IGlmICghcikgcmV0dXJuICcnOwogICAgICAgICAgICAgICAgICAg"
    "ICAgICByZXR1cm4gW3IubmFtZSwgJ1JlbnQgY2hhbmdlOiAnICsgKHIuY2hhbmdlPT1udWxsPyfigJQnOnBjdChyLmNoYW5nZSkp"
    "LAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICdBY3R1YWwvcmVudDogJyArIHIucGN0UmVudC50b0ZpeGVkKDEpICsg"
    "JyUnLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICdSZW50OiAnICsgZXVybyhyLnJlbnQpICsgJyAgQWN0dWFsOiAn"
    "ICsgZXVybyhyLmFjdHVhbCldOwogICAgICAgICAgICAgICAgICAgIH0gfSB9CiAgICAgICAgICAgICAgICB9CiAgICAgICAgICAg"
    "IH0KICAgICAgICB9KTsKICAgIH0KCiAgICBmdW5jdGlvbiByZW5kZXJSYW5raW5nKHJvd3MsIHllYXIpIHsKICAgICAgICB2YXIg"
    "cmsgPSByb3dzLmZpbHRlcihmdW5jdGlvbihyKXsgcmV0dXJuIHIucGN0UmVudCAhPSBudWxsOyB9KS5zbGljZSgpLnNvcnQoZnVu"
    "Y3Rpb24oYSxiKXsgcmV0dXJuIGIucGN0UmVudCAtIGEucGN0UmVudDsgfSk7CiAgICAgICAgdmFyIGxhYmVscyA9IHJrLm1hcChm"
    "dW5jdGlvbihyKXsgcmV0dXJuIHIubmFtZTsgfSk7CiAgICAgICAgdmFyIHZhbHMgPSByay5tYXAoZnVuY3Rpb24ocil7IHJldHVy"
    "biArci5wY3RSZW50LnRvRml4ZWQoMSk7IH0pOwogICAgICAgIHZhciBiZyA9IHJrLm1hcChmdW5jdGlvbihyKXsgcmV0dXJuIHIu"
    "cGN0UmVudCA+PSBEQU5HRVJfUENUID8gJ3JnYmEoMjIwLDUzLDY5LDAuOCknIDogJyMxN2EyYjgnOyB9KTsKICAgICAgICB2YXIg"
    "d3JhcCA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoJy5hbmFseXNpcy1jaGFydC13cmFwJyk7CiAgICAgICAgd3JhcC5zdHlsZS5o"
    "ZWlnaHQgPSBNYXRoLm1heCgyMDAsIHJrLmxlbmd0aCAqIDMwICsgNTApICsgJ3B4JzsKICAgICAgICBpZiAoY2hhcnQpIGNoYXJ0"
    "LmRlc3Ryb3koKTsKICAgICAgICB2YXIgY3R4ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ2FuYWx5c2lzQ2hhcnQnKS5nZXRD"
    "b250ZXh0KCcyZCcpOwogICAgICAgIGNoYXJ0ID0gbmV3IENoYXJ0KGN0eCwgewogICAgICAgICAgICB0eXBlOiAnYmFyJywKICAg"
    "ICAgICAgICAgZGF0YTogeyBsYWJlbHM6IGxhYmVscywgZGF0YXNldHM6IFt7IGxhYmVsOiAnQWN0dWFsICUgb2YgcmVudCcsIGRh"
    "dGE6IHZhbHMsIGJhY2tncm91bmRDb2xvcjogYmcsIG1heEJhclRoaWNrbmVzczogMjIgfV0gfSwKICAgICAgICAgICAgb3B0aW9u"
    "czogewogICAgICAgICAgICAgICAgaW5kZXhBeGlzOiAneScsIHJlc3BvbnNpdmU6IHRydWUsIG1haW50YWluQXNwZWN0UmF0aW86"
    "IGZhbHNlLAogICAgICAgICAgICAgICAgc2NhbGVzOiB7IHg6IHsgYmVnaW5BdFplcm86IHRydWUsIHRpdGxlOiB7ZGlzcGxheTp0"
    "cnVlLCB0ZXh0OidBY3R1YWwgZXhwZW5zZXMgKCUgb2YgcmVudCkg4oCUICcgKyB5ZWFyfSwgdGlja3M6IHsgY2FsbGJhY2s6IGZ1"
    "bmN0aW9uKHYpeyByZXR1cm4gdiArICclJzsgfSB9IH0gfSwKICAgICAgICAgICAgICAgIHBsdWdpbnM6IHsgbGVnZW5kOiB7IGRp"
    "c3BsYXk6ZmFsc2UgfSwgdG9vbHRpcDogeyBjYWxsYmFja3M6IHsgbGFiZWw6IGZ1bmN0aW9uKGMpeyByZXR1cm4gYy5wYXJzZWQu"
    "eCArICclIG9mIHJlbnQnOyB9IH0gfSB9CiAgICAgICAgICAgIH0KICAgICAgICB9KTsKICAgIH0KCiAgICBmdW5jdGlvbiByZW5k"
    "ZXJUYWJsZShyb3dzLCBzaW5nbGUpIHsKICAgICAgICB2YXIgYm9keSA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdhbmFseXNp"
    "c1RhYmxlQm9keScpOwogICAgICAgIGJvZHkuaW5uZXJIVE1MID0gJyc7CiAgICAgICAgcm93cy5zbGljZSgpLnNvcnQoZnVuY3Rp"
    "b24oYSxiKXsgcmV0dXJuIChiLnBjdFJlbnR8fDApIC0gKGEucGN0UmVudHx8MCk7IH0pLmZvckVhY2goZnVuY3Rpb24ocikgewog"
    "ICAgICAgICAgICB2YXIgdHIgPSBkb2N1bWVudC5jcmVhdGVFbGVtZW50KCd0cicpOwogICAgICAgICAgICBpZiAoci5kYW5nZXIp"
    "IHRyLmNsYXNzTmFtZSA9ICdkYW5nZXItcm93JzsKICAgICAgICAgICAgdmFyIGNoZyA9IChyLmNoYW5nZSA9PSBudWxsKSA/ICc8"
    "c3BhbiBjbGFzcz0iYW5hbHlzaXMtc3JjIj7igJQ8L3NwYW4+JwogICAgICAgICAgICAgICAgICAgICA6ICgnPHNwYW4gc3R5bGU9"
    "ImNvbG9yOicgKyAoci5jaGFuZ2UgPCAwID8gJyNkYzM1NDUnIDogJyMxZjdhMzcnKSArICc7Ij4nICsgcGN0KHIuY2hhbmdlKSAr"
    "ICc8L3NwYW4+Jyk7CiAgICAgICAgICAgIHZhciBwY3RDZWxsID0gKHIucGN0UmVudCA9PSBudWxsKSA/ICfigJQnIDogci5wY3RS"
    "ZW50LnRvRml4ZWQoMSkgKyAnJSc7CiAgICAgICAgICAgIHRyLmlubmVySFRNTCA9CiAgICAgICAgICAgICAgICAnPHRkPicgKyBl"
    "c2NhcGVIdG1sKHIubmFtZSkgKyAnIDxzcGFuIGNsYXNzPSJhbmFseXNpcy1zcmMiPignICsgci5zb3VyY2UgKyAnKTwvc3Bhbj48"
    "L3RkPicgKwogICAgICAgICAgICAgICAgJzx0ZCBjbGFzcz0ibnVtIj4nICsgZXVybyhyLnJlbnQpICsgJzwvdGQ+JyArCiAgICAg"
    "ICAgICAgICAgICAnPHRkIGNsYXNzPSJ0ZXh0LWNlbnRlciI+JyArIHIubGV0ICsgJy8xMjwvdGQ+JyArCiAgICAgICAgICAgICAg"
    "ICAnPHRkIGNsYXNzPSJudW0iPicgKyBldXJvKHIuYWN0dWFsKSArICc8L3RkPicgKwogICAgICAgICAgICAgICAgJzx0ZCBjbGFz"
    "cz0ibnVtIj4nICsgcGN0Q2VsbCArICc8L3RkPicgKwogICAgICAgICAgICAgICAgJzx0ZCBjbGFzcz0ibnVtIj4nICsgY2hnICsg"
    "JzwvdGQ+JyArCiAgICAgICAgICAgICAgICAnPHRkIGNsYXNzPSJ0ZXh0LWNlbnRlciI+JyArIChyLmRhbmdlciA/ICc8c3BhbiBj"
    "bGFzcz0iYW5hbHlzaXMtZmxhZyB3YXJuIj5XYXRjaDwvc3Bhbj4nIDogJzxzcGFuIGNsYXNzPSJhbmFseXNpcy1mbGFnIG9rIj5P"
    "Szwvc3Bhbj4nKSArICc8L3RkPic7CiAgICAgICAgICAgIGJvZHkuYXBwZW5kQ2hpbGQodHIpOwogICAgICAgIH0pOwogICAgfQoK"
    "ICAgIC8vIExvYWQgb24gZmlyc3Qgb3BlbiAodmFuaWxsYSBsaXN0ZW5lciDigJQgc2FtZSByZWFzb24gYXMgdGhlIFJlcG9ydCBt"
    "b2RhbCkuCiAgICBkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCdbZGF0YS10YXJnZXQ9IiNleHBlbnNlQW5hbHlzaXNNb2RhbCJd"
    "JykuZm9yRWFjaChmdW5jdGlvbihidG4pIHsKICAgICAgICBidG4uYWRkRXZlbnRMaXN0ZW5lcignY2xpY2snLCBmdW5jdGlvbigp"
    "IHsKICAgICAgICAgICAgaWYgKCFsb2FkZWQpIHsgbG9hZGVkID0gdHJ1ZTsgbG9hZCgpOyB9CiAgICAgICAgICAgIGVsc2UgaWYg"
    "KGNoYXJ0KSB7IHNldFRpbWVvdXQoZnVuY3Rpb24oKXsgY2hhcnQucmVzaXplKCk7IH0sIDI1MCk7IH0KICAgICAgICB9KTsKICAg"
    "IH0pOwp9KSgpOwo8L3NjcmlwdD4K"
])).decode('utf-8')

DESKTOP_BTN = (
    '\n        <!-- Desktop Analysis (hidden on mobile, in the More menu) -->\n'
    '        <button type="button" class="btn btn-info action-secondary" '
    'data-toggle="modal" data-target="#expenseAnalysisModal">\n'
    '            <i class="fas fa-chart-line"></i> Analysis\n'
    '        </button>'
)
MOBILE_BTN = (
    '\n                <button type="button" class="action-more-item" role="menuitem"\n'
    '                        data-toggle="modal" data-target="#expenseAnalysisModal">\n'
    '                    <i class="fas fa-chart-line"></i> Analysis\n'
    '                </button>'
)


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def find_template(root):
    for dirpath, _, files in os.walk(root):
        if '__pycache__' in dirpath:
            continue
        for fn in files:
            if fn.endswith('.html'):
                p = os.path.join(dirpath, fn)
                try:
                    if 'id="expenseReportModal"' in read(p):
                        return p
                except Exception:
                    pass
    return None


def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print("!! Run from the project root (the folder with manage.py).")
        sys.exit(1)

    tpl = find_template(root)
    if not tpl:
        print("!! Could not find act_expense.html (no template has "
              "id=\"expenseReportModal\"). Nothing changed.")
        sys.exit(1)
    print("Template: " + tpl + (" (dry run)" if DRY else ""))
    text = read(tpl)

    if 'expenseAnalysisModal' in text:
        print("   [skip] Analysis modal already installed — nothing to do.")
        return

    # 1) desktop Analysis button, after the desktop Report button
    dm = re.search(r'<button\b(?=[^>]*action-secondary)(?=[^>]*expenseReportModal)[^>]*>.*?</button>', text, re.S)
    if dm:
        text = text[:dm.end()] + DESKTOP_BTN + text[dm.end():]
        print("   [OK] inserted desktop Analysis button")
    else:
        print("   [WARN] couldn't find the desktop Report button — add the "
              "Analysis button next to it manually.")

    # 2) mobile Analysis item, after the mobile Report more-menu item
    mm = re.search(r'<button\b(?=[^>]*action-more-item)(?=[^>]*expenseReportModal)[^>]*>.*?</button>', text, re.S)
    if mm:
        text = text[:mm.end()] + MOBILE_BTN + text[mm.end():]
        print("   [OK] inserted mobile More-menu Analysis item")
    else:
        print("   [WARN] couldn't find the mobile Report menu item — add it manually.")

    # 3) the modal + JS, just before the last {% endblock %}
    idx = text.rfind('{% endblock %}')
    if idx == -1:
        print("   [WARN] no {% endblock %} found — appending modal at end of file.")
        text = text + "\n" + MODAL_BLOCK + "\n"
    else:
        text = text[:idx] + MODAL_BLOCK + "\n\n" + text[idx:]
        print("   [OK] inserted the Analysis modal + script before {% endblock %}")

    if DRY:
        print("   [dry-run] nothing written.")
        return
    bak = tpl + '.bak_analysis_modal'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8') as f:
            f.write(read(tpl))
    with open(tpl, 'w', encoding='utf-8') as f:
        f.write(text)
    print("   backup: " + os.path.basename(tpl) + ".bak_analysis_modal")
    print("\nDone. Hard-refresh the Expenses page — the Analysis button sits next to Report.")


if __name__ == '__main__':
    main()