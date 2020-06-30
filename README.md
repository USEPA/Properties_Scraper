# Properties scraper

<p align="center">
  <img src=https://github.com/jodhernandezbe/CAMEO_Scraper/blob/master/Diamond.png width="20%">
</p>

This is a Python script to gather from CAMEO Database, data about the classification of hazardous chemicals according to the **National Fire Protection Association** (NFPA). Also, the scripts retrieve exposure and physical properties from the **Occupational Safety and Health Administration** (OSHA)'s Occupational Chemical Database. 

## Requirements

In order to use this code you need the following requirements:

1. Google Chrome installed in your computer. However, you can modify the code and use other selenium driver (e.g., Firefox)
2. A .csv with a column named as CAS NUMBER (except for the OSHA database)
3. Install:
   - selenium (https://pypi.org/project/selenium/)
   - webdriver_manager (https://pypi.org/project/webdriver-manager/)
   - pandas (https://pypi.org/project/pandas/)
   - regex (https://pypi.org/project/regex/)
   - argparse (https://pypi.org/project/argparse/)
   - pyyaml (https://pyyaml.org/wiki/PyYAMLDocumentation)


## How to use

To run the code from the Linux/Ubuntu terminal or Windows CMD:

1. You must move to the folder where is Main.py
2. Run the following command: 

```
   python Main.py Option -FR file_path_to_read_CAS -FS file_path_to_save_infomartion
```

The positional argument Option has currently the following values:
    - A: for runing OSHA_Scraper.py
    - B: for runing CAMEO_Scraper.py

The inputs accompanying the flags represent:

   - *file_path_to_read_CAS*: path of the file where you have the CAS numbers for searching (except for OSHA database)
   - *file_path_to_save_infomartion*: path of the file where you will save the information.

Additionally, you can use each scraper separately, for example:

```
   python CAMEO_Scraper.py -FR file_path_to_read_CAS -FS file_path_to_save_infomartion
```
