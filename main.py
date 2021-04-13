"""
Script that sends the most profitable shoes to email...
Define profitability by taking last sale price and dividing by retail price to determine ratio

basic idea:
define how many shoes to look for first

1. send request to stockx to scrape every shoe on the upcoming calendar
2. iterate through the ufck mess to get href
3. append all href to a list
4. iterate through list and send get request to stockx + href
5. scrape retail price, date and closest ask price (put dates in parentheeses)
6. calculate ratio between retail and last ask
7. either twitter, text or email to communicate

run every 2 days or something
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
import schedule
from sendEmail import *

class Shoe:
    """
    Class with attributes of release date, last sale price, retail price, ratio, name, size of last sale and link.
    """
    def __init__(self, date, price, retail, ratio, name, size, link):
        self.date = date
        self.price = price
        self.retail = retail
        self.ratio = ratio
        self.name = name
        self.size = size
        self.link = link

    def __str__(self):
        return '{self.name}, retailing at {self.retail}, is selling at {self.price} at a premium of {self.ratio} on {self.date} in size {self.size}'.format(self=self)

def wait():
    """
    helper function that delays for a random amount between 1-3 seconds to avoid suspusion
    """
    time.sleep(random.randint(1, 3))

def getShoes():
    """
    Returns a list of shoe links of upcoming releases from stockx as strings
    """
    url = "https://stockx.com/new-releases/sneakers"
    headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    # send request to stockx with headers
    response = requests.get(url, headers=headers)

    #soup
    soup = BeautifulSoup(response.content,'lxml')
    newshoes = soup.select('div[data-testid=calendar-tile]') # list of every shoe in a "calendar tile"

    shoeList = [] # iterate through shoes to get links
    for item in newshoes:
        item = str(item)
        index = item.index("href")
        item = item[index+6:]  # probably more efficient way to do this with BeautifulSoup
        index = item.index('"')
        item = item[:index]
        shoeList.append("https://stockx.com" + item)
    return shoeList # return the list

def searchShoe(url):
    """
    Takes a url as a string parameter and returns a Shoe object with:
    last sale price, retail price, release date, name and premium ratio
    """
    headers = { # headers; note, should include referer if i ever figure it out
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    } # potentially randomize user-agent?

    # send request to url with headers
    response = requests.get(url, headers=headers)
    # create soup object
    soup = BeautifulSoup(response.content,'lxml')
    # find the last sale price
    price = soup.find("div", {"class": "sale-value"}).get_text(strip=True)
    # find the name of the shoe
    name = soup.find("h1", {"class": "name"}).get_text(strip=True)

    try: # find size
        size = soup.find("span", {"class": "bid-ask-sizes cursor"}).get_text(strip=True)
        size = ''.join([char for char in list(size) if char.isalpha() == False])
    except AttributeError: # sometimes size can be "--" if no last sale
        print("could not find size for", name)
        size = "NA"

    link = url

    # these 2 do the same thing - find retail and release date
    """for item in soup.find_all():
        if "data-testid" in item.attrs:
            #print(item.attrs)
            #if item["data-testid"] == "product-detail-retail price":
            if item["data-testid"] in {"product-detail-retail price","product-detail-release date"}:
                print(item)"""

    result = soup.findAll(attrs={"data-testid": "product-detail-retail price"})
    result = [str(item) for item in result] # convert to string
    try:
        retail = re.search('<!-- -->(.+?)<!-- -->', result[0]).group(1)
    except IndexError: # if indexerror, price cannot be found
        retail = "NA"

    result = soup.findAll(attrs={"data-testid": "product-detail-release date"})
    result = [str(item) for item in result] # convert to string
    try: # if indexerror, date cannot be found
        date = re.search('<!-- -->(.+?)<!-- -->', result[0]).group(1)
    except IndexError:
        date = "NA"

    # calculate ratio of sale price / retail
    try:
        ratio = round(int(price.replace('$', '')) / int(retail.replace('$', '')), 3)
    # sometimes, there is no last sale price because shoe isnt popular
    except ValueError: # "--" or "NA" is probably price, so replace with "NA"
        ratio = "NA"

    # return an instance of a shoe object instantiated with scraped info and link
    return Shoe(str(date), str(price), str(retail), ratio, str(name), str(size), link)


def main():
    """
    Main function that takes the first 15 entries from getShoes and calls searchShoe on every one of them,
    and if ratio >= 2, then append to a list and send the contents of that list with sendEmail
    """
    finalList = []
    shoez = getShoes() # shoez is a list of upcoming shoes
    message = ''
    #print(shoez)
    for shoe in shoez[:15]: # first 15 of the 40 shoes that are from stockx
        result = searchShoe(shoe)
        #print(result.ratio)
        # ratio has to be a float (not "NA") and greater than/ equal to 2
        if isinstance(result.ratio, float) and result.ratio >= 2.000:
            finalList.append(result)
        wait() # wait bw every request to not seem sus
    for shoe in finalList:
        #print(shoe)
        message += "<a href=" + shoe.link + ">" + str(shoe) + "</a>" + "<br> <br>" # make the whole thing a link

    # sanity check to see if shoes are in list and nothing is broken
    print(len(finalList), "/", len(shoez[:15]))

    # list of random harry potter names to sign off email with
    # TODO: add last names to characters
    signature = ["Harry Potter", "Dumbledore", "Voldemort", "Severus Snape", "Sirius Black", "Hermione Granger", "Ron Weasley", "Draco Malfoy", "Hagrid", "Neville Longbottom", "Dobby", "Remus Lupin", "Bellatrix Lestrange", "Minerva McGonagall"]

    # html that will be sent with each email
    html = """
    <html>
      <head></head>
      <body>
        <p>Hi!<br> <br>
           These are the shoes with a price/retail >= 2:<br><br>""" + message + """
           Best,<br>""" + random.choice(signature) + """
        </p>
      </body>
    </html>
    """

    sendEmail(html) # send the email with html as body

if __name__ == "__main__":
    # send everyday at certain time
    schedule.every().day.at("22:30").do(main)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

    #main()
    #searchShoe("https://stockx.com/adidas-zx-8500-overkill-graffiti")
