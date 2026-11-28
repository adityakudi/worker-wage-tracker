import React, {useCallback, useEffect, useReducer, useState} from 'react';
import {RecordsWorkspace, useAction} from './RecordsWorkspace';

export default function LiveApp() {
  const [language, setLanguage] = useState('en');
  const [token, setToken] = useState('');
  const [user, setUser] = useState(null);
  const [signup, setSignup] = useState(false);
  const [tab, setTab] = useState('worksites');
  const t = (en, hi) => language === 'hi' ? hi : en;
  const signOut = useCallback(() => {
    setUser(null);
    setToken('');
    setSignup(false);
    setTab('worksites');
  }, []);
  const api = useCallback(async (path, options = {}) => {
    const base = import.meta.env.VITE_API_BASE_URL || '/api';
    if (!import.meta.env.VITE_API_BASE_URL && !['localhost', '127.0.0.1'].includes(location.hostname)) {
      throw Error('The API is unavailable in this preview. Open the hosted application or use the sample workspace.');
    }
    const response = await fetch(base + path, {
      ...options,
      headers: {'Content-Type': 'application/json',
        ...(token ? {Authorization: 'Bearer ' + token} : {}), ...options.headers},
    });
    if (response.status === 204) return null;
    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await response.json() : await response.text();
    if (!response.ok) {
      if (response.status === 401 && token) signOut();
      const validation = Array.isArray(data?.detail) ? data.detail.map(item => item.msg).join(' · ') : '';
      throw Error(typeof data?.detail === 'string' ? data.detail : validation || 'The server could not complete that request.');
    }
    return data;
  }, [token, signOut]);
  const auth = useAction();

  async function authenticate(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const credentials = {email: form.get('email'), password: form.get('password')};
    await auth.run(async () => {
      if (signup) await api('/auth/signup', {method: 'POST', body: JSON.stringify({...credentials, role: form.get('role')})});
      const {access_token} = await api('/auth/login', {method: 'POST', body: JSON.stringify(credentials)});
      const identity = await api('/auth/me', {headers: {Authorization: 'Bearer ' + access_token}});
      setTab(identity.role === 'worker' ? 'records' : 'worksites');
      setUser(identity);
      setToken(access_token);
    });
  }

  return <main lang={language} className="live-app">
    <header className="live-header">
      <span>WORKER WAGE TRACKER</span>
      <label>{t('Language', 'भाषा')} <select value={language} onChange={e => setLanguage(e.target.value)}>
        <option value="en">English</option><option value="hi">हिन्दी</option>
      </select></label>
      {user && <button onClick={signOut}>{t('Sign out', 'साइन आउट')}</button>}
    </header>
    <h1>{user ? t('Your workspace', 'आपका कार्यक्षेत्र') : t('Work recorded. Wages clear.', 'काम का हिसाब, मज़दूरी साफ़।')}</h1>
    {!user ? <section className="live-panel">
      <h2>{signup ? t('Create an account', 'खाता बनाएँ') : t('Sign in', 'साइन इन')}</h2>
      {auth.error && <p role="alert">{auth.error}</p>}
      <form onSubmit={authenticate}>
        <label>{t('Email', 'ईमेल')}<input name="email" type="email" required autoComplete="email"/></label>
        <label>{t('Password', 'पासवर्ड')}<input name="password" type="password" minLength="10" maxLength="128" required
          autoComplete={signup ? 'new-password' : 'current-password'}/></label>
        {signup && <label>{t('Role', 'भूमिका')}<select name="role" aria-label={t('Role', 'भूमिका')}>
          <option value="worker">{t('Worker', 'कामगार')}</option>
          <option value="contractor">{t('Contractor', 'ठेकेदार')}</option>
        </select></label>}
        <button disabled={auth.busy}>{auth.busy ? t('Please wait…', 'कृपया प्रतीक्षा करें…')
          : signup ? t('Create account and sign in', 'खाता बनाएँ और साइन इन करें') : t('Sign in', 'साइन इन')}</button>
      </form>
      <button disabled={auth.busy} onClick={() => {setSignup(!signup); auth.clear();}}>
        {signup ? t('Already registered? Sign in', 'पहले से खाता है? साइन इन करें') : t('Create an account', 'खाता बनाएँ')}
      </button>
    </section> : <>
      <div className="live-account">
        <strong>{user.email}</strong> · {user.role === 'worker' ? t('Worker', 'कामगार') : t('Contractor', 'ठेकेदार')}
        {user.role === 'worker' && <p>{t('Your worker ID', 'आपकी कामगार आईडी')} <code>{user.id}</code></p>}
      </div>
      {user.role === 'contractor' && <nav className="live-tabs" aria-label={t('Workspace sections', 'कार्य क्षेत्र')}>
        <button aria-pressed={tab === 'worksites'} onClick={() => setTab('worksites')}>{t('Worksites', 'कार्यस्थल')}</button>
        <button aria-pressed={tab === 'records'} onClick={() => setTab('records')}>{t('Workers & wages', 'कामगार और मज़दूरी')}</button>
      </nav>}
      {tab === 'worksites' && user.role === 'contractor'
        ? <Worksites api={api} t={t}/>
        : <RecordsWorkspace api={api} user={user} t={t}/>}
    </>}
  </main>;
}

