import logging
from elasticsearch import Elasticsearch
_es = None


def connect_elasticsearch():
    _es = Elasticsearch([{'host': '35.196.63.188', 'port': 9200}])
    if _es.ping():
        print('Yay Connect')
    else:
        print('Awww it could not connect!')
    return _es


def insert_one(asin, json_data):
    _es.index(index="amazon", doc_type="product-title", id=asin, body=json_data)


def count():
    _es.count(index="amazon", doc_type="product-title")