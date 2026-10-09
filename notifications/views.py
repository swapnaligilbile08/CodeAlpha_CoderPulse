from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def notification_list(request):
    items = list(request.user.notifications.select_related('actor', 'post')[:50])
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/list.html', {'items': items})
