# isocronut

For a given geospatial location, calculate an [isochrone (same time) contour](http://en.wikipedia.org/wiki/Isochrone_map) around it. Any point on an x-minute isochrone contour should take a total of x minutes of travel to reach from the origin. Any point within an x-minute contour should be reachable in fewer than x minutes.

### Update: Javascript implementation

Thanks to help from [wolframteetz](https://github.com/wolframteetz), I've also created a more useable Mapbox/turf.js implementation which allows you to just click on a spot on a map and it calculates 30/60/90/120 minute isochrones real-time. It lives inside [MapboxIsochrones.html](https://github.com/drewfustin/isocronut/blob/master/MapboxIsochrones.html). You can change the desired isochrone limits by editing the html itself. Also, make sure to insert your Mapbox access token into the html.

If you want to try it out yourself and are a Python noob, put the .html file in a folder. From the terminal, cd to that folder. If you're running Python 2, enter the command

```python
python -m SimpleHTTPServer
```

or if you're running Python 3, enter the command

```python
python3 -m http.server
```

Go to your favorite browser, and point it to [http://localhost:8000/MapboxIsochrones.html](http://localhost:8000/MapboxIsochrones.html). Click away on the map.

### Use

```python
import isocronut

origin = '111 W Washington, Chicago'
duration = 10

isochrone = isocronut.get_isochrone(origin, duration)
```

or generate your own html file with an embedded Google Maps with isochrone (which will be written to isochrone.html in the current directory):

```python
import isocronut

origin = '111 W Washington, Chicago'
duration = 10

isochrone = isocronut.generate_isochrone_map(origin, duration)
```

### Parameters

__origin__ : Google Maps parseable origination address (str) or [lat, lng] 2-list ([scalar, scalar])

__duration__ : Number of minutes (scalar) for the isochrone contour

__number_of_angles__ : Number of points defining the isochrone (int) -- think of it as a resolution, default: 12

__tolerance__ : Number of minutes (scalar) that a test point can be away from __duration__ to be considered acceptable, default: 0.1

__access_type__ : Either 'personal' or 'business' (str), specifying if you are using a personal or business API access for Google Maps, default: 'personal'

  * If 'personal', you won't have access to traffic conditions. The format of the 'google_maps.cfg' config file must be (e.g. if your api_number were 1234567890, you would replace \<your api number\> below with 1234567890):

```
[api]
api_number=<your api number>
```

  * If 'business', you will be able to use current traffic conditions, which will tighten your contour distance. The format of the 'google_maps.cfg' config file must be:

```
[api]
client_id=<your client id>
crypto_key=<your crypto key>
```

__config_path__ : Path location (str) of the 'google_maps.cfg' file, default 'config/'

### Returns

Isochrone contour as a list of [lat, lng] 2-lists -- [[lat1, lng1], [lat2, lng2], ..., [latn, lngn]] where n = number_of_angles.

### Dependencies

This module makes use of the following Python modules that you must have installed.

* hashlib
* hmac
* base64
* urlparse
* ConfigParser
* simplejson
* urllib2
* time
* datetime
* math
