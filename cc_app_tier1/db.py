# app.py
from flask import Flask, jsonify  # import flask
from pymongo import MongoClient
import populartimes
import json
from time import time, ctime
from datetime import datetime
import threading

# app = Flask(__name__)             # create an app instance

client = MongoClient("mongodb+srv://<usr:pwd>@cc-project2-cluster-1n756.gcp.mongodb.net/test?retryWrites=true&w=majority")  # host uri
#client = MongoClient("mongodb://127.0.0.1:27017")
db = client.CCProject  # Select the database
tasks_collection = None
latest_collection = None

days = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}


def get_current_crowd(place_ids, dest_place_id, api_key, cur_time, cur_zone):
    time1 = int(round(time() * 1000))
    current_time = cur_time
    print(cur_time)
    todays_day = cur_time[:3]
    print(todays_day)
    occ_map = {}

    if cur_zone == 'America/New_York':
        tasks_collection = db.NewYorkAnalytics  # Select the collection name
        latest_collection = db.NewYorkPopularTime
    elif cur_zone == 'America/Phoenix':
        tasks_collection = db.PhoenixAnalytics  # Select the collection name
        latest_collection = db.PhoenixPopularTime
    else:
        tasks_collection = db.OtherZonesAnalytics  # Select the collection name
        latest_collection = db.OtherZonesPopularTime

    current_hour = get_time_InHour(current_time)
    print("Current hour: " + str(current_hour))
    itr = latest_collection.find({"_id": {"$in": place_ids}})
    cnt = itr.count()
    place_set = set(place_ids)

    for i in range(cnt):
        # stored_time = itr[0]["Time"]
        place_set.remove(itr[i]["_id"])

        if itr[i]["Data"] == "NA":
            continue
        else:
            if itr[i]["_id"] == dest_place_id:
                current_occupancy = itr[i]["Data"]["data"]
            else:
                current_occupancy = itr[i]["Data"]["data"][current_hour]

        occ_map[itr[i]["_id"]] = current_occupancy

    print(len(place_set))
    insert_list = []
    place_set = list(place_set)

    pop_dict = {}
    thrd_list = []

    def calculate_populatime(place):
        pop_dict[place] = populartimes.get_id(api_key, place)

    for place in place_set:
        thrd_list.append(threading.Thread(target=calculate_populatime, args=(place,)))
        thrd_list[-1].start()

    for thrd in thrd_list:
        thrd.join()

    for place in place_set:
        time_popular = pop_dict[place]
        if "populartimes" not in time_popular:
            insert_list.append({"_id": place, 'Zone': cur_zone, 'Data': "NA"})
            continue
        else:
            if place == dest_place_id:
                current_occupancy = time_popular['populartimes'][days[todays_day]]["data"]
            else:
                current_occupancy = time_popular['populartimes'][days[todays_day]]["data"][current_hour]

        insert_list.append({"_id": place, 'Zone': cur_zone, 'Data': time_popular['populartimes'][days[todays_day]]})
        occ_map[place] = current_occupancy

    if len(insert_list) > 0:
        latest_collection.insert(insert_list)
        Analytics_thrd = threading.Thread(target=Add_Analytics_data,
                                          args=(place_set, pop_dict, tasks_collection, cur_zone,))
        Analytics_thrd.start()

    return occ_map


def get_time_InMintues(stored_time):
    get_time = stored_time.split(" ")[4].split(":")
    min_stored = int(get_time[0]) * 60 + int(get_time[1])
    return min_stored


def get_time_InHour(stored_time):
    get_time = stored_time.split(" ")[3].split(":")
    hrs_stored = int(get_time[0])
    return hrs_stored


def Add_Analytics_data(place_ids, pop_dict, collection_Obj, cur_zone):
    analytics_collection = collection_Obj
    itr = analytics_collection.find({"_id": {"$in": place_ids}})
    cnt = itr.count()
    place_set = set(place_ids)
    for i in range(cnt):
        place_set.remove(itr[i]["_id"])

    insert_list = []
    place_set = list(place_set)

    for place in place_set:
        time_popular = pop_dict[place]
        if "populartimes" not in time_popular:
            insert_list.append({"_id": place, 'Zone': cur_zone, 'Data': "NA"})
            continue
        insert_list.append({"_id": place, 'Zone': cur_zone, 'Data': time_popular['populartimes']})

    if len(insert_list) > 0:
        analytics_collection.insert(insert_list)
