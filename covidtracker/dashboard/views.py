from django.shortcuts import render
from data.models import Country, CovidData
import plotly.express as px
import pandas as pd


from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
import json

@require_GET
@csrf_exempt  # Only for development - remove in production
def country_data_api(request):
    try:
        # Get and validate parameters
        country_code = request.GET.get('country', '').upper()
        metric = request.GET.get('metric', 'total_cases').lower()

        if not country_code:
            return JsonResponse({'error': 'Country code is required'}, status=400)

        # Validate date format
        try:
            start_date = request.GET.get('start_date', '2020-01-01')
            end_date = request.GET.get('end_date', datetime.now().strftime('%Y-%m-%d'))
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        # Get data
        try:
            country = Country.objects.get(iso_code__iexact=country_code)
            data = CovidData.objects.filter(
                country=country,
                date__range=[start_date, end_date]
            ).exclude(**{f'{metric}__isnull': True}).order_by('date')

            if not data.exists():
                return JsonResponse({
                    'error': f'No {metric.replace("_", " ")} data available for {country.name}',
                    'suggestion': 'Try a different date range or metric'
                }, status=404)

            response_data = {
                'country': country.name,
                'metric': metric.replace('_', ' ').title(),
                'dates': [d.date.strftime('%Y-%m-%d') for d in data],
                'values': [float(getattr(d, metric)) for d in data],
                'units': 'count' if metric != 'death_rate' else 'percentage'
            }

            return JsonResponse(response_data)

        except Country.DoesNotExist:
            similar = Country.objects.filter(iso_code__icontains=country_code)[:5]
            suggestions = [c.iso_code for c in similar]
            return JsonResponse({
                'error': f'Country code "{country_code}" not found',
                'suggestions': suggestions
            }, status=404)

    except Exception as e:
        return JsonResponse({
            'error': 'Server error',
            'details': str(e)
        }, status=500)

