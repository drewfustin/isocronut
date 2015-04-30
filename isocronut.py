from __future__ import division
import hashlib
import hmac
import base64
import urlparse
import ConfigParser
import simplejson
import urllib2
import time
import datetime
from math import cos, sin, tan, sqrt, pi, radians, degrees, asin, atan2


def build_url(origin='',
              destination='',
              access_type='personal',
              config_path='config/'):
    """
    Determine the url to pass for the desired search.
    This is complicated when using Google Maps for Business.
    """
    # origin is either an address string (like '1 N State St Chicago IL') or a [lat, lng] 2-list
    if origin == '':
        raise Exception('origin cannot be blank.')
    elif isinstance(origin, str):
        origin_str = origin.replace(' ', '+')
    elif isinstance(origin, list) and len(origin) == 2:
        origin_str = ','.join(map(str, origin))
    else:
        raise Exception('origin should be a list [lat, lng] or an address string.')
    # destination is similar, although it can be a list of address strings or [lat, lng] 2 lists
    if destination == '':
        raise Exception('destination cannot be blank.')
    elif isinstance(destination, str):
        destination_str = destination.replace(' ', '+')
    elif isinstance(destination, list):
        destination_str = ''
        for element in destination:
            if isinstance(element, str):
                destination_str = '{0}|{1}'.format(destination_str, element.replace(' ', '+'))
            elif isinstance(element, list) and len(element) == 2:
                destination_str = '{0}|{1}'.format(destination_str, ','.join(map(str, element)))
            else:
                raise Exception('destination must be a list of lists [lat, lng] or a list of strings.')
        destination_str = destination_str.strip('|')
    else:
        raise Exception('destination must be a a list of lists [lat, lng] or a list of strings.')
    # access_type is either 'personal' or 'business'
    if access_type not in ['personal', 'business']:
        raise Exception("access_type must be either 'personal' or 'business'.")

    # Get the Google API keys from an external config file
    # If you are using Google Maps for Business (needed for traffic data),
    #   this file is of the form:
    #
    # [api]
    # client_id=<your client id>
    # crypto_key=<your crypto key>
    #
    # If it's your own personal Google Maps account, it looks like this:
    #
    # [api]
    # api_number=<your api number>
    #
    config = ConfigParser.SafeConfigParser()
    config.read('{}google_maps.cfg'.format(config_path))
    if access_type == 'personal':
        key = config.get('api', 'api_number')
    if access_type == 'business':
        client = config.get('api', 'client_id')

    # If using Google Maps for Business, the calculation will use current traffic conditions
    departure = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1, 0, 0, 0)

    # Convert the URL string to a URL, which we can parse
    # using the urlparse() function into path and query
    # Note that this URL should already be URL-encoded
    prefix = 'https://maps.googleapis.com/maps/api/distancematrix/json?mode=driving&units=imperial&avoid=tolls|ferries'
    if access_type == 'personal':
        url = urlparse.urlparse('{0}&origins={1}&destinations={2}&key={3}'.format(prefix,
                                                                                  origin_str,
                                                                                  destination_str,
                                                                                  key))
        full_url = url.scheme + '://' + url.netloc + url.path + '?' + url.query
        return full_url
    if access_type == 'business':
        url = urlparse.urlparse('{0}&origins={1}&destinations={2}&departure_time={3}&client={4}'.format(prefix,
                                                                                                        origin_str,
                                                                                                        destination_str,
                                                                                                        int(departure.total_seconds()),
                                                                                                        client))
        # Get the private_key used to sign the API request
        private_key = config.get('api', 'crypto_key')
        # We only need to sign the path+query part of the string
        url_to_sign = url.path + "?" + url.query
        # Decode the private key into its binary format
        decoded_key = base64.urlsafe_b64decode(private_key)
        # Create a signature using the private key and the URL-encoded
        #   string using HMAC SHA1. This signature will be binary.
        signature = hmac.new(decoded_key, url_to_sign, hashlib.sha1)
        # Encode the binary signature into base64 for use within a URL
        encoded_signature = base64.urlsafe_b64encode(signature.digest())
        original_url = url.scheme + '://' + url.netloc + url.path + '?' + url.query
        full_url = original_url + '&signature=' + encoded_signature
        return full_url


