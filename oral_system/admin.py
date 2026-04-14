from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from .models import SubProblem

@admin.register(SubProblem)
class SubProblemAdmin(admin.ModelAdmin):
    list_display = ['problem', 'solution_limit', 'filter_ref']
    # 讓後台可以直接搜尋題目代號來找設定
    search_fields = ['problem__code', 'problem__name']