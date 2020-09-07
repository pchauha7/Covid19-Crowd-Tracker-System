from pymongo import MongoClient
import populartimes
from time import time, ctime
import threading
import os

client = MongoClient("mongodb+srv://<usr:pwd>@cc-project2-cluster-1n756.gcp.mongodb.net/test?retryWrites=true&w=majority")  # host uri
#client = MongoClient("mongodb://127.0.0.1:27017")
db = client.CCProject  # Select the database
tasks_collection = None
latest_collection = None

days = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}


def get_current_crowd(place_ids, dest_place_id, api_key, day, hour, cur_zone):
    # time1 = int(round(time()*1000))
    os.environ['TZ'] = cur_zone
    dt = ctime(time())
    today_day = dt[:3]
    # print(todays_day)
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

    # print("Current hour: "+str(current_hour))
    itr = tasks_collection.find({"_id": {"$in": place_ids}})
    cnt = itr.count()
    place_set = set(place_ids)
    # print(len(place_set))
    # print(cnt)
    for i in range(cnt):
        # stored_time = itr[0]["Time"]
        place_set.remove(itr[i]["_id"])

        if itr[i]["Data"] == "NA":
            continue
        else:
            if itr[i]["_id"] == dest_place_id:
                current_occupancy = itr[i]["Data"][days[day]]["data"]
            else:
                current_occupancy = itr[i]["Data"][days[day]]["data"][hour]

        occ_map[itr[i]["_id"]] = current_occupancy

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

    tmp_lst = place_set
    for place in place_set:
        # time_popular = populartimes.get_id(api_key, place)
        time_popular = pop_dict[place]
        if "populartimes" not in time_popular:
            insert_list.append({"_id": place, 'Zone': cur_zone, 'Data': "NA"})
            continue
        else:
            if place == dest_place_id:
                current_occupancy = time_popular['populartimes'][days[day]]["data"]
            else:
                current_occupancy = time_popular['populartimes'][days[day]]["data"][hour]

        insert_list.append({"_id": place, 'Zone': cur_zone, 'Data': time_popular['populartimes']})
        # current_occupancy = time_popular['populartimes'][days[todays_day]]["data"][current_hour]
        occ_map[place] = current_occupancy

    if len(insert_list) > 0:
        tasks_collection.insert(insert_list)

    # creating thread to add popular time of place_ids in the Latest collection
    if len(tmp_lst) > 0:
        current_thrd = threading.Thread(target=Add_Current_data, args=(tmp_lst, latest_collection, pop_dict, cur_zone, today_day,))
        current_thrd.start()

    return occ_map


def Add_Current_data(place_ids, collection_obj, pop_dict, cur_zone, today_day):

    itr = collection_obj.find({"_id": {"$in": place_ids}})
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
        insert_list.append({"_id": place, 'Zone': cur_zone, 'Data': time_popular['populartimes'][days[today_day]]})

    if len(insert_list) > 0:
        collection_obj.insert(insert_list)
