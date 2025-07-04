from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import CustomUserForm as CreateUserForm, AssignTaskForm
from accounts.models import CustomUser
from core.models import Task
from veterinarian_dashboard.models import Animal
from admin_dashboard.models import VetTask  # 🛠️ Fix 1
from user_dashboard.models import DailyActivityReport  # 🛠️ Fix 2
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from .forms import CustomUserForm
from user_dashboard.models import DailyActivityReport, AnimalLog
from core.models import SupportTicket, TicketReply
from .forms import SupportTicketForm, TicketReplyForm
from user_dashboard.models import EmergencyIncident
from core.models import SupportTicket  # ✅ import




@login_required
def admin_dashboard_view(request, branch):
    if request.user.branch != branch or request.user.role != 'admin':
        return render(request, 'errors/unauthorized.html', status=403)

    total_users = CustomUser.objects.filter(branch=branch, role__in=['user', 'veterinarian']).count()
    pending_tasks = VetTask.objects.filter(branch=branch, status='pending').count()
    total_animals = Animal.objects.filter(branch=branch).count()
    reports_today = DailyActivityReport.objects.filter(branch=branch, date__date=timezone.now().date()).count()
    open_tickets = SupportTicket.objects.filter(branch=branch, status='open').count()
    closed_tickets = SupportTicket.objects.filter(branch=branch, status='closed').count()

    return render(request, 'admin_dashboard/dashboard.html', {
        'branch': branch,
        'total_users': total_users,
        'pending_tasks': pending_tasks,
        'total_animals': total_animals,
        'reports_today': reports_today,
        'open_tickets': open_tickets,
        'closed_tickets': closed_tickets,
    })


# 🔐 Admin Role Check
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

# 📊 Admin Dashboard
@login_required
def admin_dashboard(request, branch):
    if request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    context = {
        'branch': request.user.branch.title()
    }
    return render(request, 'admin_dashboard/dashboard.html', context)

# 👤 Create User
@login_required
def create_user(request, branch):
    if request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.branch = request.user.branch  # force same branch
            user.save()
            return redirect('admin_dashboard', branch=branch)
    else:
        form = CreateUserForm()

    return render(request, 'admin_dashboard/create_user.html', {
        'form': form,
        'branch': request.user.branch.title()
    })

# ✅ Assign Task
def task_assign(request, branch):
    if request.user.branch != branch or request.user.role != 'admin':
        return render(request, 'errors/unauthorized.html', status=403)

    form = VetTaskForm(request.POST or None, branch=branch)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.assigned_by = request.user
        task.branch = branch
        task.save()
        return redirect('admin_task_list', branch=branch)

    return render(request, 'admin_dashboard/task_form.html', {'form': form, 'branch': branch})

# List Tasks
def task_list(request, branch):
    if request.user.branch != branch or request.user.role != 'admin':
        return render(request, 'errors/unauthorized.html', status=403)

    tasks = VetTask.objects.filter(branch=branch).order_by('-created_at')
    return render(request, 'admin_dashboard/task_list.html', {'tasks': tasks, 'branch': branch})

# Task Detail
def task_detail(request, branch, task_id):
    task = get_object_or_404(VetTask, id=task_id, branch=branch)
    if request.user.branch != branch or request.user.role != 'admin':
        return render(request, 'errors/unauthorized.html', status=403)

    return render(request, 'admin_dashboard/task_detail.html', {'task': task, 'branch': branch})

# ✅ Approve Activities
@login_required
def approve_activities(request, branch):
    if not is_admin(request.user) or request.user.branch.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    return render(request, 'admin_dashboard/approve_activities.html', {
        'branch': request.user.branch.title()
    })

# ✅ Admin Reports (placeholder)
@login_required
def admin_reports(request, branch):
    if not is_admin(request.user) or request.user.branch.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    return HttpResponse(f"Admin reports for branch: {branch} (placeholder view)")

# ✅ Animal List (placeholder)
@login_required
def animal_list(request, branch):
    if not is_admin(request.user) or request.user.branch.lower() != branch.lower():
        return HttpResponseForbidden("Unauthorized access")

    return HttpResponse(f"Animal list for branch: {branch} (placeholder view)")

