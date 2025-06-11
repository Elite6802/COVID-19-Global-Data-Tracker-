# COVID-19 Global Data Tracker

![Dashboard](https://github.com/user-attachments/assets/628a01c4-70f6-43e6-896f-889cbe2c82ec)

A Django web application that tracks and visualizes global COVID-19 trends, featuring interactive dashboards, country comparisons, and time-series visualizations.

## Project Objectives

✅ Import and clean COVID-19 global data  
✅ Analyze time trends (cases, deaths, vaccinations)  
✅ Compare metrics across countries/regions  
✅ Visualize trends with interactive charts and maps  
✅ Provide an intuitive user interface for data exploration  

## Key Features

- Interactive choropleth world map showing cases per million
- Country comparison tool with customizable metrics
- Time-series analysis with date range selection
- Automatic data updates from Our World in Data
- Responsive design for desktop and mobile

## Technology Stack

### Backend
- **Python 3.12**
- **Django 5.0**
- **Pandas** (data processing)
- **Plotly** (visualization generation)

### Frontend
- **Bootstrap 5** (UI components)
- **Plotly.js** (interactive charts)
- **jQuery** (AJAX requests)

### Data Sources
- [Our World in Data COVID-19 Dataset](https://github.com/owid/covid-19-data)
- Johns Hopkins University CSSE (backup source)

## Installation Guide

### Prerequisites
- Python 3.10+
- Git
- PostgreSQL (recommended) or SQLite

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Elite6802/COVID-19-Global-Data-Tracker-.git
   cd COVID-19-Global-Data-Tracker
Set up virtual environment:

bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
Install dependencies:

bash
pip install -r requirements.txt
Configure environment variables:
Create a .env file:

ini
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/covid_tracker
Run migrations:

bash
python manage.py migrate
Import COVID-19 data:

bash
python manage.py import_covid_data
Start development server:

bash
python manage.py runserver
Access the application:
Open http://localhost:8000 in your browser
