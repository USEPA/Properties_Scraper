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
import datetime
import re
import argparse
import sys, os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/..')
from auxiliary import organizing_input, checking_existing_chemicals_in_outfile
from common import config

class NIST_scraper:

    def __init__(self, Chemicals, File_save):
        self._config = config()['web_sites']['NIST']
        self._queries = self._config['queries']
        self._url = self._config['url']
        self._existing, self.chemicals = checking_existing_chemicals_in_outfile(File_save, Chemicals)
        self.file_save = File_save
        self._now = datetime.datetime.now().strftime('%m_%d_%Y')
        self._dir_path = os.path.dirname(os.path.realpath(__file__))


    def _dynamic_wait(self, XPath, action = None):
        delay = 10
        try:
            element = WebDriverWait(self._browser, delay).until(EC.presence_of_element_located((By.XPATH, XPath)))
            if action == 'text':
                return element.text
            elif action == 'table':
                return element
        except TimeoutException:
            pass


    def _searching_headers(self, CAS):
        self._browser.get(self._url + 'cgi/cbook.cgi?ID=' + CAS + '&Units=SI&cTG=on&cTC=on&cTP=on&cIE=on')
        try:
            Name = self._dynamic_wait(self._queries['name'], action = 'text')
            Mass_text = self._browser.find_element_by_xpath(self._queries['mass']).text
            Molecular_Weight = float(re.search(r'([0-9]+\.?[0-9]*)', Mass_text).group(0))
            headers = [header.text for header in self._browser.find_elements_by_xpath(self._queries['headers'])]
            headers_names = list()
            for key in headers:
                if (key == 'Gas phase thermochemistry data') | (key == 'Condensed phase thermochemistry data') | (key == 'Phase change data') | (key == 'Gas phase ion energetics data'):
                    headers_names.append(key)
            return headers_names, Name, Molecular_Weight
        except AttributeError:
            return list(), None, None


    def _searching_properties(self, header, CAS):
        Properties = {}
        if (header == 'Gas phase thermochemistry data'):
            self._browser.get(self._url + 'cgi/cbook.cgi?ID=' + CAS + '&Units=SI&cTG=on')
            Table_gas_phase = self._dynamic_wait(self._queries['tables'], action = 'table')
            n_row = 0
            n_find = None
            for row in Table_gas_phase.find_elements_by_xpath(self._queries['row']):
                class_attribute = row.get_attribute('class').strip()
                n_row += 1
                if ('exp' == class_attribute) | ('cal' == class_attribute):
                    text_attribute = row.find_element_by_xpath(self._queries['column']).text.strip()
                    if (text_attribute == 'ΔcH°gas'):
                        n_find =  n_row
                        break
                else:
                    continue
            if (not n_find):
                Properties.update({'ΔcH°gas':[None, None]})
            else:
                Property = Table_gas_phase.find_element_by_xpath('.//child::tr[' + str(n_find) + ']//child::td[2]').text
                try:
                    Property =  float(Property.rstrip().split()[0])
                    Proterty_unit = Table_gas_phase.find_element_by_xpath('.//child::tr[' + str(n_find) + ']//child::td[3]').text
                    Properties.update({'ΔcH°gas': [Property, Proterty_unit]})
                except IndexError:
                    Properties.update({'ΔcH°gas':[None, None]})
            return Properties
        elif (header == 'Condensed phase thermochemistry data'):
            self._browser.get(self._url + 'cgi/cbook.cgi?ID=' + CAS + '&Units=SI&cTC=on')
            Table_condensed_phase = self._dynamic_wait(self._queries['tables'], action = 'table')
            n_row = 0
            n_find_Hl = None
            n_find_Hs = None
            for row in Table_condensed_phase.find_elements_by_xpath(self._queries['row']):
                class_attribute = row.get_attribute('class').strip()
                n_row += 1
                if ('exp' == class_attribute) | ('cal' == class_attribute):
                    text_attribute = row.find_element_by_xpath(self._queries['column']).text.strip()
                    if (text_attribute == 'ΔcH°liquid'):
                        n_find_Hl =  n_row
                    elif (text_attribute == 'ΔcH°solid'):
                        n_find_Hs = n_row
                    if (n_find_Hl) and (n_find_Hs):
                        break
                else:
                    continue
            if (not n_find_Hl):
                Properties.update({'ΔcH°liquid':[None, None]})
            else:
                Property = Table_condensed_phase.find_element_by_xpath('.//child::tr[' + str(n_find_Hl) + ']//child::td[2]').text
                try:
                    Property =  float(Property.rstrip().split()[0])
                    Proterty_unit = Table_condensed_phase.find_element_by_xpath('.//child::tr[' + str(n_find_Hl) + ']//child::td[3]').text
                    Properties.update({'ΔcH°liquid': [Property, Proterty_unit]})
                except NoSuchElementException:
                    Properties.update({'ΔcH°liquid':[None, None]})
            if (not n_find_Hs):
                Properties.update({'ΔcH°solid':[None, None]})
            else:
                Property = Table_condensed_phase.find_element_by_xpath('.//child::tr[' + str(n_find_Hs) + ']//child::td[2]').text
                try:
                    Property =  float(Property.rstrip().split()[0])
                    Proterty_unit = Table_condensed_phase.find_element_by_xpath('.//child::tr[' + str(n_find_Hs) + ']//child::td[3]').text
                    Properties.update({'ΔcH°solid': [Property, Proterty_unit]})
                except NoSuchElementException:
                     Properties.update({'ΔcH°solid':[None, None]})
            return Properties
        elif (header == 'Phase change data'):
            self._browser.get(self._url + 'cgi/cbook.cgi?ID=' + CAS + '&Units=SI&cTP=on')
            Table_phase_change = self._dynamic_wait(self._queries['tables'], action = 'table')
            n_row = 0
            n_find_Tf = None
            n_find_Tb = None
            for row in Table_phase_change.find_elements_by_xpath('.//tr'):
                class_attribute = row.get_attribute('class').strip()
                n_row += 1
                if ('exp' == class_attribute) | ('cal' == class_attribute):
                    text_attribute = row.find_element_by_xpath('.//td').text.strip()
                    if (text_attribute == 'Tfus'):
                        n_find_Tf =  n_row
                    elif (text_attribute == 'Tboil'):
                        n_find_Tb = n_row
                    if (n_find_Tf) and (n_find_Tb):
                        break
                else:
                    continue
            if (not n_find_Tf):
                Properties.update({'Tfus':[None, None]})
            else:
                Property = Table_phase_change.find_element_by_xpath('.//child::tr[' + str(n_find_Tf) + ']//child::td[2]').text
                try:
                    Property =  float(Property.rstrip().split()[0])
                    Proterty_unit = Table_phase_change.find_element_by_xpath('.//child::tr[' + str(n_find_Tf) + ']//child::td[3]').text
                    Properties.update({'Tfus': [Property, Proterty_unit]})
                except NoSuchElementException:
                    Properties.update({'Tfus':[None, None]})
            if (not n_find_Tb):
                Properties.update({'Tboil':[None, None]})
            else:
                Property = Table_phase_change.find_element_by_xpath('.//child::tr[' + str(n_find_Tb) + ']//child::td[2]').text
                try:
                    Property =  float(Property.rstrip().split()[0])
                    Proterty_unit = Table_phase_change.find_element_by_xpath('.//child::tr[' + str(n_find_Tb) + ']//child::td[3]').text
                    Properties.update({'Tboil': [Property, Proterty_unit]})
                except NoSuchElementException:
                    Properties.update({'Tboil':[None, None]})
            return Properties
        elif (header == 'Gas phase ion energetics data'):
            self._browser.get(self._url + 'cgi/cbook.cgi?ID=' + CAS + '&Units=SI&cIE=on')
            Table_ion_energetics = self._dynamic_wait(self._queries['tables'], action = 'table')
            n_row = 0
            n_find_IE = None
            n_find_PA = None
            n_find_GB = None
            n_cols = len(Table_ion_energetics.find_elements_by_xpath('.//child::tr[1]/th'))
            if n_cols == 4:
                n_find_IE = 2
            else:
                for row in Table_ion_energetics.find_elements_by_xpath('.//tr'):
                    n_row += 1
                    class_attribute = row.get_attribute('class').strip()
                    if ('exp' == class_attribute) | ('cal' == class_attribute):
                        text_attribute = row.find_element_by_xpath('.//td').text.strip()
                        if ('IE' in text_attribute):
                            n_find_IE =  n_row
                        elif ('Proton affinity' in text_attribute):
                            n_find_PA = n_row
                        elif ('Gas basicity' in text_attribute):
                            n_find_GB = n_row
                        if (n_find_IE) and (n_find_PA) and (n_find_GB):
                            break
                    else:
                        continue
            if (not n_find_IE):
                Properties.update({'IE':[None, None]})
            else:
                if n_cols == 4:
                    Property = Table_ion_energetics.find_element_by_xpath('.//child::tr[' + str(n_find_IE) + ']//child::td[1]').text
                    Property = re.findall(r'\-?[0-9]+\.?\,?[0-9]*', Property)[0]
                    Property =  float(Property.rstrip().split()[0])
                    Properties.update({'IE': [Property, 'eV']})
                else:
                    Property = Table_ion_energetics.find_element_by_xpath('.//child::tr[' + str(n_find_IE) + ']//child::td[2]').text
                    try:
                        Property = re.findall(r'\-?[0-9]+\.?\,?[0-9]*', Property)[0]
                        Property =  float(Property.rstrip().split()[0])
                        Proterty_unit = Table_ion_energetics.find_element_by_xpath('.//child::tr[' + str(n_find_IE) + ']//child::td[3]').text
                        Properties.update({'IE': [Property, Proterty_unit]})
                    except NoSuchElementException:
                        Properties.update({'IE':[None, None]})
            if (not n_find_PA):
                Properties.update({'Proton affinity':[None, None]})
            else:
                Property = Table_ion_energetics.find_element_by_xpath('.//child::tr[' + str(n_find_PA) + ']//child::td[2]').text
                try:
                    Property = re.findall(r'\-?[0-9]+\.?\,?[0-9]*', Property)[0]
                    Property =  float(Property.rstrip().split()[0])
                    Proterty_unit = Table_ion_energetics.find_element_by_xpath('.//child::tr[' + str(n_find_PA) + ']//child::td[3]').text
                    Properties.update({'Proton affinity': [Property, Proterty_unit]})
                except NoSuchElementException:
                    Properties.update({'Proton affinity':[None, None]})
            if (not n_find_GB):
                Properties.update({'Gas basicity':[None, None]})
            else:
                Property = Table_ion_energetics.find_element_by_xpath('.//child::tr[' + str(n_find_GB) + ']//child::td[2]').text
                try:
                    Property = re.findall(r'\-?[0-9]+\.?\,?[0-9]*', Property)[0]
                    Property =  float(Property.rstrip().split()[0])
                    Proterty_unit = Table_ion_energetics.find_element_by_xpath('.//child::tr[' + str(n_find_GB) + ']//child::td[3]').text
                    Properties.update({'Gas basicity': [Property, Proterty_unit]})
                except NoSuchElementException:
                    Properties.update({'Gas basicity':[None, None]})
            return Properties


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
        df = pd.DataFrame(columns = columns_order)
        for chemical in self.chemicals:
            try:
                headers, Name, Molecular_Weight = self._searching_headers(chemical)
                Properties = {'Name': Name, 'Molecular Mass': Molecular_Weight,
                              'Consulted Date': self._now, 'Source': self._url,
                              'CAS NUMBER': chemical}
                if len(headers) == 0:
                    df_aux = pd.DataFrame({key: [value] for key, value in Properties.items()})
                    df = pd.concat([df, df_aux], ignore_index = True,
                                           sort = True, axis = 0)
                    self._browser.back()
                else:
                    for header in headers:
                        Results = self._searching_properties(header, chemical)
                        for key, val in Results.items():
                            Properties.update({key: val[0], key + ' - Units': val[1]})
                        self._browser.back()
                        df_aux = pd.DataFrame({key: [value] for key, value in Properties.items()})
                        df = pd.concat([df, df_aux], ignore_index = True,
                                               sort = True, axis = 0)
            except NoSuchElementException:
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
    Scraper = NIST_scraper(Chemicals, File_save)
    Scraper.searching_information()
