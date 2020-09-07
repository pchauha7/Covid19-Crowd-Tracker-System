from time import time, ctime
from pymongo import MongoClient
import populartimes
import threading


def UpdateDB():
    client = MongoClient("mongodb+srv://<usr:pwd>@cc-project2-cluster-1n756.gcp.mongodb.net/test?retryWrites=true&w=majority")  # host uri
    db = client.CCProject
    NewYork_Analytics_collection = db.NewYorkAnalytics
    Phoenix_Analytics_collection = db.PhoenixAnalytics
    other_Analytics_collection = db.OtherZonesAnalytics
    Analytics_collection = [NewYork_Analytics_collection, Phoenix_Analytics_collection, other_Analytics_collection]

    api_key = ''

    for collection in Analytics_collection:
        pop_dict = {}
        thrd_list = []
        place_ids = [str(id) for id in collection.find().distinct('_id')]

        def calculate_populatime(place):
            pop_dict[place] = populartimes.get_id(api_key, place)

        for place in place_ids:
            thrd_list.append(threading.Thread(target=calculate_populatime, args=(place,)))
            thrd_list[-1].start()

        for thrd in thrd_list:
            thrd.join()

        for place in place_ids:
            time_popular = pop_dict[place]
            if "populartimes" not in time_popular:
                collection.update_one({"_id": place}, {"$set": {'Data' : "NA"}})
                continue
            else:
                collection.update_one({"_id": place}, {"$set": {'Data': time_popular['populartimes']}})