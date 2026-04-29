{
    'name': 'Custom Quotation Template (Saudi Style)',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Custom quotation PDF',
    'description': 'Makes Odoo quotation  with Arabic/English header.',
    'depends': ['sale',"account","l10n_sa"],
    'data': [
        'views/report_saleorder.xml',
        'views/report_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}