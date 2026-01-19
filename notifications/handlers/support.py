from notifications.email_service import send_email_via_requests



#客服回覆信
def send_support_reply_email(ticket, reply_message):

    user = ticket.user
    subject = f"Support Ticket #{ticket.subject} - New Reply"
    
    context = {
        "user": user,
        "ticket": ticket,
        "reply_message": reply_message,
    }

    send_email_via_requests(
        subject=subject,
        to_email=user.email,
        template_base_name="support_reply",
        context=context
    )

