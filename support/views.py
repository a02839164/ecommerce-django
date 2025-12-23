# support/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SupportTicket, SupportMessage
from .forms import SupportTicketForm
from django.contrib import messages
from django.db import transaction

@login_required
def support_center(request):

    form = SupportTicketForm(request.POST or None, request=request)
    tickets = SupportTicket.objects.filter(user=request.user).order_by("-created_at")  #先找出工單

    if request.method == "POST" and form.is_valid():
         
        with transaction.atomic():
            # 建立工單
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.email = request.user.email
            ticket.save()

            # 表單的message在這裡
            SupportMessage.objects.create(
                ticket=ticket,
                user=request.user,
                message=form.cleaned_data["message"],
                is_staff_reply=False,
            )

        messages.success(request, "Your support request has been submitted.")
        return redirect("support-center")
        
    context = {"tickets": tickets, "form": form,}

    return render(request, "support/support_center.html", context)


@login_required
def ticket_detail(request, ticket_id):

    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)

    messages = ticket.messages.order_by("created_at")

    context = {"ticket": ticket, "messages": messages,}

    return render(request, "support/ticket_detail.html", context)