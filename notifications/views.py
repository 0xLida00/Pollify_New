from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Notification

@login_required
def notifications_list(request):
    """Display all notifications with pagination."""
    notifications = request.user.notifications.order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    page_number = request.GET.get('page', 1)
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page

    try:
        notifications_page = paginator.page(page_number)
    except Exception:
        notifications_page = paginator.page(1)

    return render(request, 'notifications/notifications_list.html', {
        'notifications': notifications_page,
        'unread_notifications_count': unread_count,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator,
        'page_obj': notifications_page
    })


@login_required
def notification_detail(request, notification_id):
    """View a specific notification detail."""
    notification = get_object_or_404(Notification, id=notification_id)

    # Ensure only the recipient can view the notification
    if notification.recipient != request.user:
        return HttpResponseForbidden("You are not allowed to view this notification.")

    return render(request, 'notifications/notification_detail.html', {
        'notification': notification,
    })


@login_required
def mark_notification_as_read(request, notification_id):
    """Mark a single notification as read, with AJAX support."""
    notification = get_object_or_404(Notification, id=notification_id)

    # Ensure only the recipient can mark it as read
    if notification.recipient != request.user:
        return HttpResponseForbidden("You cannot mark this notification as read.")

    notification.is_read = True
    notification.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Notification marked as read'})

    return redirect('notifications_list')


@login_required
def mark_all_notifications_as_read(request):
    """Mark all unread notifications as read, with AJAX support."""
    request.user.notifications.filter(is_read=False).update(is_read=True)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'All notifications marked as read'})

    return redirect('notifications_list')