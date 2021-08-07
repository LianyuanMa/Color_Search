import time
import os
from elasticsearch import Elasticsearch
import requests
from piffle.iiif import IIIFImageClient
import json
import math


def create_es_client():
    es = Elasticsearch(
        hosts=os.environ['LOCAL_HOST'],
        http_auth=(
            os.environ['LOCAL_USER'],
            os.environ['LOCAL_PASS']
        )
    )
    accepting_connections = es.ping()
    while not accepting_connections:
        time.sleep(1)
        accepting_connections = es.ping()
    return es


index_name = 'lab_clustering_hex'


def Extracting_url_ID(response):  # run through each page and get the url
    for doc in response['hits']['hits']:
        ID_url_dict = {'id': doc['_id'], 'url': doc['_source']['state']['derivedData']['thumbnail']['url']}
        yield ID_url_dict  # this is convenient!


def clustering_api_request(image_url):  # send request to clustering API
    header = {'image-url': image_url}
    response = requests.get('http://api:80/image/cluster/', headers=header)
    dr = json.loads(response.text)
    return dr['center_list'], dr['center_number'], dr['cluster_size'], dr['cluster_proportion'], dr['lab_center_list']


def hex2rgb(hexcolor):
    rgb = [(hexcolor >> 16) & 0xff,
           (hexcolor >> 8) & 0xff,
           hexcolor & 0xff
           ]
    return rgb


def rgb2hex(rgbcolor):
    r, g, b = rgbcolor
    return hex((r << 16) + (g << 8) + b)


def rgblist2hexlist(rgbcolorlist):
    hexcolorlist = []
    for rgbcenter in rgbcolorlist:
        hexcenter = rgb2hex(rgbcenter)
        hexcolorlist.append(hexcenter)
    return hexcolorlist


def labcenters2searchterm(cluster_number, lab_centers_list):  ##color searching term.
    searchstr = str(cluster_number)
    for center in lab_centers_list:
        l = str(math.floor(center[0] * 10 / 255)).zfill(2)
        a = str(math.floor(center[1] / 16)).zfill(2)
        b = str(math.floor(center[2] / 16)).zfill(2)
        searchstr = searchstr + '_' + l + a + b
    return searchstr


def index_traversing(size, index_name):
    # run for 1 time and get a last_result
    es = create_es_client()
    #####document this after first run
    #     # create a new index
    #     es.indices.create(
    #     index='lab_clustering_hex',
    #     )
    #####
    response = es.search(
        index=os.environ['INDEX_NAME'],
        body={
            "query": {"match_all": {}},
            "size": size,
            "from": 0,
            "sort": {
                "_id": "desc",  # document ID.
            },
        }
    )
    # post the first 20 dictionaries
    for ID_url_dict in Extracting_url_ID(response):
        image_url = str(IIIFImageClient().init_from_url(ID_url_dict['url']).size(width=50))
        cluster_centers_list, cluster_number, cluster_size, cluster_proportion, lab_centers_list = clustering_api_request(
            image_url)  # Clustering in lab space.
        cluster_centers_list_hex = rgblist2hexlist(cluster_centers_list)
        searchstr = labcenters2searchterm(cluster_number, lab_centers_list)
        # update the document
        es.index(
            index=index_name,
            id=ID_url_dict['id'],
            body={
                "iiif_url": ID_url_dict['url'],
                "image_url": image_url,
                "cluster_info": {
                    "cluster_centers_list": cluster_centers_list,
                    "cluster_centers_list_hex": cluster_centers_list_hex,
                    "cluster_number": cluster_number,
                    "cluster_size": cluster_size,
                    "cluster_proportion": cluster_proportion,
                    "lab_centers_list": lab_centers_list,
                    "searchstr": searchstr,
                }

            }
        )
        print(ID_url_dict['id'])
    last_result_id = response['hits']['hits'][size - 1]['_id']
    counter = size  # just to make the waiting time less painful

    while len(response['hits']['hits']) == size:  # get in the loop!
        response = es.search(
            index=os.environ['INDEX_NAME'],
            body={
                "query": {"match_all": {}},
                "size": size,
                "from": 0,
                "sort": {
                    "_id": "desc",  # document ID.
                },
                "search_after": [last_result_id],
            }
        )
        for ID_url_dict in Extracting_url_ID(response):  # post the dictionaries
            image_url = str(IIIFImageClient().init_from_url(ID_url_dict['url']).size(width=50))
            cluster_centers_list, cluster_number, cluster_size, cluster_proportion, lab_centers_list = clustering_api_request(
                image_url)
            cluster_centers_list_hex = rgblist2hexlist(cluster_centers_list)
            searchstr = labcenters2searchterm(cluster_number, lab_centers_list)
            es.index(
                index=index_name,
                id=ID_url_dict['id'],
                body={
                    "iiif_url": ID_url_dict['url'],
                    "image_url": image_url,
                    "cluster_info": {
                        "cluster_centers_list": cluster_centers_list,
                        "cluster_centers_list_hex": cluster_centers_list_hex,
                        "cluster_number": cluster_number,
                        "cluster_size": cluster_size,
                        "cluster_proportion": cluster_proportion,
                        "lab_centers_list": lab_centers_list,
                        "searchstr": searchstr,
                    }

                }
            )
            print(ID_url_dict['id'])  # just to make the waiting time less painful
        last_result_id = ID_url_dict['id']  # update the last ID
        counter += size
        print(counter)


index_traversing(20, index_name)
