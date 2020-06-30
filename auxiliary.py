#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import os

def organizing_input(Reading_file_path):
    Chemicals = list()
    for file in Reading_file_path:
        df_chemicals = pd.read_csv(file, usecols = ['CAS NUMBER'], dtype = {'CAS NUMBER': 'object'})
        df_chemicals = df_chemicals.loc[~df_chemicals['CAS NUMBER'].str.contains(r'[A-Z]')]
        df_chemicals['CAS NUMBER'] = df_chemicals['CAS NUMBER'].str.replace(r'\-', '')
        Chemicals = Chemicals + df_chemicals['CAS NUMBER'].tolist()
    del df_chemicals
    Chemicals = list(set(Chemicals))
    Chemicals.sort()
    return Chemicals


def checking_existing_chemicals_in_outfile(File_save, Chemicals):
    if os.path.exists(File_save):
        df_out = pd.read_csv(File_save,
                            usecols = ['CAS NUMBER'],
                            dtype = {'CAS NUMBER': 'object'})
        Chemicals = list(set(Chemicals) - set(df_out['CAS NUMBER'].unique().tolist()))
        return (True, Chemicals)
    else:
        return (False, Chemicals)
