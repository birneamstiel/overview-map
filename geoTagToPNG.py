import argparse
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import glob
import sys
import os
from mapbox import StaticStyle
import geojson
from dotenv import load_dotenv
load_dotenv()


parser = argparse.ArgumentParser(
    description='Generate a image file containing a map of the coordinates stored in the passed pictures.')
parser.add_argument('directory', metavar='path',
                    help='directory containing geotagged pictures')

args = parser.parse_args()
print(args.directory)


def get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
    exif_data = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]

                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
    except:
        print("couldn't receive exif data")

    return exif_data


def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None


def _convert_to_degress(value):
    """Helper function to convert the GPS coordinates stored in the EXIF to degress in float format"""
    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)

    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)

    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)

    return d + (m / 60.0) + (s / 3600.0)


def get_lat_lon(exif_data):
    """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
    lat = None
    lon = None

    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]

        gps_latitude = _get_if_exist(gps_info, "GPSLatitude")
        gps_latitude_ref = _get_if_exist(gps_info, 'GPSLatitudeRef')
        gps_longitude = _get_if_exist(gps_info, 'GPSLongitude')
        gps_longitude_ref = _get_if_exist(gps_info, 'GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degress(gps_latitude)
            if gps_latitude_ref != "N":
                lat = 0 - lat

            lon = _convert_to_degress(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon

    return lat, lon


def processImages(path):
    directory = path + '/*.jpg'
    coordinates = []
    for filename in glob.glob(directory):  # assuming gif
        im = Image.open(filename)
        coordinates.append(getCoordinateForImage(im))

    coordinates = preprocessCoordinates(coordinates)
    boundingBox = findBoundingBox(coordinates)
    print("bounding box: ", boundingBox)
    getMapForCoordinates(boundingBox)
    print(coordinates)


def findBoundingBox(coordinates):
    minX = sys.float_info.max
    minY = sys.float_info.max
    maxX = sys.float_info.min
    maxY = sys.float_info.min
    for coordinatePair in coordinates:
        x = coordinatePair[0]
        y = coordinatePair[1]
        if x < minX:
            minX = x
        if x > maxX:
            maxX = x
        if y < minY:
            minY = y
        if y > maxY:
            maxY = y
        print(coordinatePair)
    boundingBox = [(minX, minY), (maxX, maxY)]
    return boundingBox

def preprocessCoordinates(coordinates, precision = 2):
    newCoordinates = []
    for coordinate in coordinates:

        x = coordinate[1]
        y = coordinate[0]

        if isinstance(x, float) and isinstance(y, float):
            newCoordinate = round(x, precision), round(y, precision)
            newCoordinates.append(newCoordinate)
    return newCoordinates

def getMapForCoordinates(coordinates):
    ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
    USERNAME = os.getenv("MAPBOX_STYLE_USER")
    STYLE_ID = os.getenv("MAPBOX_STYLE_ID")
    service = StaticStyle()
    multipoint = geojson.MultiPoint(coordinates)
    feature = geojson.Feature(geometry=multipoint)
    print (feature)


    response = service.image(username=USERNAME, style_id=STYLE_ID, features=[feature], width=1200, height=1200, retina=True)
    print(response.status_code)

    with open(args.directory + '/_map.png', 'wb') as output:
        _ = output.write(response.content)


def getCoordinateForImage(image):
    return get_lat_lon(get_exif_data(image))

def retrieveBoundingBox():
    print('retrieving')


processImages(args.directory)
