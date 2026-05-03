from django.contrib import admin

from .models import Learner,SubUnit, Unit
admin.site.register(Learner)

# ─── Unit (optionnel, pour voir  les unités) ─
@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'level', 'order']
    list_filter = ['level']
    search_fields = ['title']


# ─── SubUnit ─────────────────────────────────────
@admin.register(SubUnit)
class SubUnitAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'unit', 'order']
    list_filter = ['unit__level', 'unit']
    search_fields = ['title', 'unit__title']
    ordering = ['unit__level', 'unit__order', 'order']