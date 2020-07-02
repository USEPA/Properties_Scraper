#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
import datetime
import re
import argparse
import sys, os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/..')
from auxiliary import organizing_input, checking_existing_chemicals_in_outfile
from common import config

class CAMEO_scraper:

    def __init__(self, Chemicals, File_save):
        self._config = config()['web_sites']['CAMEO']
        self._queries = self._config['queries']
        self._url = self._config['url']
        self._existing, self.chemicals = checking_existing_chemicals_in_outfile(File_save, Chemicals)
        self.file_save = File_save
        self._now = datetime.datetime.now().strftime('%m_%d_%Y')


    def browsing(self):
        options = Options()
        options.headless = True
        options.add_argument('--disable-notifications')
        options.add_argument('--no-sandbox')
        options.add_argument('--verbose')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument("--log-level=3")
        options.add_argument('--hide-scrollbars')
        self._browser = webdriver.Chrome(ChromeDriverManager().install(), chrome_options = options)
        self._browser.get(self._url)
        df_result = pd.DataFrame()
        print('-' * 45)
        print('{:15s} {:15s}'.format('CAS Number', 'Found?'))
        print('-' * 45)
        for chemical in self.chemicals:
            result = self._searching_chemicals(chemical)
            if not result.empty:
                print('{:15s} {:15s}'.format(chemical, 'Yes'))
                result['CAS NUMBER'] = chemical
            else:
                print('{:15s} {:15s}'.format(chemical, 'No'))
                result = pd.DataFrame({'HAZARD': [None],
                                      'VALUE': [None],
                                      'DESCRIPTION': [None],
                                      'CAS NUMBER': [chemical]})
            df_result = pd.concat([result, df_result], ignore_index = True,
                                       sort = True, axis = 0)
            href = self._browser.find_element_by_xpath(self._queries['new_search']).get_attribute('href')
            self._browser.get(href)
        self._browser.close()
        df_result['DATE CONSULTED'] = self._now
        if self._existing:
            df_result.to_csv(self.file_save, index = False, mode = 'a', sep = ',', header=False)
        else:
            df_result.to_csv(self.file_save, index = False, sep = ',')


    def _searching_chemicals(self, chemical):
        # Looking for the searching bar
        searching_bar = self._queries['cas_searching_bar']
        self._dynamic_wait(searching_bar, chem = chemical)
        # Confirming the appearance of results
        result_header = self._queries['search_result']
        result =  self._dynamic_wait(self._queries['pages'], action = 'wait_1')
        return result


    def _gathering_results(self):
        try:
            text_navigator = self._browser.find_element_by_xpath(self._queries['pages']).text
            regex = re.compile(r'Page 1 of ([0-9]+)\s+Go to page:')
            n_pages = int(re.search(regex, text_navigator).group(1))
            counting_pages = 0
            no_found_result = True
            for page in range(n_pages):
                hrefs = [link.get_attribute('href') for link in self._browser.find_elements_by_xpath(self._queries['links'])]
                for href in hrefs:
                    self._browser.get(href)
                    table = self._queries['table']
                    result = self._dynamic_wait(table, action = 'wait_2')
                    self._browser.execute_script('window.history.go(-1)')
                    if not result.empty:
                        no_found_result = False
                        break
                if not result.empty:
                    no_found_result = False
                    break
                if n_pages != 1 and page != n_pages - 1:
                    next_button = self._queries['next']
                    self._dynamic_wait(next_button, action = 'click')
        except AttributeError or StaleElementReferenceException:
            result = pd.DataFrame()
        return result


    def _retrieving_info_from_table(self):
        hazards = self._browser.find_elements_by_xpath(self._queries['hazard'])
        values = self._browser.find_elements_by_xpath(self._queries['value'])
        descriptions = self._browser.find_elements_by_xpath(self._queries['description'])
        hazard_list = list()
        value_list = list()
        description_list = list()
        result = pd.DataFrame()
        for idx, hazard in enumerate(hazards):
            hazard_list.append(hazard.text)
            value_list.append(values[idx].text)
            description_list.append(descriptions[idx].text)
        result = pd.DataFrame({'HAZARD': hazard_list,
                                'VALUE': value_list,
                                'DESCRIPTION': description_list})
        return result


    def _dynamic_wait(self, XPath, action = 'send', chem = None):
        delay = 5
        try:
            element = WebDriverWait(self._browser, delay).until(EC.presence_of_element_located((By.XPATH, XPath)))
            if action == 'send':
                element.send_keys(chem)
                self._browser.find_element_by_xpath(self._queries['cas_buttton']).click()
            elif action == 'wait_1':
                result = self._gathering_results()
                return result
            elif action == 'wait_2':
                result = self._retrieving_info_from_table()
                return result
            elif action == 'click':
                element.click()
        except TimeoutException:
            return pd.DataFrame()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(argument_default = argparse.SUPPRESS)

    parser.add_argument('-FR', '--Reading_file_path', nargs = '+',
                        help = 'Enter the file(s) with the CAS NUMBER.',
                        type = str)

    parser.add_argument('-FS', '--Saving_file_path',
                        help = 'Enter the path for the file with the database.',
                        required = True)

    args = parser.parse_args()


    Reading_file_path = args.Reading_file_path
    Chemicals = organizing_input(Reading_file_path)
    File_save = args.Saving_file_path
    Scraper = CAMEO_Scraper(Chemicals, File_save)
    Scraper.browsing()
