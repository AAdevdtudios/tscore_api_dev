from django.forms.models import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from .forms import NotificationForm
from .models import Notifications
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from account.models import User
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import View
from django.views.generic.edit import CreateView
from django.views.generic import FormView


class CreateNotification(CreateView, PermissionRequiredMixin):
    template_name = "admin/send_notification.html"
    permission_required = "notifications.add_notifications"
    success_url = "/admin/account/user/"
    model = Notifications
    fields = ["title", "description", "content"]

    def get_queryset(self):
        data = self.request.GET.get("ids", None)
        if data:
            id_list = [int(id) for id in data.split(",")]
            queryset = User.objects.filter(id__in=id_list)
        else:
            queryset = User.objects.none()
        return queryset

    def form_valid(self, form):
        queryset = self.get_queryset()
        title = form.cleaned_data["title"]
        description = form.cleaned_data["description"]
        content = form.cleaned_data["content"]
        for user in queryset:
            Notifications.objects.create(
                user=user, title=title, description=description, content=content
            )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context["users"] = queryset
        admin_site_context = AdminSite().each_context(self.request)
        context.update(admin_site_context)
        context["opts"] = self.model._meta
        return context


class SendNotification(View):
    template_name = "admin/send_notification.html"

    def get_queryset(self):
        data = self.request.GET.get("ids", None)
        if data:
            id_list = [int(id) for id in data.split(",")]
            queryset = User.objects.filter(id__in=id_list)
        else:
            queryset = User.objects.none()
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        form = NotificationForm()
        context = {"users": queryset, "form": form}
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        form = NotificationForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            for user in queryset:
                notification = Notifications(
                    user=user, title=title, description=description
                )
                notification.save()


def custom_view(request):
    data = request.GET.get("ids", None)
    if data:
        id_list = [int(id) for id in data.split(",")]
        queryset = User.objects.filter(id__in=id_list)
    else:
        queryset = User.objects.none()

    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            for user in queryset:
                notification = Notifications(
                    user=user, title=title, description=description
                )
                notification.save()
        else:
            print(form.errors)
    else:
        form = NotificationForm()
    return render(
        request, "admin/send_notification.html", {"users": queryset, "form": form}
    )


def send_notification(modeladmin, request, queryset):
    if "apply" in request.POST:
        form = NotificationForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data["message"]
            for user in queryset:
                Notifications.objects.create(
                    user=user,
                    message=message,
                )
            modeladmin.message_user(request, "Notification sent to selected users.")
            return HttpResponseRedirect(request.get_full_path())

        return HttpResponseRedirect(request.get_full_path())

    form = NotificationForm(
        initial={"_selected_action": request.POST.getlist(admin.ACTION_CHECKBOX_NAME)}
    )
    return render(
        request,
        "admin/send_notification.html",
        {"users": queryset, "notification_form": form},
    )


send_notification.short_description = "Send notification to selected users"
