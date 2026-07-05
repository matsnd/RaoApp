import pymysql
from decimal import Decimal
from collections import defaultdict
import json, math, datetime

DB = dict(host='localhost', user='rao_user', password='RaoPass2026!', database='rao_new', charset='utf8mb4')
conn = pymysql.connect(**DB)
cur = conn.cursor()

DAYS_PER_PERIOD = {'dziennie':1,'dzienna':1,'tygodniowo':7,'dwutygodniowo':14,'miesiecznie':30,'miesieczne':30,'godzinowo':1,'jednorazowo':1}

def lookup_value(rental_days, conds):
    if not conds or not rental_days or rental_days<=0: return Decimal('0.00')
    sc = sorted(conds, key=lambda c: c.get('period_count') or 0)
    max_pc_op2 = max((c.get('period_count') or 0 for c in sc if (c.get('rate2') or 0)>0), default=0)
    rate = Decimal('0.00')
    if rental_days > max_pc_op2:
        cand = [c for c in sc if (c.get('period_count') or 0) <= rental_days]
        if cand:
            c = cand[-1]; op2=Decimal(str(c.get('rate2') or 0)); op1=Decimal(str(c.get('rate1') or 0))
            rate = op2 if op2>0 else op1
    else:
        cand = [c for c in sc if (c.get('period_count') or 0) >= rental_days]
        if cand:
            c = cand[0]; op2=Decimal(str(c.get('rate2') or 0)); op1=Decimal(str(c.get('rate1') or 0))
            rate = op2 if op2>0 else op1
    if rate<=0: return Decimal('0.00')
    return rate*rental_days

def tiered_value(rental_days, billing_frequency, unit_price, quantity, conds):
    if not conds:
        if unit_price and quantity: return Decimal(str(unit_price))*int(quantity)
        return Decimal('0.00')
    days = rental_days or 0
    if days<=0: return Decimal('0.00')
    freq = billing_frequency or 'dziennie'
    dpp = DAYS_PER_PERIOD.get(freq,1)
    total_periods = math.ceil(days/dpp) if dpp>0 else 0
    min_periods = conds[0].get('minimum') or 0
    if total_periods<min_periods: total_periods=min_periods
    if total_periods<=0: return Decimal('0.00')
    total_value=Decimal('0.00'); remaining=total_periods
    for i,cond in enumerate(conds):
        if remaining<=0: break
        pc = cond.get('period_count') or remaining
        rate = Decimal(str(cond.get('rate1') or 0))
        if rate<=0: continue
        if i==0: pit=min(remaining,pc)
        else:
            prev_pc = conds[i-1].get('period_count') or 0
            ts = (pc or 999)-prev_pc
            pit = min(remaining,ts)
        total_value += rate*pit
        remaining -= pit
    if remaining>0:
        for cond in reversed(conds):
            rate = Decimal(str(cond.get('rate1') or 0))
            if rate>0:
                total_value += rate*remaining; break
    return total_value*int(quantity or 1)

