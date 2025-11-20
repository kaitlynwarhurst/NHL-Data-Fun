# Hockey Data Fun

## Description
This personal project collects and updates NHL data, storing it in a SQLite database. 
The goal is to minimize the number of API calls needed every time I want to access the data, 
while making it convenient to use. 
The project will expand as I develop new applications for this data.

---

## Features
- Fully normalized SQLite database for hockey teams, players, games, goals, assists, and stats
- Automated scripts for populating data
- Structured tables with foreign key relationships for accurate data modeling
- Ready for expansion into analytics and reporting

---

## Tech Stack
- Python 3.11+
- SQLite3 for database storage
- nhlpy API for data collection (https://pypi.org/project/nhl-api-py/ or https://github.com/coreyjs/nhl-api-py/)
- Pandas (planned for analysis)

---

## Folders
- Databases: all files related to creating, populating and updating the database
- Applications: all files and folders that use the data in some way

- relevant documentation can be found in the subfolders