# List users
def admin_user_list(request, branch):
    if request.user.role != 'admin' or request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    users = CustomUser.objects.filter(branch__iexact=branch)
    print("Users found:", users.count())
    return render(request, 'admin_dashboard/user_list.html', {'users': users, 'branch': branch})


# Add user
def user_add(request, branch):
    if request.user.role != 'admin' and request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    form = CustomUserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        if form.cleaned_data['password']:
            user.password = make_password(form.cleaned_data['password'])
        user.save()
        return redirect('admin_user_list', branch=branch)

    return render(request, 'admin_dashboard/user_form.html', {'form': form, 'branch': branch, 'title': 'Add User'})

# Edit user
def user_edit(request, branch, user_id):
    if request.user.role != 'admin' and request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    user = get_object_or_404(CustomUser, id=user_id, branch__iexact=branch)
    form = CustomUserForm(request.POST or None, instance=user)

    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        if form.cleaned_data['password']:
            user.password = make_password(form.cleaned_data['password'])
        user.save()
        return redirect('admin_user_list', branch=branch)

    return render(request, 'admin_dashboard/user_form.html', {'form': form, 'branch': branch, 'title': 'Edit User'})


# Delete user
@login_required
def user_delete(request, branch, user_id):
    if request.user.role != 'admin' and request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    user = get_object_or_404(CustomUser, id=user_id, branch=branch)

    if request.method == 'POST':
        user.delete()
        return redirect('admin_user_list', branch=branch)  # make sure this matches your URL name

    return render(request, 'admin_dashboard/user_confirm_delete.html', {
        'user': user,
        'branch': branch
    })

# View daily reports
def reports_view(request, branch):
    if request.user.role != 'admin' and request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    reports = ReportActivity.objects.filter(branch=branch).order_by('-date')
    return render(request, 'admin_dashboard/admin_reports.html', {'reports': reports, 'branch': branch})

# View animal care logs
def care_logs_view(request, branch):
    logs = AnimalLog.objects.filter(branch=branch, log_type='care').order_by('-date')
    return render(request, 'admin_dashboard/care_logs.html', {'logs': logs, 'branch': branch})

# View incident logs
def incident_logs_view(request, branch):
    logs = AnimalLog.objects.filter(branch=branch, log_type='incident').order_by('-date')
    return render(request, 'admin_dashboard/incident_logs.html', {'logs': logs, 'branch': branch})

def admin_incident_logs(request, branch):
    if request.user.role != 'admin' and request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    incidents = EmergencyIncident.objects.filter(animal__branch=branch).order_by('-date_reported')
    return render(request, 'admin_dashboard/incident_logs.html', {
        'branch': branch,
        'incidents': incidents
    })

@login_required
def admin_care_logs(request, branch):
    if request.user.role != 'admin' and request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    logs = AnimalLog.objects.filter(animal__branch=branch).order_by('-date')
    return render(request, 'admin_dashboard/care_logs.html', {
        'branch': branch,
        'logs': logs,
    })

def admin_support(request, branch):
    if request.user.role != 'admin' and request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)


@login_required
def admin_animals(request, branch):
    animals = Animal.objects.filter(branch=branch)
    return render(request, 'admin_dashboard/admin_animals.html', {
        'animals': animals,
        'branch': branch
    })

@login_required
def support_ticket_list(request, branch):
    if request.user.role != 'admin' or request.user.branch != branch:
        return HttpResponseForbidden("Unauthorized")

    tickets = SupportTicket.objects.filter(created_by__branch=branch).order_by('-created_at')
    return render(request, 'admin_dashboard/support_list.html', {'tickets': tickets, 'branch': branch})

@login_required
def support_ticket_detail(request, branch, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    replies = TicketReply.objects.filter(ticket=ticket).order_by('created_at')

    if request.method == 'POST':
        form = TicketReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.ticket = ticket
            reply.user = request.user
            reply.save()
            ticket.status = 'in_progress'
            ticket.save()
            return redirect('admin_support_detail', branch=branch, ticket_id=ticket.id)
    else:
        form = TicketReplyForm()

    return render(request, 'admin_dashboard/support_detail.html', {
        'ticket': ticket,
        'replies': replies,
        'form': form,
        'branch': branch
    })

@login_required
def close_support_ticket(request, branch, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    ticket.status = 'closed'
    ticket.save()
    return redirect('admin_support_detail', branch=branch, ticket_id=ticket.id)