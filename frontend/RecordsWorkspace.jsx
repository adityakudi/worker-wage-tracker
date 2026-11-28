import {useEffect, useReducer, useRef, useState} from 'react';

export function useAction() {
  const lock = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  return {busy, error, clear: () => setError(''), async run(task) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError('');
    try {await task();}
    catch (failure) {setError(failure.message);}
    finally {lock.current = false; setBusy(false);}
  }};
}

function useRead(api, path, version) {
  const [value, setValue] = useState({data: null, error: '', loading: Boolean(path)});
  useEffect(() => {
    const controller = new AbortController();
    setValue({data: null, error: '', loading: Boolean(path)});
    if (path) {
      api(path, {signal: controller.signal}).then(data => {
        if (!controller.signal.aborted) setValue({data, error: '', loading: false});
      }).catch(error => {
        if (!controller.signal.aborted) setValue({data: null, error: error.message, loading: false});
      });
    }
    return () => controller.abort();
  }, [api, path, version]);
  return value;
}

function dateInIndia() {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts();
  const date = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return [date.year, date.month, date.day].join('-');
}

function money(value) {
  const paise = BigInt(value);
  const absolute = paise < 0n ? -paise : paise;
  const rupees = new Intl.NumberFormat('en-IN').format(absolute / 100n);
  return (paise < 0n ? '−' : '') + '₹' + rupees + '.' + String(absolute % 100n).padStart(2, '0');
}

function parseRupees(input, signed = false) {
  const value = String(input).trim();
  const pattern = signed ? /^-?\d{1,14}(\.\d{1,2})?$/ : /^\d{1,14}(\.\d{1,2})?$/;
  if (!pattern.test(value)) throw Error('Enter rupees with up to two decimal places / रुपये में अधिकतम दो दशमलव अंक दें।');
  const negative = value.startsWith('-');
  const [whole, fraction = ''] = value.replace(/^-/, '').split('.');
  const paise = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, '0'));
  if (paise > BigInt(Number.MAX_SAFE_INTEGER)) throw Error('Amount exceeds the supported form limit.');
  return Number(negative ? -paise : paise);
}

function post(api, path, body) {
  return api(path, {method: 'POST', ...(body === undefined ? {} : {body: JSON.stringify(body)})});
}

function Notice({state, t}) {
  if (state.error) return <p role="alert">{state.error}</p>;
  if (state.loading || state.busy) return <p role="status">{t('Loading…', 'लोड हो रहा है…')}</p>;
  return null;
}

function Form({onSave, button, t, children, idempotent = false}) {
  const status = useAction();
  const last = useRef({signature: '', key: ''});
  function submit(event) {
    event.preventDefault();
    const element = event.currentTarget;
    const fields = new FormData(element);
    status.run(async () => {
      let key;
      if (idempotent) {
        const signature = JSON.stringify([...fields]);
        if (last.current.signature !== signature) last.current = {signature, key: globalThis.crypto.randomUUID()};
        key = last.current.key;
      }
      await onSave(fields, key);
      last.current = {signature: '', key: ''};
      element.reset();
    });
  }
  return <form className="live-form" onSubmit={submit}>
    <Notice state={status} t={t}/>{children}
    <button disabled={status.busy}>{button}</button>
  </form>;
}

function postReason({field = 'reason', label, required = true, t}) {
  return <label>{label || t('Reason', 'कारण')}<textarea name={field} rows="2" maxLength="500" required={required}/></label>;
}

const names = {
  earning: ['Attendance', 'उपस्थिति'], advance: ['Advance', 'अग्रिम'], payment: ['Wage payment', 'मज़दूरी भुगतान'],
  adjustment: ['Adjustment', 'समायोजन'], reversal: ['Reversal', 'वापसी प्रविष्टि'],
  invited: ['Invited', 'आमंत्रित'], accepted: ['Accepted', 'स्वीकृत'],
  disputed: ['Dispute open', 'विवाद खुला है'], responded: ['Response ready', 'उत्तर तैयार है'],
  correction_proposed: ['Correction proposed', 'सुधार प्रस्तावित'], response_rejected: ['Response declined', 'उत्तर अस्वीकृत'],
  resolved: ['Resolved', 'हल हुआ'], posted: ['Posted', 'दर्ज'], reversed: ['Reversed', 'वापस लिया गया'],
  acknowledged: ['Reviewed', 'समीक्षा की गई'], receipt_confirmed: ['Receipt confirmed', 'प्राप्ति की पुष्टि'],
};

