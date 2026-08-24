from django.contrib import admin
from .models import (
    props, petty, tenant, invoices, issues, issues_details, supplier, 
    prop_values, revenue_types, revenue_line_types, revenue, expense_types, 
    expense_line_types, expense, act_expense,
    # Recipe Keeper Models
    MeasurementUnit, IngredientCategory, Ingredient,
    RecipeCourse, RecipeCategory, Recipe, CustomProtein,
    RecipeIngredient, RecipeInstruction,
    PhysicalInvoiceProfile, PhysicalInvoice, PhysicalInvoiceLine, PhysicalInvoiceNumbering,
    FinancialFigureHistory,
)

# Register your existing models
admin.site.register(props)
admin.site.register(petty)
admin.site.register(invoices)
admin.site.register(issues)
admin.site.register(issues_details)
admin.site.register(supplier)
admin.site.register(prop_values)
admin.site.register(revenue_types)
admin.site.register(revenue_line_types)
admin.site.register(revenue)
admin.site.register(expense_types)
admin.site.register(expense_line_types)
admin.site.register(expense)
admin.site.register(act_expense)


##### RECIPE KEEPER ADMIN CONFIGURATION #####

# ===== MEASUREMENT UNITS =====
@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbreviation', 'unit_type', 'created_date']
    list_filter = ['unit_type']
    search_fields = ['name', 'abbreviation']
    ordering = ['unit_type', 'name']


# ===== INGREDIENT CATEGORY =====
@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_date']
    search_fields = ['name']
    ordering = ['name']


