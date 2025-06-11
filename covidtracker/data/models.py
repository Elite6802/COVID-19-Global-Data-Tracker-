from django.db import models

class Country(models.Model):
    iso_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    continent = models.CharField(max_length=50)
    population = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class CovidData(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='covid_data')
    date = models.DateField()

    # Cases
    total_cases = models.FloatField(null=True, blank=True)
    new_cases = models.FloatField(null=True, blank=True)
    new_cases_smoothed = models.FloatField(null=True, blank=True)

    # Deaths
    total_deaths = models.FloatField(null=True, blank=True)
    new_deaths = models.FloatField(null=True, blank=True)
    new_deaths_smoothed = models.FloatField(null=True, blank=True)

    # Vaccinations
    total_vaccinations = models.FloatField(null=True, blank=True)
    people_vaccinated = models.FloatField(null=True, blank=True)
    people_fully_vaccinated = models.FloatField(null=True, blank=True)
    new_vaccinations = models.FloatField(null=True, blank=True)
    new_vaccinations_smoothed = models.FloatField(null=True, blank=True)

    # Other metrics
    reproduction_rate = models.FloatField(null=True, blank=True)
    icu_patients = models.FloatField(null=True, blank=True)
    hosp_patients = models.FloatField(null=True, blank=True)
    positive_rate = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('country', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.country.name} - {self.date}"