# -*- coding: utf-8 -*-
# Importing librari

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

class IFA_scraper:

    def __init__(self, Chemicals, File_save):
        self._config = config()['web_sites']['IFA']
        self._queries = self._config['queries']
        self._url = self._config['url']
        self._existing, self.chemicals = checking_existing_chemicals_in_outfile(File_save, Chemicals)
        self.file_save = File_save
        self._now = datetime.datetime.now().strftime('%m_%d_%Y')


    def _dynamic_wait(self, XPath, action = None):
        delay = 5
        try:
            element = WebDriverWait(self._browser, delay).until(EC.presence_of_element_located((By.XPATH, XPath)))
            if not action:
                return element
            elif action == 'click':
                element.click()
            elif action == 'result':
                return True
        except TimeoutException:
            pass


    def _building_data_to_ifa(self, cas_non_hyphen, url, now):
        regex = re.compile(r'\-?([0-9]+\.?\,?[0-9]*[^\(\)\[\]])')
        Column_names = ['TWA [ppm]', 'TWA [mg/m³]', 'STEL [ppm]',
                        'STEL [mg/m³]']
        rows = self._browser.find_elements_by_xpath(self._queries['Row_table_of_limits'])[1:]
        df = pd.DataFrame()
        for row in rows:
            try:
                columns = row.find_elements_by_xpath(self._queries['Column_table_of_limits'])
                Limits = {'COUNTRY': [columns[0].find_element_by_xpath('./a').text]}
                Limits_aux = {col: re.findall(regex, columns[idx + 1].text) for idx, col in enumerate(Column_names)}
                Limits.update({col: [float(re.sub(',','.',val[0].strip())) \
                                if len(val) !=0 else None]\
                                for col, val in Limits_aux.items()})
                df_aux = pd.DataFrame(Limits)
                df = pd.concat([df, df_aux], ignore_index = True,
                                           sort = True, axis = 0)
            except NoSuchElementException:
                continue
        df.insert(0, 'CAS NUMBER', [cas_non_hyphen]*df.shape[0],
                  allow_duplicates = True)
        df['SOURCE'] = url
        df['DATE CONSULTED'] = now
        return df



    def _organizig_cas(self, CAS_NoN_Hyphen):
        CAS = {}
        for item in CAS_NoN_Hyphen:
            CAS_Hyphen = str()
            count = 0
            for number in reversed(str(int(item))):
                count += 1
                if (count == 2) | (count == 4):
                    CAS_Hyphen = '-' + CAS_Hyphen
                CAS_Hyphen =  number + CAS_Hyphen
            CAS[str(int(item))] = CAS_Hyphen
        return CAS


    def retrieving_exposure_limits(self):
        # Firing up Selenium
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
        self.chemicals = self._organizig_cas(self.chemicals)
        #self.chemicals = {'10380286':'10380-28-6'}
        df = pd.DataFrame()
        for cas_non_hyphen, cas_hyphen in self.chemicals.items():
            searching_cas_bar = self._dynamic_wait(self._queries['Searching_bar_CAS'])
            searching_cas_bar.send_keys(cas_hyphen)
            button_search = self._browser.find_element_by_xpath(self._queries['Searching_button'])
            button_search.click()
            try:
                self._browser.find_element_by_xpath(self._queries['No_result'])
            except NoSuchElementException:
                Val = False
                Val = self._dynamic_wait(self._queries['Results'], action = 'result')
                if Val:
                    df_chem = self._building_data_to_ifa(cas_non_hyphen, self._url, self._now)
                    df = pd.concat([df, df_chem], ignore_index = True,
                                               sort = True, axis = 0)
                    self._browser.back()
            self._dynamic_wait(self._queries['Clear_button'], action = 'click')
        df = df[['CAS NUMBER', 'COUNTRY', 'TWA [ppm]', 'TWA [mg/m³]', 'STEL [ppm]',
                        'STEL [mg/m³]', 'SOURCE', 'DATE CONSULTED']]
        if self._existing:
            df.to_csv(self.file_save, index = False, mode = 'a', sep = ',', header=False)
        else:
            df.to_csv(self.file_save, index = False, sep = ',')
        self._browser.close()


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
    Scraper = IFA_scraper(Chemicals, File_save)
    Scraper.retrieving_exposure_limits()
