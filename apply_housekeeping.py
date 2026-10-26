# -*- coding: utf-8 -*-
"""apply_housekeeping.py - round HK-1, 26 Oct 2026.

RELEASE 19 HOUSEKEEPING - WHAT HE FOUND ON LIVE, AND TWO THINGS I DID.

    - The System tab is four cells again: three tiles and ONE reserved
      blank ("The tab should only be big enough for 4 buttons, not 6").
    - The Tenant Details Report names the first tenant ("We don't have
      the name of the first tenant") - T2-7 fixed the property page only.
    - No paper-plane on Manage Lease Agreements ("if a Lease Agreement is
      in here, it has already been signed"); Lease Signing help follows.
    - The background job runs ONCE A DAY at 06:00 UTC - his Railway
      screenshot - and the Help said every five minutes in seven places.
      His decision: keep the schedule, correct the words.
    - 48 controls on the Recipes and Passports screens asked for
      can_edit_personal, which migration 0065 deleted; they ask
      can_edit_recipes / can_edit_passports, as the views already do.
    - The push stops at once when the local database is missing a
      migration (Release 15 lost a 20-minute gate to that).

Stands on ES-8. Idempotent. Edits backed up to .bak_housekeep; nothing
ships new but this patcher and its suite.
"""
import os
import re
import sys