# ===== INGREDIENTS =====
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'default_unit', 'created_date']
    list_filter = ['category']
    search_fields = ['name']
    ordering = ['name']
    autocomplete_fields = ['category', 'default_unit']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'default_unit')
        }),
        ('Additional Details', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


# ===== RECIPE COURSE =====
@admin.register(RecipeCourse)
class RecipeCourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_order', 'created_date']
    ordering = ['display_order', 'name']


# ===== RECIPE CATEGORY =====
@admin.register(RecipeCategory)
class RecipeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_date']
    search_fields = ['name']
    ordering = ['name']


# ===== CUSTOM PROTEIN =====
@admin.register(CustomProtein)
class CustomProteinAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_date']
    search_fields = ['name']
    ordering = ['name']


# ===== RECIPE INGREDIENT INLINE =====
class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ['ingredient', 'unit']
    fields = ['ingredient_order', 'ingredient', 'amount', 'unit', 'preparation_note', 'ingredient_group']
    ordering = ['ingredient_order']


# ===== RECIPE INSTRUCTION INLINE =====
class RecipeInstructionInline(admin.TabularInline):
    model = RecipeInstruction
    extra = 1
    fields = ['step_number', 'instruction_text', 'instruction_group', 'time_estimate', 'step_image']
    ordering = ['step_number']


# ===== RECIPE =====
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        'recipe_name', 
        'get_courses', 
        'get_categories', 
        'get_proteins',
        'servings',
        'get_total_time_display',
        'difficulty_level',
        'is_vegetarian',
        'created_date'
    ]
    list_filter = [
        'difficulty_level', 
        'is_vegetarian',
        'created_date'
    ]
    search_fields = ['recipe_name', 'recipe_description']
    ordering = ['-created_date']
    inlines = [RecipeIngredientInline, RecipeInstructionInline]
    filter_horizontal = ['courses', 'categories', 'proteins']  # Makes M2M easier to manage in admin
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('recipe_name', 'recipe_description', 'recipe_image')
        }),
        ('Classification', {
            'fields': ('courses', 'categories', 'difficulty_level')
        }),
        ('Timing', {
            'fields': ('prep_time', 'cook_time', 'total_time', 'servings')
        }),
        ('Dietary Information', {
            'fields': ('is_vegetarian', 'proteins')
        }),
        ('Metadata', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_date', 'updated_date']
    
    def get_courses(self, obj):
        """Display all courses as comma-separated list"""
        return ", ".join([course.name for course in obj.courses.all()])
    get_courses.short_description = 'Courses'
    
    def get_categories(self, obj):
        """Display all categories as comma-separated list"""
        return ", ".join([cat.name for cat in obj.categories.all()])
    get_categories.short_description = 'Categories'
    
    def get_proteins(self, obj):
        """Display all proteins as comma-separated list"""
        if obj.is_vegetarian:
            return "Vegetarian"
        proteins = obj.proteins.all()
        return ", ".join([protein.name for protein in proteins]) if proteins else "-"
    get_proteins.short_description = 'Proteins'
    
    def get_readonly_fields(self, request, obj=None):
        # Make total_time readonly if prep_time and cook_time are set
        if obj and obj.prep_time and obj.cook_time:
            return self.readonly_fields + ['total_time']
        return self.readonly_fields


# ===== STANDALONE RECIPE INGREDIENT ADMIN (for bulk editing) =====
@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = [
        'recipe', 
        'ingredient', 
        'amount', 
        'unit', 
        'preparation_note',
        'ingredient_group',
        'ingredient_order'
    ]
    list_filter = ['recipe', 'ingredient__category']
    search_fields = ['recipe__recipe_name', 'ingredient__name']
    autocomplete_fields = ['recipe', 'ingredient', 'unit']
    ordering = ['recipe', 'ingredient_order']


# ===== STANDALONE RECIPE INSTRUCTION ADMIN (for bulk editing) =====
@admin.register(RecipeInstruction)
class RecipeInstructionAdmin(admin.ModelAdmin):
    list_display = [
        'recipe',
        'step_number',
        'instruction_text_short',
        'instruction_group',
        'time_estimate'
    ]
    list_filter = ['recipe', 'instruction_group']
    search_fields = ['recipe__recipe_name', 'instruction_text']
    ordering = ['recipe', 'step_number']
    
    def instruction_text_short(self, obj):
        return obj.instruction_text[:100] + '...' if len(obj.instruction_text) > 100 else obj.instruction_text
    instruction_text_short.short_description = 'Instruction'


class PhysicalInvoiceProfileInline(admin.StackedInline):
    model = PhysicalInvoiceProfile
    can_delete = True
    extra = 1
    max_num = 1
    verbose_name_plural = "Physical Invoice Profile"


@admin.register(tenant)
class TenantAdmin(admin.ModelAdmin):
    inlines = [PhysicalInvoiceProfileInline]
    list_display = [
        'tenant_name', 'prop', 'tenant_current',
        'tenant_physical_invoice_required', 'tenant_bill_levies',
    ]
    list_filter = [
        'tenant_current', 'tenant_physical_invoice_required', 'tenant_bill_levies',
    ]
    search_fields = ['tenant_name']


class PhysicalInvoiceLineInline(admin.TabularInline):
    model = PhysicalInvoiceLine
    extra = 0
    fields = ['sort_order', 'service', 'unit_of_measure', 'description', 'qty', 'unit_price', 'vatable', 'line_total']
    readonly_fields = ['line_total']


@admin.register(PhysicalInvoice)
class PhysicalInvoiceAdmin(admin.ModelAdmin):
    inlines = [PhysicalInvoiceLineInline]
    list_display = ['__str__', 'tenant', 'period_year', 'period_month', 'status', 'total', 'invoice_number', 'sent_at']
    list_filter = ['status', 'period_year', 'period_month']
    search_fields = ['tenant__tenant_name', 'invoice_number']
    readonly_fields = ['subtotal', 'vat', 'total', 'approved_at', 'approved_by', 'sent_at', 'created_at', 'updated_at']
    actions = ['action_approve', 'action_unapprove']

    def get_readonly_fields(self, request, obj=None):
        ro = list(self.readonly_fields)
        if obj and not obj.is_editable:
            ro += ['tenant', 'period_year', 'period_month', 'invoice_date', 'invoice_number', 'vat_rate', 'currency', 'status']
        return ro

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalc_totals()  # keep totals in step after inline line edits

    @admin.action(description="Approve selected (draft only)")
    def action_approve(self, request, queryset):
        done = sum(1 for pi in queryset if pi.status == PhysicalInvoice.STATUS_DRAFT and (pi.approve(request.user) or True))
        self.message_user(request, f"Approved {done} draft invoice(s).")

    @admin.action(description="Un-approve selected (back to draft)")
    def action_unapprove(self, request, queryset):
        done = sum(1 for pi in queryset if pi.status == PhysicalInvoice.STATUS_APPROVED and (pi.unapprove() or True))
        self.message_user(request, f"Un-approved {done} invoice(s).")

@admin.register(PhysicalInvoiceNumbering)
class PhysicalInvoiceNumberingAdmin(admin.ModelAdmin):
    list_display = ["__str__", "prefix", "pad_width", "next_number", "updated_at"]

    def has_add_permission(self, request):
        return not PhysicalInvoiceNumbering.objects.exists()  # singleton

    def has_delete_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# Financial figure history
#
# READ-ONLY on purpose. This is an append-only record of what a budgeted figure
# was worth and from when; the finance screens write it as a side effect of
# saving. Editing a snapshot by hand produces a history that no longer matches
# the money, which is the one failure this table exists to prevent.
# ---------------------------------------------------------------------------

@admin.register(FinancialFigureHistory)
class FinancialFigureHistoryAdmin(admin.ModelAdmin):
    list_display = ('effective_date', 'prop', 'line_type', 'kind', 'amount',
                    'source', 'is_orphan', 'changed_by', 'changed_at')
    list_filter = ('kind', 'source', 'effective_date', 'prop')
    search_fields = ('line_type', 'prop__prop_name', 'source_pk')
    date_hierarchy = 'effective_date'
    ordering = ('-effective_date', '-changed_at')
    list_per_page = 50

    @admin.display(boolean=True, description='Live?')
    def is_orphan(self, obj):
        """False when the row this snapshot describes no longer exists.

        source_pk is a plain integer, not a foreign key, so nothing cascades
        when the source is deleted and an orphan looks exactly like live
        history. Ten dead Company Tax ids hold 30 of them; without this column
        the first person to open this screen would read them as current.

        Shown as a tick for live, a cross for orphaned - the wording is
        "Live?", so a cross means the source is gone.
        """
        return obj.source_pk in self._live_pks(obj.kind)

    def get_queryset(self, request):
        # A ModelAdmin is instantiated ONCE, at registration, and lives for the
        # life of the process - so anything cached on `self` never expires. The
        # live-pk cache is therefore emptied here, which Django calls once per
        # changelist request, rather than being allowed to go stale until the
        # next restart.
        self._pk_cache = {}
        return super().get_queryset(request).select_related('prop', 'changed_by')

    def _live_pks(self, kind):
        # Refilled per request by get_queryset above; one query per kind.
        cache = getattr(self, '_pk_cache', None)
        if cache is None:
            cache = self._pk_cache = {}
        if kind not in cache:
            from pages.models import expense, revenue, prop_values, act_expense
            model_pk = {
                'budget_expense': (expense, 'expense_id'),
                'revenue': (revenue, 'revenue_id'),
                'valuation': (prop_values, 'prop_values_id'),
                'expense_actual': (act_expense, 'act_expense_id'),
            }.get(kind)
            cache[kind] = (set(model_pk[0].objects.values_list(model_pk[1], flat=True))
                           if model_pk else set())
        return cache[kind]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
