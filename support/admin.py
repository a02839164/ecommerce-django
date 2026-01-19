from django.contrib import admin
from django import forms
from .models import SupportTicket, SupportMessage
from django.utils.safestring import mark_safe


# 建立一個後台表單，增加客服回覆的欄位
class SupportTicketAdminForm(forms.ModelForm):
    reply_message = forms.CharField(
        label="Reply",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6})
    )
    # 使用 fields="all" 完整保留預設 ModelForm 對 SupportTicket 欄位的處理能力
    class Meta:
        model = SupportTicket
        fields = "__all__"


# 對話紀錄
class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    can_delete = False
    show_change_link = False

    readonly_fields = ("formatted_message",)
    fields = ("formatted_message",)

    def formatted_message(self, obj):
        if obj.is_staff_reply:
            sender = f"Staff({obj.user.profile.name})" if obj.user else "Staff"
        else:
            sender = obj.user.username
        html = f"""
        <div style="white-space: pre-wrap; word-break: break-word; overflow-wrap: break-word;">
            <strong>{sender}</strong>：{obj.message}
        </div>
        """

        return mark_safe(html)
    
    formatted_message.short_description = "對話紀錄"

            # 禁止新增 inline item
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):

    list_display = ("id", "subject", "category", "user", "email","status", "priority", "created_at")
    list_filter = ("status", "priority", "category", "created_at")
    search_fields = ("subject", "email", "user__username")
    readonly_fields = ("user", "email", "subject", "category","created_at", "updated_at")
    fields = ("user", "email", "subject", "category","status", "priority","created_at", "updated_at","reply_message")

    inlines = [SupportMessageInline]

    # 禁止新增
    def has_add_permission(self, request):
        return False 
    
    # 禁止刪除
    def has_delete_permission(self, request, obj=None):
        return False  
    
    form = SupportTicketAdminForm
    # 在 Admin 儲存流程使用save_model 非save  ；插入自訂業務邏輯
    def save_model(self, request, obj, form, change):
        reply = form.cleaned_data.get("reply_message")

        if reply:
            SupportMessage.objects.create(
                ticket=obj,
                user=request.user,   # 哪個客服回覆
                message=reply,
                is_staff_reply=True,
            )

            #首次回覆改狀態
            if obj.status == "OPEN":
                obj.status = "PENDING"
            
        super().save_model(request, obj, form, change)
