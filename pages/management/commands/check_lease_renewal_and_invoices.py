# FIXED CODE - Replace the declined renewals section (around lines 260-275 and 420-440)

# HTML VERSION (around line 260):
if declined_count > 0:
    # Correct grammar for singular vs plural
    tenant_word = "tenant" if declined_count == 1 else "tenants"
    tenant_verb = "has" if declined_count == 1 else "have"
    property_word = "property" if declined_count == 1 else "properties"
    property_verb = "will need a new tenant" if declined_count == 1 else "will need new tenants"
    
    if declined_count == 1:
        html_body += f"""<p><b><u>DECLINED RENEWALS - NEED NEW TENANT ({declined_count}):</u></b><br>
        This {tenant_word} has declined lease renewal. This {property_word} {property_verb}. Contact estate agents ASAP.</p><ul>"""
    else:
        html_body += f"""<p><b><u>DECLINED RENEWALS - NEED NEW TENANTS ({declined_count}):</u></b><br>
        These {tenant_word} {tenant_verb} declined lease renewals. These {property_word} {property_verb}. Contact estate agents ASAP.</p><ul>"""
    
    for declined in declined_renewals:
        html_body += f"<li><b>{declined['prop_name']} ({declined['prop_country']})</b> - Current Tenant: {declined['tenant_name']}<br>"
        html_body += f"(Lease ends: {declined['lease_end_date']} - {declined['message']})</li>"
    html_body += """</ul><br>"""

# TEXT VERSION (around line 420):
if declined_count > 0:
    # Correct grammar for singular vs plural
    tenant_word = "tenant" if declined_count == 1 else "tenants"
    tenant_verb = "has" if declined_count == 1 else "have"
    property_word = "property" if declined_count == 1 else "properties"
    property_verb = "will need a new tenant" if declined_count == 1 else "will need new tenants"
    
    if declined_count == 1:
        text_body += f"""DECLINED RENEWALS - NEED NEW TENANT ({declined_count}):
This {tenant_word} has declined lease renewal. This {property_word} {property_verb}. Contact estate agents ASAP."""
    else:
        text_body += f"""DECLINED RENEWALS - NEED NEW TENANTS ({declined_count}):
These {tenant_word} {tenant_verb} declined lease renewals. These {property_word} {property_verb}. Contact estate agents ASAP."""
    
    for declined in declined_renewals:
        text_body += f"\n • {declined['prop_name']} ({declined['prop_country']}) - Current Tenant: {declined['tenant_name']}"
        text_body += f"\n   (Lease ends: {declined['lease_end_date']} - {declined['message']})"
    text_body += f"\n\n"