# -*- coding: utf-8 -*-
# Importing libraries

import os, sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import re
import argparse
import datetime
import numpy as np

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/..')
from common import config

# Class that handles database
class OSHA_scraper:

    def __init__(self, File_save):
        self._config = config()['web_sites']['OSHA']
        self._queries = self._config['queries']
        self._url = self._config['url']
        self.file_save = File_save
        self._now = datetime.datetime.now().strftime('%m_%d_%Y')
        self._dir_path = os.path.dirname(os.path.realpath(__file__))


    def _dynamic_wait(self, XPath):
        delay = 10
        try:
            element = WebDriverWait(self._browser, delay).until(EC.presence_of_element_located((By.XPATH, XPath)))
            return element
        except TimeoutException:
            pass


    def _visit(self):
        options = Options()
        options.headless = True
        options.add_argument('--disable-notifications')
        options.add_argument('--no-sandbox')
        options.add_argument('--verbose')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument("--log-level=3")
        options.add_argument('--hide-scrollbars')
        self._browser = webdriver.Chrome(ChromeDriverManager().install(), \
                                        chrome_options = options)
        self._browser.get(self._url)
        self.main_table = self._dynamic_wait(self._queries['main_table'])


    def _retrieving_info(self, results_table, properties_to_OSHA):
        regex_name = re.compile(r'^%?([₀-₉⁰-⁹0-9a-zA-Z\-\,\s\.&\(\)\#\%\>\<\≥\≤]*)')
        regex_cas = re.compile(r'([-?[0-9]{1,}]*)')
        regex_property_1 = re.compile(r'\-?([1-9]+\.?[0-9]*)\s?([\%pbµmlg\/³3]{1,}[^°Fat\(\)\s]{0,})\s?\(?.*\)?')
        regex_property_2 = re.compile(r'([0-9]+\.?[0-9]*)')
        regex_exposure = re.compile(r'([0-9]+\.?\,?[0-9]*)\s?([\%pmbgfiercµ\/³²]{0,}).*')
        Results = {}
        # Name of the substance
        Name = results_table.find_element_by_xpath(self._queries['chemical_name']).text
        Name = re.sub(u'\u03B4','delta',\
               re.sub(u'\u03B2','beta', \
               re.sub(u'\u03B1','alpha',Name)))
        Name = re.findall(regex_name, Name)[0]
        print(Name)
        Results.update({'SUBSTANCE': [Name]})
        tables = results_table.find_elements_by_xpath(self._queries['specific_tables'])
        # Chemical Identification
        CAS = tables[0].find_element_by_xpath(self._queries['cas_number']).text
        if re.match(regex_cas, CAS):
            CAS = re.search(regex_cas, CAS).group(1).rstrip()
            CAS_non = re.sub('-', '', CAS)
        else:
            CAS = None
            CAS_non = None
        Results.update({'CAS NUMBER': [CAS], 'CAS NON-HYPHEN': [CAS_non]})
        Dict_table = {'Physical': 1, 'Exposure': 6}
        for table_name, properties in properties_to_OSHA.items():
            Specific_table = tables[Dict_table[table_name]]
            for property_name in properties:
                proper_text = Specific_table.find_element_by_xpath(self._queries[table_name][property_name]).text
                if table_name == 'Physical':
                    if (property_name == 'Lower explosive limit (LEL)') or (property_name == 'Upper explosive limit (UEL)'):
                        datum = re.findall(regex_property_1, proper_text)
                        if datum:
                            if (datum[0][0]) and (datum[0][1]):
                                Results.update({property_name: [datum[0][0]],
                                                property_name + ' - Units': [datum[0][1]]})
                    else:
                        datum = re.findall(regex_property_2, proper_text)
                        if datum:
                            Results.update({property_name: [datum[0]]})
                else:
                    datum = re.findall(regex_exposure, proper_text)
                    if len(datum) != 0:
                        if (datum[0][0]) and (datum[0][1]):
                            Results.update({property_name: [datum[0][0]],
                                            property_name + ' - Units': [datum[0][1]]})
                        else:
                            Results.update({property_name: [datum[0][0]],
                                            property_name + ' - Units': ['ppm']})
                del datum
            del Specific_table
        return Results


    def exploring_links(self):
        self._visit()
        df_properties_to_OSHA = pd.read_csv(self._dir_path + '/Properties_to_OSHA.txt',
                                        header = None)
        columns_order = pd.read_csv(self._dir_path + '/Columns_order.txt',
                                        header = None)
        columns_order = columns_order[0].tolist()
        kind_of_table = df_properties_to_OSHA[0].unique().tolist()
        Properties_to_OSHA = {k_t: [row.iloc[1] for idx, row in df_properties_to_OSHA.loc[df_properties_to_OSHA[0] == k_t].iterrows()] for k_t in kind_of_table}
        del df_properties_to_OSHA
        hrefs = [element.get_attribute('href') for element in self.main_table.find_elements_by_xpath(self._queries['links'])]
        df = pd.DataFrame()
        for href in hrefs:
            self._browser.get(href)
            results_table = self._dynamic_wait(self._queries['body_result'])
            try:
                properties = self._retrieving_info(results_table, Properties_to_OSHA)
                df_aux = pd.DataFrame(properties)
                df_aux['SOURCE'] = href
                df = pd.concat([df, df_aux], ignore_index = True,
                                            sort = True, axis = 0)
            except UnicodeEncodeError:
                continue
        self._browser.close()
        df['DATE CONSULTED'] = self._now
        df = df[columns_order]
        df.to_csv(self.file_save, index = False, sep = ',')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(argument_default = argparse.SUPPRESS)

    parser.add_argument('-FS', '--Saving_file_path',
                        help = 'Enter the path for the file with the database.',
                        required = True)

    args = parser.parse_args()

    File_save = args.Saving_file_path
    Scraper = OSHA_scraper(File_save)
    Scraper.exploring_links()
