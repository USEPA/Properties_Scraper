# -*- coding: utf-8 -*-
# Importing libraries

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pandas as pd
import datetime, time
import re
import argparse
import sys, os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/..')
from auxiliary import organizing_input, checking_existing_chemicals_in_outfile
from common import config

class CompTox_scraper:

    def __init__(self, File_save, Chemicals):
        self._config = config()['web_sites']['CompTox']
        self._queries = self._config['queries']
        self._url = self._config['url']
        self._existing, self.chemicals = checking_existing_chemicals_in_outfile(File_save, Chemicals)
        self.file_save = File_save
        self._now = datetime.datetime.now().strftime('%m_%d_%Y')
        self._dir_path = os.path.dirname(os.path.realpath(__file__))


    def _visit(self, dsstox_substance_id, option):
        self._browser.get(self._url + '/dsstoxdb/results?search=' + dsstox_substance_id + '#' + option)


    def _opening_dsstox_identifiers_and_casrn(self):
        DSSTox_Identifiers = pd.read_csv(self._dir_path + '/DSSTox_Identifiers_and_CASRN.csv',
                                        header = 0,
                                        sep = ',',
                                        low_memory = False,
                                        usecols = ['casrn',
                                                   'dsstox_substance_id',
                                                   'preferred_name'])
        DSSTox_Identifiers['casrn'] = DSSTox_Identifiers['casrn'].str.replace(r'\-', '')
        DSSTox_Identifiers.rename(columns = {'casrn': 'CAS NUMBER',
                                             'dsstox_substance_id': 'DSSTOX ID',
                                             'preferred_name': 'PREFERRED NAME'},
                                  inplace = True)
        self.chemicals = pd.merge(DSSTox_Identifiers, self.chemicals,
                                  on = ['CAS NUMBER'], how = 'right')


    def _searching_properties(self):
        Data = {}
        regex_property = re.compile(r'(\-?[0-9]+\.?[0-9]*[eE]?[\-\+]?[0-9]*)\s?\(?[0-9]*\)?')
        try:
            self._browser.find_element_by_xpath(self._queries['no_matching'])
            return Data
        except NoSuchElementException:
            try:
                table = self._dynamic_wait(self._queries['properties/env-fate-transport']['table'])
                rows = table.find_elements_by_xpath(self._queries['properties/env-fate-transport']['row'])[1:]
                for row in rows:
                    columns = row.find_elements_by_xpath(self._queries['properties/env-fate-transport']['column'])
                    columns = [val for idx, val in enumerate(columns) if idx in [0, 1, 2, 3, 4, 7]]
                    Searching = ['Property', 'Experimental average',
                                 'Predicted average', 'Experimental median',
                                 'Predicted median', 'Unit']
                    Aux_dict = dict()
                    for idx, val in enumerate(Searching):
                        if idx == 0:
                            Name = columns[idx].text.strip()
                        elif idx == 5:
                            Unit = columns[idx].text.strip()
                            if Unit and Unit != '-':
                                Data.update({Name + ' - Units': Unit})
                        else:
                            condition = re.match(regex_property, columns[idx].text.strip())
                            if condition:
                                result = re.search(regex_property, columns[idx].text).group(1)
                            else:
                                result = None
                            Aux_dict.update({val: result})
                    Scores = {'Experimental median': 1, 'Experimental average': 2,
                             'Predicted median': 3, 'Predicted average': 4}
                    for key, value in Scores.items():
                        Property = Aux_dict[key]
                        Score = value
                        if Property:
                            Data.update({Name: Property,
                                        Name + ' - Score': Score})
                            break
                return Data
            except AttributeError:
                return Data


    def _searching_details(self):
        Data = {'Molecular Mass': [None], 'Data Quality - CompTox': [None]}
        try:
            # Opening panel molecular weight
            self._dynamic_wait(self._queries['details']['close_collapse_panel_mass'], action = 'click')
            open_panel = self._browser.find_element_by_xpath(self._queries['details']['open_collapse_panel_mass'])
            if open_panel:
                # Fetching molecular weight
                time.sleep(3) # It is needed an static wait
                regex = re.compile(r'[0-9]+\.?[0-9]*')
                text_mass = self._browser.find_element_by_xpath(self._queries['details']['weight']).text
                weight = float(re.sub(r'[a-zA-Z]*','',re.sub(r'\/\n\:','',re.search(regex, text_mass)[0])))
            # Opening panel DQ level
            self._browser.find_element_by_xpath(self._queries['details']['close_collapse_panel_dq']).click()
            open_panel = self._browser.find_element_by_xpath(self._queries['details']['open_collapse_panel_dq'])
            if open_panel:
                # DQ Level
                time.sleep(3)
                DQ = self._browser.find_element_by_xpath(self._queries['details']['data_quality']).text
            Data = {'Molecular Mass': [weight], 'Data Quality - CompTox': [DQ]}
            return Data
        except AttributeError:
            return Data
        except NameError:
            return Data
        except NoSuchElementException:
            return Data


    def _dynamic_wait(self, XPath, action = None):
        delay = 10
        try:
            element = WebDriverWait(self._browser, delay).until(EC.presence_of_element_located((By.XPATH, XPath)))
            if action == 'click':
                element.click()
            elif action == 'dialog':
                element.find_element_by_xpath(self._queries['close_dialog_window']).click()
            else:
                return element
        except TimeoutException:
            pass


    def searching_information(self):
        columns_order = pd.read_csv(self._dir_path + '/Columns_order.txt',
                                        header = None)
        columns_order = columns_order[0].tolist()
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
                                        options = options)
        self.chemicals = pd.DataFrame({'CAS NUMBER': self.chemicals})
        self._opening_dsstox_identifiers_and_casrn()
        df = pd.DataFrame()
        for idx, row in self.chemicals.iterrows():
            dsstox_substance_id = row['DSSTOX ID']
            cas = row['CAS NUMBER']
            preferred_name = row['PREFERRED NAME']
            try:
                if not dsstox_substance_id:
                    df_aux = pd.DataFrame({'CAS NUMBER': [cas],
                                          'Consulted Date': [self._now]})
                else:
                    Properties = {'CAS NUMBER': [cas],
                                  'Data Source': [self._url + '/dsstoxdb/results?search=' + dsstox_substance_id],
                                  'Consulted Date': [self._now],
                                  'PREFERRED NAME': [preferred_name],
                                  'DSSTOX ID': [dsstox_substance_id]}
                    list_tabs = ['properties', 'env-fate-transport', 'details']
                    for tab in list_tabs:
                        self._visit(dsstox_substance_id, tab)
                        self._dynamic_wait(self._queries['dialog_window'], action = 'dialog')
                        if tab == 'details':
                            Properties.update(self._searching_details())
                        else:
                            Properties.update(self._searching_properties())
                        self._browser.back()
                        time.sleep(2)
                    df_aux = pd.DataFrame(Properties)
                df = pd.concat([df, df_aux], ignore_index = True,
                                           sort = True, axis = 0)
            except TimeoutException:
                continue
        df = df[columns_order]
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
    Scraper = CompTox_scraper(File_save, Chemicals)
    Scraper.searching_information()