def parse_json(url=''):
    """
    Parse the json response from the API
    """
    req = urllib2.Request(url)
    opener = urllib2.build_opener()
    f = opener.open(req)
    d = simplejson.load(f)

    if not d['status'] == 'OK':
        raise Exception('Error. Google Maps API return status: {}'.format(d['status']))

    addresses = d['destination_addresses']

    i = 0
    durations = [0] * len(addresses)
    for row in d['rows'][0]['elements']:
        if not row['status'] == 'OK':
            # raise Exception('Error. Google Maps API return status: {}'.format(row['status']))
            durations[i] = 9999
        else:
            if 'duration_in_traffic' in row:
                durations[i] = row['duration_in_traffic']['value'] / 60
            else:
                durations[i] = row['duration']['value'] / 60
        i += 1
    return [addresses, durations]


def geocode_address(address='',
                    access_type='personal',
                    config_path='config/'):
    """
    For use in calculating distances between 2 locations, the [lat, lng] is needed instead of the address.
    """
    # Convert origin and destination to URL-compatible strinågs
    if address == '':
        raise Exception('address cannot be blank.')
    elif isinstance(address, str):
        address_str = address.replace(' ', '+')
    else:
        raise Exception('address should be a string.')
    # access_type is either 'personal' or 'business'
    if access_type not in ['personal', 'business']:
        raise Exception("access_type must be either 'personal' or 'business'.")

    # Get the Google API keys from an external config file
    # If you are using Google Maps for Business (needed for traffic data),
    #   this file is of the form:
    #
    # [api]
    # client_id=<your client id>
    # crypto_key=<your crypto key>
    #
    # If it's your own personal Google Maps account, it looks like this:
    #
    # [api]
    # api_number=<your api number>
    #
    config = ConfigParser.SafeConfigParser()
    config.read('{}google_maps.cfg'.format(config_path))
    if access_type == 'personal':
        key = config.get('api', 'api_number')
    if access_type == 'business':
        client = config.get('api', 'client_id')

    # Convert the URL string to a URL, which we can parse
    # using the urlparse() function into path and query
    # Note that this URL should already be URL-encoded
    prefix = 'https://maps.googleapis.com/maps/api/geocode/json'
    if access_type == 'personal':
        url = urlparse.urlparse('{0}?address={1}&key={2}'.format(prefix,
                                                                 address_str,
                                                                 key))
        full_url = url.scheme + '://' + url.netloc + url.path + '?' + url.query
    if access_type == 'business':
        url = urlparse.urlparse('{0}?address={1}&client={2}'.format(prefix,
                                                                    address_str,
                                                                    client))
        # Get the private_key used to sign the API request
        private_key = config.get('api', 'crypto_key')
        # We only need to sign the path+query part of the string
        url_to_sign = url.path + "?" + url.query
        # Decode the private key into its binary format
        decoded_key = base64.urlsafe_b64decode(private_key)
        # Create a signature using the private key and the URL-encoded
        #   string using HMAC SHA1. This signature will be binary.
        signature = hmac.new(decoded_key, url_to_sign, hashlib.sha1)
        # Encode the binary signature into base64 for use within a URL
        encoded_signature = base64.urlsafe_b64encode(signature.digest())
        original_url = url.scheme + '://' + url.netloc + url.path + '?' + url.query
        full_url = original_url + '&signature=' + encoded_signature

    # Request geocode from address
    req = urllib2.Request(full_url)
    opener = urllib2.build_opener()
    f = opener.open(req)
    d = simplejson.load(f)

    # Parse the json to pull out the geocode
    if not d['status'] == 'OK':
        raise Exception('Error. Google Maps API return status: {}'.format(d['status']))
    geocode = [d['results'][0]['geometry']['location']['lat'],
               d['results'][0]['geometry']['location']['lng']]
    return geocode


