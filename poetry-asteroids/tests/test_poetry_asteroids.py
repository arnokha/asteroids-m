from poetry_asteroids import __version__

## Import utilities file
import sys
sys.path.append('utilities')
from asteroids_api_utils import *


def test_version():
    assert __version__ == '0.1.0'
    
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## nearest_misses() input validation
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def test_type_n_misses():
    """ Test that type errors for nearest_misses(n) are caught """
    try:
        nearest_misses(n=1.0)
        assert(False)
    except TypeError:
        assert(True)
        
def test_value_n_misses():
    """ Test that value errors for nearest_misses(n) are caught """
    try:
        nearest_misses(n=0)
        assert(False)
    except ValueError:
        assert(True)
        
def test_type_n_pages():
    """ Test that type errors for variable total_n_pages in nearest_misses() are caught """
    try:
        nearest_misses(total_n_pages="1")
        assert(False)
    except TypeError:
        assert(True)
        
def test_value_n_pages():
    """ Test that value errors for variable total_n_pages in nearest_misses() are caught """
    try:
        nearest_misses(total_n_pages=0)
        assert(False)
    except ValueError:
        assert(True)
        
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## month_closest_approaches() input validation
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def test_type_date_str():
    """ Test that type errors for variable date_str in month_closest_approaches() are caught """
    try:
        month_closest_approaches(202004)
        assert(False)
    except TypeError:
        assert(True)
        
def test_value_n_pages_1():
    """ Test that value errors for variable date_str in month_closest_approaches() are caught: empty string """
    try:
        month_closest_approaches("")
        assert(False)
    except ValueError:
        assert(True)
        
def test_value_n_pages_2():
    """ Test that value errors for variable date_str in month_closest_approaches() are caught: month length """
    try:
        month_closest_approaches("2020-121")
        assert(False)
    except ValueError:
        assert(True)
        
def test_value_n_pages_3():
    """ Test that value errors for variable total_n_pages in month_closest_approaches() are caught: year length  """
    try:
        month_closest_approaches("20201-10")
        assert(False)
    except ValueError:
        assert(True)
        
def test_value_n_pages_4():
    """ Test that value errors for variable total_n_pages in month_closest_approaches() are caught: month value """
    try:
        month_closest_approaches("2020-13")
        assert(False)
    except ValueError:
        assert(True)
        
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## month_closest_approaches() general
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def test_month_closest_approaches_output_dates():
    """ Test that the all the close_approach_dates returned by month_closest_approaches() are in the same year/month """
    start_date = "2020-12-01"
    tokenized_date_str = start_date.split("-")
    year = tokenized_date_str[0]
    month = tokenized_date_str[1]
    
    test_month = month_closest_approaches(start_date)
    
    for neo in test_month["near_earth_objects"]:
        date_str_neo = neo["close_approach_data"][0]["close_approach_date"]
        tokenized_date_str = date_str_neo.split("-")
        year_neo = tokenized_date_str[0]
        month_neo = tokenized_date_str[1]
        if not (month_neo == month) or (month_neo == year):
            assert(False)
    
def test_month_closest_approaches_more_data_than_week():
    """ Test that the number of elements in month_closest_approaches() is more than that of get_week() """
    start_date = "2020-12-01"
    test_month = month_closest_approaches(start_date)
    test_week, _ = get_neo_week(start_date)
    assert(len(test_week["near_earth_objects"][start_date]) < len(test_month["near_earth_objects"]))
    
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## month_closest_approaches() general
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def test_month_closest_approaches_list_len_1():
    """ 
    Test each neo object returned by month_closest_approaches() has close_approach_data that 
    is a list of length one
    """
    test_nm_1 = nearest_misses(n=1)
    for neo in test_nm_1:
        neo_close_approach_data = neo['close_approach_data']
        if not (isinstance(neo_close_approach_data, list) or len(neo_close_approach_data) == 1):
            assert(False)
    assert(True)

def test_month_closest_approaches_n_subset():
    """ 
    Test that smaller values of n are always a subset of greater values of n, and that 
    each of these only appear in the superset one time
    """
    test_nm_1 = nearest_misses(n=1)
    test_nm_2 = nearest_misses(n=2)
    found_in_nm_2 = 0
    for neo_1 in test_nm_1:
        neo_id_1 = neo_1["id"]
        neo_close_approach_data_1 = neo_1['close_approach_data'][0]
        for neo_2 in test_nm_2:
            neo_id_2 = neo_2["id"]
            neo_close_approach_data_2 = neo_2['close_approach_data'][0]
            if neo_id_1 == neo_id_2 and neo_close_approach_data_1 == neo_close_approach_data_2:
                found_in_nm_2 += 1
    assert(found_in_nm_2 == len(test_nm_1))

def test_month_closest_approaches_total_n_pages_subset():
    """ 
    Test that smaller values of total_n_pages are always a subset of greater values of total_n_pages, and that 
    each of these only appear in the superset one time
    """
    test_nm_1 = nearest_misses(total_n_pages=1)
    test_nm_2 = nearest_misses(total_n_pages=2)
    found_in_nm_2 = 0
    for neo_1 in test_nm_1:
        neo_id_1 = neo_1["id"]
        neo_close_approach_data_1 = neo_1['close_approach_data'][0]
        for neo_2 in test_nm_2:
            neo_id_2 = neo_2["id"]
            neo_close_approach_data_2 = neo_2['close_approach_data'][0]
            if neo_id_1 == neo_id_2 and neo_close_approach_data_1 == neo_close_approach_data_2:
                found_in_nm_2 += 1
    assert(found_in_nm_2 == len(test_nm_1))
    
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## asteroid_closest_approach()
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def test_equiv_nearest_misses_neo_closest_app():
    """ Test the equivalence of nearest_misses(n=1) and asteroids_closest_approaches() """
    nm_1 = nearest_misses(n=1)
    asteroids_closest_approaches = asteroid_closest_approach()
    assert nm_1 == asteroids_closest_approaches

##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
## month_closest_approaches() variations
##-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
def test_month_closest_approaches_str_variations():
    """ Test that the different ways of specifying the same month behave the same """
    test_month_1 = month_closest_approaches("2020-12-01")
    test_month_2 = month_closest_approaches("2020-12")
    test_month_3 = month_closest_approaches("2020/12", "/")
    test_month_4 = month_closest_approaches("2020_12_01", "_")
    assert (test_month_1 == test_month_2) and (test_month_1 == test_month_3) and (test_month_1 == test_month_4)