SUFFIX = '.bak_housekeep'
MARK = 'HK-1, 26 Oct 2026'
CHECK = False
CREATES = ()

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'templates', 'admin_apms.html'), [
        (r'''      <!-- Reserved for growth, AD-1 8 Oct 2026. Empty on purpose:
           it holds the second row so the panel keeps its height.
           aria-hidden because there is nothing here to announce. -->
      <div class="admin-btn admin-btn--reserved" aria-hidden="true"></div>
      <div class="admin-btn admin-btn--reserved" aria-hidden="true"></div>

''',
         r'''      <!-- Reserved for growth, AD-1 8 Oct 2026. Empty on purpose:
           it holds the second row so the panel keeps its height.
           aria-hidden because there is nothing here to announce.
           HK-1, 26 Oct 2026 - ONE now, not two: Signature and Stamp took a
           cell, and two blanks after three tiles made a third row. His
           words: "The tab should only be big enough for 4 buttons". -->
      <div class="admin-btn admin-btn--reserved" aria-hidden="true"></div>

'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_lease_agreement.html'), [
        (r'''                {% endif %}

                {# ES-3b, 24 Oct 2026 - SEND FOR SIGNATURE, from the   #}
                {# screen that already tells you who has a lease and   #}
                {# who has not. Always offered, with or without a      #}
                {# stored file: the send screen takes an upload too,   #}
                {# so a disabled twin here would refuse something that #}
                {# works.                                              #}
                {#                                                     #}
                {# BEFORE delete AND BEFORE upload, which the          #}
                {# instrument decided: send and upload are both        #}
                {# ADVANCE, delete is DESTROY, and send after the pair #}
                {# would read 0-4-3 on every row that has a lease.     #}
                {# ES-8, 25 Oct 2026 - LEASE SIGNING IS SUPERUSER ONLY, #}
                {# his decision; the greyed twin keeps the row's shape. #}
                {% if user.is_superuser %}
                    <a href="{% url 'lease_signing_create' %}?tenant={{ tenant.tenant_id }}"
                       class="icon-action-btn icon-send" role="button"
                       title="Start e-signing">
                        <i class="fas fa-paper-plane"></i>
                    </a>
                {% else %}
                    <span class="icon-action-btn icon-disabled" title="E-signing is for superusers">
                        <i class="fas fa-paper-plane"></i>
                    </span>
                {% endif %}

                {% if perms.auth.can_edit_tenants %}
''',
         r'''                {% endif %}

                {# HK-1, 26 Oct 2026 - NO SEND HERE ANY MORE, his decision: a  #}
                {# lease on this page is already signed, so the paper-plane   #}
                {# ES-3b put on every row offered something nobody needed.    #}
                {# E-signing starts from Lease Signing > Start e-signing.     #}

                {% if perms.auth.can_edit_tenants %}
'''),
        (r'''
        <!-- Mobile-only action bar (hidden on desktop) -->
        {# ES-3b - cols-3, because there are three now. base sizes  #}
        {# the bar from this class and a bar that said two would     #}
        {# draw the third at the wrong width.                        #}
        <td class="mobile-action-bar cols-3">
            {% if tenant.tenant_lease_agreement %}
                <button type="button" class="mobile-action-btn" onclick="viewDocument('{{ tenant.tenant_lease_agreement.url|escapejs }}', '{{ tenant.tenant_lease_agreement.name|escapejs }}', '{{ tenant.tenant_name|escapejs }}')">
''',
         r'''
        <!-- Mobile-only action bar (hidden on desktop) -->
        {# HK-1 - cols-2 again: Send went (see the desktop cell). #}
        <td class="mobile-action-bar cols-2">
            {% if tenant.tenant_lease_agreement %}
                <button type="button" class="mobile-action-btn" onclick="viewDocument('{{ tenant.tenant_lease_agreement.url|escapejs }}', '{{ tenant.tenant_lease_agreement.name|escapejs }}', '{{ tenant.tenant_name|escapejs }}')">
'''),
        (r'''                    <i class="fas fa-file-contract mobile-action-icon"></i>
                    <span class="mobile-action-label">View</span>
                </span>
            {% endif %}

            {% if user.is_superuser %}
                <a href="{% url 'lease_signing_create' %}?tenant={{ tenant.tenant_id }}"
                   class="mobile-action-btn" role="button">
                    <i class="fas fa-paper-plane mobile-action-icon icon-color-send"></i>
                    <span class="mobile-action-label">Send</span>
                </a>
            {% else %}
                <span class="mobile-action-btn mobile-action-disabled">
                    <i class="fas fa-paper-plane mobile-action-icon"></i>
                    <span class="mobile-action-label">Send</span>
                </span>
            {% endif %}
''',
         r'''                    <i class="fas fa-file-contract mobile-action-icon"></i>
                    <span class="mobile-action-label">View</span>
                </span>
            {% endif %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_report.html'), [
        (r'''                    <div class="detail-group">
                        <h4 class="section-title">Tenant Information</h4>
                        <div class="detail-row">
                            <span class="detail-label">Type:</span>
''',
         r'''                    <div class="detail-group">
                        <h4 class="section-title">Tenant Information</h4>
                        {# HK-1, 26 Oct 2026 - THE FIRST TENANT'S OWN NAME, as #}
                        {# T2-7 gave the property page on 25 October and this  #}
                        {# report missed. His words on Live: "We don't have   #}
                        {# the name of the first tenant." The heading is the  #}
                        {# tenancy ("A & B"); this row is the person whose    #}
                        {# number and email sit beside it - tenant_name, not  #}
                        {# tenant_display_name.                               #}
                        <div class="detail-row">
                            <span class="detail-label">Name:</span>
                            <span class="detail-value">{{ tenant.tenant_name }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Type:</span>
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <div class="alert" style="background:#e7f5f8; border-left:4px solid #0e7c8b;">
      <i class="fas fa-robot"></i> <strong>There is no Generate Invoices card any more &mdash; and nothing to press.</strong>
      <p class="mb-1 mt-2">Rent invoices for collection are created by a background job that runs <strong>every five minutes</strong>, all month. It always dates them the <strong>1st of the current month</strong> and skips any tenant who already has one, so it is <em>self-healing</em>: add a tenant on the 15th and their invoice appears within five minutes, correctly dated the 1st.</p>
      <p class="mb-0">The button that used to sit here duplicated that job, and did it worse &mdash; it created invoices without an amount, which the job always sets. It was removed on 25 Aug 2026, having never created an invoice that survives on Live.</p>
    </div>
''',
         r'''    <div class="alert" style="background:#e7f5f8; border-left:4px solid #0e7c8b;">
      <i class="fas fa-robot"></i> <strong>There is no Generate Invoices card any more &mdash; and nothing to press.</strong>
      <p class="mb-1 mt-2">Rent invoices for collection are created by a background job that runs <strong>once a day, each morning at about 08:00 Cyprus time</strong> (06:00 UTC), all month. It always dates them the <strong>1st of the current month</strong> and skips any tenant who already has one, so it is <em>self-healing</em>: add a tenant on the 15th and their invoice appears the next morning, correctly dated the 1st.</p>
      <!-- HK-1, 26 Oct 2026 - ONCE A DAY, not on a five-minute cycle: that is what the Railway cron service actually runs (his screenshot). It cannot run more often, because each run also sends the daily digest emails. -->
      <p class="mb-0">The button that used to sit here duplicated that job, and did it worse &mdash; it created invoices without an amount, which the job always sets. It was removed on 25 Aug 2026, having never created an invoice that survives on Live.</p>
    </div>
'''),
        (r'''    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-lightbulb"></i> Best Practices</h6>
    <ul>
      <li><strong>You do not need to check invoices on the 2nd</strong> &mdash; the job that creates them runs every five minutes and skips tenants who already have one, so a run cannot stay missed. If an invoice is absent, the cause is upstream: the tenant is not current, or their property is not Active.</li>
      <li><strong>Use Generate Lease Agreement for consistency</strong> &mdash; the template-based wizard ensures every lease has the same structure, language and required fields. Manually drafted leases drift over time.</li>
      <li><strong>Keep Title Deeds and Lease Agreements up to date</strong> &mdash; these are the legal anchors of every property and tenancy. Upload as soon as you receive the signed document.</li>
''',
         r'''    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-lightbulb"></i> Best Practices</h6>
    <ul>
      <li><strong>You do not need to check invoices on the 2nd</strong> &mdash; the job that creates them runs every morning and skips tenants who already have one, so a missed run is made up the next morning. If an invoice is absent, the cause is upstream: the tenant is not current, or their property is not Active.</li>
      <li><strong>Use Generate Lease Agreement for consistency</strong> &mdash; the template-based wizard ensures every lease has the same structure, language and required fields. Manually drafted leases drift over time.</li>
      <li><strong>Keep Title Deeds and Lease Agreements up to date</strong> &mdash; these are the legal anchors of every property and tenancy. Upload as soon as you receive the signed document.</li>
'''),
        (r'''
    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-exclamation-triangle"></i> <strong>If an invoice is missing:</strong> there is no button to press &mdash; the job retries every five minutes on its own, so waiting is the first step. If it is still absent, the tenant is being skipped rather than the job failing: check that the tenant is marked <strong>current</strong> and that their property is <strong>Active</strong>, since the job only creates invoices for tenants who are both. A lease that has ended stops invoicing automatically, which is usually the answer.
    </div>
  </article>
''',
         r'''
    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-exclamation-triangle"></i> <strong>If an invoice is missing:</strong> there is no button to press &mdash; the job runs again every morning on its own, so waiting until the next morning is the first step. If it is still absent, the tenant is being skipped rather than the job failing: check that the tenant is marked <strong>current</strong> and that their property is <strong>Active</strong>, since the job only creates invoices for tenants who are both. A lease that has ended stops invoicing automatically, which is usually the answer.
    </div>
  </article>
'''),
        (r'''
    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-route"></i> How to get here</h6>
    <p>Administration <i class="fas fa-arrow-right"></i> Functional <i class="fas fa-arrow-right"></i> <strong>Manage Lease Signing</strong>. You can also start e-signing for one tenant from the paper-plane icon on <strong>Manage Lease Agreements</strong>.</p>

    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-shield-alt"></i> <strong>Superuser only:</strong> the register, the envelope pages, the signed leases and every action on them are for Superusers. Anybody else sees the tile and the paper-plane icon greyed out. Signing itself is different: whoever is <em>named</em> to sign &mdash; a tenant, or a member of staff signing for Alivente &mdash; signs from their emailed link.
    </div>

''',
         r'''
    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-route"></i> How to get here</h6>
    <p>Administration <i class="fas fa-arrow-right"></i> Functional <i class="fas fa-arrow-right"></i> <strong>Manage Lease Signing</strong>.</p>

    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-shield-alt"></i> <strong>Superuser only:</strong> the register, the envelope pages, the signed leases and every action on them are for Superusers. Anybody else sees the tile greyed out. Signing itself is different: whoever is <em>named</em> to sign &mdash; a tenant, or a member of staff signing for Alivente &mdash; signs from their emailed link.
    </div>

'''),
        (r'''  <article data-tab-slug="lsg-start" data-tab-name="Start E-signing" data-tab-icon="fa-play-circle">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-play-circle"></i> Starting an envelope</h6>
    <p>Press <strong>Start e-signing</strong> on the register (or the paper-plane on a tenant&rsquo;s row of Manage Lease Agreements, which picks the tenancy for you).</p>
    <ul style="line-height:1.8;">
      <li><strong>Tenant</strong> &mdash; the tenancy the lease is for. If it already has an envelope open you are warned: starting another does not cancel the first.</li>
''',
         r'''  <article data-tab-slug="lsg-start" data-tab-name="Start E-signing" data-tab-icon="fa-play-circle">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-play-circle"></i> Starting an envelope</h6>
    <p>Press <strong>Start e-signing</strong> on the register.</p>
    <ul style="line-height:1.8;">
      <li><strong>Tenant</strong> &mdash; the tenancy the lease is for. If it already has an envelope open you are warned: starting another does not cancel the first.</li>
'''),
        (r'''      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-bell"></i> <strong>Reminders</strong></h6>
        <p class="mb-0">On <strong>day 3</strong> and on <strong>the day before the closing day</strong> (day 3 and day 6 of the usual seven), to whoever has not signed &mdash; never to somebody who has. Each reminder carries a <strong>fresh link</strong>; the earlier one stops working.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #ffc107;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-calendar-times"></i> <strong>Expiry</strong></h6>
        <p class="mb-0">After the end of the closing day the envelope becomes <strong>Expired</strong> and its links show &ldquo;the signing period has ended&rdquo;. Every signature already given is <strong>kept</strong>.</p>
      </div>
    </div>
''',
         r'''      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-bell"></i> <strong>Reminders</strong></h6>
        <p class="mb-0">On <strong>day 3</strong> and on <strong>the day before the closing day</strong> (day 3 and day 6 of the usual seven), to whoever has not signed &mdash; never to somebody who has. They go out with the <strong>morning run, at about 08:00 Cyprus time</strong>. Each reminder carries a <strong>fresh link</strong>; the earlier one stops working.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #ffc107;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-calendar-times"></i> <strong>Expiry</strong></h6>
        <p class="mb-0">The link stops working at the end of the closing day, Cyprus time, and shows &ldquo;the signing period has ended&rdquo;. The register marks the envelope <strong>Expired</strong> the next morning (until then it says &ldquo;past its date&rdquo;). Every signature already given is <strong>kept</strong>.</p>
      </div>
    </div>
'''),
    ]),
    (os.path.join('pages', 'help_content', 'operational.html'), [
        (r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Tenant invoices &mdash; automatic</strong></h6>
        <p class="mb-0" style="font-size:13px;">A background job runs <strong>every five minutes</strong>. It does nothing for most of the month, then in the <strong>last five days</strong> it drafts an invoice for each flagged tenant for the <em>month ahead</em>. You review and approve; a second job numbers, e-mails and files them. Your only job is approving.</p>
      </div>
    </div>
''',
         r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Tenant invoices &mdash; automatic</strong></h6>
        <p class="mb-0" style="font-size:13px;">A background job runs <strong>once a day, each morning at about 08:00 Cyprus time</strong>. It does nothing for most of the month, then in the <strong>last five days</strong> it drafts an invoice for each flagged tenant for the <em>month ahead</em>. You review and approve; a second job numbers, e-mails and files them. Your only job is approving.</p>
      </div>
    </div>
'''),
        (r'''           data-tab-icon="fa-users">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-users"></i> The automatic monthly cycle</h6>
    <p>Tenant rent invoices are handled on a schedule, so you never draft them by hand. A background job runs <strong>every five minutes</strong>, all month; for most of the month it has nothing to do. The cycle:</p>

    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
''',
         r'''           data-tab-icon="fa-users">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-users"></i> The automatic monthly cycle</h6>
    <p>Tenant rent invoices are handled on a schedule, so you never draft them by hand. A background job runs <strong>once a day, each morning at about 08:00 Cyprus time</strong> (06:00 UTC), all month; for most of the month it has nothing to do. The cycle:</p>
    <!-- HK-1, 26 Oct 2026 - ONCE A DAY, not on a five-minute cycle: what the Railway cron service actually runs. Each run also sends the daily digests, so it cannot run more often. -->

    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
'''),
        (r'''
    <div class="alert alert-light" style="border-left:4px solid #6c757d;">
      <i class="fas fa-redo"></i> <strong>Running every five minutes creates nothing twice.</strong> A draft is keyed on the tenant and the month, so the job finds the existing one and leaves it alone &mdash; including any edits you have made to it.
    </div>

''',
         r'''
    <div class="alert alert-light" style="border-left:4px solid #6c757d;">
      <i class="fas fa-redo"></i> <strong>Running every day creates nothing twice.</strong> A draft is keyed on the tenant and the month, so the job finds the existing one and leaves it alone &mdash; including any edits you have made to it.
    </div>

'''),
        (r'''
    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
      <i class="fas fa-trash"></i> <strong>Deleting a tenant draft:</strong> a deleted draft comes straight back &mdash; the job runs again within five minutes and re-creates it, and will keep doing so until the month turns. Deleting is therefore not how you stop an invoice. <strong>Leave it unapproved instead:</strong> nothing unapproved is ever sent, and on the 1st it is simply passed over.
    </div>
  </article>
''',
         r'''
    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
      <i class="fas fa-trash"></i> <strong>Deleting a tenant draft:</strong> a deleted draft comes back &mdash; the job runs again the next morning and re-creates it, and will keep doing so until the month turns. Deleting is therefore not how you stop an invoice. <strong>Leave it unapproved instead:</strong> nothing unapproved is ever sent, and on the 1st it is simply passed over.
    </div>
  </article>
'''),
    ]),
    (os.path.join('pages', 'management', 'commands', 'lease_signing_tick.py'), [
        (r'''
WHAT HAPPENS TO AN ENVELOPE WHILE NOBODY IS LOOKING AT IT. Two jobs,
run from check_lease_renewal_and_invoices every five minutes, beside
the physical-invoice send that already lives there.

1. EXPIRY IS WRITTEN HERE AND NOWHERE ELSE. ES-3a's register reads
''',
         r'''
WHAT HAPPENS TO AN ENVELOPE WHILE NOBODY IS LOOKING AT IT. Two jobs,
run from check_lease_renewal_and_invoices, beside the physical-invoice
send that already lives there.

HK-1, 26 Oct 2026 - ONCE A DAY, NOT EVERY FIVE MINUTES. This said five
minutes; the Railway cron service runs that job once a day at 06:00 UTC
(his screenshot), and it cannot run more often because each run also
sends the daily digests. So expiry is written, and reminders go, with
the morning run. The LINK closes on time regardless: the signing page
asks has_expired itself.

1. EXPIRY IS WRITTEN HERE AND NOWHERE ELSE. ES-3a's register reads
'''),
        (r'''                continue
            # MARKED BEFORE SENDING. A send that half-fails must not be
            # retried every five minutes until the mail server recovers
            # - one reminder per day it is due, and the trail records
            # any address it could not reach.
''',
         r'''                continue
            # MARKED BEFORE SENDING. A send that half-fails must not be
            # retried on every run until the mail server recovers
            # - one reminder per day it is due, and the trail records
            # any address it could not reach.
'''),
    ]),
    (os.path.join('pages', 'templates', 'categories_management.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}
{% block title %}Categories Management{% endblock %}
''',
         r'''{% extends 'base.html' %}
{# HK-1, 26 Oct 2026 - can_edit_recipes, not can_edit_personal: migration 0065 split Personal into Passports, Recipes, Celebrations and CRS and DELETED can_edit_personal, so these controls had been invisible to everybody but a superuser while the views (which check can_edit_recipes) would have allowed them. #}
{% load static %}
{% block title %}Categories Management{% endblock %}
'''),
        (r'''    <h2 class="page-title-h2">CATEGORIES MANAGEMENT</h2>
<div class="page-action-buttons">
        {% if perms.auth.can_edit_personal %}
        <button type="button" class="btn action-primary" data-toggle="modal" data-target="#addCategoryModal">
            <i class="fas fa-plus"></i> Add Category
''',
         r'''    <h2 class="page-title-h2">CATEGORIES MANAGEMENT</h2>
<div class="page-action-buttons">
        {% if perms.auth.can_edit_recipes %}
        <button type="button" class="btn action-primary" data-toggle="modal" data-target="#addCategoryModal">
            <i class="fas fa-plus"></i> Add Category
'''),
        (r'''                    <td data-label="Category Name">
                        <span class="category-name-display">{{ item.category.name }}</span>
                        {% if perms.auth.can_edit_personal %}
                        <input type="text" 
                               class="category-name-edit" 
''',
         r'''                    <td data-label="Category Name">
                        <span class="category-name-display">{{ item.category.name }}</span>
                        {% if perms.auth.can_edit_recipes %}
                        <input type="text" 
                               class="category-name-edit" 
'''),
        (r'''                    <td style="text-align: center;" class="cell-actions">
                        <div class="action-buttons">
                            {% if perms.auth.can_edit_personal %}
                            <!-- View Mode Actions -->
                            <div class="view-actions">
''',
         r'''                    <td style="text-align: center;" class="cell-actions">
                        <div class="action-buttons">
                            {% if perms.auth.can_edit_recipes %}
                            <!-- View Mode Actions -->
                            <div class="view-actions">
'''),
        (r'''            <i class="fas fa-tags"></i>
            <h3>No Categories Yet</h3>
            {% if perms.auth.can_edit_personal %}
            <p>Click "Add Category" to create your first category.</p>
            {% else %}
''',
         r'''            <i class="fas fa-tags"></i>
            <h3>No Categories Yet</h3>
            {% if perms.auth.can_edit_recipes %}
            <p>Click "Add Category" to create your first category.</p>
            {% else %}
'''),
        (r'''</div>

{% if perms.auth.can_edit_personal %}
<!-- Add Category Modal -->
<div class="modal fade" id="addCategoryModal" tabindex="-1" role="dialog">
''',
         r'''</div>

{% if perms.auth.can_edit_recipes %}
<!-- Add Category Modal -->
<div class="modal fade" id="addCategoryModal" tabindex="-1" role="dialog">
'''),
        (r'''

{% if perms.auth.can_edit_personal %}
// Enter edit mode
function enterEditMode(categoryId) {
''',
         r'''

{% if perms.auth.can_edit_recipes %}
// Enter edit mode
function enterEditMode(categoryId) {
'''),
    ]),
    (os.path.join('pages', 'templates', 'ingredient_base_units_management.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}
{% load custom_filters %}
''',
         r'''{% extends 'base.html' %}
{# HK-1, 26 Oct 2026 - can_edit_recipes, not can_edit_personal: migration 0065 split Personal into Passports, Recipes, Celebrations and CRS and DELETED can_edit_personal, so these controls had been invisible to everybody but a superuser while the views (which check can_edit_recipes) would have allowed them. #}
{% load static %}
{% load custom_filters %}
'''),
        (r'''                            <strong>{{ item.ingredient.name }}</strong>
                        </span>
                        {% if perms.auth.can_edit_personal %}
                        <input type="text" 
                               class="ingredient-name-edit ingredient-name-input" 
''',
         r'''                            <strong>{{ item.ingredient.name }}</strong>
                        </span>
                        {% if perms.auth.can_edit_recipes %}
                        <input type="text" 
                               class="ingredient-name-edit ingredient-name-input" 
'''),
        (r'''                            {% endif %}
                        </span>
                        {% if perms.auth.can_edit_personal %}
                        <select class="category-edit category-input" data-original-value="{% if item.ingredient.category %}{{ item.ingredient.category.ingredient_category_id }}{% endif %}"></select>
                        {% endif %}
''',
         r'''                            {% endif %}
                        </span>
                        {% if perms.auth.can_edit_recipes %}
                        <select class="category-edit category-input" data-original-value="{% if item.ingredient.category %}{{ item.ingredient.category.ingredient_category_id }}{% endif %}"></select>
                        {% endif %}
'''),
        (r'''                            {% endif %}
                        </span>
                        {% if perms.auth.can_edit_personal %}
                        <select class="unit-edit unit-select" data-original-value="{% if item.ingredient.default_unit %}{{ item.ingredient.default_unit.measurement_unit_id }}{% endif %}"></select>
                        {% endif %}
''',
         r'''                            {% endif %}
                        </span>
                        {% if perms.auth.can_edit_recipes %}
                        <select class="unit-edit unit-select" data-original-value="{% if item.ingredient.default_unit %}{{ item.ingredient.default_unit.measurement_unit_id }}{% endif %}"></select>
                        {% endif %}
'''),
        (r'''                                  data-tip-carbs="{{ item.nutrition_values.carbs|default_if_none:'' }}"
                                  data-tip-fat="{{ item.nutrition_values.fat|default_if_none:'' }}"
                                  {% if perms.auth.can_edit_personal %}onclick="openNutritionMappingModal({{ item.ingredient.ingredient_id }})" style="cursor: pointer;"{% endif %}>
                                <i class="fas fa-check-circle"></i> Mapped{% if item.nutrition_source == 'manual' %}<span class="nutrition-source-pill source-manual">M</span>{% endif %}
                            </span>
                        {% else %}
                            <span class="nutrition-badge nutrition-unmapped"
                                  data-tip-type="nutrition"
                                  data-tip-source="none"
                                  {% if perms.auth.can_edit_personal %}onclick="openNutritionMappingModal({{ item.ingredient.ingredient_id }})" style="cursor: pointer;"{% endif %}>
                                <i class="fas fa-exclamation-triangle"></i> Not mapped
                            </span>
''',
         r'''                                  data-tip-carbs="{{ item.nutrition_values.carbs|default_if_none:'' }}"
                                  data-tip-fat="{{ item.nutrition_values.fat|default_if_none:'' }}"
                                  {% if perms.auth.can_edit_recipes %}onclick="openNutritionMappingModal({{ item.ingredient.ingredient_id }})" style="cursor: pointer;"{% endif %}>
                                <i class="fas fa-check-circle"></i> Mapped{% if item.nutrition_source == 'manual' %}<span class="nutrition-source-pill source-manual">M</span>{% endif %}
                            </span>
                        {% else %}
                            <span class="nutrition-badge nutrition-unmapped"
                                  data-tip-type="nutrition"
                                  data-tip-source="none"
                                  {% if perms.auth.can_edit_recipes %}onclick="openNutritionMappingModal({{ item.ingredient.ingredient_id }})" style="cursor: pointer;"{% endif %}>
                                <i class="fas fa-exclamation-triangle"></i> Not mapped
                            </span>
'''),
        (r'''                    <td style="text-align: center;" class="cell-actions">
                        <div class="action-buttons">
                            {% if perms.auth.can_edit_personal %}
                            <!-- View Mode Actions -->
                            <div class="view-actions">
''',
         r'''                    <td style="text-align: center;" class="cell-actions">
                        <div class="action-buttons">
                            {% if perms.auth.can_edit_recipes %}
                            <!-- View Mode Actions -->
                            <div class="view-actions">
'''),
        (r'''

{% if perms.auth.can_edit_personal %}
<!-- ============================================================
     SINGLE-INGREDIENT NUTRITION MAPPING MODAL
''',
         r'''

{% if perms.auth.can_edit_recipes %}
<!-- ============================================================
     SINGLE-INGREDIENT NUTRITION MAPPING MODAL
'''),
        (r'''})();

{% if perms.auth.can_edit_personal %}
// ============================================================
// EXISTING ROW EDIT/DELETE FUNCTIONS
''',
         r'''})();

{% if perms.auth.can_edit_recipes %}
// ============================================================
// EXISTING ROW EDIT/DELETE FUNCTIONS
'''),
    ]),
    (os.path.join('pages', 'templates', 'measurement_units_management.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}
{% block title %}Measurement Units Management{% endblock %}
''',
         r'''{% extends 'base.html' %}
{# HK-1, 26 Oct 2026 - can_edit_recipes, not can_edit_personal: migration 0065 split Personal into Passports, Recipes, Celebrations and CRS and DELETED can_edit_personal, so these controls had been invisible to everybody but a superuser while the views (which check can_edit_recipes) would have allowed them. #}
{% load static %}
{% block title %}Measurement Units Management{% endblock %}
'''),
        (r'''    <h2 class="page-title-h2">MEASUREMENT UNITS MANAGEMENT</h2>
<div class="page-action-buttons">
        {% if perms.auth.can_edit_personal %}
        <button type="button" class="btn action-primary" data-toggle="modal" data-target="#addUnitModal">
            <i class="fas fa-plus"></i> Add Measurement Unit
''',
         r'''    <h2 class="page-title-h2">MEASUREMENT UNITS MANAGEMENT</h2>
<div class="page-action-buttons">
        {% if perms.auth.can_edit_recipes %}
        <button type="button" class="btn action-primary" data-toggle="modal" data-target="#addUnitModal">
            <i class="fas fa-plus"></i> Add Measurement Unit
'''),
        (r'''                            {% endif %}
                        </span>
                        {% if perms.auth.can_edit_personal %}
                        <div class="unit-name-edit">
                            <div class="edit-field-label">Singular</div>
''',
         r'''                            {% endif %}
                        </span>
                        {% if perms.auth.can_edit_recipes %}
                        <div class="unit-name-edit">
                            <div class="edit-field-label">Singular</div>
'''),
        (r'''                            {% endif %}
                        </span>
                        {% if perms.auth.can_edit_personal %}
                        <div class="unit-abbr-edit">
                            <div class="edit-field-label">Singular</div>
''',
         r'''                            {% endif %}
                        </span>
                        {% if perms.auth.can_edit_recipes %}
                        <div class="unit-abbr-edit">
                            <div class="edit-field-label">Singular</div>
'''),
        (r'''                            </span>
                        </span>
                        {% if perms.auth.can_edit_personal %}
                        <select class="unit-type-edit unit-input" data-original-value="{{ item.unit.unit_type }}">
                            {% for value, label in unit_types %}
''',
         r'''                            </span>
                        </span>
                        {% if perms.auth.can_edit_recipes %}
                        <select class="unit-type-edit unit-input" data-original-value="{{ item.unit.unit_type }}">
                            {% for value, label in unit_types %}
'''),
        (r'''                    <td style="text-align: center;" class="cell-actions">
                        <div class="action-buttons">
                            {% if perms.auth.can_edit_personal %}
                            <!-- View Mode Actions -->
                            <div class="view-actions">
''',
         r'''                    <td style="text-align: center;" class="cell-actions">
                        <div class="action-buttons">
                            {% if perms.auth.can_edit_recipes %}
                            <!-- View Mode Actions -->
                            <div class="view-actions">
'''),
        (r'''            <i class="fas fa-ruler"></i>
            <h3>No Measurement Units Yet</h3>
            {% if perms.auth.can_edit_personal %}
            <p>Click "Add Measurement Unit" to create your first unit.</p>
            {% else %}
''',
         r'''            <i class="fas fa-ruler"></i>
            <h3>No Measurement Units Yet</h3>
            {% if perms.auth.can_edit_recipes %}
            <p>Click "Add Measurement Unit" to create your first unit.</p>
            {% else %}
'''),
        (r'''</div>

{% if perms.auth.can_edit_personal %}
<!-- Add Unit Modal -->
<div class="modal fade" id="addUnitModal" tabindex="-1" role="dialog">
''',
         r'''</div>

{% if perms.auth.can_edit_recipes %}
<!-- Add Unit Modal -->
<div class="modal fade" id="addUnitModal" tabindex="-1" role="dialog">
'''),
        (r'''

{% if perms.auth.can_edit_personal %}
// Enter edit mode
function enterEditMode(unitId) {
''',
         r'''

{% if perms.auth.can_edit_recipes %}
// Enter edit mode
function enterEditMode(unitId) {
'''),
    ]),
    (os.path.join('pages', 'templates', 'recipe_management.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}
{% load humanize %}
''',
         r'''{% extends 'base.html' %}
{# HK-1, 26 Oct 2026 - can_edit_recipes, not can_edit_personal: migration 0065 split Personal into Passports, Recipes, Celebrations and CRS and DELETED can_edit_personal, so these controls had been invisible to everybody but a superuser while the views (which check can_edit_recipes) would have allowed them. #}
{% load static %}
{% load humanize %}
'''),
        (r'''<div class="page-action-buttons">
            <!-- Add Recipe Dropdown (PRIMARY) -->
        {% if perms.auth.can_edit_personal %}
        <div class="dropdown-btn-container">
            <button class="btn action-primary dropdown-btn">
''',
         r'''<div class="page-action-buttons">
            <!-- Add Recipe Dropdown (PRIMARY) -->
        {% if perms.auth.can_edit_recipes %}
        <div class="dropdown-btn-container">
            <button class="btn action-primary dropdown-btn">
'''),
        (r'''                    <i class="fas fa-eye"></i>
                </a>
                {% if perms.auth.can_edit_personal %}
                <a href="{% url 'edit_recipe' recipe.recipe_id %}" class="recipe-image-action-btn recipe-edit-btn" title="Edit Recipe">
                    <i class="fas fa-pencil-alt"></i>
''',
         r'''                    <i class="fas fa-eye"></i>
                </a>
                {% if perms.auth.can_edit_recipes %}
                <a href="{% url 'edit_recipe' recipe.recipe_id %}" class="recipe-image-action-btn recipe-edit-btn" title="Edit Recipe">
                    <i class="fas fa-pencil-alt"></i>
'''),
        (r'''                    <i class="fas fa-eye"></i>
                </a>
                {% if perms.auth.can_edit_personal %}
                <a href="{% url 'edit_recipe' recipe.recipe_id %}" class="recipe-edit-btn" title="Edit Recipe">
                    <i class="fas fa-pencil-alt"></i>
''',
         r'''                    <i class="fas fa-eye"></i>
                </a>
                {% if perms.auth.can_edit_recipes %}
                <a href="{% url 'edit_recipe' recipe.recipe_id %}" class="recipe-edit-btn" title="Edit Recipe">
                    <i class="fas fa-pencil-alt"></i>
'''),
        (r'''                <i class="fas fa-eye"></i>
            </a>
            {% if perms.auth.can_edit_personal %}
            <a href="{% url 'edit_recipe' recipe.recipe_id %}" class="recipe-list-action-btn recipe-edit-btn" title="Edit Recipe">
                <i class="fas fa-pencil-alt"></i>
''',
         r'''                <i class="fas fa-eye"></i>
            </a>
            {% if perms.auth.can_edit_recipes %}
            <a href="{% url 'edit_recipe' recipe.recipe_id %}" class="recipe-list-action-btn recipe-edit-btn" title="Edit Recipe">
                <i class="fas fa-pencil-alt"></i>
'''),
        (r'''{% endif %}

{% if perms.auth.can_edit_personal %}
<!-- Delete Confirmation Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1" role="dialog" aria-labelledby="deleteModalLabel" aria-hidden="true">
''',
         r'''{% endif %}

{% if perms.auth.can_edit_recipes %}
<!-- Delete Confirmation Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1" role="dialog" aria-labelledby="deleteModalLabel" aria-hidden="true">
'''),
        (r'''
// Permission flag for JS-generated cards
const USER_CAN_EDIT_PERSONAL = {% if perms.auth.can_edit_personal %}true{% else %}false{% endif %};
// AP-1, 20 Oct 2026 - the permission add_meal_entry really asks for.
const USER_CAN_EDIT_RECIPES = {% if perms.auth.can_edit_recipes %}true{% else %}false{% endif %};
''',
         r'''
// Permission flag for JS-generated cards
const USER_CAN_EDIT_PERSONAL = {% if perms.auth.can_edit_recipes %}true{% else %}false{% endif %};
// AP-1, 20 Oct 2026 - the permission add_meal_entry really asks for.
const USER_CAN_EDIT_RECIPES = {% if perms.auth.can_edit_recipes %}true{% else %}false{% endif %};
'''),
    ]),
    (os.path.join('pages', 'templates', 'unit_conversions_management.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}
{% load custom_filters %}
''',
         r'''{% extends 'base.html' %}
{# HK-1, 26 Oct 2026 - can_edit_recipes, not can_edit_personal: migration 0065 split Personal into Passports, Recipes, Celebrations and CRS and DELETED can_edit_personal, so these controls had been invisible to everybody but a superuser while the views (which check can_edit_recipes) would have allowed them. #}
{% load static %}
{% load custom_filters %}
'''),
        (r'''    <h2 class="page-title-h2">UNIT CONVERSIONS MANAGEMENT</h2>
<div class="page-action-buttons">
        {% if perms.auth.can_edit_personal %}
        <button onclick="openAddModal()" class="btn action-primary">
            <i class="fas fa-plus"></i> Add New Conversion
''',
         r'''    <h2 class="page-title-h2">UNIT CONVERSIONS MANAGEMENT</h2>
<div class="page-action-buttons">
        {% if perms.auth.can_edit_recipes %}
        <button onclick="openAddModal()" class="btn action-primary">
            <i class="fas fa-plus"></i> Add New Conversion
'''),
        (r'''        {% if missing_count > 0 %}
            <!-- Desktop secondary (hidden on mobile, accessed via More menu) -->
            {% if perms.auth.can_edit_personal %}
            <button onclick="openMissingConversionsModal()" class="btn action-secondary">
                <i class="fas fa-exclamation-triangle"></i> Missing Conversions ({{ missing_count }})
''',
         r'''        {% if missing_count > 0 %}
            <!-- Desktop secondary (hidden on mobile, accessed via More menu) -->
            {% if perms.auth.can_edit_recipes %}
            <button onclick="openMissingConversionsModal()" class="btn action-secondary">
                <i class="fas fa-exclamation-triangle"></i> Missing Conversions ({{ missing_count }})
'''),
        (r'''                </button>
                <div class="action-more-menu" id="actionMoreMenu" data-menu-panel role="menu" hidden>
                    {% if perms.auth.can_edit_personal %}
                    <button type="button" class="action-more-item" role="menuitem" onclick="openMissingConversionsModal()">
                        <i class="fas fa-exclamation-triangle"></i> Missing Conversions ({{ missing_count }})
''',
         r'''                </button>
                <div class="action-more-menu" id="actionMoreMenu" data-menu-panel role="menu" hidden>
                    {% if perms.auth.can_edit_recipes %}
                    <button type="button" class="action-more-item" role="menuitem" onclick="openMissingConversionsModal()">
                        <i class="fas fa-exclamation-triangle"></i> Missing Conversions ({{ missing_count }})
'''),
        (r'''                    <!-- Actions -->
                    <td class="actions-cell cell-actions" style="text-align: center;">
                        {% if perms.auth.can_edit_personal %}
                        <span class="row-actions"><button onclick="openEditModal({{ conversion.unit_conversion_id }}, '{{ conversion.from_unit.name|escapejs }}', '{{ conversion.to_unit.name|escapejs }}', '{{ conversion.multiplier|escapejs }}', {% if conversion.specific_ingredient %}{{ conversion.specific_ingredient.ingredient_id }}{% else %}null{% endif %}, '{% if conversion.specific_ingredient %}{{ conversion.specific_ingredient.name|escapejs }}{% endif %}')" 
                                class="icon-action-btn icon-edit" 
''',
         r'''                    <!-- Actions -->
                    <td class="actions-cell cell-actions" style="text-align: center;">
                        {% if perms.auth.can_edit_recipes %}
                        <span class="row-actions"><button onclick="openEditModal({{ conversion.unit_conversion_id }}, '{{ conversion.from_unit.name|escapejs }}', '{{ conversion.to_unit.name|escapejs }}', '{{ conversion.multiplier|escapejs }}', {% if conversion.specific_ingredient %}{{ conversion.specific_ingredient.ingredient_id }}{% else %}null{% endif %}, '{% if conversion.specific_ingredient %}{{ conversion.specific_ingredient.name|escapejs }}{% endif %}')" 
                                class="icon-action-btn icon-edit" 
'''),
        (r'''            <i class="fas fa-exchange-alt"></i>
            <h3>No Conversions Defined</h3>
            {% if perms.auth.can_edit_personal %}
            <p>Click "Add New Conversion" to create your first unit conversion.</p>
            {% else %}
''',
         r'''            <i class="fas fa-exchange-alt"></i>
            <h3>No Conversions Defined</h3>
            {% if perms.auth.can_edit_recipes %}
            <p>Click "Add New Conversion" to create your first unit conversion.</p>
            {% else %}
'''),
        (r'''</div>

{% if perms.auth.can_edit_personal %}
<!-- Add Conversion Modal -->
<div class="modal fade" id="addConversionModal" tabindex="-1">
''',
         r'''</div>

{% if perms.auth.can_edit_recipes %}
<!-- Add Conversion Modal -->
<div class="modal fade" id="addConversionModal" tabindex="-1">
'''),
        (r'''// ==================== END FILTER FUNCTIONALITY ====================

{% if perms.auth.can_edit_personal %}

// Preview conversion formula while typing
''',
         r'''// ==================== END FILTER FUNCTIONALITY ====================

{% if perms.auth.can_edit_recipes %}

// Preview conversion formula while typing
'''),
    ]),
    (os.path.join('pages', 'templates', 'view_recipe.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}
{% block title %}{{ recipe.recipe_name }}{% endblock %}
''',
         r'''{% extends 'base.html' %}
{# HK-1, 26 Oct 2026 - can_edit_recipes, not can_edit_personal: migration 0065 split Personal into Passports, Recipes, Celebrations and CRS and DELETED can_edit_personal, so these controls had been invisible to everybody but a superuser while the views (which check can_edit_recipes) would have allowed them. #}
{% load static %}
{% block title %}{{ recipe.recipe_name }}{% endblock %}
'''),
        (r'''    <div class="page-action-buttons">
        <!-- PRIMARY: Edit Recipe -->
        {% if perms.auth.can_edit_personal %}
        <a href="{% url 'edit_recipe' recipe.recipe_id %}" class="btn action-primary">
            <i class="fas fa-edit"></i> Edit Recipe
''',
         r'''    <div class="page-action-buttons">
        <!-- PRIMARY: Edit Recipe -->
        {% if perms.auth.can_edit_recipes %}
        <a href="{% url 'edit_recipe' recipe.recipe_id %}" class="btn action-primary">
            <i class="fas fa-edit"></i> Edit Recipe
'''),
        (r'''                            <i class="fas fa-envelope"></i> Email this list to:
                        </label>
                        <select id="emailSelect" class="form-control" {% if not perms.auth.can_edit_personal %}disabled{% endif %}>
                            <option value="">Select email address...</option>
                            <option value="demetrimanias@gmail.com">demetrimanias@gmail.com</option>
''',
         r'''                            <i class="fas fa-envelope"></i> Email this list to:
                        </label>
                        <select id="emailSelect" class="form-control" {% if not perms.auth.can_edit_recipes %}disabled{% endif %}>
                            <option value="">Select email address...</option>
                            <option value="demetrimanias@gmail.com">demetrimanias@gmail.com</option>
'''),
        (r'''                            <i class="fas fa-copy"></i> Copy
                        </button>
                        {% if perms.auth.can_edit_personal %}
                        <button class="btn action-secondary" onclick="sendEmail()">
                            <i class="fas fa-envelope"></i> Email
''',
         r'''                            <i class="fas fa-copy"></i> Copy
                        </button>
                        {% if perms.auth.can_edit_recipes %}
                        <button class="btn action-secondary" onclick="sendEmail()">
                            <i class="fas fa-envelope"></i> Email
'''),
        (r'''                    </h5>

                    {% if perms.auth.can_edit_personal %}
                    <div class="alert alert-warning">
                        <i class="fas fa-info-circle"></i>
''',
         r'''                    </h5>

                    {% if perms.auth.can_edit_recipes %}
                    <div class="alert alert-warning">
                        <i class="fas fa-info-circle"></i>
'''),
        (r'''
// Permission flag for JS
const USER_CAN_EDIT_PERSONAL = {% if perms.auth.can_edit_personal %}true{% else %}false{% endif %};

// ========== SHOPPING LIST STATE ==========
''',
         r'''
// Permission flag for JS
const USER_CAN_EDIT_PERSONAL = {% if perms.auth.can_edit_recipes %}true{% else %}false{% endif %};

// ========== SHOPPING LIST STATE ==========
'''),
        (r'''}

{% if perms.auth.can_edit_personal %}
function sendEmail() {
    const email = document.getElementById('emailSelect').value;
''',
         r'''}

{% if perms.auth.can_edit_recipes %}
function sendEmail() {
    const email = document.getElementById('emailSelect').value;
'''),
    ]),
    (os.path.join('pages', 'templates', 'passport_management.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}
{% load humanize %}
''',
         r'''{% extends 'base.html' %}
{# HK-1, 26 Oct 2026 - can_edit_passports, not can_edit_personal: migration 0065 split Personal into Passports, Recipes, Celebrations and CRS and DELETED can_edit_personal, so these controls had been invisible to everybody but a superuser while the views (which check can_edit_passports) would have allowed them. #}
{% load static %}
{% load humanize %}
'''),
        (r'''<!-- Action Buttons (Help + Back) — Back+1 standard -->
<div class="page-action-buttons">
    {% if perms.auth.can_edit_personal %}
    <button type="button" class="btn action-primary" onclick="addNewDocument()">
        <i class="fas fa-plus"></i> Add New Passport/ID
''',
         r'''<!-- Action Buttons (Help + Back) — Back+1 standard -->
<div class="page-action-buttons">
    {% if perms.auth.can_edit_passports %}
    <button type="button" class="btn action-primary" onclick="addNewDocument()">
        <i class="fas fa-plus"></i> Add New Passport/ID
'''),
        (r'''            {% if passport.document_file %}
                <button type="button" class="icon-action-btn icon-view" onclick="viewDocument('{{ passport.document_file.url|escapejs }}', '{{ passport.document_file.name|escapejs }}', '{{ passport.holder_name|escapejs }}')" title="View Document"><i class="fas fa-eye"></i></button>
                {% if perms.auth.can_edit_personal %}
                    <button type="button" class="icon-action-btn icon-edit" onclick="editDocument({{ passport.id }}, '{{ passport.holder_name|escapejs }}', '{{ passport.document_type|escapejs }}', '{{ passport.document_number|escapejs }}', '{{ passport.country_of_issue|escapejs }}', '{{ passport.date_of_issue|date:'Y-m-d'|escapejs }}', '{{ passport.expiry_date|date:'Y-m-d'|escapejs }}', '{{ passport.status|escapejs }}')" title="Edit"><i class="fas fa-pencil-alt"></i></button>
                    <button type="button" class="icon-action-btn icon-delete" onclick="deleteDocument({{ passport.id }}, '{{ passport.holder_name|escapejs }}')" title="Delete"><i class="fas fa-trash"></i></button>
''',
         r'''            {% if passport.document_file %}
                <button type="button" class="icon-action-btn icon-view" onclick="viewDocument('{{ passport.document_file.url|escapejs }}', '{{ passport.document_file.name|escapejs }}', '{{ passport.holder_name|escapejs }}')" title="View Document"><i class="fas fa-eye"></i></button>
                {% if perms.auth.can_edit_passports %}
                    <button type="button" class="icon-action-btn icon-edit" onclick="editDocument({{ passport.id }}, '{{ passport.holder_name|escapejs }}', '{{ passport.document_type|escapejs }}', '{{ passport.document_number|escapejs }}', '{{ passport.country_of_issue|escapejs }}', '{{ passport.date_of_issue|date:'Y-m-d'|escapejs }}', '{{ passport.expiry_date|date:'Y-m-d'|escapejs }}', '{{ passport.status|escapejs }}')" title="Edit"><i class="fas fa-pencil-alt"></i></button>
                    <button type="button" class="icon-action-btn icon-delete" onclick="deleteDocument({{ passport.id }}, '{{ passport.holder_name|escapejs }}')" title="Delete"><i class="fas fa-trash"></i></button>
'''),
        (r'''                {% endif %}
            {% else %}
                {% if perms.auth.can_edit_personal %}
                    <button type="button" class="icon-action-btn icon-upload" onclick="uploadDocument({{ passport.id }})" title="Upload Document"><i class="fas fa-upload"></i></button>
                    <button type="button" class="icon-action-btn icon-edit" onclick="editDocument({{ passport.id }}, '{{ passport.holder_name|escapejs }}', '{{ passport.document_type|escapejs }}', '{{ passport.document_number|escapejs }}', '{{ passport.country_of_issue|escapejs }}', '{{ passport.date_of_issue|date:'Y-m-d'|escapejs }}', '{{ passport.expiry_date|date:'Y-m-d'|escapejs }}', '{{ passport.status|escapejs }}')" title="Edit"><i class="fas fa-pencil-alt"></i></button>
''',
         r'''                {% endif %}
            {% else %}
                {% if perms.auth.can_edit_passports %}
                    <button type="button" class="icon-action-btn icon-upload" onclick="uploadDocument({{ passport.id }})" title="Upload Document"><i class="fas fa-upload"></i></button>
                    <button type="button" class="icon-action-btn icon-edit" onclick="editDocument({{ passport.id }}, '{{ passport.holder_name|escapejs }}', '{{ passport.document_type|escapejs }}', '{{ passport.document_number|escapejs }}', '{{ passport.country_of_issue|escapejs }}', '{{ passport.date_of_issue|date:'Y-m-d'|escapejs }}', '{{ passport.expiry_date|date:'Y-m-d'|escapejs }}', '{{ passport.status|escapejs }}')" title="Edit"><i class="fas fa-pencil-alt"></i></button>
'''),
        (r'''                </button>
            {% else %}
                {% if perms.auth.can_edit_personal %}
                    <button type="button" class="mobile-action-btn" onclick="uploadDocument({{ passport.id }})">
                        <i class="fas fa-upload mobile-action-icon icon-color-upload"></i>
''',
         r'''                </button>
            {% else %}
                {% if perms.auth.can_edit_passports %}
                    <button type="button" class="mobile-action-btn" onclick="uploadDocument({{ passport.id }})">
                        <i class="fas fa-upload mobile-action-icon icon-color-upload"></i>
'''),
        (r'''            {% endif %}

            {% if perms.auth.can_edit_personal %}
                <button type="button" class="mobile-action-btn" onclick="editDocument({{ passport.id }}, '{{ passport.holder_name|escapejs }}', '{{ passport.document_type|escapejs }}', '{{ passport.document_number|escapejs }}', '{{ passport.country_of_issue|escapejs }}', '{{ passport.date_of_issue|date:'Y-m-d'|escapejs }}', '{{ passport.expiry_date|date:'Y-m-d'|escapejs }}', '{{ passport.status|escapejs }}')">
                    <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
''',
         r'''            {% endif %}

            {% if perms.auth.can_edit_passports %}
                <button type="button" class="mobile-action-btn" onclick="editDocument({{ passport.id }}, '{{ passport.holder_name|escapejs }}', '{{ passport.document_type|escapejs }}', '{{ passport.document_number|escapejs }}', '{{ passport.country_of_issue|escapejs }}', '{{ passport.date_of_issue|date:'Y-m-d'|escapejs }}', '{{ passport.expiry_date|date:'Y-m-d'|escapejs }}', '{{ passport.status|escapejs }}')">
                    <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
'''),
        (r'''            {% endif %}

            {% if passport.document_file and perms.auth.can_edit_personal %}
                <button type="button" class="mobile-action-btn" onclick="deleteDocument({{ passport.id }}, '{{ passport.holder_name|escapejs }}')">
                    <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
''',
         r'''            {% endif %}

            {% if passport.document_file and perms.auth.can_edit_passports %}
                <button type="button" class="mobile-action-btn" onclick="deleteDocument({{ passport.id }}, '{{ passport.holder_name|escapejs }}')">
                    <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
'''),
        (r'''</div>

{% if perms.auth.can_edit_personal %}
<!-- Add/Edit Modal -->
<div class="modal fade" id="addEditModal" tabindex="-1" role="dialog" aria-hidden="true">
''',
         r'''</div>

{% if perms.auth.can_edit_passports %}
<!-- Add/Edit Modal -->
<div class="modal fade" id="addEditModal" tabindex="-1" role="dialog" aria-hidden="true">
'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 282, 122, 95   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 282, 120, 95   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
'''),
    ]),
    (os.path.join('test_table_lease_agreement.py'), [
        (r'''# a twin for the same reason the other two do: a slot that disappears
# on some rows walks the whole cluster sideways down the page.
check('  all three slots keep a disabled twin, so the cluster never '
      'shifts (%d)' % SRC.count('icon-disabled'),
      SRC.count('icon-disabled') == 3)
check('  and the document viewer keeps its three arguments',
      SRC.count('viewDocument(') >= 2
''',
         r'''# a twin for the same reason the other two do: a slot that disappears
# on some rows walks the whole cluster sideways down the page.
#
# HK-1, 26 Oct 2026 - TWO AGAIN. The paper-plane left this page, his
# decision ("if a Lease Agreement is in here, it has already been
# signed"), and its twin with it.
check('  both slots keep a disabled twin, so the cluster never '
      'shifts (%d)' % SRC.count('icon-disabled'),
      SRC.count('icon-disabled') == 2)
check('  and the document viewer keeps its three arguments',
      SRC.count('viewDocument(') >= 2
'''),
        (r'''# has to change a number here rather than discover a wrapped button
# on a phone.
check('the mobile bar declares three columns', 'cols-3' in SRC)


''',
         r'''# has to change a number here rather than discover a wrapped button
# on a phone.
#
# HK-1, 26 Oct 2026 - TWO, Send gone.
check('the mobile bar declares two columns',
      'cols-2' in SRC and 'cols-3' not in SRC)


'''),
        (r'''# ES-3b, 24 Oct 2026 - SEVEN. Send and Send-disabled. Still one
# button per slot on any given row: three drawn, four standing by.
check('  the row buttons are house icon buttons now (%d)'
      % SRC.count('icon-action-btn'), SRC.count('icon-action-btn') == 7)
check('  Upload carries the new tone', 'icon-upload' in SRC)
check('  and base.html defines it', '.icon-upload' in BASE_SRC)
''',
         r'''# ES-3b, 24 Oct 2026 - SEVEN. Send and Send-disabled. Still one
# button per slot on any given row: three drawn, four standing by.
#
# HK-1, 26 Oct 2026 - FIVE again: Send and Send-disabled went.
check('  the row buttons are house icon buttons now (%d)'
      % SRC.count('icon-action-btn'), SRC.count('icon-action-btn') == 5)
check('  Upload carries the new tone', 'icon-upload' in SRC)
check('  and base.html defines it', '.icon-upload' in BASE_SRC)
'''),
        (r'''_icons = re.findall(r'row-actions(.*?)</span>\s*</td>', SRC, re.S)
_glyphs = re.findall(r'<i class="fas (fa-[a-z-]+)"', _icons[0] if _icons else '')
check('  the row draws four possible glyphs across three slots (%s)'
      % ', '.join(sorted(set(_glyphs))),
      set(_glyphs) == {'fa-file-contract', 'fa-paper-plane',
                       'fa-trash', 'fa-upload'})

# ------------------------------------------------- the permission gates again
''',
         r'''_icons = re.findall(r'row-actions(.*?)</span>\s*</td>', SRC, re.S)
_glyphs = re.findall(r'<i class="fas (fa-[a-z-]+)"', _icons[0] if _icons else '')
#
# HK-1, 26 Oct 2026 - THREE GLYPHS ACROSS TWO SLOTS: the paper plane went.
check('  the row draws three possible glyphs across two slots (%s)'
      % ', '.join(sorted(set(_glyphs))),
      set(_glyphs) == {'fa-file-contract', 'fa-trash', 'fa-upload'})

# ------------------------------------------------- the permission gates again
'''),
        (r'''                  _off is not None and abs(_off) <= 1.5)
            ra = cs(pg, '.row-actions', ['display', 'gap'])
            check('  the three buttons sit inline with a gap',
                  ra['display'] == 'inline-flex' and ra['gap'] == '6px')
            # ES-3b, 24 Oct 2026 - THREE. Send for Signature is the
            # third slot, and this is the claim that proves the twins
            # work: whatever the row's permissions and whether or not
            # it holds a lease, three buttons are drawn.
            check('  and there are exactly THREE of them in the row',
                  pg.evaluate("()=>document.querySelectorAll("
                              "'tbody tr:first-child .row-actions "
                              ".icon-action-btn').length") == 3)
            check('  one actions cell per row, not four',
                  pg.evaluate("()=>document.querySelectorAll("
''',
         r'''                  _off is not None and abs(_off) <= 1.5)
            ra = cs(pg, '.row-actions', ['display', 'gap'])
            check('  the buttons sit inline with a gap',
                  ra['display'] == 'inline-flex' and ra['gap'] == '6px')
            # ES-3b, 24 Oct 2026 - THREE. Send for Signature is the
            # third slot, and this is the claim that proves the twins
            # work: whatever the row's permissions and whether or not
            # it holds a lease, three buttons are drawn.
            # HK-1, 26 Oct 2026 - TWO: Send left the row.
            check('  and there are exactly TWO of them in the row',
                  pg.evaluate("()=>document.querySelectorAll("
                              "'tbody tr:first-child .row-actions "
                              ".icon-action-btn').length") == 2)
            check('  one actions cell per row, not four',
                  pg.evaluate("()=>document.querySelectorAll("
'''),
        (r'''            # base.html's default happen to agree now, so the class
            # alone would pass even if the rule behind it had gone.
            check('mobile: the action bar is a 3-up grid (cols-3)',
                  len(cs(pg, '.mobile-action-bar',
                         ['grid-template-columns'])
                      ['grid-template-columns'].split()) == 3)
            check('mobile: the per-action cells step aside',
                  cs(pg, '.desktop-action-cell', ['display'])['display']
''',
         r'''            # base.html's default happen to agree now, so the class
            # alone would pass even if the rule behind it had gone.
            # HK-1, 26 Oct 2026 - 2-up, Send gone.
            check('mobile: the action bar is a 2-up grid (cols-2)',
                  len(cs(pg, '.mobile-action-bar',
                         ['grid-template-columns'])
                      ['grid-template-columns'].split()) == 2)
            check('mobile: the per-action cells step aside',
                  cs(pg, '.desktop-action-cell', ['display'])['display']
'''),
    ]),
    (os.path.join('test_help_physical_invoices.py'), [
        (r'''# ====================================== EVERY NUMBER AGAINST ITS REAL SOURCE
# --- the cadence
check('the help says every five minutes',
      'every five minutes' in OV and 'every five minutes' in TEN)
check('  and railway.json really schedules */5',
      '"*/5 * * * *"' in RAIL_SRC)
check('  on the command that drives this',
      'check_lease_renewals' in RAIL_SRC)
check('  which calls the prepare command',
      "call_command('prepare_physical_invoices')" in RUN_SRC)
''',
         r'''# ====================================== EVERY NUMBER AGAINST ITS REAL SOURCE
# --- the cadence
# HK-1, 26 Oct 2026 - ONCE A DAY. His Railway screenshot: the cron
# service runs cron-service/start.sh at 06:00 UTC daily. The */5 in
# railway.json is not what Railway runs - the schedule lives in the
# service settings, which no file in this tree can show - so the help is
# asked for the daily wording and start.sh for the command it runs.
check('the help says once a day, each morning',
      'once a day, each morning' in OV and 'once a day, each morning' in TEN
      and 'every five minutes' not in OV + TEN)
check('  and the cron service runs the command that drives this',
      'check_lease_renewals' in read(os.path.join(ROOT, 'cron-service',
                                                  'start.sh')))
check('  which calls the prepare command',
      "call_command('prepare_physical_invoices')" in RUN_SRC)
'''),
        (r'''      re.search(r'get_or_create\(\s*\n?\s*tenant=t, period_year=', PREP_SRC)
      is not None)
check('the help says a deleted draft comes back',
      'comes straight back' in TEN)
check('  and warns that leaving it unapproved is the real control',
      'Leave it unapproved instead' in TEN)
''',
         r'''      re.search(r'get_or_create\(\s*\n?\s*tenant=t, period_year=', PREP_SRC)
      is not None)
# HK-1, 26 Oct 2026 - "straight back" assumed a five-minute cycle; on the
# daily schedule it comes back the next morning, and the help says so.
check('the help says a deleted draft comes back',
      'a deleted draft comes back' in TEN and 'the next morning' in TEN)
check('  and warns that leaving it unapproved is the real control',
      'Leave it unapproved instead' in TEN)
'''),
    ]),
    (os.path.join('test_remove_legacy_reports.py'), [
        (r'''    check('  the Overview drops invoice generation from Functional',
          'lease agreements, title deeds and invoice generation' not in AH_SRC)
    check('  it explains the job runs every five minutes instead',
          'every five minutes' in AH_SRC and 'self-healing' in AH_SRC)
    check('  and points at the real places to look',
          'Financial Management &rarr; Invoices' in AH_SRC
''',
         r'''    check('  the Overview drops invoice generation from Functional',
          'lease agreements, title deeds and invoice generation' not in AH_SRC)
    # HK-1, 26 Oct 2026 - ONCE A DAY: the schedule Railway really runs.
    check('  it explains the job runs once a day instead',
          'once a day, each morning' in AH_SRC and 'self-healing' in AH_SRC)
    check('  and points at the real places to look',
          'Financial Management &rarr; Invoices' in AH_SRC
'''),
    ]),
    (os.path.join('test_send_lease.py'), [
        (r'''    mk = T.code_only_js(d.get(PAGE, ''))
    u = T.python_code_only(d[URLS], payloads=True)
    cell = row_cell(T.code_only_js(d[MANAGE]))
    return {
        'an envelope can be made at all':
''',
         r'''    mk = T.code_only_js(d.get(PAGE, ''))
    u = T.python_code_only(d[URLS], payloads=True)
    return {
        'an envelope can be made at all':
'''),
        (r'''            "{% url 'lease_signing_create' %}" in T.code_only_js(
                d[REGISTER]),
        'Manage Lease Agreements gains a Send row action':
            'icon-send' in cell,
        '  in house order, which alv_rowactions decides':
            # 'send' IN IT, AND THEN IN ORDER. in_order() alone was
            # true of the OLD cell too - view then delete is perfectly
            # ordered - so the control reported this round's own claim
            # as holding before it. A claim has to be about the thing
            # the round did.
            bool(cell) and 'send' in RA.verbs_of(cell)
            and RA.in_order(RA.verbs_of(cell)),
        '  and the phone bar says it holds three':
            'mobile-action-bar cols-3' in T.code_only_js(d[MANAGE]),
    }

''',
         r'''            "{% url 'lease_signing_create' %}" in T.code_only_js(
                d[REGISTER]),
        # HK-1, 26 Oct 2026 - THE SEND ROW ACTION ON MANAGE LEASE
        # AGREEMENTS IS GONE, his decision ("if a Lease Agreement is in
        # here, it has already been signed"). Its three claims went with
        # it; test_housekeeping.py asserts the absence. The way in is the
        # register button above.
    }

'''),
        (r'''# the planter ceiling of 21 October: print the measurement, assert the
# shape.
verbs = RA.verbs_of(row_cell(T.code_only_js(NOW[MANAGE])))
print('       row actions now: %s' % ' -> '.join(verbs))
ok('send' in verbs and verbs.index('send') < verbs.index('delete')
   if 'delete' in verbs else 'send' in verbs,
   '  and send comes before delete, because ADVANCE precedes DESTROY',
   verbs)


''',
         r'''# the planter ceiling of 21 October: print the measurement, assert the
# shape.
#
# HK-1, 26 Oct 2026 - send left the row, his decision; what remains must
# still be in house order.
verbs = RA.verbs_of(row_cell(T.code_only_js(NOW[MANAGE])))
print('       row actions now: %s' % ' -> '.join(verbs))
ok('send' not in verbs and RA.in_order(verbs),
   '  Manage Lease Agreements offers no send since HK-1, and what is left '
   'is in house order', verbs)


'''),
        (r'''head('6. THE WAYS IN')
# ==========================================================================
cell = row_cell(T.code_only_js(NOW[MANAGE]))
ok('{% url \'lease_signing_create\' %}?tenant=' in cell,
   'the row action carries the tenancy with it, so the screen opens on '
   'the right one')
bar_i = T.code_only_js(NOW[MANAGE]).find('mobile-action-bar')
bar = T.code_only_js(NOW[MANAGE])[bar_i:bar_i + 2400]
ok('fa-paper-plane' in bar and 'Send' in bar,
   'and the phone bar has it too, labelled')
ok('cols-3' in bar[:60],
   '  and says it holds three, because base sizes the bar from that '
   'class', bar[:60])

# THE ICON VOCABULARY IS NOT A FREE CHOICE. icon-send wears
# fa-paper-plane everywhere in this tree and test_icon_names fails any
# class that wears two glyphs.
i_s = cell.find('icon-send')
ok(i_s >= 0 and 'fa-paper-plane' in cell[i_s:i_s + 320],
   'the send action wears the house glyph for send, which the register '
   'already uses for Resend')


''',
         r'''head('6. THE WAYS IN')
# ==========================================================================
# HK-1, 26 Oct 2026 - ONE WAY IN NOW: Lease Signing > Start e-signing.
# The Manage Lease Agreements row action and its phone twin went, his
# decision; the phone bar says two again, because base sizes it from that.
ok('lease_signing_create' not in T.code_only_js(NOW[MANAGE]),
   'Manage Lease Agreements no longer starts e-signing (HK-1)')
bar_i = T.code_only_js(NOW[MANAGE]).find('mobile-action-bar')
bar = T.code_only_js(NOW[MANAGE])[bar_i:bar_i + 2400]
ok('fa-paper-plane' not in bar and 'cols-2' in bar[:60],
   '  nor its phone bar, which says it holds two', bar[:60])

# THE ICON VOCABULARY IS NOT A FREE CHOICE. icon-send wears
# fa-paper-plane everywhere in this tree and test_icon_names fails any
# class that wears two glyphs.
#
# HK-1, 26 Oct 2026 - asked of the register's Resend now, the one
# icon-send left in this flow.
reg = T.code_only_js(NOW[REGISTER])
i_s = reg.find('icon-send')
ok(i_s >= 0 and 'fa-paper-plane' in reg[i_s:i_s + 320],
   'the register Resend wears the house glyph for send')


'''),
    ]),
    (os.path.join('test_signing_finish.py'), [
        (r'''         and 'Lease signing is for superusers' in adm,
         '  the Administration tile greys out for anybody else'),
        ("{% if user.is_superuser %}\n                    <a href=\"{% url 'lease_signing_create' %}" in tla
         and 'E-signing is for superusers' in tla,
         '  and so does the paper-plane on Manage Lease Agreements'),
        ('Start e-signing' in lt and 'Send a lease for signature' not in lt,
         'the button reads Start e-signing'),
''',
         r'''         and 'Lease signing is for superusers' in adm,
         '  the Administration tile greys out for anybody else'),
        # HK-1, 26 Oct 2026 - or it is not there at all: the paper-plane
        # left Manage Lease Agreements, his decision. Either way nobody
        # but a superuser can start e-signing from that page.
        (("{% if user.is_superuser %}\n                    <a href=\"{% url 'lease_signing_create' %}" in tla
          and 'E-signing is for superusers' in tla)
         or ('lease_signing_create' not in tla
             and 'HK-1, 26 Oct 2026' in src[TLA_T]),
         '  and so does the paper-plane on Manage Lease Agreements - or, '
         'since HK-1, it is gone'),
        ('Start e-signing' in lt and 'Send a lease for signature' not in lt,
         'the button reads Start e-signing'),
'''),
        (r'''for cond, msg in claims(NOW):
    ok(cond, msg)
missing = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))
''',
         r'''for cond, msg in claims(NOW):
    ok(cond, msg)
# HK-1, 26 Oct 2026 took this round's block off Manage Lease Agreements,
# date and all; that file now carries HK-1's date instead.
missing = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]
           and not (p == TLA_T and 'HK-1, 26 Oct 2026' in NOW[p])]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('HK-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_housekeeping.py'" in read(pq):
        print('HK-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_signing_finish.py'" not in read(pq):
        refuse('ES-8 is not applied - this round registers after it.')

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- THE PUSH ASKS WHETHER THE LOCAL DATABASE IS MIGRATED
    q = out.get(pq, read(pq))
    q = swap(q, """Head 'Django system check'
""", """# HK-1, 26 Oct 2026 - IS THE LOCAL DATABASE MIGRATED? makemigrations above
# asks whether the MODELS need a new migration; this asks whether THIS
# DATABASE has every migration applied. Release 15 lost a twenty-minute
# gate to a missing local migration: dozens of suites failed against a
# table that was not there, and the cause was one command he had not run.
# migrate --check exits non-zero while anything is unapplied and changes
# nothing. Like makemigrations, its exit code alone is not trusted - a
# command that could not start is reported as that, not as a refusal.
Head 'Is your local database up to date?'
$miOut = & python manage.py migrate --check 2>&1
$miCode = $LASTEXITCODE
$miText = ($miOut | Out-String)
if ($miCode -eq 0) {
    Good 'every migration is applied to your local database'
} elseif ($miText -match 'Traceback|ImproperlyConfigured|OperationalError|Unknown command') {
    $miOut | ForEach-Object { Say ('  ' + $_) }
    Warn 'migrate --check could not run (settings or database) - check this by hand'
} else {
    $miOut | ForEach-Object { Say ('  ' + $_) }
    Bad 'your local database is missing a migration - the suites would fail against it.'
    Say  '        Run this, then push again:'
    Say  '            python manage.py migrate'
    if (-not $Force) { exit 1 }
}

Head 'Django system check'
""", '%s (the migration gate)' % PS1)

    # ---- REGISTRATION
    q = swap(q, """    'test_signing_finish.py'
)""", """    'test_signing_finish.py',
    # HK-1, 26 Oct 2026 - Release 19 housekeeping.
    'test_housekeeping.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'Push-PendingChanges.ps1'; Text = '& python manage.py migrate --check 2>&1'; What = 'HK-1: the push refuses to run its suites against a local database with a migration unapplied - without it, a forgotten migrate costs a twenty-minute gate of false failures' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_signing_finish.py',
]""", """    'test_signing_finish.py',
    # HK-1, 26 Oct 2026 - Release 19 housekeeping.
    'test_housekeeping.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_signfinish',
]""", """    '.bak_signfinish',
    # HK-1, 26 Oct 2026 - Release 19 housekeeping.
    '.bak_housekeep',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # HK-1, 26 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    tla = T.code_only(out[os.path.join(root, 'pages', 'templates',
                                       'tenant_lease_agreement.html')])
    if 'lease_signing_create' in tla:
        refuse('Manage Lease Agreements still starts e-signing.')
    for k, v in out.items():
        if k.endswith('.html') and 'perms.auth.can_edit_personal' in \
                T.code_only(v):
            refuse('%s still asks for can_edit_personal, which does not '
                   'exist.' % os.path.relpath(k, root))
    adm = out[os.path.join(root, 'pages', 'templates', 'admin_apms.html')]
    if adm.count('<div class="admin-btn admin-btn--reserved"') != 1:
        refuse('the System panel must keep exactly ONE reserved cell.')

    if CHECK:
        print('HK-1 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('HK-1 applied - System tab four cells; first tenant named on the '
          'report; no paper-plane; daily job described; permissions; '
          'migration gate.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