def select_destination(origin='',
                       angle='',
                       radius='',
                       access_type='personal',
                       config_path='config/'):
    """
    Given a distance and polar angle, calculate the geocode of a destination point from the origin.
    """
    if origin == '':
        raise Exception('origin cannot be blank.')
    if angle == '':
        raise Exception('angle cannot be blank.')
    if radius == '':
        raise Exception('radius cannot be blank.')

    if isinstance(origin, str):
        origin_geocode = geocode_address(origin, access_type, config_path)
    elif isinstance(origin, list) and len(origin) == 2:
        origin_geocode = origin
    else:
        raise Exception('origin should be a list [lat, lng] or a string address.')

    # Find the location on a sphere a distance 'radius' along a bearing 'angle' from origin
    # This uses haversines rather than simple Pythagorean distance in Euclidean space
    #   because spheres are more complicated than planes.
    r = 3963.1676  # Radius of the Earth in miles
    bearing = radians(angle)  # Bearing in radians converted from angle in degrees
    lat1 = radians(origin_geocode[0])
    lng1 = radians(origin_geocode[1])
    lat2 = asin(sin(lat1) * cos(radius / r) + cos(lat1) * sin(radius / r) * cos(bearing))
    lng2 = lng1 + atan2(sin(bearing) * sin(radius / r) * cos(lat1), cos(radius / r) - sin(lat1) * sin(lat2))
    lat2 = degrees(lat2)
    lng2 = degrees(lng2)
    return [lat2, lng2]


def get_bearing(origin='',
                destination=''):
    """
    Calculate the bearing from origin to destination
    """
    if origin == '':
        raise Exception('origin cannot be blank')
    if destination == '':
        raise Exception('destination cannot be blank')

    bearing = atan2(sin((destination[1] - origin[1]) * pi / 180) * cos(destination[0] * pi / 180),
                    cos(origin[0] * pi / 180) * sin(destination[0] * pi / 180) -
                    sin(origin[0] * pi / 180) * cos(destination[0] * pi / 180) * cos((destination[1] - origin[1]) * pi / 180))
    bearing = bearing * 180 / pi
    bearing = (bearing + 360) % 360
    return bearing


def sort_points(origin='',
                iso='',
                access_type='personal',
                config_path='config/'):
    """
    Put the isochrone points in a proper order
    """
    if origin == '':
        raise Exception('origin cannot be blank.')
    if iso == '':
        raise Exception('iso cannot be blank.')

    if isinstance(origin, str):
        origin_geocode = geocode_address(origin, access_type, config_path)
    elif isinstance(origin, list) and len(origin) == 2:
        origin_geocode = origin
    else:
        raise Exception('origin should be a list [lat, lng] or a string address.')

    bearings = []
    for row in iso:
        bearings.append(get_bearing(origin_geocode, row))

    points = zip(bearings, iso)
    sorted_points = sorted(points)
    sorted_iso = [point[1] for point in sorted_points]
    return sorted_iso


