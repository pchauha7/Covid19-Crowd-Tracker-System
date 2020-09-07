# Covid19-Crowd-Tracker-System
### Introduction

The idea of this project is to develop an intelligent crowd management system that will let a user know whether if it's safe to go to a superstore or restaurant of their choice and using the place safety grade presented, they can delay their shopping time and plan to go at a time when there is less crowd and it also recommends the user different superstores or restaurant with place safety grade, within a certain distance as set by the user. The system will also recommend nearby superstores/restaurants sorted with respect to place safety grade and its open-close status. This application will also help the stores and restaurants to get control over the crowd management so that it puts less strain on their store workers and supply chain demands in these difficult times. The application tells a user who is looking to go out for grocery shopping or eating at a restaurant, about the current place safety grade which we have divided into 3 grades namely “Very safe”, “Safe” and “Hard to maintain social distancing”.

### Steps to configure and execute the project

1. Set-up MongoDB atlas service and create the collections for different zones.

2. Host the Web tier and application tier codes in google app engine and create separate projects for each.

3. Update keys information in main.py and mongo db client in db.py.
4. Deploy live and analytics application tier code, when deployed use the links and update the urls in web tier's main.py
5. Deploy the web tier code then using google app engine.
6. Configure cron jobs by creating google functions and adding topics as pub/subs. These topics can be used for cron job execution
7. Use the web tier link and use it for running the application

 
