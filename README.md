# CAMEO Scraper

<p align="center">
  <img src=https://github.com/jodhernandezbe/CAMEO_Scraper/blob/master/Diamond.png width="20%">
</p>

This is a Python script to gather information about the **National Fire Protection Association (NFPA) 704** for hazardous chemicals from CAMEO database.

## Requirements

In order to use this code you kneed the following requirements:

1. Google Chrome installed in your computer. However, you can modify the code and use other selenium driver (e.g., Firefox)
2. A .csv with a column named as CAS NUMBER
3. Install:
   - selenium (https://pypi.org/project/selenium/)
   - webdriver_manager (https://pypi.org/project/webdriver-manager/)
   - pandas (https://pypi.org/project/pandas/)
   - regex (https://pypi.org/project/regex/)
   - argparse (https://pypi.org/project/argparse/)

## How to use

To run the code from the Linux/Ubuntu terminal or Windows CMD:

1. You must move to the folder where is CAMEO_Scapper.py
2. Run the following command: 

```
   python CAMEO_Scapper.py -FR file_path_to_read_CAS -FS file_path_to_save_infomartion
```
The inputs accompanying the flags represent:

   - *file_path_to_read_CAS*: path of the file where you have the CAS numbers for searching.
   - *file_path_to_save_infomartion*: path of the file where you will save the information.

## Output

You will obtain a .csv file with the following columns:

| Column name | Description |
| ------------- | ------------- |
| CAS | CAS number for the chemical |
| HAZARD | Based on NFPA system (e.g., fire hazard) |
| VALUE | Value in the numbering scale ranging from 0 to 4 |
| DESCRIPTION | Explanation about the value (e.g., may detonate) |
