from django.contrib import admin

from .models import Bank, Account, BankStatement, Transaction


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ("name", "mapping_version", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "bank", "account_type", "last4", "is_active", "updated_at")
    list_filter = ("account_type", "is_active", "bank")
    search_fields = ("name", "user__username", "user__email", "bank__name", "last4")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("bank", "user")


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "account", "source_type", "uploaded_at", "row_count", "parsed_ok")
    list_filter = ("source_type", "parsed_ok", "account__bank")
    search_fields = ("account__name", "user__username", "user__email", "file_hash")
    readonly_fields = ("uploaded_at",)
    autocomplete_fields = ("account", "user")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_date", "account", "amount", "short_description", "statement")
    list_filter = ("account", "account__bank", "transaction_date")
    search_fields = ("description", "account__name", "user__email", "user__username")
    autocomplete_fields = ("account", "statement", "user")
    date_hierarchy = "transaction_date"

    def short_description(self, obj):
        return (obj.description[:60] + "…") if len(obj.description) > 60 else obj.description

    short_description.short_description = "Description"
