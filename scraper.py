from selenium import webdriver as wd
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import os

file = open("config.json")
config = json.load(file)
movie_name = config["name"]
movie_venues = config["venues"]

my_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument(f"--user-agent={my_user_agent}")

print("SCRAPER ONLINE")

while True: 
    scrape_flag = True
    print("SCRAPING...")
    try:
        BMS_URL = "https://in.bookmyshow.com/explore/movies-" + config["city"]
        driver = wd.Chrome(options=chrome_options)
        driver.get(BMS_URL)
        sleep(2)
        movies = driver.find_elements(
            By.CLASS_NAME, "style__CardContainer-sc-1ljcxl3-1"
        )[1:]
        movie_element = None
        for movie in movies:
            if movie.get_attribute("href").split("/")[5] == movie_name:
                try:
                    movie.click()
                    sleep(2)
                    movie_element = movie
                    break
                except:
                    print("Something Went Wrong :(")
                    exit(1)

        book_ticket_url = None

        if movie_element:
            book_btn = driver.find_element(By.CLASS_NAME, "sc-1vmod7e-2")
            sleep(2)
            book_btn.click()
            sleep(2)
            if config['multilingual'] == "Yes":
                lang_section = driver.find_elements(By.TAG_NAME,'li')
                for lang in lang_section:
                    print(lang.find_element(By.TAG_NAME,'span').get_attribute('innerHTML'))
                    if config['language'] == lang.find_element(By.TAG_NAME,'span').get_attribute('innerHTML'):
                        lang.find_element(By.CLASS_NAME,'sc-vhz3gb-3').click()
                        sleep(2)
                        break
            book_ticket_url = driver.current_url
        else:
            print("Could not find movie :(")
            sleep(config['interval'])
            scrape_flag = False

        driver.quit()

        if scrape_flag and book_ticket_url:
            driver = wd.Chrome(options=chrome_options)
            driver.get(book_ticket_url)
            sleep(2)

        elif not scrape_flag and book_ticket_url:
            print("Booking Not Open :(")
            sleep(config['interval'])
            scrape_flag = False

        else:
            scrape_flag = False
            print("Trying Again")
            sleep(config['interval'])


        if scrape_flag:
            message = """
                <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
                        <title>Document</title>
                    </head>
                    <body>
                        <div>
            """

            venues = driver.find_element(By.ID, "venuelist").find_elements(
                By.TAG_NAME, "li"
            )

            shows_cnt = 0

            for venue in venues:
                venue_name = venue.get_attribute("data-name")
                venue_link = venue.find_element(
                    By.CLASS_NAME, "__venue-name"
                ).get_attribute("href")
                if venue_name in movie_venues:
                    shows = venue.find_elements(By.TAG_NAME, "a")[1:]
                    print(shows)
                    shows_cnt += len(shows)
                    if len(shows) > 0:
                        message += (
                            "<h3 style='text-align:center;'><a href='"
                            + venue_link
                            + "'>"
                            + venue_name
                            + "</a></h3>"
                        )
                        message += """
                                <table style="border-collapse:collapse;width:100%;">
                                    <thead>
                                    <tr>
                                        <th style="padding:8px; background-color:#04AA6D; color:white;">Show Time</th>
                                        <th style="padding:8px;background-color:#04AA6D; color:white;">Availability</th>
                                    </tr>
                                    </thead>
                                    <tbody>
                                """
                        for show in shows:
                            showtime = (
                                show.get_attribute("data-display-showtime")
                                if show.get_attribute("data-display-showtime")
                                else "No Show"
                            )
                            details = show.get_attribute("data-cat-popup")
                            availability = (
                                json.loads(details)[0]["availabilityText"]
                                if details
                                else "Not Available"
                            )
                            message += (
                                "<tr><td style='padding:8px;text-align:center;border-bottom:1px solid #ddd'>"
                                + showtime
                                + "</td><td style='padding:8px;text-align:center;border-bottom:1px solid #ddd'>"
                                + availability
                                + "</td></tr>"
                            )
                        message += """
                                </tbody>
                            </table>
                        """

            driver.quit()

            message += """
                    </div>
                </body>
            </html>
            """

            print("SCRAPED :)")

            msg = MIMEMultipart("alternatives")
            msg["Subject"] = (
                "Ticket Availability Update for "
                + movie_name
                + " "
                + datetime.datetime.now().strftime("%H:%M:%S")
            )
            msg["From"] = config["sender"]
            msg["To"] = ", ".join(config["reciever"])
            msg.attach(MIMEText(message, "html"))
            smtpObj = smtplib.SMTP("smtp.gmail.com", 587)
            smtpObj.ehlo()
            smtpObj.starttls()
            smtpObj.login(config["sender"], config["password"])
            if shows_cnt > 0:
                smtpObj.sendmail(config["sender"], config["reciever"], msg.as_string())
            else:
                print("Nothing to Send...")
            smtpObj.quit()

            print("MAIL SENT")
            sleep(config['interval'])
            os.system("clear || cls")

    except Exception as exp:
        print("Ending Task :(")
        print(exp)
        exit(1)
