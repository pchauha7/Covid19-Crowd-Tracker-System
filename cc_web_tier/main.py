import requests
from flask import Flask, render_template, request
from flask_googlemaps import GoogleMaps
from forms import InfoForm
from flask_googlemaps import Map
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz

app = Flask(__name__)  # create an app instance
app.config['SECRET_KEY'] = 'nopassword'
app.config['GOOGLEMAPS_KEY'] = ""

GoogleMaps(app)


@app.route("/icms", methods=['GET', 'POST'])
def icms():
    form = InfoForm()
    if form.is_submitted():
        formResult = request.form.to_dict()
        dictToJson = formResultParser(formResult)
        if formResult["hour"] == '':
            print("visit now")
            print(dictToJson)
            res = requests.post('https://app-tier1-latest-collections.uc.r.appspot.com/places', json=dictToJson)
            print(str(res))
            if str(res) != '<Response [200]>':
                res = requests.post('https://app-tier1-latest-collections.uc.r.appspot.com/places', json=dictToJson)
            print(res)
        else:
            dictToJson["hour"] = int(formResult["hour"][:2])
            dictToJson["day"] = datetime.strptime(formResult["day"], "%Y-%m-%d").strftime('%a')
            # call to analytics url
            res = requests.post('https://app-tier2-analytics-collection.uc.r.appspot.com/analytics', json=dictToJson)
            if str(res) != '<Response [200]>':
                res = requests.post('https://app-tier2-analytics-collection.uc.r.appspot.com/analytics', json=dictToJson)
            print(res)
        response_data = res.json()
        # print(response_data)

        markers_list, result_list, placeid_result_dict, message = responseParser(response_data, formResult["location"],
                                                                                 formResult["qtype"],
                                                                                 formResult["hour"])
        #########################################################################################
        mymap = Map(
            identifier="view-side",
            lat=37.4419,
            lng=-122.1419,
            # markers=[(loc['icon'],loc['lat'], loc['lng'], loc['infobox']) for loc in markers_list]
        )
        sndmap = Map(
            identifier="sndmap",
            lat=33.4166117,
            lng=-111.9235453,
            markers=list(loc for loc in markers_list),
            fit_markers_to_bounds=True
        )
        queryType = formResult["qtype"].capitalize()
        return render_template('example.html', mymap=mymap, sndmap=sndmap, recommendations=result_list,
                               firstResult=placeid_result_dict, qtype=queryType, message=message)

    return render_template('display.html', form=form)


def formResultParser(formResult):
    dictToJson = {}
    print(formResult)
    address = formResult["location"]
    # print(address)
    coordinates = get_coordinates(app.config['GOOGLEMAPS_KEY'], address)
    dictToJson["latitude"] = coordinates["lat"]
    dictToJson["longitude"] = coordinates["lng"]
    dictToJson["range"] = float(formResult["range"]) * 1609.34
    dictToJson["qtype"] = formResult["qtype"]
    dictToJson["place_id"] = formResult["placeId"]

    return dictToJson


def responseParser(response_data, address, qtype, visitTime):
    markers_list = []
    result_list = []
    # placeid_result_list = []

    results = response_data.get('results')
    placeid_result_dict = {}
    placeid_markers_dict = {}
    message = ""
    if 'placeId' in response_data:
        placeId = response_data.get('placeId')

        # process placeId elements first
        placeid_markers_dict['lat'] = placeId['geometry']['location']['lat']
        placeid_markers_dict['lng'] = placeId['geometry']['location']['lng']
        if visitTime == '':
            curr_time = getCurrentTime(placeid_markers_dict['lng'], placeid_markers_dict['lat'])
        else:
            curr_time = int(visitTime[:2])

        placeid_markers_dict['infobox'] = "<b>" + placeId['name'] + "</b>"
        placeid_markers_dict['icon'] = 'http://maps.google.com/mapfiles/ms/micons/arrow.png'
        markers_list.append(placeid_markers_dict)
        print(placeid_markers_dict)
        placeid_result_dict['Name'] = placeId['name']
        placeid_result_dict['Address'] = placeId['vicinity']
        placeSafety = []
        if 'open_close_duration' in placeId:
            a = 0
            open_close_duration = placeId.get('open_close_duration')
            start = max(curr_time, open_close_duration[0])
            close = open_close_duration[1]
            if start < close:
                for curr_time in range(start, close):
                    placeSafety.append([str(curr_time) + ":00 ", placeId['place_safety'][curr_time]])
        else:
            for vTime in range(curr_time, 24):
                placeSafety.append([str(vTime) + ":00 ", placeId['place_safety'][vTime]])
        placeid_result_dict['PlaceSafety'] = placeSafety
        print(placeid_result_dict['PlaceSafety'])
        # placeid_result_dict['Current Occupancy'] = placeId['cur_occupancy']
        placeid_result_dict['Rating'] = placeId['rating']
        if 'opening_hours' in placeId:
            if not placeId['opening_hours']['open_now']:
                placeid_result_dict['OpenNow'] = 'No'
            else:
                placeid_result_dict['OpenNow'] = 'Yes'
        # result_list.append(placeid_result_dict)
    else:
        a = 0
        message = "The " + address + " is not a valid " + qtype + " address OR this " + qtype + \
                  " is not registered with us. See the recommendations for nearby " + qtype + "s"

    # process elements in results
    for stores in results:
        print("Type:", type(stores['geometry']['location']['lat']))
        result_dict = {}
        markers_dict = {}
        markers_dict['lat'] = stores['geometry']['location']['lat']
        markers_dict['lng'] = stores['geometry']['location']['lng']
        # print(markers_dict)
        markers_dict['infobox'] = "<b>" + stores['name'] + "</b>"
        if stores['place_safety'] == "Very Safe":
            markers_dict['icon'] = 'http://maps.google.com/mapfiles/ms/micons/green-dot.png'
        elif stores['place_safety'] == "Safe":
            markers_dict['icon'] = 'http://maps.google.com/mapfiles/ms/micons/yellow-dot.png'
        else:
            markers_dict['icon'] = 'http://maps.google.com/mapfiles/ms/micons/red-dot.png'
        markers_list.append(markers_dict)

        result_dict['Name'] = stores['name']
        result_dict['Address'] = stores['vicinity']
        result_dict['PlaceSafety'] = stores['place_safety']
        # result_dict['Current Occupancy'] = stores['cur_occupancy']
        result_dict['Rating'] = stores['rating']
        if 'opening_hours' in stores:
            if not stores['opening_hours']['open_now']:
                result_dict['OpenNow'] = 'No'
            else:
                result_dict['OpenNow'] = 'Yes'

        result_list.append(result_dict)

    return markers_list, result_list, placeid_result_dict, message


def getCurrentTime(long, lat):
    tf = TimezoneFinder()
    time_zone = tf.timezone_at(lng=long, lat=lat)
    tz = pytz.timezone(time_zone)
    dt = datetime.now(tz).ctime()
    get_time = dt.split(" ")[3].split(":")
    hrs_stored = int(get_time[0])
    return hrs_stored

def get_coordinates(API_KEY, address_text):
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json?address="
        + address_text
        + "&key="
        + API_KEY
    ).json()
    return response["results"][0]["geometry"]["location"]


if __name__ == "__main__":  # on running python 
    # name="cloud"
    app.run()  # run the flask app
