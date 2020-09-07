from flask import Flask, logging, request  # import flask
import requests
import json
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime

from db import get_current_crowd

app = Flask(__name__)  # create an app instance

GOOGLE_API_KEY = ""
base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="

def perform_ordering_restaurant(result, occupancy_map):
    final_results = []
    for res in result:
        if res["place_id"] in occupancy_map:
            final_results.append(res)
            final_results[-1]["cur_occupancy"] = occupancy_map[res["place_id"]]
            if "rating" not in final_results[-1]:
                final_results[-1]["rating"] = 1
            if final_results[-1]["cur_occupancy"] <= 30:
                final_results[-1]["place_safety"] = "Very Safe"
            elif 30 < final_results[-1]["cur_occupancy"] <= 50:
                final_results[-1]["place_safety"] = "Safe"
            else:
                final_results[-1]["place_safety"] = "Hard to Maintain Social distancing"

    final_results = sorted(final_results, key=lambda X: [X["cur_occupancy"], -X["rating"]])
    open=[]
    close = []
    for res in final_results:
        if "opening_hours" in res:
            if not res["opening_hours"]["open_now"]:
                close.append(res)
            else:
                open.append(res)
        else:
            open.append(res)

    final_results = open + close

    return final_results


def perform_ordering_grocery(result, occupancy_map):
    final_results = []
    for res in result:
        if res["place_id"] in occupancy_map:
            final_results.append(res)
            final_results[-1]["cur_occupancy"] = occupancy_map[res["place_id"]]
            if "rating" not in final_results[-1]:
                final_results[-1]["rating"] = 1
            if final_results[-1]["cur_occupancy"] <= 40:
                final_results[-1]["place_safety"] = "Very Safe"
            elif 40 < final_results[-1]["cur_occupancy"] <= 70:
                final_results[-1]["place_safety"] = "Safe"
            else:
                final_results[-1]["place_safety"] = "Hard to Maintain Social distancing"

    final_results = sorted(final_results, key=lambda X: [X["cur_occupancy"], -X["rating"]])

    open = []
    close = []
    for res in final_results:
        if "opening_hours" in res:
            if not res["opening_hours"]["open_now"]:
                close.append(res)
            else:
                open.append(res)
        else:
            open.append(res)

    final_results = open + close

    return final_results


def find_restaurants(lat, long, radius, placeid):
    subPart = "{},{}&radius={}&type=restaurant&key={}".format(lat, long, radius, GOOGLE_API_KEY)
    url = base_url + subPart
    #print(url)
    response = requests.get(url)
    jsn = response.json()
    #print(response)
    result = []
    st = set()
    for place in jsn["results"]:
        result.append(place)
        st.add(place["place_id"])

    tf = TimezoneFinder()
    time_zone = tf.timezone_at(lng=long, lat=lat)
    tz = pytz.timezone(time_zone)
    dt = datetime.now(tz).ctime()
    #print(dt)
    occupancy_map = get_current_crowd(list(st), placeid, GOOGLE_API_KEY, dt, time_zone)

    #print(occupancy_map)

    result_place_id = {}
    if placeid in occupancy_map:
        for val in result:
            if val["place_id"] == placeid:
                result_place_id[placeid] = val
                break
        occ_list = occupancy_map.pop(placeid)
        safe_list = []
        for occ in occ_list:
            if occ <= 30:
                safe_list.append("Very Safe")
            elif 30 < occ <= 50:
                safe_list.append("Safe")
            else:
                safe_list.append("Hard to Maintain Social distancing")

        result_place_id[placeid]["place_safety"] = safe_list

    ordered_results = perform_ordering_restaurant(result, occupancy_map)

    my_json = {'results': ordered_results}

    if placeid in result_place_id:
        open_hour_url = "https://maps.googleapis.com/maps/api/place/details/json?place_id={}&fields=name," \
                        "opening_hours&key={}".format(placeid, GOOGLE_API_KEY)
        day = dt[:3]
        days = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
        response = requests.get(open_hour_url)
        jsn = response.json()
        res = []
        if "opening_hours" in jsn["result"]:
            for period in jsn["result"]["opening_hours"]["periods"]:
                if period["open"]["day"] == days[day]:
                    res.append(int(period["open"]["time"][:2]))
                    if period["open"]["day"] == period["close"]["day"]:
                        res.append(int(period["close"]["time"][:2]))
                    else:
                        res.append(24)
                    result_place_id[placeid]["open_close_duration"] = res
                    break

        my_json["placeId"] = result_place_id[placeid]

    return json.dumps(my_json), 200


