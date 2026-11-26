"""Capture real browser flows against a disposable CI database, never production."""
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
from pathlib import Path
import time
from uuid import uuid4
from playwright.sync_api import sync_playwright, expect

CAPTURE_DATE = datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat()
OUTPUT = Path('docs/screenshots')
OUTPUT.mkdir(parents=True, exist_ok=True)
MEDIA = Path('docs/demo')
MEDIA.mkdir(parents=True, exist_ok=True)


def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width':1280,'height':800},
            record_video_dir=str(MEDIA/'raw'), record_video_size={'width':1280,'height':800},
            reduced_motion='reduce')
        page = context.new_page()
        errors=[]
        page.on('pageerror', lambda error: errors.append(str(error)))
        started=time.monotonic()

        def chapter(title, text):
            page.evaluate('''([title,text]) => {
              let el=document.getElementById('recording-caption');
              if(!el){el=document.createElement('aside');el.id='recording-caption';document.body.appendChild(el);}
              Object.assign(el.style,{position:'fixed',bottom:'0',left:'0',right:'0',zIndex:'99999',
                background:'#17202a',color:'white',padding:'14px 28px',font:'16px Arial',pointerEvents:'none'});
              el.replaceChildren();const heading=document.createElement('strong');heading.textContent=title;
              const line=document.createElement('div');line.textContent=text;el.append(heading,line);
            }''',[title,text])

        def until(seconds):
            page.wait_for_timeout(max(0,seconds-(time.monotonic()-started))*1000)

        def screenshot(name):
            page.screenshot(path=str(OUTPUT/name),full_page=True,animations='disabled')

        def signup(email,role):
            page.get_by_role('button',name='Create an account',exact=True).click()
            page.get_by_label('Email',exact=True).fill(email)
            page.get_by_label('Password',exact=True).fill('Disposable-demo-password-2026')
            page.get_by_label('Role',exact=True).select_option(role)
            page.get_by_role('button',name='Create account and sign in',exact=True).click()
            expect(page.get_by_role('button',name='Sign out',exact=True)).to_be_visible()

        page.goto('http://127.0.0.1:8080',wait_until='networkidle')
        chapter('Worker Wage Tracker · development progress · '+CAPTURE_DATE,
                'Real browser + disposable PostgreSQL. Partial build; no public deployment or live payroll.')
        screenshot('01-landing.png')
        until(12)
        page.get_by_role('button',name='Open workspace',exact=True).first.click()
        expect(page.get_by_role('heading',name='Sign in',exact=True)).to_be_visible()
        chapter('01 · Live authentication', 'Contractor signup uses the real API, Argon2 hashing and an in-memory JWT.')
        screenshot('02-sign-in.png')
        until(25)
        email='contractor-'+uuid4().hex[:8]+'@example.com'
        signup(email,'contractor')
        expect(page.get_by_text('No worksites found.',exact=True)).to_be_visible()
        chapter('02 · Contractor workspace', 'This empty list is loaded from PostgreSQL for the new contractor.')
        screenshot('03-empty-workspace.png')
        until(38)
        page.get_by_label('Name',exact=True).fill('Jaipur demonstration site')
        page.get_by_label('Location',exact=True).fill('Jaipur · synthetic demonstration data')
        page.get_by_role('button',name='Create worksite',exact=True).click()
        expect(page.get_by_role('button',name='Jaipur demonstration site',exact=True)).to_be_visible()
        chapter('03 · Create and search', 'The worksite is persisted by the authenticated API; this is not the sample dashboard.')
        screenshot('04-created-worksite.png')
        until(52)
        page.get_by_label('Search worksites',exact=True).fill('Jaipur')
        page.get_by_role('button',name='Jaipur demonstration site',exact=True).click()
        expect(page.get_by_role('heading',name='Edit worksite',exact=True)).to_be_visible()
        chapter('04 · Details and editing', 'Worksite details come from the live API. Other contractors cannot access this record.')
        screenshot('05-worksite-detail.png')
        until(66)
        page.get_by_label('Name',exact=True).fill('Jaipur updated site')
        page.get_by_role('button',name='Save changes',exact=True).click()
        expect(page.get_by_role('button',name='Jaipur updated site',exact=True)).to_be_visible()
        page.get_by_role('button',name='Sign out',exact=True).click()
        # The signup form remains selected after sign-out. Switch explicitly to login.
        if page.get_by_role('button',name='Already registered? Sign in',exact=True).is_visible():
            page.get_by_role('button',name='Already registered? Sign in',exact=True).click()
        page.get_by_label('Email',exact=True).fill(email)
        page.get_by_label('Password',exact=True).fill('Disposable-demo-password-2026')
        page.get_by_role('button',name='Sign in',exact=True).click()
        expect(page.get_by_role('button',name='Jaipur updated site',exact=True)).to_be_visible()
        chapter('05 · Sign out and return', 'Signing in again retrieves the saved worksite. The JWT is cleared on sign-out.')
        until(82)
        page.get_by_role('button',name='Jaipur updated site',exact=True).click()
        page.once('dialog',lambda dialog:dialog.accept())
        page.get_by_role('button',name='Delete worksite',exact=True).click()
        expect(page.get_by_text('No worksites found.',exact=True)).to_be_visible()
        assert context.request.get('http://127.0.0.1:8080/api/worksites').status==401
        chapter('06 · Eligible deletion and route protection', 'The unassigned site is deleted; unauthenticated API access returns 401.')
        until(96)
        page.get_by_role('button',name='Sign out',exact=True).click()
        signup('worker-'+uuid4().hex[:8]+'@example.com','worker')
        expect(page.get_by_role('heading',name='Worker account',exact=True)).to_be_visible()
        chapter('07 · Honest worker view', 'Worker signup works. Attendance and wage screens are still unimplemented in the live UI.')
        screenshot('06-worker-account.png')
        until(108)
        chapter('Next: attendance, payments, reversals and disputes',
                'Assignment/rate APIs are tested separately. Hosting, pilot validation and a full product launch remain unfinished.')
        until(121)
        assert not errors,errors
        video=page.video
        context.close()
        video.save_as(str(MEDIA/'browser-recording.webm'))
        browser.close()
        (MEDIA/'capture.json').write_text(json.dumps({'source_commit':os.environ.get('GITHUB_SHA'),
            'capture_date':CAPTURE_DATE,'duration_target_seconds':120,
            'scope':'Browser-verified partial build; synthetic accounts; no financial workflow or public deployment',
            'checks':['contractor signup','worksite create/search/detail/update/delete','sign out/login persistence',
                      'unauthenticated 401','worker signup','no browser page errors']},indent=2)+'\n')
        print('PASS: browser authentication, persisted worksite CRUD, sign-out/login and worker signup')


if __name__=='__main__':
    capture()