def fetch_positions(df, dt, service_filter=None, contractor_id=None, city=None, exclude_archival=True):
    sql = ("SELECT cp.id, cp.article_id, cp.contract_id, cp.rental_days, cp.billing_frequency, "
           "cp.unit_price, cp.quantity, a.name, a.internal_number, a.is_service, "
           "c.number, c.contractor_name, c.contractor_id, c.date_from, c.date_to, "
           "a.category_main, a.category_sub1, a.category_sub2, a.category_sub3, "
           "c.city, c.contract_type, c.branch_id, a.is_archival, a.is_external "
           "FROM contract_positions cp JOIN contracts c ON c.id=cp.contract_id "
           "JOIN articles a ON a.id=cp.article_id "
           "WHERE c.date_from <= %s AND c.date_to >= %s")
    params = [dt, df]
    if service_filter is not None:
        sql += ' AND a.is_service = %s'; params.append(1 if service_filter else 0)
    if exclude_archival:
        sql += ' AND a.is_archival = 0 AND a.is_external = 0'
    if contractor_id is not None:
        sql += ' AND c.contractor_id = %s'; params.append(contractor_id)
    if city is not None:
        sql += ' AND LOWER(c.city) = LOWER(%s)'; params.append(city)
    cur.execute(sql, params)
    rows = cur.fetchall()
    if not rows: return []
    pos_ids = [r[0] for r in rows]
    fmt = ','.join(['%s']*len(pos_ids))
    cur.execute(f'SELECT position_id, rate1, rate2, period_count, minimum, rate_type_id FROM position_conditions WHERE position_id IN ({fmt}) ORDER BY position_id, period_count', pos_ids)
    conds_by = defaultdict(list)
    for r in cur.fetchall():
        conds_by[r[0]].append({'rate1':r[1],'rate2':r[2],'period_count':r[3],'minimum':r[4],'rate_type_id':r[5]})
    cur.execute(f'SELECT position_id, SUM(cost_client) FROM contract_settlements WHERE position_id IN ({fmt}) AND cost_client IS NOT NULL GROUP BY position_id', pos_ids)
    sett_by = {r[0]: Decimal(str(r[1])) for r in cur.fetchall() if r[1] is not None}
    out=[]
    for r in rows:
        pid=r[0]; conds=conds_by.get(pid,[])
        rev_actual = sett_by.get(pid)
        rev_lookup = lookup_value(r[3], conds)
        rev_tiered = tiered_value(r[3], r[4], r[5], r[6], conds)
        if rev_actual is not None:
            rev=rev_actual; src='actual'
        elif rev_lookup>0:
            rev=rev_lookup; src='estimate_lookup'
        else:
            rev=rev_tiered; src='estimate_tiered'
        if r[13] is None or r[14] is None:
            c_from=df; c_to=dt
        else:
            c_from = r[13] if r[13]>=df else df
            c_to = r[14] if r[14]<=dt else dt
        clamped = max((c_to-c_from).days+1,0)
        out.append({'position_id':pid,'article_id':r[1],'contract_id':r[2],'rental_days':r[3] or 0,
            'article_name':r[7],'internal_number':r[8],'is_service':bool(r[9]),
            'contract_number':r[10],'contractor_name':r[11],'contractor_id':r[12],
            'date_from':r[13],'date_to':r[14],'clamped_days':clamped,
            'category_main':r[15],'category_sub1':r[16],'category_sub2':r[17],'category_sub3':r[18],
            'city':r[19],'contract_type':r[20] or 'S','branch_id':r[21],
            'revenue':rev,'revenue_source':src})
    return out

def summarize(positions):
    total_rev = sum((p['revenue'] for p in positions), Decimal('0'))
    total_days = sum(p['clamped_days'] for p in positions)
    contracts = set(p['contract_id'] for p in positions)
    return {'total_revenue': float(total_rev), 'total_rented_days': total_days,
            'contracts_count': len(contracts), 'positions_count': len(positions)}

scenarios = [
    ('1. Baseline month (2026-07-01..07-05) ALL', dict(df=datetime.date(2026,7,1), dt=datetime.date(2026,7,5))),
    ('2. preset=today (2026-07-05)', dict(df=datetime.date(2026,7,5), dt=datetime.date(2026,7,5))),
    ('3. preset=week (2026-06-29..07-05)', dict(df=datetime.date(2026,6,29), dt=datetime.date(2026,7,5))),
    ('4. preset=month (2026-07-01..07-05)', dict(df=datetime.date(2026,7,1), dt=datetime.date(2026,7,5))),
    ('5. preset=quarter (2026-04-01..07-05)', dict(df=datetime.date(2026,4,1), dt=datetime.date(2026,7,5))),
    ('6. preset=year (2026-01-01..07-05)', dict(df=datetime.date(2026,1,1), dt=datetime.date(2026,7,5))),
    ('7. preset=all (no date filter)', dict(df=datetime.date(2000,1,1), dt=datetime.date(2100,1,1))),
    ('8. type=machine (baseline month)', dict(df=datetime.date(2026,7,1), dt=datetime.date(2026,7,5), service_filter=False)),
    ('9. type=service (baseline month)', dict(df=datetime.date(2026,7,1), dt=datetime.date(2026,7,5), service_filter=True)),
    ('10. contractor_id=14441 (baseline month)', dict(df=datetime.date(2026,7,1), dt=datetime.date(2026,7,5), contractor_id=14441)),
    ('11. city=Warszawa (baseline month)', dict(df=datetime.date(2026,7,1), dt=datetime.date(2026,7,5), city='Warszawa')),
    ('12. year + machine + contractor=14441', dict(df=datetime.date(2026,1,1), dt=datetime.date(2026,7,5), service_filter=False, contractor_id=14441)),
    ('13. month + service + city=Warszawa', dict(df=datetime.date(2026,7,1), dt=datetime.date(2026,7,5), service_filter=True, city='Warszawa')),
]

results = {}
print('=== SCENARIOS ===')
for name, kw in scenarios:
    pos = fetch_positions(**kw)
    s = summarize(pos)
    results[name] = s
    print(f'{name}: revenue={s["total_revenue"]:.2f} days={s["total_rented_days"]} contracts={s["contracts_count"]} positions={s["positions_count"]}')

