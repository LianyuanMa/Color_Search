import os
from elasticsearch import Elasticsearch
import requests
from piffle.iiif import IIIFImageClient
import json

# connect to ElasticSearch
local_es = Elasticsearch(
    hosts=os.environ['LOCAL_HOST'],
    http_auth=(
        os.environ['LOCAL_USER'],
        os.environ['LOCAL_PASS']
    )
)

# create a new index
# local_es.indices.create(
#     index='id_url_index',
#
# )
index_name = 'id_url_index'


def Extracting_url_ID(response):  # run through each page and get the url
    for doc in response['hits']['hits']:
        ID_url_dict = {'id': doc['_id'], 'url': doc['_source']['state']['derivedData']['thumbnail']['url']}
        yield ID_url_dict  # this is convenient!

def clustering_api_request(image_url): #send request to clustering API
    header = {'image-url': image_url}
    response = requests.get('http://localhost/image/cluster/', headers = header)
    dr = json.loads(response.text)
    return dr['center_list'], dr['center_number']

def index_traversing(es_object, size, index_name):
    # run for 1 time and get a last_result
    response = es_object.search(
        index=os.environ['INDEX_NAME'],
        body={
            "query": {"match_all": {}},
            "size": size,
            "from": 0,
            "sort": {
                "_id": "asc",  # document ID.
            },
        }
    )
    # post the first 20 dictionaries
    for ID_url_dict in Extracting_url_ID(response):
        image_url = str(IIIFImageClient().init_from_url(ID_url_dict['url']).size(width=500))
        cluster_centers_list, cluster_number = clustering_api_request(image_url)   #this always goes wrong. Connection error.
        es_object.index(
            index=index_name,
            id=ID_url_dict['id'],
            body={
                "iiif_url": ID_url_dict['url'],
                "image_url": image_url,
                "cluster_infor": {
                    "cluster_centers_list": cluster_centers_list,
                    "cluster_number": cluster_number
                }

            }
        )
        print(ID_url_dict['id'])
    last_result_id = response['hits']['hits'][size - 1]['_id']
    counter = size  # just to make the waiting time less painful

    while len(response['hits']['hits']) == size:  # get in the loop!
        response = es_object.search(
            index=os.environ['INDEX_NAME'],
            body={
                "query": {"match_all": {}},
                "size": size,
                "from": 0,
                "sort": {
                    "_id": "asc",  # document ID.
                },
                "search_after": [last_result_id],
            }
        )
        for ID_url_dict in Extracting_url_ID(response):  # post the dictionaries
            image_url = str(IIIFImageClient().init_from_url(ID_url_dict['url']).size(width=500))
            cluster_centers_list, cluster_number = clustering_api_request(image_url)
            es_object.index(
                index=index_name,
                id=ID_url_dict['id'],
                body={
                    "iiif_url": ID_url_dict['url'],
                    "image_url": image_url,
                    "cluster_infor":{
                        "cluster_centers_list": cluster_centers_list,
                        "cluster_number": cluster_number
                    }

                }
            )
            print(ID_url_dict['id'])  # just to make the waiting time less painful
        last_result_id = ID_url_dict['id']  # update the last ID
        counter += size
        print(counter)


index_traversing(local_es, 20, index_name)
