import argparse
from PIL import Image
import glob
import sys
import os
from get_lat_lon_exif_pil import get_lat_lon
from get_lat_lon_exif_pil import get_exif_data
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


def process_images(path):
    directory = path + '/*.jpg'
    coordinates = []
    for filename in glob.glob(directory):  # assuming gif
        im = Image.open(filename)
        coordinates.append(get_coordinates_from_image(im))

    coordinates = preprocess_coordinates(coordinates)
    boundingBox = find_bounding_box(coordinates)
    print("bounding box: ", boundingBox)
    get_map_for_coordinates(boundingBox)
    print(coordinates)


def find_bounding_box(coordinates):
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


def preprocess_coordinates(coordinates, precision=2):
    newCoordinates = []
    for coordinate in coordinates:

        x = coordinate[1]
        y = coordinate[0]

        if isinstance(x, float) and isinstance(y, float):
            newCoordinate = round(x, precision), round(y, precision)
            newCoordinates.append(newCoordinate)
    return newCoordinates


def get_map_for_coordinates(coordinates):
    ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
    USERNAME = os.getenv("MAPBOX_STYLE_USER")
    STYLE_ID = os.getenv("MAPBOX_STYLE_ID")
    service = StaticStyle()
    multipoint = geojson.MultiPoint(coordinates)
    feature = geojson.Feature(geometry=multipoint)
    print (feature)

    response = service.image(username=USERNAME, style_id=STYLE_ID, features=[feature], width=1200, height=1200,
                             retina=True)
    print(response.status_code)

    with open(args.directory + '/_map.png', 'wb') as output:
        _ = output.write(response.content)


def get_coordinates_from_image(image):
    return get_lat_lon(get_exif_data(image))


process_images(args.directory)
