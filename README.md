
# Public Issue Resolution Dashboard

This project is a web-based dashboard for visualizing public issues. It includes features such as a Kanban board for issue tracking, a map for geographical visualization, and various filters and sorting options.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Mock Data](#mock-data)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/ArranHL/public-issue-resolution-dashboard.git
    cd public-issue-resolution-dashboard
    ```

2. Install dependencies using Poetry:
    ```sh
    poetry install
    ```

3. Create a `.env` file in the root directory and add your environment variables:
    ```env
    FLASK_APP=main.py
    FLASK_ENV=development
    ```

    ```
    API_EMAIL=ODK_USERNAME
    API_PASSWORD=ODK_PASSWORD 
    ```

4. Activate the virtual environment:
    ```sh
    poetry shell
    ```

5. Run the Flask application:
    ```sh
    flask run
    ```

## Usage

Open your web browser and navigate to `http://127.0.0.1:5000` to access the dashboard.


## Features

- **Kanban Board**: Track issues with different statuses (New, Open, Waiting, Fixed).
- **Map Integration**: Visualize issues on a map.
- **Filters and Sorting**: Apply various filters and sorting options to manage issues.
- **Issue Details Modal**: View detailed information about each issue.
- **Real-time Updates**: Receive real-time updates using Socket.IO. (Optimizations needed)

## Project Structure
This project is an MVP developed for the [Climate Collective Accelerator](https://climatecollective.org/green-accountability-tech-accelerator) designed to work with the Open Data Kit (ODK). Users will need to have an ODK instance running, either self-hosted ([ODK Central](https://docs.getodk.org/central-intro/)) or hosted by ODK ([getodk.org](https://getodk.org/)).

The project leverages ODK entities to facilitate issue reporting by citizens, which can then be followed up on by citizens themselves or public officials. It follows the resolution methodologies of Integrity Action and takes inspiration from [integrityaction.org](https://integrityaction.org).

Within the ODK API, the details of the first form, entity, and response form need to be adjusted.

The data page utilizes existing project data displayed though a PowerBi Published Dashboard embedded via an iframe.

## Mock Data
This project contains mock data for demonstration purposes. The mock data is used to showcase the features and functionality of the dashboard.
The issued.db recreates at project launch so can be deleted for a fresh project. 


## Contributing

This is a MVP / proof of concept

## License

This project is licensed under the Apache 2 License. 
