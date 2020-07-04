# -*- coding: utf-8 -*-

# Importing libraries

import argparse
from osha.osha_scraper import *
from cameo.cameo_scraper import *
from ifa.ifa_scraper import *
from comptox.comptox_scraper import *
from nist.nist_scraper import *

if __name__ == '__main__':

    parser = argparse.ArgumentParser(argument_default = argparse.SUPPRESS)

    parser.add_argument('Option',
                        help = 'What website do you want to use:\
                        [A]: OSHA.\
                        [B]: CAMEO.\
                        [C]: CompTox.\
                        [D]: NIST.\
                        [E]: IFA.', \
                        type = str)

    parser.add_argument('-FR', '--Reading_file_path', nargs = '+',
                        help = 'Enter the file(s) with the CAS NUMBER.',
                        type = str,
                        required = False,
                        default = None)

    parser.add_argument('-FS', '--Saving_file_path',
                        help = 'Enter the path for the file with the database.',
                        required = True)

    args = parser.parse_args()

    Option = args.Option
    Reading_file_path = args.Reading_file_path
    File_save = args.Saving_file_path

    if Option == 'A':
        Scraper = OSHA_scraper(File_save)
        Scraper.exploring_links()
    elif Option == 'B':
        Chemicals = organizing_input(Reading_file_path)
        Scraper = CAMEO_scraper(Chemicals, File_save)
        Scraper.browsing()
    elif Option == 'C':
        Chemicals = organizing_input(Reading_file_path)
        Scraper = CompTox_scraper(Chemicals, File_save)
        Scraper.searching_information()
    elif Option == 'D':
        Chemicals = organizing_input(Reading_file_path)
        Scraper = NIST_scraper(Chemicals, File_save)
        Scraper.searching_information()
    elif Option == 'E':
        Chemicals = organizing_input(Reading_file_path)
        Scraper = IFA_scraper(Chemicals, File_save)
        Scraper.retrieving_exposure_limits()
