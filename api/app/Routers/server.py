from fastapi import APIRouter
from fastapi import  Header
from typing import Optional
import requests
from io import BytesIO
import numpy as np
import cv2
from sklearn.cluster import KMeans
from PIL import Image
from sklearn import metrics


router = APIRouter()

def extract_colour(image): #split the image into three: red, green, blue. Then merge the color histogram in a dictionary of lists which have int elements.
    rgbdict = {}
    for colour, colour_name in zip(image.split(), ["red", "green", "blue"]):
        #We need to zip the two lists, otherwise the for loop will regard the two lists as two elements of a new list.
        n,bins = np.histogram(colour, bins=256)
        # the return value bins is the width list of columns(from 0 to 256-1). We still need a sorted list.
        int_list_n = [int(i) for i in n]
        #n is in numpy.ndarrrary type. Zipping the two list will have elements as numpy.int64, which can not be
        # transfered into json. Variable type conversion is required.
        rgbdict[colour_name] = dict(zip(range(256), int_list_n)) 
    return rgbdict

@router.get("/image/rgbdata/")
async def read_items(image_url: Optional[str] = Header(None)): #fastapi will transfer the dash from - to _
    response = requests.get(image_url) #send get request to the image_url
    image = Image.open(BytesIO(response.content))

    rgbdict = extract_colour(image)

    return rgbdict

def Kmeans_cluster(img_arrary, k=3):
    """

    :param img_file: image file location
    :param k: number of clusters
    :return: clustering result, cluster labels, pixel numbers, RGB cluster centers list, clustering score, LAB cluster centers list
    """
    img = img_arrary  # RGB form
    data = cv2.cvtColor(img, cv2.COLOR_RGB2LAB) # LAB form.
    data = data.reshape((-1, 3)) # n*3 matrix
    kmeans = KMeans(n_clusters=k).fit(data) # K clusters

    pixel_label = kmeans.labels_ # cluster label array
    label_value = set(list(pixel_label)) # values of labels
    cluster_centers = kmeans.cluster_centers_ #Centroid
    label_count = [] # number of pixels clustered in each cluster
    for value in label_value:
        label_count.append(np.sum(pixel_label == value))

    cluster_centers_array = np.reshape(np.array(cluster_centers), (k, 1, 3))
    cluster_centers_array = cluster_centers_array.astype(np.uint8)
    rgb_array = cv2.cvtColor(cluster_centers_array, cv2.COLOR_LAB2RGB)
    rgb_array = np.reshape(rgb_array, (k, 3))
    lab_array = np.reshape(cluster_centers_array, (k, 3))
    # Calinski-Harabasz score
    ch_score = metrics.calinski_harabasz_score(data, pixel_label)

    return pixel_label, np.array(list(label_value)), np.array(label_count), rgb_array, ch_score, lab_array


@router.get("/image/cluster/")
async def read_items(image_url: Optional[str] = Header(None)): #fastapi will transfer the dash from - to _
    response = requests.get(image_url) #send get request to the image_url
    imgpil = Image.open(BytesIO(response.content))
    img = np.array(imgpil)

    max_score = -1000
    for k in range(3, 5):
        pixel_label, label_value, label_count, rgb_array, ch_score, lab_arrary = Kmeans_cluster(img, k)
        if max_score < ch_score:
            max_score = ch_score
            best_k = k
            best_centers = rgb_array
            best_pixcount = label_count
            best_lab_centers = lab_arrary

    center_list = best_centers.tolist()

    cluster_size = best_pixcount.tolist()
    lab_center_list = best_lab_centers.tolist()
    totalpix = sum(cluster_size)
    cluster_proportion = []
    for pix_count in cluster_size:
        pix_proportion = pix_count/totalpix
        cluster_proportion.append(pix_proportion)
    return {'center_list': center_list, 'center_number': best_k, 'cluster_size': cluster_size, 'cluster_proportion': cluster_proportion, 'lab_center_list': lab_center_list}