def get_isochrone(origin='',
                  duration='',
                  number_of_angles=12,
                  tolerance=0.1,
                  access_type='personal',
                  config_path='config/'):
    """
    Putting it all together.
    Given a starting location and amount of time for the isochrone to represent (e.g. a 15 minute isochrone from origin)
      use the Google Maps distance matrix API to check travel times along a number of bearings around the origin for
      an equal number of radii. Perform a binary search on radius along each bearing until the duration returned from
      the API is within a tolerance of the isochrone duration.
    origin = string address or [lat, lng] 2-list
    duration = minutes that the isochrone contour value should map
    number_of_angles = how many bearings to calculate this contour for (think of this like resolution)
    tolerance = how many minutes within the exact answer for the contour is good enough
    access_type = 'business' or 'personal' (business required for traffic info)
    config_path = where the google_maps.cfg file is located that contains API credentials (described in build_url)
    """
    if origin == '':
        raise Exception('origin cannot be blank')
    if duration == '':
        raise Exception('duration cannot be blank')
    if not isinstance(number_of_angles, int):
        raise Exception('number_of_angles must be an int')

    if isinstance(origin, str):
        origin_geocode = geocode_address(origin, access_type, config_path)
    elif isinstance(origin, list) and len(origin) == 2:
        origin_geocode = origin
    else:
        raise Exception('origin should be a list [lat, lng] or a string address.')

    # Make a radius list, one element for each angle,
    #   whose elements will update until the isochrone is found
    rad1 = [duration / 12] * number_of_angles  # initial r guess based on 5 mph speed
    phi1 = [i * (360 / number_of_angles) for i in range(number_of_angles)]
    data0 = [0] * number_of_angles
    rad0 = [0] * number_of_angles
    rmin = [0] * number_of_angles
    rmax = [1.25 * duration] * number_of_angles  # rmax based on 75 mph speed
    iso = [[0, 0]] * number_of_angles

    # Counter to ensure we're not getting out of hand
    j = 0

    # Here's where the binary search starts
    while sum([a - b for a, b in zip(rad0, rad1)]) != 0:
        rad2 = [0] * number_of_angles
        for i in range(number_of_angles):
            iso[i] = select_destination(origin, phi1[i], rad1[i], access_type, config_path)
            time.sleep(0.1)
        url = build_url(origin, iso, access_type, config_path)
        data = parse_json(url)
        for i in range(number_of_angles):
            if (data[1][i] < (duration - tolerance)) & (data0[i] != data[0][i]):
                rad2[i] = (rmax[i] + rad1[i]) / 2
                rmin[i] = rad1[i]
            elif (data[1][i] > (duration + tolerance)) & (data0[i] != data[0][i]):
                rad2[i] = (rmin[i] + rad1[i]) / 2
                rmax[i] = rad1[i]
            else:
                rad2[i] = rad1[i]
            data0[i] = data[0][i]
        rad0 = rad1
        rad1 = rad2
        j += 1
        if j > 30:
            raise Exception("This is taking too long, so I'm just going to quit.")

    for i in range(number_of_angles):
        iso[i] = geocode_address(data[0][i], access_type, config_path)
        time.sleep(0.1)

    iso = sort_points(origin, iso, access_type, config_path)
    return iso


def generate_isochrone_map(origin='',
                           duration='',
                           number_of_angles=12,
                           tolerance=0.1,
                           access_type='personal',
                           config_path='config/'):
    """
    Call the get_isochrone function and generate a simple html file using its output.
    """
    if origin == '':
        raise Exception('origin cannot be blank')
    if duration == '':
        raise Exception('duration cannot be blank')
    if not isinstance(number_of_angles, int):
        raise Exception('number_of_angles must be an int')

    if isinstance(origin, str):
        origin_geocode = geocode_address(origin, access_type, config_path)
    elif isinstance(origin, list) and len(origin) == 2:
        origin_geocode = origin
    else:
        raise Exception('origin should be a list [lat, lng] or a string address.')

    iso = get_isochrone(origin, duration, number_of_angles, tolerance, access_type, config_path)

    htmltext = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no">
    <meta charset="utf-8">
    <title>Isochrone</title>
    <style>
      html, body, #map-canvas {{
        height: 100%;
        margin: 0px;
        padding: 0px
      }}
    </style>

    <script src="https://maps.googleapis.com/maps/api/js?v=3.exp&signed_in=true"></script>

    <script>
    function initialize() {{
      var mapOptions = {{
        zoom: 14,
        center: new google.maps.LatLng({0},{1}),
        mapTypeId: google.maps.MapTypeId.TERRAIN
      }};

      var map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);

      var marker = new google.maps.Marker({{
          position: new google.maps.LatLng({0},{1}),
          map: map
      }});

      var isochrone;

      var isochroneCoords = [
    """.format(origin_geocode[0], origin_geocode[1])

    for i in iso:
        htmltext += 'new google.maps.LatLng({},{}), \n'.format(i[0], i[1])

    htmltext += """
      ];

      isochrone = new google.maps.Polygon({
        paths: isochroneCoords,
        strokeColor: '#000',
        strokeOpacity: 0.5,
        strokeWeight: 1,
        fillColor: '#000',
        fillOpacity: 0.25
      });

      isochrone.setMap(map);

    }

    google.maps.event.addDomListener(window, 'load', initialize);
    </script>

    </head>
    <body>
    <div id="map-canvas"></div>
    </body>
    </html>
    """

    with open('isochrone.html', 'w') as f:
        f.write(htmltext)

    return iso