def get_country_data(request):
    if request.method == 'GET':
        country_iso = request.GET.get('country')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        metric = request.GET.get('metric', 'total_cases')

        # Validate parameters
        if not country_iso:
            return JsonResponse({'error': 'Country code is required'}, status=400)

        try:
            # Get the country object
            country = Country.objects.get(iso_code=country_iso)

            # Set default dates if not provided
            end_date = datetime.now().date() if not end_date else datetime.strptime(end_date, '%Y-%m-%d').date()
            start_date = end_date - timedelta(days=365) if not start_date else datetime.strptime(start_date, '%Y-%m-%d').date()

            # Get data with null checks
            data = CovidData.objects.filter(
                country=country,
                date__gte=start_date,
                date__lte=end_date
            ).exclude(**{f'{metric}__isnull': True}).order_by('date')

            if not data.exists():
                return JsonResponse({'error': 'No data available for the selected parameters'}, status=404)

            # Prepare response
            response_data = {
                'dates': [d.date.strftime('%Y-%m-%d') for d in data],
                'values': [getattr(d, metric) for d in data],
                'country': country.name,
                'metric': metric.replace('_', ' ').title(),
                'message': 'Success'
            }

            return JsonResponse(response_data)

        except Country.DoesNotExist:
            return JsonResponse({'error': 'Country not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

# dashboard/views.py
def country_search(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'error': 'No search query provided'}, status=400)

    countries = Country.objects.filter(
        name__icontains=query
    ).values('iso_code', 'name')[:10]  # Limit to 10 results

    return JsonResponse(list(countries), safe=False)


# dashboard/views.py
def data_status(request):
    from data.models import Country, CovidData

    status = {
        'total_countries': Country.objects.count(),
        'countries_with_population': Country.objects.exclude(population__isnull=True).count(),
        'total_covid_records': CovidData.objects.count(),
        'latest_date': CovidData.objects.latest('date').date if CovidData.objects.exists() else None,
        'sample_data': list(CovidData.objects.select_related('country').order_by('-date')[:5].values(
            'date', 'total_cases', 'new_cases', 'country__name', 'country__population'
        ))
    }
    return JsonResponse(status)

def global_dashboard(request):
    try:
        # Get the most recent date with actual data
        latest_date = CovidData.objects.exclude(
            total_cases__isnull=True
        ).latest('date').date

        # Get countries with complete data
        countries_with_data = Country.objects.exclude(
            population__isnull=True
        ).exclude(
            population=0
        ).filter(
            covid_data__date=latest_date
        ).distinct()

        if not countries_with_data.exists():
            return render(request, 'dashboard/global.html', {
                'error': 'No countries with complete data available'
            })

        # Prepare map data
        map_data = []
        for country in countries_with_data:
            try:
                data = country.covid_data.get(date=latest_date)
                if data.total_cases:
                    cases_per_million = (data.total_cases / country.population) * 1e6
                    map_data.append({
                        'iso_code': country.iso_code,
                        'country': country.name,
                        'total_cases': data.total_cases,
                        'cases_per_million': cases_per_million,
                    })
            except CovidData.DoesNotExist:
                continue

        if not map_data:
            return render(request, 'dashboard/global.html', {
                'error': 'Could not calculate metrics for any country'
            })

        # Create visualizations
        df = pd.DataFrame(map_data)
        fig = px.choropleth(
            df,
            locations="iso_code",
            color="cases_per_million",
            hover_name="country",
            hover_data=["total_cases"],
            title=f"COVID-19 Cases per Million (Latest Data)"
        )
        map_html = fig.to_html(full_html=False)

        return render(request, 'dashboard/global.html', {
            'map_html': map_html,
            'last_updated': latest_date
        })

    except Exception as e:
        return render(request, 'dashboard/global.html', {
            'error': f'Error loading data: {str(e)}'
        })


# In views.py
def debug_country_data(request, iso_code):
    country = Country.objects.get(iso_code=iso_code)
    data = CovidData.objects.filter(country=country).order_by('-date')[:5]
    return JsonResponse({
        'country': country.name,
        'data': list(data.values('date', 'total_cases', 'new_cases', 'total_deaths'))
    })

def debug_all_countries(request):
    countries = Country.objects.all().values('iso_code', 'name')
    return JsonResponse(list(countries), safe=False)

def interactive_dashboard(request):
    countries = Country.objects.all()
    default_end = datetime.now().date()
    default_start = default_end - timedelta(days=365)

    context = {
        'countries': countries,
        'default_start': default_start.strftime('%Y-%m-%d'),
        'default_end': default_end.strftime('%Y-%m-%d'),
    }


    return render(request, 'dashboard/interactive.html', context)

"""

def global_dashboard(request):
    # Get latest data for each country
    latest_data = CovidData.objects.filter(
        date=CovidData.objects.latest('date').date
    ).select_related('country')

    # Prepare data for choropleth map with proper null checks
    map_data = []
    for data in latest_data:
        # Skip entries without population data
        if not data.country.population or not data.total_cases:
            continue

        try:
            cases_per_million = (data.total_cases / data.country.population) * 1e6
        except (TypeError, ZeroDivisionError):
            cases_per_million = None

        map_data.append({
            'iso_code': data.country.iso_code,
            'country': data.country.name,
            'total_cases': data.total_cases,
            'total_deaths': data.total_deaths,
            'total_vaccinations': data.total_vaccinations,
            'cases_per_million': cases_per_million,
        })

    if not map_data:
        return render(request, 'dashboard/global.html', {
            'error': 'No valid data available for visualization'
        })

    df = pd.DataFrame(map_data)

    # Create choropleth map
    fig = px.choropleth(
        df,
        locations="iso_code",
        color="cases_per_million",
        hover_name="country",
        hover_data=["total_cases", "total_deaths", "total_vaccinations"],
        color_continuous_scale=px.colors.sequential.Plasma,
        title="COVID-19 Cases per Million"
    )

    # Convert to HTML
    map_html = fig.to_html(full_html=False)

    # Get top 10 countries by cases (excluding None values)
    top_countries = latest_data.exclude(total_cases__isnull=True).order_by('-total_cases')[:10]

    # Create bar chart
    bar_fig = px.bar(
        pd.DataFrame([{
            'country': data.country.name,
            'total_cases': data.total_cases,
            'total_deaths': data.total_deaths
        } for data in top_countries]),
        x='country',
        y='total_cases',
        title='Top 10 Countries by Total Cases'
    )
    bar_html = bar_fig.to_html(full_html=False)

    context = {
        'map_html': map_html,
        'bar_html': bar_html,
        'last_updated': CovidData.objects.latest('date').date
    }

    return render(request, 'dashboard/global.html', context)

def country_comparison(request):
    countries = Country.objects.all()

    if request.method == 'POST':
        selected_countries = request.POST.getlist('countries')
        metric = request.POST.get('metric', 'total_cases')

        # Get data for selected countries
        data = CovidData.objects.filter(
            country__iso_code__in=selected_countries
        ).select_related('country').order_by('date')

        # Prepare data for line chart
        line_data = []
        for entry in data:
            line_data.append({
                'date': entry.date,
                'country': entry.country.name,
                'value': getattr(entry, metric)
            })

        df = pd.DataFrame(line_data)

        # Create line chart
        line_fig = px.line(
            df,
            x='date',
            y='value',
            color='country',
            title=f"{metric.replace('_', ' ').title()} Over Time"
        )
        line_html = line_fig.to_html(full_html=False)

        context = {
            'countries': countries,
            'selected_countries': selected_countries,
            'metric': metric,
            'line_html': line_html
        }

        return render(request, 'dashboard/comparison.html', context)

    context = {
        'countries': countries
    }
    return render(request, 'dashboard/comparison.html', context)

"""""