print()
print('=== TOP 5 MACHINES by revenue (baseline month) ===')
base = fetch_positions(df=datetime.date(2026,7,1), dt=datetime.date(2026,7,5), service_filter=False)
m = defaultdict(lambda:{'name':'','internal':'','rev':Decimal('0'),'days':0,'contracts':set()})
for p in base:
    k=p['article_id']; m[k]['name']=p['article_name']; m[k]['internal']=p['internal_number']
    m[k]['rev']+=p['revenue']; m[k]['days']+=p['clamped_days']; m[k]['contracts'].add(p['contract_id'])
top_m = sorted(m.items(), key=lambda x:x[1]['rev'], reverse=True)[:5]
top_machines=[]
for k,v in top_m:
    row={'article_id':k,'article_name':v['name'],'internal_number':v['internal'],'revenue':float(v['rev']),'rented_days':v['days'],'contracts_count':len(v['contracts'])}
    top_machines.append(row); print(f'  {v["name"][:40]:40} | {v["internal"] or "-":10} | rev={float(v["rev"]):.2f} days={v["days"]} contracts={len(v["contracts"])}')

print()
print('=== TOP 5 CITIES by revenue (baseline month) ===')
base_all = fetch_positions(df=datetime.date(2026,7,1), dt=datetime.date(2026,7,5))
ci = defaultdict(lambda:{'rev':Decimal('0'),'rentals':0,'contracts':set()})
for p in base_all:
    city = p['city'] or '(brak)'
    ci[city]['rev']+=p['revenue']; ci[city]['rentals']+=1; ci[city]['contracts'].add(p['contract_id'])
top_c = sorted(ci.items(), key=lambda x:x[1]['rev'], reverse=True)[:5]
top_cities=[]
for k,v in top_c:
    row={'city':k,'rentals_count':v['rentals'],'total_revenue':float(v['rev']),'contracts_count':len(v['contracts'])}
    top_cities.append(row); print(f'  {k:30} | rentals={v["rentals"]} rev={float(v["rev"]):.2f} contracts={len(v["contracts"])}')

print()
print('=== TOP 5 CATEGORIES by revenue (baseline month) ===')
cat = defaultdict(lambda:{'rev':Decimal('0'),'count':0,'contracts':set()})
for p in base_all:
    cn = p['category_main'] or '(bez kategorii)'
    cat[cn]['rev']+=p['revenue']; cat[cn]['count']+=1; cat[cn]['contracts'].add(p['contract_id'])
top_cat = sorted(cat.items(), key=lambda x:x[1]['rev'], reverse=True)[:5]
top_categories=[]
for k,v in top_cat:
    row={'category_main':k,'revenue':float(v['rev']),'count':v['count'],'contracts_count':len(v['contracts'])}
    top_categories.append(row); print(f'  {k:30} | count={v["count"]} rev={float(v["rev"]):.2f} contracts={len(v["contracts"])}')

print()
print('=== SERVICES (additional fees) with revenue (baseline month) ===')
svc_pos = [p for p in base_all if p['is_service']]
svc_agg = defaultdict(lambda:{'rev':Decimal('0'),'count':0})
for p in svc_pos:
    svc_agg[p['article_name']]['rev']+=p['revenue']; svc_agg[p['article_name']]['count']+=1
cur.execute("SELECT csf.name, COALESCE(SUM(s.cost_client),0) AS rev, COUNT(DISTINCT csf.id) AS cnt "
            "FROM contract_service_fees csf JOIN contracts c ON c.id=csf.contract_id "
            "LEFT JOIN contract_settlements s ON s.service_fee_id=csf.id AND s.cost_client IS NOT NULL "
            "WHERE c.date_from<=%s AND c.date_to>=%s AND csf.is_active=1 "
            "GROUP BY csf.name ORDER BY rev DESC",
            (datetime.date(2026,7,5), datetime.date(2026,7,1)))
fees = cur.fetchall()
services_list=[]
for nm,rev,cnt in fees:
    if rev is None: rev=0
    services_list.append({'service_name':nm,'total_revenue':float(rev),'count':cnt,'kind':'fee'})
    print(f'  fee: {nm[:40]:40} | rev={float(rev):.2f} count={cnt}')
for nm,v in svc_agg.items():
    services_list.append({'service_name':nm,'total_revenue':float(v["rev"]),'count':v["count"],'kind':'position'})
    print(f'  pos: {nm[:40]:40} | rev={float(v["rev"]):.2f} count={v["count"]}')

out = {'scenarios':results,'top_machines':top_machines,'top_cities':top_cities,'top_categories':top_categories,'services':services_list}
with open(r'c:\projects\repos\RaoApp_new\.devin\audit_db_truth.json','w',encoding='utf-8') as f:
    json.dump(out,f,indent=2,ensure_ascii=False,default=str)
print()
print('Saved JSON to .devin/audit_db_truth.json')
conn.close()
