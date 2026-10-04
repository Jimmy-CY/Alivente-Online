# -*- coding: utf-8 -*-
"""The 23 phone rules base.html now provides, verbatim.

Generated from the file PD-2 is about to edit, so the patcher
matches text that really is there rather than text retyped.
"""
DROP = [
    '    /* Categories table — keep but tighten */\n    .categories-table {\n        font-size: 14px;\n    }',
    '    .categories-table th,\n    .categories-table td {\n        padding: 8px;\n    }',
    '    .categories-table th.count-col {\n        width: auto;\n    }',
    '    /* Assets table → card layout (Property Report section) */\n    .assets-table {\n        border: none;\n        background: transparent;\n    }',
    '    .assets-table thead {\n        display: none;\n    }',
    '    .assets-table,\n    .assets-table tbody,\n    .assets-table tr,\n    .assets-table td {\n        display: block;\n        width: 100%;\n    }',
    '    .assets-table tbody tr {\n        background: white;\n        border: 1px solid #dee2e6;\n        border-radius: 8px;\n        margin-bottom: 12px;\n        padding: 12px;\n        box-shadow: 0 2px 4px rgba(0,0,0,0.04);\n    }',
    '    .assets-table td {\n        border: none !important;\n        padding: 6px 0 !important;\n        text-align: left !important;\n        display: flex;\n        justify-content: space-between;\n        align-items: flex-start;\n        gap: 8px;\n        min-height: 24px;\n    }',
    '    .assets-table td::before {\n        content: attr(data-label);\n        font-weight: 600;\n        color: #495057;\n        font-size: 12px;\n        text-transform: uppercase;\n        letter-spacing: 0.3px;\n        flex-shrink: 0;\n        padding-top: 2px;\n    }',
    '    .assets-table td[data-label="Asset Name"] {\n        font-size: 15px;\n        font-weight: 600;\n        color: #2c3e50;\n        padding-bottom: 8px !important;\n        margin-bottom: 4px;\n        border-bottom: 1px solid var(--alv-line-soft) !important;\n        display: block;\n    }',
    '    .assets-table td[data-label="Asset Name"]::before {\n        display: none;\n    }',
    '    /* Generic shared mobile-card styling for the 5 box-type tables */\n    .issues-table,\n    .actual-expenses-table,\n    .expenses-table,\n    .revenue-table,\n    .invoices-table {\n        border: none;\n        background: transparent;\n        font-size: 14px;\n    }',
    '    .issues-table thead,\n    .actual-expenses-table thead,\n    .expenses-table thead,\n    .revenue-table thead,\n    .invoices-table thead {\n        display: none;\n    }',
    '    .issues-table,\n    .issues-table tbody,\n    .issues-table tr,\n    .issues-table td,\n    .actual-expenses-table,\n    .actual-expenses-table tbody,\n    .actual-expenses-table tr,\n    .actual-expenses-table td,\n    .expenses-table,\n    .expenses-table tbody,\n    .expenses-table tr,\n    .expenses-table td,\n    .revenue-table,\n    .revenue-table tbody,\n    .revenue-table tr,\n    .revenue-table td,\n    .invoices-table,\n    .invoices-table tbody,\n    .invoices-table tr,\n    .invoices-table td {\n        display: block;\n        width: 100%;\n    }',
    '    .issues-table tbody tr,\n    .actual-expenses-table tbody tr,\n    .expenses-table tbody tr,\n    .revenue-table tbody tr,\n    .invoices-table tbody tr {\n        background: white;\n        border: 1px solid #dee2e6;\n        border-radius: 8px;\n        margin-bottom: 12px;\n        padding: 12px;\n        box-shadow: 0 2px 4px rgba(0,0,0,0.04);\n    }',
    '    .issues-table td,\n    .actual-expenses-table td,\n    .expenses-table td,\n    .revenue-table td,\n    .invoices-table td {\n        border: none !important;\n        padding: 6px 0 !important;\n        text-align: left !important;\n        display: flex !important;\n        justify-content: space-between !important;\n        align-items: flex-start;\n        gap: 8px;\n        min-height: 24px;\n    }',
    '    .issues-table td::before,\n    .actual-expenses-table td::before,\n    .expenses-table td::before,\n    .revenue-table td::before,\n    .invoices-table td::before {\n        content: attr(data-label);\n        font-weight: 600;\n        color: #495057;\n        font-size: 12px;\n        text-transform: uppercase;\n        letter-spacing: 0.3px;\n        flex-shrink: 0;\n        padding-top: 2px;\n    }',
    '    /* Issues — table-specific tweaks */\n    .issues-table td[data-label="Issue"] {\n        font-size: 15px;\n        font-weight: 600;\n        color: #2c3e50;\n        padding-bottom: 8px !important;\n        margin-bottom: 4px;\n        border-bottom: 1px solid var(--alv-line-soft) !important;\n        display: block !important;\n    }',
    '    .issues-table td[data-label="Issue"]::before {\n        display: none;\n    }',
    '    /* Budgeted Expenses — Line Type prominent at top */\n    .expenses-table td[data-label="Expense Line Type"] {\n        font-size: 15px;\n        font-weight: 600;\n        color: #2c3e50;\n        padding-bottom: 8px !important;\n        margin-bottom: 4px;\n        border-bottom: 1px solid var(--alv-line-soft) !important;\n        display: block !important;\n    }',
    '    .expenses-table td[data-label="Expense Line Type"]::before {\n        display: none;\n    }',
    '    /* Revenues — Line Type prominent at top */\n    .revenue-table td[data-label="Revenue Line Type"] {\n        font-size: 15px;\n        font-weight: 600;\n        color: #2c3e50;\n        padding-bottom: 8px !important;\n        margin-bottom: 4px;\n        border-bottom: 1px solid var(--alv-line-soft) !important;\n        display: block !important;\n    }',
    '    .revenue-table td[data-label="Revenue Line Type"]::before {\n        display: none;\n    }',
]