def find_store(lat, long, radius, placeid):
    subPart1 = "{},{}&radius={}&type=supermarket&key={}".format(lat, long, radius, GOOGLE_API_KEY)
    subPart2 = "{},{}&radius={}&keyword=grocerystore&key={}".format(lat, long, radius, GOOGLE_API_KEY)
    url = base_url + subPart1
    # print(url)
    response1 = requests.get(url)
    response2 = requests.get(base_url + subPart2)
    json1 = response1.json()
    json2 = response2.json()
    result = []
    st = set()
    for place in json1["results"]:
        if place["place_id"] not in st:
            result.append(place)
            st.add(place["place_id"])
    for place in json2["results"]:
        if place["place_id"] not in st:
            result.append(place)
            st.add(place["place_id"])

    tf = TimezoneFinder()
    time_zone = tf.timezone_at(lng=long, lat=lat)
    tz = pytz.timezone(time_zone)
    dt = datetime.now(tz).ctime()

    occupancy_map = get_current_crowd(list(st), placeid, GOOGLE_API_KEY, dt, time_zone)

    result_place_id ={}
    if placeid in occupancy_map:
        for val in result:
            if val["place_id"] == placeid:
                result_place_id[placeid] = val
                break
        occ_list = occupancy_map.pop(placeid)
        safe_list = []
        for occ in occ_list:
            if occ <= 40:
                safe_list.append("Very Safe")
            elif 40 < occ <= 70:
                safe_list.append("Safe")
            else:
                safe_list.append("Hard to Maintain Social distancing")

        result_place_id[placeid]["place_safety"] = safe_list

    ordered_results = perform_ordering_grocery(result, occupancy_map)

    my_json = {'results': ordered_results}
    if placeid in result_place_id:
        open_hour_url = "https://maps.googleapis.com/maps/api/place/details/json?place_id={}&fields=name," \
                        "opening_hours&key={}".format(placeid, GOOGLE_API_KEY)
        day = dt[:3]
        days = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
        response = requests.get(open_hour_url)
        jsn = response.json()
        res = []
        if "opening_hours" in jsn["result"]:
            for period in jsn["result"]["opening_hours"]["periods"]:
                if period["open"]["day"] == days[day]:
                    res.append(int(period["open"]["time"][:2]))
                    if period["open"]["day"] == period["close"]["day"]:
                        res.append(int(period["close"]["time"][:2]))
                    else:
                        res.append(24)
                    result_place_id[placeid]["open_close_duration"] = res
                    break

        my_json["placeId"] = result_place_id[placeid]

    # to_send.append(my_json)
    return json.dumps(my_json), 200


@app.route("/")  # at the end point /
def hello():  # call method hello
    return "Hello World!"  # which returns "hello world"


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


@app.route("/places", methods=['POST', 'GET'])
def places():
    body = request.json
    print(body)
    query_type = body["qtype"]
    lat = body["latitude"]
    long = body["longitude"]
    distance = int(body["range"])
    placeid = body["place_id"]
    snd = str(lat) + " " + str(long) + " Result"
    print(snd)
    if query_type == "restaurant":
        return find_restaurants(lat, long, distance, placeid)
    else:
        return find_store(lat, long, distance, placeid)


if __name__ == "__main__":  # on running python app.py
    app.run()  # run the flask app
