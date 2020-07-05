# Properties scraper

<p align="center">
  <img src=https://github.com/jodhernandezbe/CAMEO_Scraper/blob/master/Diamond.png width="20%">
</p>

This is a Python program to massively gather information about exposure limits and physical properties from different publicly-available sources:

| Organization | Data source| Information | Website |
| ------------- | ------------- | ------------- | ------------- |
| National Oceanic and Atmospheric Administration (NOAA) | Computer-Aided Management of Emergency Operations (CAMEO) Database  | National Fire Protection Association (NFPA) 704 classification for hazardous chemicals | https://cameochemicals.noaa.gov/search/simple  |
| Occupational Safety and Health Administration (OSHA) | Occupational Chemical Database | Physcial properties and exposure limits | https://www.osha.gov/chemicaldata |
| National Institute of Standards and Technology (NIST) | Chemistry WebBook | Physical properties | https://webbook.nist.gov/ |
| Environmental Protection Agency (EPA) | CompTox Chemicals Dashboard | Environmental fate, transport and physical properties | https://comptox.epa.gov/dashboard |
| Institute for Occupational Safety and Health of the German Social Accident Insurance (IFA) | GESTIS Substance Database | International limit values | http://limitvalue.ifa.dguv.de |

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

1. You must move to the folder where is main.py
2. Run the following command: 

```
   python main.py Option -FR file_path_to_read_CAS -FS file_path_to_save_infomartion
```

The inputs accompanying the flags represent:

   - *file_path_to_read_CAS*: path of the file where you have the CAS numbers for searching (except for OSHA database).
   - *file_path_to_save_infomartion*: path of the file where you will save the information.
   
The positional argument *Option* has the following values currently:

  - A: for running osha_scraper.py.
  - B: for running cameo_scraper.py.
  - C: for running comptox_scraper.py.
  - D: for running nist_scraper.py.
  - E: for running ifa_scraper.py

Additionally, you can use each scraper separately, for example:

```
   python cameo_scraper.py -FR file_path_to_read_CAS -FS file_path_to_save_infomartion
```
