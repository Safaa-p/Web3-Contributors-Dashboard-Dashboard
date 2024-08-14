from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import models
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.core.serializers.json import DjangoJSONEncoder
from .models import Treasury_guild
import json
from django.contrib.auth import authenticate, login as auth_login , logout
from django.contrib import messages


def Signout(request):
    logout(request)
    return redirect('login')
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # If authentication is successful, log the user in
            auth_login(request, user)
            return redirect('members')  # Redirect to a home page or dashboard
        else:
            # If authentication fails, show an error message
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')
def first(request):
    # Calculate the total minutes, USD, and AGIX
    total_minutes = Treasury_guild.objects.aggregate(total_mins=Sum('mins'))['total_mins'] or 0
    total_usd = Treasury_guild.objects.aggregate(total_usd=Sum('usd'))['total_usd'] or 0
    total_agix = Treasury_guild.objects.aggregate(total_agix=Sum('agix'))['total_agix'] or 0

    # Calculate the combined total USD + AGIX
    total_combined = total_usd + total_agix

    # Fetch the subgroup data and calculate the combined totals for each subgroup
    subgroup_data = Treasury_guild.objects.values('subgroup').annotate(
        total_mins=Sum('mins'),
        total_usd=Sum('usd'),
        total_agix=Sum('agix'),
        combined_total=Sum('usd') + Sum('agix'),
        contributor_count=Count('wallet_address', distinct=True)
    ).order_by('-total_mins')  # Order by total_mins in descending order

    # Calculate percentages for each subgroup
    for subgroup in subgroup_data:
        subgroup['combined_percentage'] = (subgroup['combined_total'] / total_combined * 100) if total_combined > 0 else 0
        subgroup['mins_percentage'] = (subgroup['total_mins'] / total_minutes * 100) if total_minutes > 0 else 0
        subgroup['usd_percentage'] = (subgroup['total_usd'] / total_usd * 100) if total_usd > 0 else 0
        subgroup['agix_percentage'] = (subgroup['total_agix'] / total_agix * 100) if total_agix > 0 else 0

    # Find the top subgroup with the most combined total
    top_subgroup_combined = max(subgroup_data, key=lambda x: x['combined_total'], default={})
    if top_subgroup_combined:
        top_subgroup_combined['combined_percentage'] = (top_subgroup_combined['combined_total'] / total_combined * 100) if total_combined > 0 else 0

    # Fetch the subgroup with the most minutes
    subgroup_with_most_minutes = Treasury_guild.objects.values('subgroup').annotate(
        total_mins=Sum('mins')
    ).order_by('-total_mins').first()
    if subgroup_with_most_minutes:
        subgroup_with_most_minutes['percentage'] = (subgroup_with_most_minutes['total_mins'] / total_minutes * 100) if total_minutes > 0 else 0

    # Fetch the subgroup with the most distinct wallet addresses
    subgroup_with_most_contributors = Treasury_guild.objects.values('subgroup').annotate(
        contributor_count=Count('wallet_address', distinct=True)
    ).order_by('-contributor_count').first()

    # Calculate percentage for the most contributors subgroup
    total_contributors = Treasury_guild.objects.values('subgroup').annotate(
        contributor_count=Count('wallet_address', distinct=True)
    ).aggregate(total_contributors=Sum('contributor_count'))['total_contributors'] or 0

    if subgroup_with_most_contributors:
        subgroup_with_most_contributors['percentage'] = (subgroup_with_most_contributors['contributor_count'] / total_contributors * 100) if total_contributors > 0 else 0

    # Calculate the total USD and AGIX
    total_usd_agix = {'total_usd': total_usd, 'total_agix': total_agix}

    context = {
        'subgroup_with_most_minutes': subgroup_with_most_minutes,
        'total_usd_agix': total_usd_agix,
        'subgroup_with_most_contributors': subgroup_with_most_contributors,
        'top_subgroup_combined': top_subgroup_combined,
        'subgroup_data': subgroup_data,
    }

    return render(request, 'first.html', context)

from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import Treasury_guild
import json
from django.core.serializers.json import DjangoJSONEncoder