function label(t, key) {
  return names[key] ? t(...names[key]) : key;
}

function Pager({offset, limit, count, total, onChange, t}) {
  const more = total === undefined ? count === limit : offset + limit < total;
  return <nav className="live-actions" aria-label={t('Pagination', 'पृष्ठ बदलें')}>
    <button disabled={!offset} onClick={() => onChange(Math.max(0, offset - limit))}>{t('Previous', 'पिछला')}</button>
    <span>{offset ? offset + 1 : 1}–{offset + count}</span>
    <button disabled={!more} onClick={() => onChange(offset + limit)}>{t('Next', 'अगला')}</button>
  </nav>;
}

export function RecordsWorkspace({api, user, t}) {
  const owner = user.role === 'contractor';
  const [memberOffset, setMemberOffset] = useState(0);
  const [selected, select] = useState(null);
  const [version, refresh] = useReducer(n => n + 1, 0);
  const memberships = useRead(api, '/memberships?limit=20&offset=' + memberOffset, version);
  const action = useAction();

  async function invite(form) {
    await post(api, '/memberships', {worker_id: form.get('worker').trim()});
    setMemberOffset(0);
    refresh();
  }

  return <>
    <section className="live-panel">
      <h2>{owner ? t('Worker memberships', 'कामगार सदस्यताएँ') : t('Worker account', 'कामगार खाता')}</h2>
      <Notice state={memberships} t={t}/>
      <Notice state={action} t={t}/>
      {owner && <Form onSave={invite} button={t('Invite worker', 'कामगार को आमंत्रित करें')} t={t}>
        <label>{t('Worker ID', 'कामगार आईडी')}
          <input name="worker" required maxLength="36" placeholder={t('Ask the worker for their account ID', 'कामगार से उनकी खाता आईडी लें')}/>
        </label>
      </Form>}
      {memberships.data && (memberships.data.items.length ? <>
        <ul className="live-list">{memberships.data.items.map(member => <li key={member.id}>
          <strong>{owner ? member.worker_email : member.contractor_email}</strong>
          <span>{label(t, member.status)}</span>
          {member.status === 'accepted' && <button onClick={() => select(member)}>
            {t('Open worker record', 'कामगार का रिकॉर्ड खोलें')}
          </button>}
          {!owner && member.status === 'invited' && <button disabled={action.busy} onClick={() => action.run(async () => {
            await post(api, '/memberships/' + member.id + '/accept');
            select({...member, status: 'accepted'});
            refresh();
          })}>{t('Accept invitation', 'आमंत्रण स्वीकार करें')}</button>}
        </li>)}</ul>
        {(memberOffset > 0 || memberships.data.items.length === 20) && <Pager offset={memberOffset} limit={20}
          count={memberships.data.items.length} onChange={setMemberOffset} t={t}/>}
      </> : <p>{t('No memberships found.', 'कोई सदस्यता नहीं मिली।')}</p>)}
    </section>
    {selected && <MemberWorkspace key={selected.id} api={api} member={selected} owner={owner} t={t}/>}
  </>;
}

