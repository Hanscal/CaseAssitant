# -*- coding: utf-8 -*-

"""
@Time    : 2021/5/19 4:44 下午
@Author  : hcai
@Email   : hua.cai@unidt.com
"""

import json
from collections import defaultdict

def read_json(filepath):
    intent_dict = defaultdict(list)
    with open(filepath,'r') as f:
        data = json.load(f)
        for line in data['rasa_nlu_data']['common_examples']:
            text = line['text']
            intent = line['intent']
            entities = line['entities']
            intent_dict[intent].append({'text':text, 'entities':entities})
    return intent_dict

def convert_to_md(intent_dict):
    dict_all = {}
    for intent, value_list in intent_dict.items():
        dict_all[intent] = []
        for value in value_list:
            entities = value['entities']
            text = value['text']
            for e in entities:
                e_value = e['value']
                # e_start = text.find(e_value)
                # assert e_start == int(e['start'])
                e_type = e['entity']
                text = text.replace(e_value,'['+e_value+']('+e_type+')')
            dict_all[intent].append(text)
    return dict_all

def write_to_md(dict_all):
    with open('nlu_data.md', 'w') as fw:
        for intent, value_list in dict_all.items():
            fw.write('## intent:'+intent+'\n')
            for v in value_list:
                fw.write('- '+v+'\n')
            fw.write('\n')



if __name__ == '__main__':
    filepath = './nlu_data.json'
    intent_dict = read_json(filepath)
    dict_all = convert_to_md(intent_dict)
    write_to_md(dict_all)