def workgroup(request):
    # Fetch the default date range
    if Treasury_guild.objects.exists():
        start_date = Treasury_guild.objects.earliest('completed_at').completed_at.date()
        end_date = Treasury_guild.objects.latest('completed_at').completed_at.date()
    else:
        start_date = end_date = timezone.now().date()

    # Get selected date range from the request
    selected_start_date = request.GET.get('startdate', start_date)
    selected_end_date = request.GET.get('enddate', end_date)
    selected_subgroups = request.GET.getlist('subgroups[]')

    # Parse the dates if they are provided as strings
    if isinstance(selected_start_date, str):
        selected_start_date = parse_date(selected_start_date)
    if isinstance(selected_end_date, str):
        selected_end_date = parse_date(selected_end_date)

    # Initialize the queryset with date filter
    queryset = Treasury_guild.objects.filter(completed_at__date__range=[selected_start_date, selected_end_date])

    # Filter by selected subgroups
    if selected_subgroups and 'all' not in selected_subgroups:
        queryset = queryset.filter(subgroup__in=selected_subgroups)

    # Annotate data for charts
    monthly_distribution = queryset.values('subgroup').annotate(
        total_mins=Sum('mins'),
        total_agix=Sum('agix')
    ).order_by('subgroup')

    task_contributor_data = queryset.annotate(
        month=TruncMonth('completed_at')
    ).values('month').annotate(
        task_count=Count('task_name'),
        contributor_count=Count('wallet_owner')
    ).order_by('month')

    monthly_agix_mins_distribution = queryset.annotate(
        month=TruncMonth('completed_at')
    ).values('month').annotate(
        total_mins=Sum('mins'),
        total_agix=Sum('agix')
    ).order_by('month')

    wallet_distribution = queryset.values('wallet_address').annotate(
        total_mins=Sum('mins'),
        total_agix=Sum('agix')
    ).order_by('wallet_address')

    # Get distinct subgroups for filter
    subgroups = Treasury_guild.objects.values_list('subgroup', flat=True).distinct()

    # Pass the context to the template
    context = {
        'monthly_distribution': json.dumps(list(monthly_distribution), cls=DjangoJSONEncoder),
        'task_contributor_data': json.dumps(list(task_contributor_data), cls=DjangoJSONEncoder),
        'monthly_agix_mins_distribution': json.dumps(list(monthly_agix_mins_distribution), cls=DjangoJSONEncoder),
        'wallet_distribution': json.dumps(list(wallet_distribution), cls=DjangoJSONEncoder),
        'start_date': selected_start_date,
        'end_date': selected_end_date,
        'subgroups': subgroups,  # Pass subgroups to the template
        'selected_subgroups': selected_subgroups,  # Pass selected subgroups to the template
    }

    return render(request, 'work_guild.html', context)

def workgroup_data(request):
    # Get selected date range from the request
    start_date = request.GET.get('startdate')
    end_date = request.GET.get('enddate')

    # Parse the dates if they are provided as strings
    if isinstance(start_date, str):
        start_date = parse_date(start_date)
    if isinstance(end_date, str):
        end_date = parse_date(end_date)

    # Initialize the queryset with date filter
    queryset = Treasury_guild.objects.filter(completed_at__date__range=[start_date, end_date])

    # Filter by selected subgroups
    selected_subgroups = request.GET.getlist('subgroups[]')
    if selected_subgroups and 'all' not in selected_subgroups:
        queryset = queryset.filter(subgroup__in=selected_subgroups)

    # Annotate data for charts
    monthly_distribution = queryset.values('subgroup').annotate(
        total_mins=Sum('mins'),
        total_agix=Sum('agix')
    ).order_by('subgroup')

    subgroup_labels = [item['subgroup'] for item in monthly_distribution]
    mins_data = [item['total_mins'] for item in monthly_distribution]
    agix_data = [item['total_agix'] for item in monthly_distribution]

    return JsonResponse({
        'subgroup_chart': {
            'labels': subgroup_labels,
            'datasets': [
                {
                    'label': 'AGIX',
                    'data': agix_data,
                    'backgroundColor': 'rgba(255, 206, 86, 0.2)',
                    'borderColor': 'rgba(255, 206, 86, 1)',
                    'borderWidth': 1
                },
                {
                    'label': 'MINS',
                    'data': mins_data,
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }
            ]
        }
    })


def members(request):
    contributor_name = request.GET.get('contributor_name')
    tasks = Treasury_guild.objects.filter(wallet_owner=contributor_name)

    #  the total values across all subgroups
    total_mins = tasks.aggregate(total_mins=Sum('mins'))['total_mins'] or 1
    total_agix = tasks.aggregate(total_agix=Sum('agix'))['total_agix'] or 1
    total_usd = tasks.aggregate(total_usd=Sum('usd'))['total_usd'] or 1

    # Calculate percentages for each subgroup
    subgroup_data = tasks.values('subgroup').annotate(
    mins_percentage=(Sum('mins') / total_mins) * 100,
    agix_percentage=(Sum('agix') / total_agix) * 100,
    usd_percentage=(Sum('usd') / total_usd) * 100,
    total_mins=Sum('mins')  
).distinct().order_by('-total_mins')
    top_mins_group = subgroup_data.order_by('-mins_percentage').first()
    top_agix_group = subgroup_data.order_by('-agix_percentage').first()
    top_usd_group = subgroup_data.order_by('-usd_percentage').first()

    context = {
        'contributor_name': contributor_name,
        'subgroup_data': subgroup_data,
        'top_mins_group': top_mins_group,
        'top_agix_group': top_agix_group,
        'top_usd_group': top_usd_group,
    }
    return render(request, 'members.html', context)

