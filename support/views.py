# support/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SupportTicket, SupportMessage
from .forms import SupportTicketForm
from django.contrib import messages


@login_required
def support_center(request):

    form = SupportTicketForm(request.POST or None)
    tickets = SupportTicket.objects.filter(user=request.user).order_by("-created_at")  #先找出工單

    if request.method == "POST" and form.is_valid():

        # 建立 ticket（沒有訊息內容）
        ticket = SupportTicket.objects.create(
            user=request.user,
            email=request.user.email,
            subject=form.cleaned_data["subject"],
            category=form.cleaned_data["category"],
            priority="NORMAL",
            status="OPEN",   
        )

        # 建立 meessage
        SupportMessage.objects.create(
            ticket=ticket,
            user=request.user,
            message=form.cleaned_data["message"],
            is_staff_reply=False,
        )
        messages.success(request, "Your support request has been submitted.")

        return redirect("support-center")
    
    context = {
        "tickets": tickets,
        "form": form,
    }

    return render(request, "support/support_center.html", context)


@login_required
def ticket_detail(request, ticket_id):

    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)

    messages = ticket.messages.order_by("created_at")

    context = {
        "ticket": ticket,
        "messages": messages,
    }

    return render(request, "support/ticket_detail.html", context)