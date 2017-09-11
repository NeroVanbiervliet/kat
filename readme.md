# Kat
Kat is a layered chat application built upon [telegram](https://telegram.org/). 

<img style="width:100%;" src="/screenshot.png">
*A screenshot of Kat running on ubuntu*

## Dependencies
Necessary to run/build from source: 
* python3
* PyQt4
* telethon

## Development
Updating the design can be done using the QtDesigner visual editor. Updating the .py file: `pyuic4 design.ui -o design.py`. Updating the image resources: `pyrcc4 -py3 resources.qrc -o resources_rc.py`. Building: `python3 setup.py build`