function MemberWorkspace({api, member, owner, t}) {
  const now = dateInIndia();
  const base = '/memberships/' + member.id;
  const [version, refresh] = useReducer(n => n + 1, 0);
  const [assignmentOffset, setAssignmentOffset] = useState(0);
  const [siteOffset, setSiteOffset] = useState(0);
  const [assignment, setAssignment] = useState('');
  const [assignmentQ, setAssignmentQ] = useState('');
  const [from, setFrom] = useState(now.slice(0, 7) + '-01');
  const [to, setTo] = useState(now);
  const [q, setQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const [entry, setEntry] = useState('');
  const [month, setMonth] = useState(now.slice(0, 7));
  const [paymentKind, setPaymentKind] = useState('advance');
  const action = useAction();
  const assignments = useRead(api, '/assignments?' + new URLSearchParams({
    membership_id: member.id, limit: 20, offset: assignmentOffset, q: assignmentQ,
  }), version);
  const sites = useRead(api, owner ? '/worksites?active=true&limit=20&offset=' + siteOffset : '', version);
  const wages = useRead(api, assignment ? '/assignments/' + assignment + '/wage-agreements?limit=20' : '', version);
  const [rateOffset, setRateOffset] = useState(0);
  const olderWages = useRead(api, assignment && rateOffset
    ? '/assignments/' + assignment + '/wage-agreements?limit=20&offset=' + rateOffset : '', version);
  const ratePage = rateOffset ? olderWages : wages;
  const records = useRead(api, base + '/ledger?' + new URLSearchParams({
    start: from, end: to, q, limit: 20, offset,
  }), version);

  async function download() {
    const csv = await api(base + '/statement.csv?' + new URLSearchParams({month}));
    const url = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'wages-' + month + '.csv';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <>
    <section className="live-panel">
      <h2>{t('Assignments and agreed rates', 'कार्य और तय मज़दूरी')}</h2>
      <p>{owner ? member.worker_email : member.contractor_email}</p>
      <Notice state={assignments} t={t}/>
      {owner && <Notice state={sites} t={t}/>}
      {owner && sites.data?.items.length > 0 && <>
        <Form t={t} button={t('Create assignment', 'कार्य सौंपें')} onSave={async form => {
          const result = await post(api, '/assignments', {
            membership_id: member.id, worksite_id: form.get('worksite'), start_date: form.get('start'),
            end_date: form.get('end') || null,
          });
          setRateOffset(0); setAssignment(result.id); refresh();
        }}>
          <label>{t('Worksite', 'कार्यस्थल')}<select aria-label={t('Worksite', 'कार्यस्थल')} name="worksite" required>
            {sites.data.items.map(site => <option key={site.id} value={site.id}>{site.name}</option>)}
          </select></label>
          <label>{t('Assignment start', 'कार्य शुरू होने की तारीख')}<input name="start" type="date" required defaultValue={now}/></label>
          <label>{t('Assignment end', 'कार्य समाप्ति की तारीख')}<input name="end" type="date"/></label>
        </Form>
        {(siteOffset > 0 || siteOffset + 20 < sites.data.total) && <Pager offset={siteOffset} limit={20}
          count={sites.data.items.length} total={sites.data.total} onChange={setSiteOffset} t={t}/>}
      </>}
      {owner && sites.data?.total === 0 && <p>{t('Create an active worksite to make an assignment.', 'कार्य सौंपने के लिए सक्रिय कार्यस्थल बनाएँ।')}</p>}
      <label>{t('Search assignments by worksite', 'कार्यस्थल से कार्य खोजें')}<input value={assignmentQ} maxLength="120"
        onChange={e => {setAssignmentQ(e.target.value); setAssignmentOffset(0);}}/></label>
      {assignments.data && (assignments.data.items.length ? <>
        <ul className="live-list">{assignments.data.items.map(item => <li key={item.id}>
          <button aria-pressed={assignment === item.id} onClick={() => {setAssignment(item.id); setRateOffset(0);}}>
            {item.worksite_name} · {item.start_date}
          </button>
          {item.end_date && <span>{t('Ends', 'समाप्त')} {item.end_date}</span>}
        </li>)}</ul>
        {(assignmentOffset > 0 || assignmentOffset + 20 < assignments.data.total) && <Pager offset={assignmentOffset} limit={20}
          count={assignments.data.items.length} total={assignments.data.total} onChange={setAssignmentOffset} t={t}/>}
      </> : <p>{t('No assignments found.', 'कोई कार्य नहीं मिला।')}</p>)}
      {assignment && <div key={assignment}>
        <h3>{t('Wage rates', 'मज़दूरी की दरें')}</h3>
        <Notice state={ratePage} t={t}/><Notice state={action} t={t}/>
        {owner && <Form t={t} button={t('Propose rate', 'दर प्रस्तावित करें')} onSave={async form => {
          await post(api, '/assignments/' + assignment + '/wage-agreements', {
            daily_rate_paise: parseRupees(form.get('rate')), effective_from: form.get('effective'),
          });
          refresh();
        }}>
          <label>{t('Daily rate (INR)', 'दैनिक मज़दूरी (रुपये)')}<input name="rate" inputMode="decimal" required/></label>
          <label>{t('Effective date', 'लागू होने की तारीख')}<input name="effective" type="date" required defaultValue={now}/></label>
        </Form>}
        {ratePage.data && (ratePage.data.items.length ? <>
          <ul className="live-list">{ratePage.data.items.map(rate => <li key={rate.id}>
            <strong>{money(rate.daily_rate_paise_text)} / {t('day', 'दिन')}</strong>
            <span>{rate.effective_from} · {rate.acknowledged_at ? t('Agreed', 'स्वीकृत') : t('Awaiting worker', 'कामगार की स्वीकृति बाकी')}</span>
            {!owner && !rate.acknowledged_at && <button disabled={action.busy} onClick={() => action.run(async () => {
              await post(api, '/wage-agreements/' + rate.id + '/acknowledge'); refresh();
            })}>{t('Acknowledge rate', 'दर स्वीकार करें')}</button>}
          </li>)}</ul>
          {(rateOffset > 0 || rateOffset + 20 < ratePage.data.total) && <Pager offset={rateOffset} limit={20}
            count={ratePage.data.items.length} total={ratePage.data.total} onChange={setRateOffset} t={t}/>}
        </> : <p>{t('No wage rates yet.', 'अभी कोई मज़दूरी दर नहीं है।')}</p>)}
        {owner && <Form t={t} idempotent button={t('Record attendance', 'उपस्थिति दर्ज करें')} onSave={async (form, request_id) => {
          await post(api, '/attendance', {assignment_id: assignment, work_date: form.get('day'),
            half_day_units: Number(form.get('units')), notes: form.get('notes'), request_id});
          setOffset(0); refresh();
        }}>
          <label>{t('Attendance date', 'उपस्थिति की तारीख')}<input name="day" type="date" defaultValue={now} max={now} required/></label>
          <label>{t('Attendance units', 'उपस्थिति')}<select aria-label={t('Attendance units', 'उपस्थिति')} name="units" defaultValue="2">
            <option value="0">{t('Absent', 'अनुपस्थित')}</option><option value="1">{t('Half day', 'आधा दिन')}</option>
            <option value="2">{t('Full day', 'पूरा दिन')}</option>
          </select></label>
          {postReason({field:'notes', label:t('Attendance note', 'उपस्थिति का नोट'), required:false, t})}
        </Form>}
      </div>}
    </section>

    {owner && <section className="live-panel">
      <h2>{t('Record a payment or adjustment', 'भुगतान या समायोजन दर्ज करें')}</h2>
      <Form t={t} idempotent button={t('Save financial entry', 'राशि दर्ज करें')} onSave={async (form, request_id) => {
        await post(api, base + '/ledger', {kind: form.get('kind'), effective_date: form.get('day'),
          amount_paise: parseRupees(form.get('amount'), paymentKind === 'adjustment'), notes: form.get('notes'), request_id});
        setOffset(0); refresh();
      }}>
        <label>{t('Entry type', 'प्रविष्टि का प्रकार')}<select aria-label={t('Entry type', 'प्रविष्टि का प्रकार')} name="kind"
          value={paymentKind} onChange={e => setPaymentKind(e.target.value)}>
          {['advance','payment','adjustment'].map(kind => <option key={kind} value={kind}>{label(t, kind)}</option>)}
        </select></label>
        <label>{t('Financial entry date', 'प्रविष्टि की तारीख')}<input name="day" type="date" required defaultValue={now} max={now}/></label>
        <label>{t('Amount (INR)', 'राशि (रुपये)')}<input name="amount" inputMode="decimal" required/></label>
        {postReason({field:'notes', required:paymentKind === 'adjustment', t})}
      </Form>
    </section>}

    <section className="live-panel">
      <h2>{t('Wage ledger', 'मज़दूरी बही')}</h2>
      <div className="live-filters">
        <label>{t('From', 'से')}<input aria-label={t('From', 'से')} type="date" value={from}
          onChange={e => {setFrom(e.target.value); setOffset(0);}}/></label>
        <label>{t('Through', 'तक')}<input type="date" value={to} onChange={e => {setTo(e.target.value); setOffset(0);}}/></label>
        <label>{t('Search ledger', 'बही में खोजें')}<input value={q} maxLength="120"
          onChange={e => {setQuery(e.target.value); setOffset(0);}}/></label>
      </div>
      <Notice state={records} t={t}/>
      {records.data && <>
        <dl className="live-totals">{Object.entries(records.data.totals).map(([key, value]) => {
          const titles = {opening_paise:['Opening', 'आरंभिक शेष'], earnings_paise:['Earned', 'कमाई'],
            advances_paise:['Advances', 'अग्रिम'], payments_paise:['Payments', 'भुगतान'],
            adjustments_paise:['Corrections', 'सुधार'], closing_paise:['Closing balance', 'अंतिम शेष']};
          return <div key={key}><dt>{t(...titles[key])}</dt><dd>{money(value)}</dd></div>;
        })}</dl>
        {records.data.items.length ? <>
          <ul className="live-list">{records.data.items.map(row => <li key={row.id}>
            <strong>{label(t, row.kind)} · {money(row.amount_paise)}</strong>
            <span>{row.effective_date}{row.worksite_name && ' · ' + row.worksite_name}</span>
            {row.dispute_status && <span className="live-status">{label(t, row.dispute_status)}</span>}
            {row.reversed && <span>{label(t, 'reversed')}</span>}
            <button onClick={() => setEntry(row.id)}>{t('Entry details', 'प्रविष्टि का विवरण')}</button>
          </li>)}</ul>
          {(offset > 0 || offset + 20 < records.data.total) && <Pager offset={offset} limit={20}
            count={records.data.items.length} total={records.data.total} onChange={setOffset} t={t}/>}
        </> : <p>{t('No records in this view.', 'इस दृश्य में कोई प्रविष्टि नहीं है।')}</p>}
      </>}
      <div className="live-actions">
        <label>{t('Statement month', 'विवरण का महीना')}<input type="month" required value={month} onChange={e => setMonth(e.target.value)}/></label>
        <button disabled={action.busy || !month} onClick={() => action.run(download)}>{t('Download monthly CSV', 'मासिक CSV डाउनलोड करें')}</button>
      </div>
      <Notice state={action} t={t}/>
    </section>
    {entry && <EntryDetail key={entry} api={api} entry={entry} version={version} refresh={refresh}
      owner={owner} close={() => setEntry('')} t={t}/>}
  </>;
}

function CorrectionFields({kind, t}) {
  if (kind === 'earning') return <label>{t('Replacement attendance', 'नई उपस्थिति')}
    <select aria-label={t('Replacement attendance', 'नई उपस्थिति')} name="replacement">
      <option value="">{t('Reverse only', 'केवल वापस लें')}</option><option value="0">{t('Absent', 'अनुपस्थित')}</option>
      <option value="1">{t('Half day', 'आधा दिन')}</option><option value="2">{t('Full day', 'पूरा दिन')}</option>
    </select></label>;
  return <label>{t('Replacement amount (INR, optional)', 'नई राशि (रुपये, वैकल्पिक)')}<input name="replacement" inputMode="decimal"/></label>;
}

function replacement(form, kind) {
  const value = form.get('replacement');
  if (!value) return {};
  return kind === 'earning' ? {replace_units: Number(value)} : {replace_amount_paise: parseRupees(value, kind === 'adjustment')};
}

function EntryDetail({api, entry, version, refresh, owner, close, t}) {
  const path = '/ledger/' + entry;
  const {data, ...state} = useRead(api, path, version);
  const action = useAction();
  const [propose, setPropose] = useState(false);
  async function change(suffix, body) {
    await post(api, path + suffix, body);
    refresh();
  }

  return <section className="live-panel" aria-label={t('Ledger record details', 'बही प्रविष्टि का विवरण')}>
    <div className="live-actions">
      <h2>{t('Ledger record details', 'बही प्रविष्टि का विवरण')}</h2>
      <button onClick={close}>{t('Close record', 'प्रविष्टि बंद करें')}</button>
    </div>
    <Notice state={state} t={t}/><Notice state={action} t={t}/>
    {data && <>
      <p><strong>{label(t, data.kind)} · {money(data.amount_paise)}</strong> · {data.effective_date}</p>
      {data.daily_rate_paise && <p>{t('Recorded daily rate', 'दर्ज दैनिक दर')} {money(data.daily_rate_paise)} ·
        {' '}{[t('Absent', 'अनुपस्थित'), t('Half day', 'आधा दिन'), t('Full day', 'पूरा दिन')][data.half_day_units]}</p>}
      {data.notes && <p>{data.notes}</p>}
      <p>{[data.acknowledged && 'acknowledged', data.receipt_confirmed && 'receipt_confirmed',
        data.reversed && 'reversed', data.dispute_status].filter(Boolean).map(value => label(t, value)).join(' · ')}</p>
      <h3>{t('Activity history', 'गतिविधि का इतिहास')}</h3>
      <ol className="live-history">{data.history.map((event, i) => <li key={i}>
        <strong>{label(t, event.kind)}</strong> · {new Date(event.created_at).toLocaleString()} · <code>{event.actor_id}</code>
        {event.details.reason && <p>{event.details.reason}</p>}
        {event.details.notes && <p>{event.details.notes}</p>}
        {event.details.replace_units !== undefined && event.details.replace_units !== null && <p>
          {t('Proposed attendance', 'प्रस्तावित उपस्थिति')}{' '}
          {[t('Absent', 'अनुपस्थित'), t('Half day', 'आधा दिन'), t('Full day', 'पूरा दिन')][event.details.replace_units]}
        </p>}
        {event.details.replace_amount_paise && <p>{t('Proposed amount', 'प्रस्तावित राशि')} {money(event.details.replace_amount_paise)}</p>}
        {event.kind === 'correction_proposed' && event.details.replace_units == null && event.details.replace_amount_paise == null
          && <p>{t('Reverse only', 'केवल वापस लें')}</p>}
      </li>)}</ol>
      {!owner && <div className="live-actions">
        {!data.acknowledged && <button disabled={action.busy} onClick={() => action.run(() => change('/reviews/acknowledged'))}>
          {t('Acknowledge review', 'समीक्षा की पुष्टि करें')}
        </button>}
        {!data.reversed && !data.receipt_confirmed && ['advance','payment'].includes(data.kind) && <button disabled={action.busy}
          onClick={() => action.run(() => change('/reviews/receipt_confirmed'))}>{t('Confirm money received', 'राशि मिलने की पुष्टि करें')}</button>}
      </div>}
      {!owner && !data.reversed && data.kind !== 'reversal' && !data.dispute_status &&
        <Form t={t} button={t('Raise dispute', 'विवाद दर्ज करें')} onSave={form => change('/dispute', {reason: form.get('reason')})}>
          {postReason({t})}
        </Form>}
      {owner && !data.reversed && data.kind !== 'reversal' && (!data.dispute_status || data.dispute_status === 'resolved') &&
        <Form t={t} button={t('Reverse entry', 'प्रविष्टि वापस लें')} onSave={form => {
          if (window.confirm(t('Reverse this entry and keep its history?', 'प्रविष्टि वापस लेकर इतिहास बनाए रखें?'))) {
            return change('/reverse', {reason: form.get('reason'), ...replacement(form, data.kind)});
          }
        }}>
          {postReason({t})}<CorrectionFields kind={data.kind} t={t}/>
        </Form>}
      {owner && ['disputed','response_rejected'].includes(data.dispute_status) &&
        <Form t={t} button={t('Send dispute response', 'विवाद का उत्तर भेजें')} onSave={async form => {
          await change('/dispute/respond', {reason: form.get('reason'), correct: propose,
            ...(propose ? replacement(form, data.kind) : {})});
          setPropose(false);
        }}>
          {postReason({label:t('Response', 'उत्तर'), t})}
          <label><input type="checkbox" checked={propose} onChange={e => setPropose(e.target.checked)}/>
            {t('Propose a correction', 'सुधार का प्रस्ताव दें')}</label>
          {propose && <CorrectionFields kind={data.kind} t={t}/>}
        </Form>}
      {!owner && ['responded','correction_proposed'].includes(data.dispute_status) &&
        <Form t={t} button={t('Submit dispute decision', 'विवाद का निर्णय भेजें')} onSave={form => change('/dispute/decide',
          {accept: form.get('decision') === 'accept', notes: form.get('notes')})}>
          <label>{t('Decision', 'निर्णय')}<select aria-label={t('Decision', 'निर्णय')} name="decision">
            <option value="accept">{t('Accept and resolve', 'स्वीकार करके हल करें')}</option>
            <option value="decline">{t('Decline and request another response', 'अस्वीकार करके नया उत्तर माँगें')}</option>
          </select></label>
          {postReason({field:'notes', label:t('Decision note', 'निर्णय का नोट'), required:false, t})}
        </Form>}
    </>}
  </section>;
}
