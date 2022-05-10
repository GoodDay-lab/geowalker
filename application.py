import copy
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import requests
from io import BytesIO
import argparse
import math


"""
НЕТ! Это не потому что я настолько ленив, что не хочу копаться в PyQt!
Это потому что внегласный закон линукса гласит - всё должно выполняться в командной строке!
"""


parser = argparse.ArgumentParser()
parser.add_argument('--coordinates', type=float, nargs=2)
parser.add_argument('--scale', type=int, default=-3)
parser.add_argument('--search', type=str)
parser.add_argument('--search_precision', type=str)
args = parser.parse_args()


def get_coordinates(city_name):
    try:
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            'geocode': city_name,
            'format': 'json'
        }
        response = requests.get(url, params)
        json = response.json()
        coordinates_str = json['response']['GeoObjectCollection'][
            'featureMember'][0]['GeoObject']['Point']['pos']
        long, lat = map(float, coordinates_str.split())
        return long, lat
    except Exception as e:
        return e


def get_address(coords):
    try:
        url = "https://geocode-maps.yandex.ru/1.x"
        apikey = "40d1649f-0493-4b70-98ba-98533de7710b"
        params = {
            'geocode': ",".join(str(f) for f in coords),
            'format': 'json',
            'apikey': apikey,
            'results': 1
        }
        if args.search_precision:
            params['kind'] = args.search_precision
        response = requests.get(url, params=params).json()
        return response
    except Exception as e:
        return e


if not args.search and not args.coordinates:
    exit(1)

point = None
add_post_index = False
auto_updating = False

if args.search:
    current_pos = list(get_coordinates(args.search))
else:
    current_pos = list(args.coordinates)
point = copy.deepcopy(current_pos)
current_size = max(min(args.scale, 3), -8)
map_type = {'cur': 0, 'types': ['map', 'sat', 'skl']}


class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def normalize(self, screen, objs):
        for obj in objs:
            screen.blit(obj.image, (obj.rect.x, obj.rect.y))


def make_output(pt):
    if not pt:
        print("---- Point's Data ----")
        print("NO DATA")
        print("----------------------")
        return
    obj = get_address(pt)['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
    address = obj['metaDataProperty']['GeocoderMetaData']['Address']['formatted']
    kind = obj['metaDataProperty']['GeocoderMetaData']['kind']
    coords = obj['Point']['pos']
    postal_code = obj['metaDataProperty']['GeocoderMetaData']['Address'].get('postal_code', None)
    print("---- Point's Data ----")
    print("Address: %s" % address)
    if add_post_index:
        print("Postal Code: %s" % (postal_code if postal_code else "NO DATA"))
    print("Kind: %s" % kind)
    print("Coords: %s" % coords)
    print("----------------------")


def get_image(coordinate, size):
    url = 'https://static-maps.yandex.ru/1.x/'
    v = 2 ** int(size)
    params = {
        'l': map_type['types'][map_type['cur']],
        'll': ','.join(map(str, coordinate)),
        'spn': f"{v},{v}"
    }
    if point:
        params['pt'] = ",".join(str(f) for f in point) + ',pmwts1'
    response = requests.get(url, params=params)
    return BytesIO(response.content)


def get_coordinates(city_name):
    try:
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            'geocode': city_name,
            'format': 'json'
        }
        response = requests.get(url, params)
        json = response.json()
        coordinates_str = json['response']['GeoObjectCollection'][
            'featureMember'][0]['GeoObject']['Point']['pos']
        long, lat = map(float, coordinates_str.split())
        return long, lat
    except Exception as e:
        return e


def lonlat_distance(a, b):
    degree_to_meters_factor = 111 * 1000
    a_lon, a_lat = a
    b_lon, b_lat = b
    radians_lattitude = math.radians((a_lat + b_lat) / 2.)
    lat_lon_factor = math.cos(radians_lattitude)
    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor
    distance = math.sqrt(dx * dx + dy * dy)
    return distance


def get_click_point(mapping, pos_click):
    rect = mapping.rect
    if not rect.collidepoint(pos_click):
        return
    percentage = [0, 0]
    percentage[0] = (pos_click[0] - rect.x) / rect.width - 0.5
    percentage[1] = (pos_click[1] - rect.y) / rect.height - 0.5

    point = [0, 0]
    point[0] = current_pos[0] + percentage[0] * 2 ** current_size * 3.26
    point[1] = current_pos[1] - percentage[1] * 2 ** current_size * 1.37
    return point


def register_click(mapping, pos_click):
    global point
    point = get_click_point(mapping, pos_click)

    mapping.image = pygame.image.load(get_image(current_pos, current_size))
    mapping.rect = mapping.image.get_rect()
    mapping.rect.x += (800 - mapping.rect.width) / 2
    mapping.rect.y += (600 - mapping.rect.height) / 2


class Image(pygame.sprite.Sprite):
    def __init__(self, bytesio):
        super().__init__()
        self.image = bytesio
        self.rect = self.image.get_rect()


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    image = pygame.image.load(get_image(current_pos, current_size))
    mapping = Image(image)
    mapping.rect = mapping.image.get_rect()
    mapping.rect.x += (800 - mapping.rect.width) / 2
    mapping.rect.y += (600 - mapping.rect.height) / 2
    group = pygame.sprite.Group(mapping)
    camera = Camera()
    while True:
        screen.fill('black')
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_1:
                current_size = min(current_size + 1, 3)

            elif e.type == pygame.KEYDOWN and e.key == pygame.K_2:
                current_size = max(current_size - 1, -8)

            elif e.type == pygame.KEYDOWN and e.key in [pygame.K_RIGHT, pygame.K_LEFT]:
                k1 = (e.key == pygame.K_RIGHT)
                k2 = (e.key == pygame.K_LEFT)
                current_pos[0] = current_pos[0] + 0.003 * (k1 - k2)

            elif e.type == pygame.KEYDOWN and e.key in [pygame.K_UP, pygame.K_DOWN]:
                k1 = (e.key == pygame.K_UP)
                k2 = (e.key == pygame.K_DOWN)
                current_pos[1] = current_pos[1] + 0.003 * (k1 - k2)

            elif e.type == pygame.KEYDOWN and e.key == pygame.K_4:
                map_type['cur'] = (map_type['cur'] + 1) % 3

            elif e.type == pygame.KEYDOWN and e.key == pygame.K_5:
                point = None

            elif e.type == pygame.KEYDOWN and e.key == pygame.K_o:
                make_output(point)

            elif e.type == pygame.KEYDOWN and e.key == pygame.K_6:
                add_post_index = not add_post_index

            elif e.type == pygame.KEYDOWN and e.key == pygame.K_7:
                auto_updating = not auto_updating

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                register_click(mapping, e.pos)

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                pt = get_click_point(mapping, e.pos)
                distance = lonlat_distance(pt, current_pos)
                print(f"[INFO] Distance is {distance} m")
                if distance > 100:
                    print("[!] THERE's more than 50 meters")
                else:
                    make_output(pt)
                break

            elif e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                current_pos = copy.deepcopy(point)

            if e.type == pygame.KEYDOWN:
                if auto_updating:
                    point = copy.deepcopy(current_pos)
                mapping.image = pygame.image.load(get_image(current_pos, current_size))
                mapping.rect = mapping.image.get_rect()
                mapping.rect.x += (800 - mapping.rect.width) / 2
                mapping.rect.y += (600 - mapping.rect.height) / 2
        camera.normalize(screen, group)
        pygame.display.flip()
