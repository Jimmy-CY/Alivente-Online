"""
crs.urls — URL routing for the CRS module.
"""
from django.urls import path

from crs.views import main, config, fi, submission

app_name = "crs"

urlpatterns = [
    # Landing
    path("", main.index, name="index"),

    # Country Configurations
    path("countries/",                 config.country_list,   name="country_list"),
    path("countries/add/",             config.country_add,    name="country_add"),
    path("countries/<int:pk>/edit/",   config.country_edit,   name="country_edit"),
    path("countries/<int:pk>/delete/", config.country_delete, name="country_delete"),

    # Reporting Financial Institutions
    path("fis/",                 fi.fi_list,   name="fi_list"),
    path("fis/add/",             fi.fi_add,    name="fi_add"),
    path("fis/<int:pk>/edit/",   fi.fi_edit,   name="fi_edit"),
    path("fis/<int:pk>/delete/", fi.fi_delete, name="fi_delete"),

    # Submissions
    path("submissions/",                        submission.submission_list,            name="submission_list"),
    path("submissions/start/",                  submission.submission_start,           name="submission_start"),
    path("submissions/<int:pk>/",               submission.submission_detail,          name="submission_detail"),
    path("submissions/<int:pk>/save/",          submission.submission_save,            name="submission_save"),
    path("submissions/<int:pk>/fix-cell/",      submission.submission_fix_cell,        name="submission_fix_cell"),
    path("submissions/<int:pk>/upload-excel/",  submission.submission_upload_excel,    name="submission_upload_excel"),
    path("submissions/<int:pk>/remove-excel/",  submission.submission_remove_excel,    name="submission_remove_excel"),
    path("submissions/<int:pk>/excel/",         submission.submission_excel_download,  name="submission_excel_download"),
    path("submissions/<int:pk>/generate-xml/",  submission.submission_generate_xml,    name="submission_generate_xml"),
    path("submissions/<int:pk>/xml-files/download-all/",            submission.submission_xml_files_download_all,  name="submission_xml_files_download_all"),
    path("submissions/<int:pk>/xml-files/<int:xml_file_id>/view/",  submission.submission_xml_file_view,           name="submission_xml_file_view"),
    path("submissions/<int:pk>/xml-files/<int:xml_file_id>/",       submission.submission_xml_file_download,       name="submission_xml_file_download"),
    path("submissions/<int:pk>/close/",                             submission.submission_close,                   name="submission_close"),    
    path("submissions/<int:pk>/mark-submitted/",     submission.submission_mark_submitted,     name="submission_mark_submitted"),
    path("submissions/<int:pk>/mark-acknowledged/",  submission.submission_mark_acknowledged,  name="submission_mark_acknowledged"),
    path("submissions/<int:pk>/mark-rejected/",      submission.submission_mark_rejected,      name="submission_mark_rejected"),
    path("submissions/<int:pk>/delete/",             submission.submission_delete,             name="submission_delete"),

    ]