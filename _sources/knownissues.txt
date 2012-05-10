Known Issues
============

* ``KB #1``:  ``pyBot`` fails to start Selenium with an error message complaining about ``libX11.so.6``:  This is related to ``python`` invoking 32-bit X11 lib files instead of 64-bit when using Selenium web (see `this <http://bit.ly/J1cDG0>`_ for more information). Here's how to work around it though:

::

    sudo rm /usr/lib/libX11.so.6
    sudo ln -s /usr/lib64/libX11.so.6.3.0 /usr/lib/libX11.so.6
