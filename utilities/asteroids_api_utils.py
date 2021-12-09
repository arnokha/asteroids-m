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
## Accepted types for variables
TYPES_N = (int)
TYPES_SLEEP = (int, float)
TYPES_WAIT = (bool)
TYPES_DATE = (str)
TYPES_SPLIT = (str)

## Accepted mins and maxes for variables
MIN_SLEEP = 0
MAX_SLEEP = 10_000
MIN_N_MISSES = 1
MAX_N_MISSES = 100
MIN_N_PAGES = 1
MAX_N_PAGES = 1_500
LEN_YEAR = 4
LEN_MONTH = 2
MIN_MONTH = 1
MAX_MONTH = 12

## Error strings
DATE_STR_ERR = "Invalid date string format. Should be (YYYY-MM or YYYY-MM-DD). Make sure splitting token is not a number."

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
neo_endpoint = "https://api.nasa.gov/neo/rest/v1/neo/"   # Near Earth Objects
feed_endpoint = "https://api.nasa.gov/neo/rest/v1/feed" # Used for querying data for specific time periods

## Keys
API_KEY = os.environ["ASTEROID_API_KEY"]

##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## Helper functions
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def get_neo_page(page, size=20):
    """
    For a given page, return the associated JSON object from the browse endpoint
    
    Parameters:
      page -- Page of the data to browse. Defaults to first page
      size -- Number of results per page. Defaults to 20
      
    Returns:
      json_response -- The JSON object representing the page requested. 
                       Returns None if an error is encountered
      remaining_requests_hour -- The remaining requests available to make this hour for this API key
    """
    browse_endpoint = neo_endpoint + f"browse?page={page}&size={size}&api_key={API_KEY}"
    response = requests.get(browse_endpoint)
    status_code = response.status_code
    remaining_requests_hour = int(response.headers["X-RateLimit-Remaining"])
    
    if status_code == GOOD:
        json_response = response.json()
    else:
        if status_code in decode_status:
            print(f"Error: {decode_status[status_code]}")
        else:
            print(f"Unknown error: {status_code}")
        return None, remaining_requests_hour

    return json_response, remaining_requests_hour

def get_neo_week(start_date):
    """
    For a given start date, return the closest asteroid approaches for that week 
    from the feed endpoint
    
    Parameters:
      start_date -- First date of the week being considered
      
    Returns:
      misses -- A list of nearest misses of asteroids for the given calendar week
      remaining_requests_hour -- The remaining requests available to make this hour for this API key
    """
    date_endpoint = feed_endpoint + f"?start_date={start_date}&api_key={API_KEY}"
    response = requests.get(date_endpoint)
    status_code = response.status_code
    remaining_requests_hour = int(response.headers["X-RateLimit-Remaining"])
    
    if status_code == GOOD:
        json_response = response.json()
    else:
        if status_code in decode_status:
            print(f"Error: {decode_status[status_code]}")
        else:
            print(f"Unknown error: {status_code}")
        return None, remaining_requests_hour

    return json_response, remaining_requests_hour

def get_n_nearest_misses(neo, n):
    """
    For a given NEO and number of nearest misses `n`, return the `n` nearest misses in order,
    where each nearest miss is a JSON object with closest_approach_data list 
    replaced by the corresponding miss.
    
    Parameters:
      neo -- A NEO or asteroid JSON object, containing data about the asteroid 
      n -- The number of nearest misses to return
      
    Returns:
      nearest_misses_neo -- a sorted list of NEO objects, corresponding to the same asteroid, but
                            with each closest_approach_data field replaced by the kth closest miss
    """
    nearest_misses_neo = []
    close_approach_data = neo["close_approach_data"]

    nearest_misses = sorted(close_approach_data, key=lambda data: float(data["miss_distance"]["miles"]))
    for i in range(n):
        new_neo = copy.deepcopy(neo)
        new_neo["close_approach_data"] = [nearest_misses[i]]
        nearest_misses_neo.append(new_neo)
    
    return nearest_misses_neo

##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## Input validation functions
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def check_val_range(var, min_val, max_val, name="Variable"):
    """
    If variable is not in the range min_val to max_val, inclusive, raise ValueError.
    
    Parameters:
      var -- the variable to check
      min_val -- the minimum acceptable value for the variable
      max_val -- the maximum acceptable value for the variable
      
    Returns:
      None
    """
    if var < min_val or var > max_val:
        raise ValueError(f"{name} not in accepted range: [{min_val},{max_val}]")

def check_val_type(var, expected_types, name="Variable"):
    """
    If variable is not an instance of one of the expected types, raise TypeError.
    
    Parameters:
      var -- the variable to check
      expected_type -- a list of acceptable types for the variable
      
    Returns:
      None
    """
    if not isinstance(var, expected_types):
        raise TypeError(f"{name} not of an expected type: {expected_types}")
        
