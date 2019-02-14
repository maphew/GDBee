# Matt's notebook for GDBee

_Notes to myself as I come up to speed with GDBee, and maybe-possibly make contributions upstream._

## Getting started

Prep: install [Miniconda][1]. Then in a command shell:

    conda create -n gdbee
    activate gdbee
    conda install pip pyqt pandas gdal


~375 MB to download in 54 packages.

Through trial and error determined it's better to install with conda first rather than pip. Doing pip first I ended up with more than one version of numpy installed, and maybe other packages also.

It might uneccessary to install whole GDAL suite just for GDBee, but I don't feel like taking the time to dig into that just now.


Old way:

Run `python src\main.py` followed by `pip install x` until no more ModuleNotFound errors. When works, save requirements:

    pip freeze > requirements-install.txt

----
----

## Rocks in the path
### ogr isn't our ogr

    pip install ogr

    $ python src\main.py
    Traceback (most recent call last):
      File "src\main.py", line 7, in <module>
        from window import Window
      File "D:\code-external\GDBee\src\window.py", line 22, in <module>
        from tab_widget import TabWidget
      File "D:\code-external\GDBee\src\tab_widget.py", line 7, in <module>
        from tab import Tab
      File "D:\code-external\GDBee\src\tab.py", line 13, in <module>
        from geodatabase import Geodatabase
      File "D:\code-external\GDBee\src\geodatabase.py", line 5, in <module>
        ogr.UseExceptions()
    AttributeError: module 'ogr' has no attribute 'UseExceptions'


Nope! pypi ogr is not GDAL/OGR. Pypi ogr is _"One API for multiple git forges."_


`pip install GDAL` fails with _"error: Microsoft Visual C++ 14.0 is required. Get it with "Microsoft Visual C++ Build Tools": https://visualstudio.microsoft.com/downloads/"_

Oh right, I used to know that. Try:

    conda install gdal
    

----

### keywords.txt not found

`python src\main.py` then in GUI: _File >> New query_

```
$ python src\main.py
Traceback (most recent call last):
  File "D:\code-external\GDBee\src\window.py", line 215, in open_new_tab
    self.tab_widget.add_tab_page()
  File "D:\code-external\GDBee\src\tab_widget.py", line 46, in add_tab_page
    empty_tab = Tab()
  File "D:\code-external\GDBee\src\tab.py", line 92, in __init__
    self.highlighter = Highlighter(self.query.document())
  File "D:\code-external\GDBee\src\highlighter.py", line 80, in __init__
    r'completer_data\keywords.txt', 'r', encoding='utf-8') as f:
FileNotFoundError: [Errno 2] No such file or directory: 'completer_data\\keywords.txt'
```

Should be an easy fix, because if we change to `./src` first it Just Works(tm).


  [1]: https://conda.io/en/latest/miniconda.html
