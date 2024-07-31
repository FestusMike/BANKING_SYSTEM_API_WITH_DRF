# Geographical Information API

***Welcome to the Geographical Information API, a comprehensive resource for geographical data, providing details about continents, countries, states, and local governments. This API is designed to be freely accessible to everyone.***

The base url for accessing the api is: https://geographicalinfoapiforeveryone.pythonanywhere.com/api/v1/
Click [Here](https://geographicalinfoapiforeveryone.pythonanywhere.com/api/v1/docs) to view the documentation.

> [!NOTE]
> Please be aware that the names of all continents, states or equivalents, and local governments or equivalents, must be capitalized. i.e. The first letter must be in upper case. If you don't get that, don't fret:smile:the API has a spelling suggestion feature that contains that provides a list of possible correct spellings. You like that? I bet you do :rofl:

+ To retrieve basic data of all the continents in the world, send a GET request to: https://geographicalinfoapiforeveryone.pythonanywhere.com/api/v1/continents. Upon a successful request, you'll get a Json response body like the one below:

```
{
  "count": 7,
  "continents": [
    {
      "name": "Africa",
      "countries_count": 54
    },
    {
      "name": "Asia",
      "countries_count": 49
    }
    // ...
  ]
}
```

+ To fetch the detailed data of all the continents, send a GET request to: https://geographicalinfoapiforeveryone.pythonanywhere.com/api/v1/planet-earth. Upon a successful request, you'll get a Json response body like the one below: 

```
 {
    "count" : 7,
    "continents" : 7,
    "countries" : [
                    "name": "Nigeria",
                    "capital": "Abuja",
                    "currency": "Naira(NGR)",
                    "language": "English",
                    "states": [
                        {
                            "name": "Plateau",
                            "capital": "Jos",
                            "local_governments": [
                                {
                                    "name": "Barikin Ladi"
                                },
                                {
                                    "name": "Bassa"
                                },
                                {
                                    "name": "Bokkos"
                                },
                                {
                                    "name": "Jos East"
                                },
                                //...
                            ]   
                        },
                    ]
                    //....
                ]
            }
```
+ To retrieve the basic detail of all the countries in the world, send a GET request to: https://geographicalinfoapiforeveryone.pythonanywhere.com/api/v1/countries. You'll get a Json Response body like the one below:
```
{
  "count": 213,
  "countries": [
    {
      "name": "Nigeria",
      "capital": "Abuja",
      "currency" : "Naira",
      "language" : "English"
    }
    // ...
  ]
}
```
+ To filter a list of countries based on their continent, send a GET request to: https://geographicalinfoapiforeveryone.pythonanywhere.com/api/v1/continents/{continent_name}/countries. A Json response body like the one below will be returned: 

```
{
  "continent": "Africa",
  "count": 54,
  "countries": [
    {
      "name": "Nigeria",
      "capital": "Abuja",
      "currency": "Naira",
      "language": "English"
    },
    {
      "name": "South Africa",
      "capital": "Pretoria",
      "currency": "Rand",
      "language": "English, Afrikaans"
    }
    // ...
  ]
}
```
+ To search for any country, send a GET request to: https://geographicalinfoapiforeveryone.pythonanywhere.com/api/v1/countries?country={country_name}. If the country exists, you will be provided with a Json response of the detailed information about the country. An example is given below:
```
{
  "count": 1,
  "country": {
    "name": "Nigeria",
    "capital": "Abuja",
    "currency": "Naira",
    "language": "English",
    "states": [
      {
        "name": "Lagos",
        "capital": "Ikeja"
      }
      // ...
    ]
  }
}

```
> [!IMPORTANT]
> Please be informed that a query parameter is necessary for the desired result. if no query parameter is provided, the /countries endpoint will simply return the count and basic detail of all the countries in the world.

+ To fetch a list of all the states in a country and their local governments, send a GET request to: https://geographicalinfoapiforeveryone.pythonanywhere.com/api/v1/countries/{country_name}/states. A Json response like the example provided below will be returned: 

``` 
{
  "count": 36,
  "country": "Nigeria",
  "states": [
    {
      "name": "Lagos",
      "capital": "Ikeja"
    },
    {
      "name": "Kano",
      "capital": "Kano"
    }
    // ...
  ]
}
```
+ To fetch the details of a state based on the country, send a GET request to: https://geographicalinfoapiforeveryone.pythonanywhere.com/api/v1/countries/{country_name}?state={state_name}. A Json response like the example provided below will be returned:

```
{
  "count": 1,
  "country": "Nigeria",
  "state": {
    "name": "Lagos",
    "capital": "Ikeja"
  }
}
```
+ To fetch all the local governments or equivalents in a state in a state, send a GET request to: https://geographicalinfoapiforeveryone.pythonanywhere.com/api/v1/countries/{country_name}/states/{state_name}/local-governments. A Json response like the example provided below will be returned:
```
{
  "count": 20,
  "country": "Nigeria",
  "state": "Lagos",
  "local_governments": [
    {
      "name": "Ikeja"
    },
    {
      "name": "Surulere"
    }
    // ...
  ]
}

```
## Spelling Suggestion
The API returns appropriate error messages with suggestions for common typos. For instance, if a user searches for "nigeria" instead of "Nigeria", the API will respond with:

```
{
  "error": "Country 'nigeria' isn't found. Did you mean 'Nigeria'?"
}

```
## Authentication
***This API is designed to be free and accessible to everyone. No API keys or authentication tokens are required. I love free and open-source technologies. Who doesn't? :sunglasses: *** 

## Contact
***To offer support, comments or suggestions, kindly reach out to me via email: festusmike98@gmail.com***
***Follow me on [linkedin](https://www.linkedin.com/in/micheal-arifajogun-830378212/).***