def val_nearest_misses_inputs(n, total_n_pages, sleep_time, rate_limit_pause, wait_for_rate_limit):
    """ Validate inputs for `nearest_misses()` """
    check_val_type(n, TYPES_N, name="n")
    check_val_type(total_n_pages, TYPES_N, name="total_n_pages")
    check_val_type(sleep_time, TYPES_SLEEP, name="sleep_time")
    check_val_type(rate_limit_pause, TYPES_SLEEP, name="rate_limit_pause")
    check_val_type(wait_for_rate_limit, TYPES_WAIT, name="wait_for_rate_limit")
    
    check_val_range(n, MIN_N_MISSES, MAX_N_MISSES, name="n")
    check_val_range(total_n_pages, MIN_N_PAGES, MAX_N_PAGES, name="total_n_pages")
    check_val_range(sleep_time, MIN_SLEEP, MAX_SLEEP, name="sleep_time")
    check_val_range(rate_limit_pause, MIN_SLEEP, MAX_SLEEP, name="rate_limit_pause")
    
def val_month_closest_approaches_inputs(date_str, split_token):
    """ Validate inputs for `month_closest_approaches()` """
    check_val_type(date_str, TYPES_DATE, name="date_str")
    check_val_type(split_token, TYPES_SPLIT, name="split_token")
    
    if split_token not in date_str:
        raise ValueError(DATE_STR_ERR)
        
    tokenized_date_str = date_str.split(split_token)
    year = tokenized_date_str[0]
    month = tokenized_date_str[1]
    
    try:
        check_val_range(len(year), LEN_YEAR, LEN_YEAR, name="year")    
        check_val_range(len(month), LEN_MONTH, LEN_MONTH, name="month")
        check_val_range(int(month), MIN_MONTH, MAX_MONTH, name="month")
        _ = int(year)
        _ = int(month)
    except:
        raise ValueError(DATE_STR_ERR)
    
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## Main functions
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
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
      misses -- A list of nearest misses of asteroids, where the closest_approach_data list
                replaced by the closest_approach_data object of the corresponding miss.
                Sorted by ascending miss distance.
    """
    ## Validate input
    val_nearest_misses_inputs(n, total_n_pages, sleep_time, rate_limit_pause, wait_for_rate_limit)
    
    ## Get n nearest misses
    misses = []
    for page_num in range(total_n_pages):
        page, remaining_requests = get_neo_page(page_num) # get page
                
        ## Process page: 
        ##   Iterate through near earth objects, getting the `n` nearest misses
        ##   for each asteroid and allocating them to the list to return
        if page is not None:
            for i, neo in enumerate(page["near_earth_objects"]):
                misses_this_neo = get_n_nearest_misses(neo, n)
                misses.extend(misses_this_neo)
        else:
            print(f"No page {page_num} found!")
            
        ## Sleep between requests:
        ##   If no more requests remaining for this hour and desire to wait, pause longer.
        ##   If not waiting, return the list generated so far
        time.sleep(sleep_time)
        if remaining_requests == 0:
            if wait_for_rate_limit:
                print("No more requests remaining. Pausing to refuel...")
                time.sleep(SECONDS_IN_MINUTE * rate_limit_pause)
            else:
                print("Exceeded request limit. Returning intermediate result.")
                return misses
        
    return misses

def asteroid_closest_approach(total_n_pages=1,
                              sleep_time=0.1, 
                              rate_limit_pause=60, wait_for_rate_limit=False):
    """ Alias for nearest_misses(n=1) """
    n = 1
    return nearest_misses(n, total_n_pages, sleep_time, rate_limit_pause, wait_for_rate_limit)

def month_closest_approaches(date_str, split_token="-"):
    """
    Get the closest approach in the calendar month specified by date_str (YYYY-MM-DD).
    
    Parameters:
      date_str -- a string representing the calendar month for which we will return the closest approach
                  asteroids. Can be in format YYYY-MM or YYYY-MM-DD.
      split_token -- an optional alternative token for splitting the date string
                  
    Returns:
      misses -- A list of nearest misses of asteroids for the given calendar month
    """
    ## Validate input
    val_month_closest_approaches_inputs(date_str, split_token)
        
    ## Get nearest misses for month
    tokenized_date_str = date_str.split(split_token)
    year = tokenized_date_str[0]
    month = tokenized_date_str[1]
    
    misses = {}
    neos = []
    element_count = 0
    start_days = ["01", "08", "15", "22", "29"]
    
    ## For each week (except last partial week), accumulate element count and neos
    for start_day in start_days[:-1]:
        start_date = f"{year}-{month}-{start_day}"
        neos_week, _ = get_neo_week(start_date)
        element_count = int(neos_week["element_count"])
        neos.extend(neos_week["near_earth_objects"][start_date])
    misses["element_count"] = element_count
    misses["near_earth_objects"] = neos
    
    ## For the last partial week, step through and accumulate if the month matches the month we are
    ## interested in
    ## ! NOTE ! this is an inefficient solution done in the interest of time
    start_date = f"{year}-{month}-{start_days[-1]}"
    neos_week, _ = get_neo_week(start_date)
    for neo in neos_week["near_earth_objects"][start_date]:
        date_str_neo = neo["close_approach_data"][0]["close_approach_date"]
        tokenized_date_str = date_str_neo.split("-")
        month_neo = tokenized_date_str[1]
        if month_neo == month:
            misses["near_earth_objects"].append(neo)
            misses["element_count"] += 1
    
    return misses