from calendar import monthrange, monthcalendar, month_name
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fractions import Fraction
from io import BytesIO
from urllib.parse import urlparse, parse_qs
import base64
import calendar
import decimal
import io
import json
import json as json_module
import logging
import os
import re
import smtplib
import string
import tempfile
import time
import uuid

import anthropic
import mysql.connector
import PyPDF2
from docx import Document
from docxtpl import DocxTemplate
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from spellchecker import SpellChecker
from xhtml2pdf import pisa

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm, UserChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage, FileSystemStorage
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.db import connection, models, transaction
from django.db.models import Count, F, Max, Min, OuterRef, Prefetch, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404, HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.static import serve

from .recipes import *
from .. import forms
from .. import recipe_ai
from ..forms import (
    ActExpenseForm,
    DetailsForm,
    ExpenseForm,
    ExpenseLineForm,
    ExpenseTypesForm,
    InvoicesForm,
    IssuesForm,
    PettyForm,
    PropForm,
    RevenueForm,
    RevenueLineForm,
    RevenueTypesForm,
    SupplierForm,
    TenantForm,
    ValuesForm,
)
from ..models import (
    act_expense,
    AssetCategory,
    AssetMaintenance,
    AssetSubcategory,
    AssetSupplier,
    CelebrationEvent,
    Contact,
    CookingCalculation,
    CustomProtein,
    EventNotification,
    expense,
    expense_line_types,
    expense_types,
    Ingredient,
    IngredientCategory,
    invoices,
    issues,
    issues_details,
    MealPlan,
    MealPlanDay,
    MealPlanRecipe,
    MeasurementUnit,
    NotificationRecipient,
    Passport,
    petty,
    PreparationMethod,
    Project,
    ProjectDocument,
    ProjectTask,
    prop_values,
    PropertyAsset,
    props,
    Recipe,
    RecipeCategory,
    RecipeCourse,
    RecipeFavourite,
    RecipeIngredient,
    RecipeIngredientText,
    RecipeInstruction,
    revenue,
    revenue_line_types,
    revenue_types,
    supplier,
    tenant,
    UnitConversion,
    UserProfile,
    VacancyPeriod,
)
from ..usda_client import get_food_details, search_foods, USDAClientError
from ..nutrition_calc import calculate_recipe_nutrition
from ..utils import convert_to_pdf, is_pdf, merge_pdfs, merge_pdfs_from_bytes, render_to_pdf
from pages.email_utils import get_email_recipients, format_email_recipients_for_header


logger = logging.getLogger(__name__)


### RECIPE MANAGEMENT ###


