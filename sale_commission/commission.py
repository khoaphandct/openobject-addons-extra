from osv import fields,osv

class report_commission_month(osv.osv):
    _name = "report.commission.month"
    _description = "Commission of month"
    _auto = False
    _columns = {
        'name': fields.char('Sales Agent Name',size=64, readonly=True, select=True),
        'sono':fields.integer('Sales Order No', readonly=True, select=True),
        'invno':fields.integer('Invoice Number', readonly=True, select=True),
        'product_quantity':fields.integer('Product Quantity', readonly=True, select=True),
        'productname':fields.char('Product Name',size=256, readonly=True, select=True),
        'inv_total':fields.float('Invoice Amount', readonly=True, select=True),
        'in_date': fields.date('Invoice Date', readonly=True, select=True),
        'comrate': fields.float('Commission Rate (%)', readonly=True, select=True),
        'commission': fields.float('Commissions Amount', readonly=True, select=True),
#        'state': fields.char('Invoice State', size=64,readonly=True, select=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('open','Open'),
            ('paid','Paid'),
            ('cancel','Canceled')
        ],'State', select=True),
        'pdate': fields.date('Invoice Paid Date', readonly=True, select=True),

    }
   # _order = 'name,sono,state'

    def init(self, cr):
        print "In init of commision month ..";
        cr.execute(""" CREATE OR REPLACE VIEW report_commission_month AS( select * from (select ai.id as id,
sg.name as name,
so.name as sono,
ai.number as invno,
al.quantity as product_quantity,
al.name as productname,
(al.quantity * al.price_unit) as inv_total,
ai.date_invoice as in_date,
sg.commission_rate as comrate,
(al.quantity *al.price_unit * sg.commission_rate / 100) as commission,
ai.state,
'' as pdate
from
account_invoice ai,
sale_order so,
account_invoice_line al,
res_partner p,
sale_agent sg

where ai.origin=so.name
and ai.state in ('draft','open','proforma','cancel')
and al.invoice_id=ai.id and p.id=ai.partner_id
and sg.id=p.agent_id


)
 as a

UNION

(

select ai.id as id,
sg.name as name,
so.name as sono,
ai.number as invno,
al.quantity as product_quantity,
al.name as productname,
(al.quantity * al.price_unit) as inv_total,
ai.date_invoice as in_date,
sg.commission_rate as comrate,
(al.quantity *al.price_unit * sg.commission_rate / 100) as commission,
ai.state,
ar.name as pdate
from
account_invoice ai,
account_move am,
account_move_line aml,

account_move_reconcile ar,
sale_order so,
account_invoice_line al,
res_partner p,
sale_agent sg

where ai.origin=so.name
and ai.state in ('paid')
and al.invoice_id=ai.id and p.id=ai.partner_id
and sg.id=p.agent_id and ai.move_id=am.id
and aml.move_id=am.id
and ar.id = aml.reconcile_id

)) """)
report_commission_month()
