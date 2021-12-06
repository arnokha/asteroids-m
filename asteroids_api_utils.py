##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## Imports
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
import requests
import os
import time
import copy

##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## Set variables
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## Decode response status codes
decode_status = {
    200: "OK",
    400: "Bad request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not found",
    429: "Too many requests"
}
GOOD = 200
MINUTES_IN_HOUR = 60

## Endpoints
neo_endpoint = 'https://api.nasa.gov/neo/rest/v1/neo/' # Near Earth Objects

## Keys
API_KEY = os.environ["ASTEROID_API_KEY"]

##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## Helper functions
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def get_neo_page(page, size=20):
    """
    For a given page, return the associated JSON object
    
    Parameters:
      page -- Page of the data to browse. Defaults to first page
      size -- ???. Defaults to 20
      
    Returns:
      json_response -- The JSON object representing the page requested. 
                       Returns None if an error is encountered
      remaining_requests_hour -- The remaining requests available to make this hour for this API key
    """
    browse_endpoint = neo_endpoint + f'browse?page={page}&size={size}&api_key={API_KEY}'
    response = requests.get(browse_endpoint)
    status_code = response.status_code
    remaining_requests_hour = int(response.headers['X-RateLimit-Remaining'])
    
    if status_code == GOOD:
        json_response = response.json()
    else:
        if status_code in decode_status:
            print(f'Error: {decode_status[status_code]}')
        else:
            print(f'Unknown error: {status_code}')
        return None, remaining_requests_hour

    return json_response, remaining_requests_hour

##
##
## TODO - might not be needed depending on answer to questions
##
##
def get_closest_approach(close_approach_data, orbitting_earth_only=False):
    """
    For a list of close_approach_data, return the JSON item with the smallest miss distance in
    miles. If `orbitting_earth_only` is True, only consider asteroid objects that are orbitting Earth
    
    Parameters:
      close_approach_data -- List of JSON close approach data points
      orbitting_earth_only -- If true, only consider objects whose orbitting body is Earth.
                              Defaults to False
      
    Returns:
      closest_approach -- A list with the closest approach data point if any are found. 
                          Else, returns None
    """
    ## Defaults
    min_miss_distance = None
    closest_approach = None
    
    ## Iterate through data points to find the nearest miss
    for close_approach_data_point in close_approach_data:
        ## Skip if only considering objects orbitting Earth
        if orbitting_earth_only and close_approach_data_point['orbiting_body'] != 'Earth':
            continue
        
        ## If closer miss distance detected, set new closest approach data point
        miss_distance = float(close_approach_data_point['miss_distance']['miles'])
        if min_miss_distance is None or miss_distance < min_miss_distance:
            min_miss_distance = float(close_approach_data_point['miss_distance']['miles']) # update min distance
            closest_approach = close_approach_data_point
        
    return [closest_approach]

def get_n_nearest_misses(neo, n):
    nearest_misses_neo = [] # nearest misses for this asteroid
    close_approach_data = neo['close_approach_data']

    nearest_misses = sorted(close_approach_data, key=lambda data: float(data['miss_distance']['miles']))
    for i in range(n):
        new_neo = copy.deepcopy(neo)
        new_neo['close_approach_data'] = [nearest_misses[i]]
        nearest_misses_neo.append(new_neo)
    
    return nearest_misses_neo
    
    
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## Main functions
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def asteroid_closest_approach(total_n_pages=1,#1407, 
                              sleep_time=0.1, 
                              rate_limit_pause=60, wait_for_rate_limit=False):
    """
    For each page of NEO data, return each asteroid object, with the closest_approach_data list
    replaced by the closest_approach_data object, where the closest approach is determined by the
    minimum miss distance
    
    Parameters:
      total_n_pages -- pages of NEO data to traverse. Defaults to 1407
      sleep_time -- Time to sleep between requests. Used to avoid rate limiting.
                    Defaults to 0.1 seconds
      wait_for_rate_limit -- If out of requests for this API key, choose whether to wait for
                             more requests (True) or return the list accumulated so far (False).
                             Defaults to False.
      rate_limit_pause -- Pause for this many minutes if encountering rate limiting.
                          Defaults to 1 hour.
      
    Returns:
      asteroids -- a list of asteroids from the NEO endpoint, where the closest_approach_data list
                   replaced by the closest_approach_data object
    """
    asteroids = []
    for page_num in range(total_n_pages):
        page, remaining_requests = get_neo_page(page_num) # get page
                
        ## Process page: 
        ##   Iterate through near earth objects, replacing the close_approach list
        ##   with just the closest approach
        if page is not None:
            for i, neo in enumerate(page['near_earth_objects']):
                closest_approach = get_closest_approach(neo['close_approach_data'])
                page['near_earth_objects'][i]['close_approach_data'] = closest_approach
            asteroids.extend(page['near_earth_objects'])
        else:
            print(f'No page {page_num} found!')
            
        ## Sleep between requests: 
        ##   If no more requests remaining for this hour and desire to wait, pause longer.
        ##   If not waiting, return the list generated so far
        time.sleep(sleep_time)
        if remaining_requests == 0:
            if wait_for_rate_limit:
                print("No more requests remaining. Pausing to refuel...")
                time.sleep(SECONDS_IN_MINUTE * rate_limit_pause)
            else:
                return asteroids
        
    return asteroids

def nearest_misses(n=10, 
                   total_n_pages=1,
                   sleep_time=0.1, 
                   rate_limit_pause=60, wait_for_rate_limit=False):
    """
    For each page of NEO data, return the `n` nearest misses for each asteroid object, 
    with the closest_approach_data list replaced by the closest_approach_data object.
    For each nearest miss, the entire astroid object is returned with the 
    closest_approach_data list replaced by the closest_approach_data object of the
    corresponding miss.
    
    Parameters:
      n -- number of nearest misses to return for each asteroid
      sleep_time -- Time to sleep between requests. Used to avoid rate limiting.
                    Defaults to 0.1 seconds
      wait_for_rate_limit -- If out of requests for this API key, choose whether to wait for
                             more requests (True) or return the list accumulated so far (False).
                             Defaults to False.
      rate_limit_pause -- Pause for this many minutes if encountering rate limiting.
                          Defaults to 1 hour.
      
    Returns:
      misses -- a list of nearest misses of asteroids, where the closest_approach_data list
                replaced by the closest_approach_data object of the corresponding miss.
    """
    misses = []
    for page_num in range(total_n_pages):
        page, remaining_requests = get_neo_page(page_num) # get page
                
        ## Process page: 
        ##   Iterate through near earth objects, getting the `n` nearest misses
        ##   for each asteroid and allocating them to the list to return
        if page is not None:
            for i, neo in enumerate(page['near_earth_objects']):
                misses_this_neo = get_n_nearest_misses(neo, n)
                misses.extend(misses_this_neo)
        else:
            print(f'No page {page_num} found!')
            
        ## Sleep between requests:
        ##   If no more requests remaining for this hour and desire to wait, pause longer.
        ##   If not waiting, return the list generated so far
        time.sleep(sleep_time)
        if remaining_requests == 0:
            if wait_for_rate_limit:
                print("No more requests remaining. Pausing to refuel...")
                time.sleep(SECONDS_IN_MINUTE * rate_limit_pause)
            else:
                return misses
        
    return misses