function Worksites({api, t}) {
  const [page, setPage] = useState(null);
  const [q, setQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [failure, setFailure] = useState('');
  const [version, refresh] = useReducer(n => n + 1, 0);
  const action = useAction();

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setFailure('');
    api('/worksites?' + new URLSearchParams({q, limit: '20', offset}), {signal: controller.signal})
      .then(setPage)
      .catch(error => {if (!controller.signal.aborted) setFailure(error.message);})
      .finally(() => {if (!controller.signal.aborted) setLoading(false);});
    return () => controller.abort();
  }, [api, q, offset, version]);

  function save(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    action.run(async () => {
      await api(selected ? '/worksites/' + selected.id : '/worksites', {
        method: selected ? 'PUT' : 'POST',
        body: JSON.stringify({name: fields.get('name'), location: fields.get('location'), active: fields.has('active')}),
      });
      setSelected(null);
      form.reset();
      setOffset(0);
      refresh();
    });
  }

  function remove() {
    if (!selected || !window.confirm(t('Delete this worksite?', 'यह कार्यस्थल मिटाएँ?'))) return;
    action.run(async () => {
      await api('/worksites/' + selected.id, {method: 'DELETE'});
      setSelected(null);
      setOffset(0);
      refresh();
    });
  }

  return <section className="live-panel">
    <h2>{t('Worksites', 'कार्यस्थल')}</h2>
    {action.error && <p role="alert">{action.error}</p>}
    <form key={selected?.id || 'new'} onSubmit={save} className="live-form">
      <h3>{selected ? t('Edit worksite', 'कार्यस्थल संपादित करें') : t('Add worksite', 'कार्यस्थल जोड़ें')}</h3>
      <label>{t('Name', 'नाम')}<input name="name" required maxLength="120" defaultValue={selected?.name || ''}/></label>
      <label>{t('Location', 'स्थान')}<input name="location" maxLength="300" defaultValue={selected?.location || ''}/></label>
      <label><input name="active" type="checkbox" defaultChecked={selected?.active ?? true}/>{t('Active', 'सक्रिय')}</label>
      <div className="live-actions">
        <button disabled={action.busy}>{selected ? t('Save changes', 'बदलाव सहेजें') : t('Create worksite', 'कार्यस्थल बनाएँ')}</button>
        {selected && <>
          <button type="button" onClick={() => setSelected(null)}>{t('Cancel edit', 'संपादन रद्द करें')}</button>
          <button type="button" disabled={action.busy} onClick={remove}>{t('Delete worksite', 'कार्यस्थल मिटाएँ')}</button>
        </>}
      </div>
    </form>
    <label>{t('Search worksites', 'कार्यस्थल खोजें')}<input value={q} onChange={e => {setQuery(e.target.value); setOffset(0);}}/></label>
    {loading && <p role="status">{t('Loading…', 'लोड हो रहा है…')}</p>}
    {failure && <p role="alert">{failure}</p>}
    {!loading && !failure && (page?.items.length ? <ul className="live-list">{page.items.map(site => <li key={site.id}>
      <button onClick={() => action.run(async () => setSelected(await api('/worksites/' + site.id)))}>{site.name}</button>
      <span>{site.active ? t('Active', 'सक्रिय') : t('Inactive', 'निष्क्रिय')}</span>
    </li>)}</ul> : <p>{t('No worksites found.', 'कोई कार्यस्थल नहीं मिला।')}</p>)}
    <nav className="live-actions">
      <button disabled={loading || offset === 0} onClick={() => setOffset(offset - 20)}>{t('Previous', 'पिछला')}</button>
      <span>{page?.total ?? 0} {t('results', 'परिणाम')}</span>
      <button disabled={loading || offset + 20 >= (page?.total ?? 0)} onClick={() => setOffset(offset + 20)}>{t('Next', 'अगला')}</button>
    </nav>
    {selected && <article>
      <h3>{selected.name}</h3><p>{selected.location || t('No location provided', 'स्थान दर्ज नहीं है')}</p>
      <button onClick={() => setSelected(null)}>{t('Close details', 'विवरण बंद करें')}</button>
    </article>}
  </section>;
}
