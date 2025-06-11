import os
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from data.models import Country, CovidData

DATA_URL = "https://covid.ourworldindata.org/data/owid-covid-data.csv"

class Command(BaseCommand):
    help = 'Imports COVID-19 data from Our World in Data'

    def handle(self, *args, **options):
        self.stdout.write("Downloading COVID-19 data...")

        # Load data
        df = pd.read_csv(DATA_URL)

        # Convert date column
        df['date'] = pd.to_datetime(df['date']).dt.date

        # Process each row
        total_rows = len(df)
        for i, row in df.iterrows():
            # Get or create country
            country, created = Country.objects.get_or_create(
                iso_code=row['iso_code'],
                defaults={
                    'name': row['location'],
                    'continent': row['continent'] if pd.notna(row['continent']) else '',
                    'population': row['population'] if pd.notna(row['population']) else None
                }
            )

            # Create or update CovidData record
            CovidData.objects.update_or_create(
                country=country,
                date=row['date'],
                defaults={
                    'total_cases': row['total_cases'],
                    'new_cases': row['new_cases'],
                    'new_cases_smoothed': row['new_cases_smoothed'],
                    'total_deaths': row['total_deaths'],
                    'new_deaths': row['new_deaths'],
                    'new_deaths_smoothed': row['new_deaths_smoothed'],
                    'total_vaccinations': row['total_vaccinations'],
                    'people_vaccinated': row['people_vaccinated'],
                    'people_fully_vaccinated': row['people_fully_vaccinated'],
                    'new_vaccinations': row['new_vaccinations'],
                    'new_vaccinations_smoothed': row['new_vaccinations_smoothed'],
                    'reproduction_rate': row['reproduction_rate'],
                    'icu_patients': row['icu_patients'],
                    'hosp_patients': row['hosp_patients'],
                    'positive_rate': row['positive_rate'],
                }
            )

            # Print progress
            if i % 100 == 0:
                self.stdout.write(f"Processed {i}/{total_rows} rows...")

        self.stdout.write(self.style.SUCCESS("Successfully imported COVID-19 data"))